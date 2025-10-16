"""
Unified voice request handler that works across all platforms.

This module contains platform-agnostic business logic for handling voice requests.
"""
import re
import json
import datetime
from typing import Optional, Dict, Any, List

from voice_assistant_adapter import VoiceRequest, VoiceResponse, VoiceAssistantPlatform
from logger import logger, log_request, log_error
import overseerr
from overseerr import OverseerrError, OverseerrConnectionError, OverseerrAuthError
from db import db_session, SessionState
from enhanced_search import search_enhancer


# ==========================================
# JSON Encoder for Date Objects
# ==========================================

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date and datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


# ==========================================
# Helper Functions
# ==========================================

def media_type_from_text(text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract media type from spoken text and preserve user's terminology.

    Returns:
        tuple: (media_type, user_term) where:
            - media_type is 'movie' or 'tv' for API calls
            - user_term is 'film', 'movie', 'TV show', etc. for speech responses
    """
    if not text:
        return None, None
    t = text.lower()
    if 'tv' in t:
        return 'tv', 'TV show'
    if 'show' in t or 'series' in t:
        return 'tv', 'show'
    if 'film' in t:
        return 'movie', 'film'
    if 'movie' in t:
        return 'movie', 'movie'
    return None, None


def build_speech_for_item(item: Dict[str, Any], prefix: str = "I found", user_term: Optional[str] = None) -> str:
    """
    Generate speech for a search result item with availability status.

    Args:
        item: The search result item
        prefix: Opening phrase (default "I found")
        user_term: User's preferred terminology (e.g., "film", "movie", "show")
    """
    from datetime import datetime

    title = item.get('_title') or item.get('title') or item.get('name') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    release_date_str = item.get('_releaseDate')
    is_unreleased = False

    if release_date_str:
        year = release_date_str[:4]
        try:
            # Check if release date is in the future
            release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
            now = datetime.now(release_date.tzinfo) if release_date.tzinfo else datetime.now()
            is_unreleased = release_date > now
        except (ValueError, AttributeError):
            pass

    # Use user's preferred term if provided, otherwise default
    if user_term and mtype == 'movie':
        type_word = user_term
    elif user_term and mtype == 'tv':
        type_word = user_term
    else:
        type_word = 'movie' if mtype == 'movie' else 'TV show'

    # Build base speech
    if year:
        if is_unreleased:
            speech = f"{prefix} the {type_word} {title}, releasing in {year}"
        else:
            speech = f"{prefix} the {type_word} {title}, released in {year}"
    else:
        speech = f"{prefix} the {type_word} {title}"

    # Add availability status and appropriate question
    if item.get('_isAvailable'):
        speech += ". This is already in your library. Were you thinking of a different one?"
        # Note: If they say "No" = correct one, "Yes" = show next
    elif item.get('_isPartiallyAvailable'):
        speech += ". This is partially in your library. Is that the one you want?"
    elif item.get('_isProcessing'):
        speech += ". This is currently being downloaded. Is that the one you want?"
    elif item.get('_isPending'):
        speech += ". This has already been requested and is pending approval. Is that the one you want?"
    elif is_unreleased:
        # Not released yet and not in library
        speech += ". That hasn't been released yet. Would you like to request it anyway?"
    else:
        # Standard case - not available, not pending, ready to request
        speech += ". Is that the one you want?"

    return speech


def build_speech_for_next(item: Dict[str, Any], user_term: Optional[str] = None) -> str:
    """
    Generate speech for the next alternative result.

    Args:
        item: The search result item
        user_term: User's preferred terminology (e.g., "film", "movie", "show")
    """
    title = item.get('_title') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]

    # Use user's preferred term if provided, otherwise default
    if user_term and mtype == 'movie':
        type_word = user_term
    elif user_term and mtype == 'tv':
        type_word = user_term
    else:
        type_word = 'movie' if mtype == 'movie' else 'TV show'

    if year:
        return f"What about the {type_word} {title}, released in {year}?"
    else:
        return f"What about the {type_word} {title}?"


def build_availability_message(item: Dict[str, Any], season_number: Optional[int] = None) -> str:
    """Build message about when content will be available based on release date"""
    from datetime import datetime

    release_date_str = item.get('_releaseDate')

    if not release_date_str:
        # No release date - use generic message
        return "It should be available soon."

    try:
        # Parse the release date
        release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
        now = datetime.now(release_date.tzinfo) if release_date.tzinfo else datetime.now()

        # Check if already released
        if release_date <= now:
            return "It should be available soon."

        # Not released yet - format the date for speech
        # Format: "October 20th" or "October 20th, 2026" (include year if not current year)
        day = release_date.day
        month = release_date.strftime('%B')  # Full month name
        year = release_date.year
        current_year = now.year

        # Add ordinal suffix (st, nd, rd, th)
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

        date_spoken = f"{month} {day}{suffix}"
        if year != current_year:
            date_spoken += f", {year}"

        return f"It'll be downloaded once it's released, which we're expecting to be on {date_spoken}."

    except (ValueError, AttributeError):
        # Error parsing date - use generic message
        return "It should be available soon."


def save_state(user_id: str, conversation_id: str, state: Dict[str, Any]):
    """Save conversation state to database"""
    with db_session() as s:
        existing = (
            s.query(SessionState)
            .filter(
                SessionState.user_id == user_id,
                SessionState.conversation_id == conversation_id
            )
            .one_or_none()
        )
        payload = json.dumps(state, cls=DateTimeEncoder)
        if existing:
            existing.state_json = payload
        else:
            row = SessionState(
                user_id=user_id,
                conversation_id=conversation_id,
                state_json=payload
            )
            s.add(row)


def load_state(user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load conversation state from database"""
    with db_session() as s:
        row = (
            s.query(SessionState)
            .filter(
                SessionState.user_id == user_id,
                SessionState.conversation_id == conversation_id
            )
            .one_or_none()
        )
        if row:
            try:
                return json.loads(row.state_json)
            except Exception as e:
                log_error("Failed to parse session state", e, user_id=user_id)
                return None
        return None


# ==========================================
# Unified Intent Handlers
# ==========================================

class UnifiedVoiceHandler:
    """Platform-agnostic voice request handler"""

    def handle_launch(self, request: VoiceRequest) -> VoiceResponse:
        """Handle skill/action launch"""
        log_request("Launch", request.user_id, platform=request.platform.value)

        speech = (
            "Welcome to Overtalkerr! You can say things like, "
            "download the movie Jurassic World, or download the upcoming TV show Robin Hood. "
            "You can also request specific seasons, like download season 2 of Breaking Bad. "
            "What would you like to download?"
        )

        return VoiceResponse(
            speech=speech,
            reprompt="What would you like to download?",
            card_title="Overtalkerr",
            card_text=speech
        )

    def handle_download(self, request: VoiceRequest) -> VoiceResponse:
        """Handle download/request intent with enhanced search"""
        log_request(
            "Download",
            request.user_id,
            platform=request.platform.value,
            slots=request.slots
        )

        # Extract slots (normalized across platforms)
        media_title = request.slots.get('MediaTitle') or request.slots.get('title')
        year = request.slots.get('Year') or request.slots.get('year')
        media_type_text = request.slots.get('MediaType') or request.slots.get('mediaType')
        upcoming_text = request.slots.get('Upcoming') or request.slots.get('upcoming')
        season_text = request.slots.get('Season') or request.slots.get('season')

        if not media_title:
            speech = "Please tell me the title. For example, say download the movie Jurassic World from 2015."
            return VoiceResponse(
                speech=speech,
                reprompt=speech
            )

        # 🚀 ENHANCED SEARCH: Parse query with NLP
        parsed_query = search_enhancer.parse_enhanced_query(media_title)
        enhanced_title = parsed_query['cleaned_query']

        logger.info(f"Enhanced search: '{media_title}' -> '{enhanced_title}'", extra=parsed_query)

        # Normalize inputs and extract user's preferred terminology
        media_type, user_term = media_type_from_text(media_type_text)

        # Also check the title itself for terminology (e.g., "download the film Superman")
        if not user_term and media_title:
            _, user_term_from_title = media_type_from_text(media_title)
            if user_term_from_title:
                user_term = user_term_from_title

        upcoming_only = False

        if upcoming_text:
            upcoming_only = str(upcoming_text).lower() in ['yes', 'true', '1', 'upcoming']

        # Check if "upcoming" is in the title itself
        if media_title and re.search(r"\bupcoming\b", media_title, re.IGNORECASE):
            upcoming_only = True

        # Use temporal filter from enhanced search if available
        if parsed_query['temporal']:
            if parsed_query['temporal']['type'] == 'relative' and parsed_query['temporal']['days'] < 0:
                upcoming_only = True
            elif parsed_query['temporal']['type'] == 'year' and not year:
                year = str(parsed_query['temporal']['year'])

        # Normalize year
        year_filter = None
        if year:
            m = re.search(r"(\d{4})", str(year))
            if m:
                year_filter = m.group(1)

        # Extract season number
        season_number = None
        if season_text:
            m = re.search(r"(\d+)", str(season_text))
            if m:
                season_number = int(m.group(1))

        # Search Overseerr
        try:
            results = overseerr.search(enhanced_title, media_type)
        except OverseerrConnectionError:
            speech = "I can't reach the media server right now. Check your connection and try again."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrAuthError:
            speech = "There's an authentication problem with the media server. Contact your administrator to fix this."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrError as e:
            log_error("Overseerr search failed", e, user_id=request.user_id, title=enhanced_title)
            speech = "Something went wrong with that search. Try a different title or try again in a moment."
            return VoiceResponse(speech=speech, should_end_session=True)

        # 🚀 ENHANCED SEARCH: Apply fuzzy matching for better results
        original_results_count = len(results) if results else 0
        if results:
            results_before_fuzzy = results.copy()  # Keep original for "did you mean" suggestions
            results = search_enhancer.fuzzy_match_results(enhanced_title, results, threshold=60)

        # Filter and rank results
        ranked = overseerr.pick_best(results, upcoming_only=upcoming_only, year_filter=year_filter)

        # If year filter yielded no results, try again without it
        if not ranked and year_filter:
            logger.info(f"No results with year filter {year_filter}, retrying without year")
            ranked_without_year = overseerr.pick_best(results, upcoming_only=upcoming_only, year_filter=None)

            if ranked_without_year:
                # Found results from other years - offer them
                first = ranked_without_year[0]
                year_from_result = None
                if first.get('_releaseDate'):
                    year_from_result = first['_releaseDate'][:4]

                if year_from_result:
                    speech = f"I couldn't find '{media_title}' from {year_filter}, but I found results from other years. Would you like to hear them?"
                else:
                    speech = f"I couldn't find '{media_title}' from {year_filter}, but I found other results. Would you like to hear them?"

                # Save state with results (but without year filter for future navigation)
                state = {
                    'query': media_title,
                    'media_type': media_type,
                    'year': None,  # Clear year filter since we're offering non-filtered results
                    'upcoming_only': upcoming_only,
                    'season': season_number,
                    'results': ranked_without_year,
                    'index': 0,
                    'user_term': user_term,
                    'pending_year_filter_question': True,  # Flag to know user needs to confirm
                }
                save_state(request.user_id, request.session_id, state)

                return VoiceResponse(
                    speech=speech,
                    reprompt="Would you like to hear results from other years?",
                    card_title="Overtalkerr",
                    card_text=speech
                )

        if not ranked:
            # Check if we had results before fuzzy filtering - suggest the closest match
            if original_results_count > 0 and 'results_before_fuzzy' in locals():
                from rapidfuzz import fuzz
                # Find the best match from original results
                best_match = None
                best_score = 0
                for result in results_before_fuzzy:
                    title = result.get('_title') or result.get('title') or result.get('name', '')
                    score = fuzz.ratio(enhanced_title.lower(), title.lower())
                    if score > best_score:
                        best_score = score
                        best_match = result

                # If we found a reasonable match (above 40% similarity), suggest it
                if best_match and best_score > 40:
                    suggested_title = best_match.get('_title') or best_match.get('title') or best_match.get('name')
                    speech = f"I couldn't find '{media_title}'. Did you mean '{suggested_title}'?"

                    # Save state with the suggestion
                    state = {
                        'query': suggested_title,  # Use the suggested title
                        'media_type': media_type,
                        'year': year_filter,
                        'upcoming_only': upcoming_only,
                        'season': season_number,
                        'results': [best_match],  # Just this one result
                        'index': 0,
                        'user_term': user_term,
                        'pending_did_you_mean_question': True,  # Flag for confirmation
                    }
                    save_state(request.user_id, request.session_id, state)

                    return VoiceResponse(
                        speech=speech,
                        reprompt=f"Did you mean '{suggested_title}'?",
                        card_title="Overtalkerr",
                        card_text=speech
                    )

            speech = f"I couldn't find any matches for '{media_title}'. Try rephrasing or being more specific."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if we have mixed media types and user didn't specify
        if not media_type and len(ranked) > 1:
            media_types_in_results = set()
            for result in ranked:
                mtype = result.get('_mediaType')
                if mtype:
                    media_types_in_results.add(mtype)

            # If we have both movies and TV shows
            if len(media_types_in_results) > 1 and 'movie' in media_types_in_results and 'tv' in media_types_in_results:
                # Find the newest result (by release date)
                newest = None
                newest_date = None
                for result in ranked:
                    release_date_str = result.get('_releaseDate')
                    if release_date_str:
                        try:
                            from datetime import datetime
                            release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
                            if newest_date is None or release_date > newest_date:
                                newest_date = release_date
                                newest = result
                        except:
                            pass

                # If we couldn't determine by date, use first result
                if not newest:
                    newest = ranked[0]

                newest_type = newest.get('_mediaType')
                newest_title = newest.get('_title') or newest.get('title') or newest.get('name')
                year = None
                if newest.get('_releaseDate'):
                    year = newest['_releaseDate'][:4]

                # Determine term to use
                type_term = user_term if user_term else ('movie' if newest_type == 'movie' else 'TV show')

                # Ask clarification based on newest result type
                if year:
                    speech = f"Is it a {type_term} named {newest_title} from {year} you're looking for?"
                else:
                    speech = f"Is it a {type_term} named {newest_title} you're looking for?"

                # Save state with pending clarification
                state = {
                    'query': media_title,
                    'media_type': None,  # Not yet determined
                    'year': year_filter,
                    'upcoming_only': upcoming_only,
                    'season': season_number,
                    'results': ranked,
                    'index': 0,
                    'user_term': user_term,
                    'pending_media_type_clarification': True,
                    'clarification_type': newest_type,  # Type we asked about
                }
                save_state(request.user_id, request.session_id, state)

                return VoiceResponse(
                    speech=speech,
                    reprompt=f"Is it the {type_term} {newest_title}?",
                    card_title="Overtalkerr",
                    card_text=speech
                )

        # Save state
        state = {
            'query': media_title,
            'media_type': media_type,
            'year': year_filter,
            'upcoming_only': upcoming_only,
            'season': season_number,
            'results': ranked,
            'index': 0,
            'user_term': user_term,  # Store user's preferred terminology
        }
        save_state(request.user_id, request.session_id, state)

        # Build response
        first = ranked[0]
        speech = build_speech_for_item(first, "I found", user_term=user_term)

        return VoiceResponse(
            speech=speech,
            reprompt="Is that the one you want?",
            card_title="Overtalkerr",
            card_text=speech
        )

    def handle_yes(self, request: VoiceRequest) -> VoiceResponse:
        """Handle yes/confirm intent"""
        log_request("Yes", request.user_id, platform=request.platform.value)

        state = load_state(request.user_id, request.session_id)

        if not state:
            speech = "I don't have an active search. Please say a title to start a new download request."
            return VoiceResponse(
                speech=speech,
                reprompt="What would you like to download?"
            )

        # Check if user is confirming media type clarification
        if state.get('pending_media_type_clarification'):
            # User said yes - they want the type we asked about
            clarification_type = state.get('clarification_type')
            results = state.get('results', [])

            # Filter results to only that type
            filtered_results = [r for r in results if r.get('_mediaType') == clarification_type]

            if filtered_results:
                # Update state with filtered results
                state['pending_media_type_clarification'] = False
                state['results'] = filtered_results
                state['index'] = 0
                state['media_type'] = clarification_type
                save_state(request.user_id, request.session_id, state)

                # Present the first result of that type
                first = filtered_results[0]
                user_term = state.get('user_term')
                speech = build_speech_for_item(first, "I found", user_term=user_term)
                return VoiceResponse(
                    speech=speech,
                    reprompt="Is that the one you want?",
                    card_title="Overtalkerr",
                    card_text=speech
                )
            else:
                speech = "I don't have any results of that type. Try a new search."
                return VoiceResponse(speech=speech, should_end_session=True)

        # Check if user is confirming they want to hear results from other years
        if state.get('pending_year_filter_question'):
            # User said yes to hearing results from other years
            state['pending_year_filter_question'] = False
            save_state(request.user_id, request.session_id, state)

            # Present the first result
            results = state.get('results', [])
            user_term = state.get('user_term')
            if results:
                first = results[0]
                speech = build_speech_for_item(first, "I found", user_term=user_term)
                return VoiceResponse(
                    speech=speech,
                    reprompt="Is that the one you want?",
                    card_title="Overtalkerr",
                    card_text=speech
                )
            else:
                speech = "I don't have any results to show. Try a new search."
                return VoiceResponse(speech=speech, should_end_session=True)

        # Check if user is confirming the "did you mean" suggestion
        if state.get('pending_did_you_mean_question'):
            # User said yes to the suggested title
            state['pending_did_you_mean_question'] = False
            save_state(request.user_id, request.session_id, state)

            # Present the result
            results = state.get('results', [])
            user_term = state.get('user_term')
            if results:
                first = results[0]
                speech = build_speech_for_item(first, "I found", user_term=user_term)
                return VoiceResponse(
                    speech=speech,
                    reprompt="Is that the one you want?",
                    card_title="Overtalkerr",
                    card_text=speech
                )
            else:
                speech = "I don't have that result anymore. Start a new search."
                return VoiceResponse(speech=speech, should_end_session=True)

        idx = state.get('index', 0)
        results = state.get('results', [])

        if idx >= len(results):
            speech = "I've run out of alternatives. Please start a new search."
            return VoiceResponse(speech=speech, should_end_session=True)

        chosen = results[idx]
        media_id = chosen.get('id') or chosen.get('mediaId') or chosen.get('tmdbId')
        media_type = chosen.get('_mediaType') or state.get('media_type') or 'movie'
        season_number = state.get('season')
        title = chosen.get('_title', 'the media')

        if not media_id:
            speech = "I couldn't identify that media. Try searching for a different title."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if media is already available
        if chosen.get('_isAvailable'):
            speech = f"{title} is already in your library! You can watch it now."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if media is being processed
        if chosen.get('_isProcessing'):
            speech = f"{title} is already being downloaded. It should be available soon!"
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if media is pending approval
        if chosen.get('_isPending'):
            speech = f"{title} has already been requested and is waiting for approval."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if partially available (might want to request missing parts)
        if chosen.get('_isPartiallyAvailable'):
            if media_type == 'tv' and season_number:
                # User is requesting a specific season - allow it
                logger.info(f"Requesting specific season {season_number} of partially available show")
            else:
                speech = f"{title} is partially in your library. Some content may already be available."
                # Continue with request but inform the user

        # Create request in backend
        try:
            result = overseerr.request_media(int(media_id), media_type, season=season_number)

            # Check if it was already requested (backend duplicate detection)
            if result.get('message') and 'already requested' in result.get('message', '').lower():
                speech = "Good news! That media has already been requested!"
            else:
                # Build availability message based on release date
                availability_msg = build_availability_message(chosen, season_number)

                if season_number:
                    speech = f"You got it! I've requested season {season_number} of {title}. {availability_msg}"
                else:
                    speech = f"You got it! I've requested {title}. {availability_msg}"

        except OverseerrConnectionError:
            speech = "I can't reach the media server right now. Your request wasn't submitted. Check your connection and try again."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrError as e:
            log_error("Failed to create Overseerr request", e, user_id=request.user_id, media_id=media_id)
            speech = "I couldn't create that request. The server might be busy. Try again in a moment."
            return VoiceResponse(speech=speech, should_end_session=True)

        return VoiceResponse(
            speech=speech,
            card_title="Request Created",
            card_text=speech,
            should_end_session=True
        )

    def handle_no(self, request: VoiceRequest) -> VoiceResponse:
        """Handle no/next intent"""
        log_request("No", request.user_id, platform=request.platform.value)

        state = load_state(request.user_id, request.session_id)

        if not state:
            speech = "Please tell me the title. For example, say download the movie Jurassic World from 2015."
            return VoiceResponse(
                speech=speech,
                reprompt=speech
            )

        # Check if user is declining media type clarification
        if state.get('pending_media_type_clarification'):
            # User said no - they want the OTHER type
            clarification_type = state.get('clarification_type')
            results = state.get('results', [])

            # Filter to the opposite type
            other_type = 'tv' if clarification_type == 'movie' else 'movie'
            filtered_results = [r for r in results if r.get('_mediaType') == other_type]

            if filtered_results:
                # Update state
                state['pending_media_type_clarification'] = False
                state['results'] = filtered_results
                state['index'] = 0
                state['media_type'] = other_type
                save_state(request.user_id, request.session_id, state)

                # Count and present
                count = len(filtered_results)
                other_type_name = 'TV show' if other_type == 'tv' else 'movie'
                plural = 's' if count > 1 else ''

                if count > 1:
                    speech = f"OK, we have {count} {other_type_name}{plural} for you. "
                else:
                    speech = f"OK, we have a {other_type_name} for you. "

                # Present first result
                first = filtered_results[0]
                user_term = state.get('user_term')
                item_speech = build_speech_for_item(first, "", user_term=user_term)  # Empty prefix since we already said "OK, we have..."
                speech += item_speech

                return VoiceResponse(
                    speech=speech,
                    reprompt="Is that the one you want?",
                    card_title="Overtalkerr",
                    card_text=speech
                )
            else:
                speech = "I don't have any results of that type. Try a new search."
                return VoiceResponse(speech=speech, should_end_session=True)

        # Check if user is declining to hear results from other years
        if state.get('pending_year_filter_question'):
            speech = "Okay. Try searching again with a different year or without the year."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if user is declining the "did you mean" suggestion
        if state.get('pending_did_you_mean_question'):
            speech = "Okay. Try searching again with a different title."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Check if current item is already in library (inverted logic)
        # If it's in library and they say "No", that means it's the right one
        idx = state.get('index', 0)
        results = state.get('results', [])

        if idx < len(results):
            current_item = results[idx]
            if current_item.get('_isAvailable'):
                # They said "No" to "Were you thinking of a different one?"
                # This means they WERE thinking of this one, so we're done
                title = current_item.get('_title', 'that title')
                speech = f"Perfect! {title} is ready to watch in your library. Enjoy!"
                return VoiceResponse(speech=speech, should_end_session=True)

        idx = idx + 1

        if idx >= len(results):
            speech = "That's all I could find. Would you like to search for something else?"
            return VoiceResponse(
                speech=speech,
                reprompt="What would you like to download?",
                should_end_session=True
            )

        # Update state
        state['index'] = idx
        save_state(request.user_id, request.session_id, state)

        # Build response
        next_item = results[idx]
        user_term = state.get('user_term')
        speech = build_speech_for_next(next_item, user_term=user_term)

        return VoiceResponse(
            speech=speech,
            reprompt="Is that the one?",
            card_title="Overtalkerr",
            card_text=speech
        )

    def handle_help(self, request: VoiceRequest) -> VoiceResponse:
        """Handle help intent"""
        log_request("Help", request.user_id, platform=request.platform.value)

        speech = (
            "You can say things like: download the movie Jurassic World from 2015, "
            "or download the upcoming TV show Robin Hood. "
            "You can also specify seasons for TV shows, like download season 2 of Breaking Bad. "
            "What would you like to download?"
        )

        return VoiceResponse(
            speech=speech,
            reprompt="What would you like to download?",
            card_title="Overtalkerr Help",
            card_text=speech
        )

    def handle_cancel_stop(self, request: VoiceRequest) -> VoiceResponse:
        """Handle cancel/stop intent"""
        log_request("Cancel/Stop", request.user_id, platform=request.platform.value)

        return VoiceResponse(
            speech="Goodbye!",
            should_end_session=True
        )

    def handle_fallback(self, request: VoiceRequest) -> VoiceResponse:
        """Handle fallback intent"""
        log_request("Fallback", request.user_id, platform=request.platform.value)

        speech = (
            "I didn't catch that. You can say things like, "
            "download the movie Jurassic World from 2015. What would you like to download?"
        )

        return VoiceResponse(
            speech=speech,
            reprompt="What would you like to download?"
        )

    def route_intent(self, request: VoiceRequest) -> VoiceResponse:
        """Route request to appropriate handler based on intent"""
        intent_name = request.intent_name.lower()

        # Map various intent names across platforms
        if 'launch' in intent_name or intent_name == 'default welcome intent':
            return self.handle_launch(request)
        elif 'download' in intent_name or 'request' in intent_name:
            return self.handle_download(request)
        elif 'yes' in intent_name or intent_name == 'confirm':
            return self.handle_yes(request)
        elif 'no' in intent_name or intent_name == 'reject':
            return self.handle_no(request)
        elif 'help' in intent_name:
            return self.handle_help(request)
        elif 'cancel' in intent_name or 'stop' in intent_name or 'exit' in intent_name:
            return self.handle_cancel_stop(request)
        elif 'fallback' in intent_name:
            return self.handle_fallback(request)
        else:
            # Unknown intent, use fallback
            return self.handle_fallback(request)


# Global handler instance
unified_handler = UnifiedVoiceHandler()
