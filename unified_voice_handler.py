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

def media_type_from_text(text: Optional[str]) -> Optional[str]:
    """Extract media type from spoken text"""
    if not text:
        return None
    t = text.lower()
    if 'tv' in t or 'show' in t or 'series' in t:
        return 'tv'
    if 'movie' in t or 'film' in t:
        return 'movie'
    return None


def build_speech_for_item(item: Dict[str, Any], prefix: str = "I found") -> str:
    """Generate speech for a search result item with availability status"""
    title = item.get('_title') or item.get('title') or item.get('name') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]

    type_word = 'movie' if mtype == 'movie' else 'TV show'

    # Build base speech
    if year:
        speech = f"{prefix} the {type_word} {title}, released in {year}"
    else:
        speech = f"{prefix} the {type_word} {title}"

    # Add availability status
    if item.get('_isAvailable'):
        speech += ". This is already in your library"
    elif item.get('_isPartiallyAvailable'):
        speech += ". This is partially in your library"
    elif item.get('_isProcessing'):
        speech += ". This is currently being downloaded"
    elif item.get('_isPending'):
        speech += ". This has already been requested and is pending approval"

    # Add confirmation question
    speech += ". Is that the one you want?"

    return speech


def build_speech_for_next(item: Dict[str, Any]) -> str:
    """Generate speech for the next alternative result"""
    title = item.get('_title') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]

    type_word = 'movie' if mtype == 'movie' else 'TV show'

    if year:
        return f"What about the {type_word} {title}, released in {year}?"
    else:
        return f"What about the {type_word} {title}?"


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

        # Normalize inputs
        media_type = media_type_from_text(media_type_text)
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
            speech = "Sorry, I couldn't connect to the media server. Please try again later."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrAuthError:
            speech = "Sorry, there's an authentication problem with the media server. Please contact the administrator."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrError as e:
            log_error("Overseerr search failed", e, user_id=request.user_id, title=enhanced_title)
            speech = "Sorry, I encountered an error searching for that title. Please try again."
            return VoiceResponse(speech=speech, should_end_session=True)

        # 🚀 ENHANCED SEARCH: Apply fuzzy matching for better results
        if results:
            results = search_enhancer.fuzzy_match_results(enhanced_title, results, threshold=60)

        # Filter and rank results
        ranked = overseerr.pick_best(results, upcoming_only=upcoming_only, year_filter=year_filter)

        if not ranked:
            if year_filter:
                speech = f"I couldn't find any matches for '{media_title}' from {year_filter}. Try rephrasing or removing the year filter."
            else:
                speech = f"I couldn't find any matches for '{media_title}'. Try rephrasing or being more specific."
            return VoiceResponse(speech=speech, should_end_session=True)

        # Save state
        state = {
            'query': media_title,
            'media_type': media_type,
            'year': year_filter,
            'upcoming_only': upcoming_only,
            'season': season_number,
            'results': ranked,
            'index': 0,
        }
        save_state(request.user_id, request.session_id, state)

        # Build response
        first = ranked[0]
        speech = build_speech_for_item(first, "I found")

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
            speech = "Sorry, I couldn't determine the media ID. Please try a different title."
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
                speech = "That media has already been requested!"
            else:
                if season_number:
                    speech = f"Okay! I've requested season {season_number} of {title}. It should be available soon."
                else:
                    speech = f"Okay! I've requested {title}. It should be available soon."

        except OverseerrConnectionError:
            speech = "Sorry, I couldn't connect to the media server. Your request wasn't submitted."
            return VoiceResponse(speech=speech, should_end_session=True)
        except OverseerrError as e:
            log_error("Failed to create Overseerr request", e, user_id=request.user_id, media_id=media_id)
            speech = "Sorry, I couldn't create the request. Please try again later."
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

        idx = state.get('index', 0) + 1
        results = state.get('results', [])

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
        speech = build_speech_for_next(next_item)

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
            "Sorry, I didn't understand that. You can say things like, "
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
