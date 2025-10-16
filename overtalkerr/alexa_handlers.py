"""
Alexa skill handlers using ask-sdk-python (modern Alexa SDK).

This module contains all Alexa intent handlers, replacing the deprecated Flask-Ask framework.
"""
import re
from typing import Optional, Dict, Any

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from logger import logger, log_request, log_error
import overseerr
from overseerr import OverseerrError, OverseerrConnectionError, OverseerrAuthError
from db import db_session, SessionState
import json


# ==========================================
# Helper Functions
# ==========================================

def get_user_id(handler_input: HandlerInput) -> str:
    """Extract user ID from Alexa request"""
    return handler_input.request_envelope.session.user.user_id


def get_session_id(handler_input: HandlerInput) -> str:
    """Extract session ID from Alexa request"""
    return handler_input.request_envelope.session.session_id


def get_slot_value(handler_input: HandlerInput, slot_name: str) -> Optional[str]:
    """Safely extract slot value from request"""
    slots = handler_input.request_envelope.request.intent.slots
    if slot_name in slots and slots[slot_name].value:
        return slots[slot_name].value
    return None


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
    """Generate speech for a search result item"""
    title = item.get('_title') or item.get('title') or item.get('name') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]

    type_word = 'movie' if mtype == 'movie' else 'TV show'

    if year:
        return f"{prefix} the {type_word} {title}, released in {year}. Is that the one you want?"
    else:
        return f"{prefix} the {type_word} {title}. Is that the one you want?"


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
        payload = json.dumps(state)
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
# Intent Handlers
# ==========================================

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for skill launch"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        log_request("LaunchRequest", user_id)

        speech = (
            "Welcome to Overtalkerr! You can say things like, "
            "download the movie Jurassic World, or download the upcoming TV show Robin Hood. "
            "What would you like to download?"
        )

        return (
            handler_input.response_builder
            .speak(speech)
            .ask(speech)
            .set_card(SimpleCard("Overtalkerr", speech))
            .response
        )


class DownloadIntentHandler(AbstractRequestHandler):
    """Handler for media download requests"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("DownloadIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        session_id = get_session_id(handler_input)

        # Extract slots
        media_title = get_slot_value(handler_input, "MediaTitle")
        year = get_slot_value(handler_input, "Year")
        media_type_text = get_slot_value(handler_input, "MediaType")
        upcoming_text = get_slot_value(handler_input, "Upcoming")
        season_text = get_slot_value(handler_input, "Season")

        log_request("DownloadIntent", user_id, title=media_title, year=year, media_type=media_type_text)

        if not media_title:
            speech = "Please tell me the title. For example, say download the movie Jurassic World from 2015."
            return (
                handler_input.response_builder
                .speak(speech)
                .ask(speech)
                .response
            )

        # Normalize inputs
        media_type = media_type_from_text(media_type_text)
        upcoming_only = False

        if upcoming_text:
            upcoming_only = upcoming_text.lower() in ['yes', 'true', '1', 'upcoming']

        # Check if "upcoming" is in the title itself
        if media_title and re.search(r"\bupcoming\b", media_title, re.IGNORECASE):
            upcoming_only = True
            media_title = re.sub(r"\bupcoming\b", "", media_title, flags=re.IGNORECASE).strip()

        # Normalize year
        year_filter = None
        if year:
            m = re.search(r"(\d{4})", year)
            if m:
                year_filter = m.group(1)

        # Extract season number
        season_number = None
        if season_text:
            m = re.search(r"(\d+)", season_text)
            if m:
                season_number = int(m.group(1))

        # Search Overseerr
        try:
            results = overseerr.search(media_title, media_type)
        except OverseerrConnectionError:
            speech = "Sorry, I couldn't connect to the media server. Please try again later."
            return handler_input.response_builder.speak(speech).response
        except OverseerrAuthError:
            speech = "Sorry, there's an authentication problem with the media server. Please contact the administrator."
            return handler_input.response_builder.speak(speech).response
        except OverseerrError as e:
            log_error("Overseerr search failed", e, user_id=user_id, title=media_title)
            speech = "Sorry, I encountered an error searching for that title. Please try again."
            return handler_input.response_builder.speak(speech).response

        # Filter and rank results
        ranked = overseerr.pick_best(results, upcoming_only=upcoming_only, year_filter=year_filter)

        if not ranked:
            speech = "I couldn't find any matches for that title. Please try a different search."
            return handler_input.response_builder.speak(speech).response

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
        save_state(user_id, session_id, state)

        # Build response
        first = ranked[0]
        speech = build_speech_for_item(first, "I found")

        return (
            handler_input.response_builder
            .speak(speech)
            .ask("Is that the one you want?")
            .set_card(SimpleCard("Overtalkerr", speech))
            .response
        )


class YesIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.YesIntent - confirms selection"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        session_id = get_session_id(handler_input)

        log_request("YesIntent", user_id)

        state = load_state(user_id, session_id)

        if not state:
            speech = "I don't have an active search. Please say a title to start a new download request."
            return (
                handler_input.response_builder
                .speak(speech)
                .ask(speech)
                .response
            )

        idx = state.get('index', 0)
        results = state.get('results', [])

        if idx >= len(results):
            speech = "I've run out of alternatives. Please start a new search."
            return handler_input.response_builder.speak(speech).response

        chosen = results[idx]
        media_id = chosen.get('id') or chosen.get('mediaId') or chosen.get('tmdbId')
        media_type = chosen.get('_mediaType') or state.get('media_type') or 'movie'
        season_number = state.get('season')

        if not media_id:
            speech = "Sorry, I couldn't determine the media ID. Please try a different title."
            return handler_input.response_builder.speak(speech).response

        # Create request in Overseerr
        try:
            result = overseerr.request_media(int(media_id), media_type, season=season_number)

            # Check if it was already requested
            if result.get('message') and 'already requested' in result.get('message', '').lower():
                speech = "That media has already been requested!"
            else:
                title = chosen.get('_title', 'the media')
                speech = f"Okay! I've requested {title}. It should be available soon."

        except OverseerrConnectionError:
            speech = "Sorry, I couldn't connect to the media server. Your request wasn't submitted."
            return handler_input.response_builder.speak(speech).response
        except OverseerrError as e:
            log_error("Failed to create Overseerr request", e, user_id=user_id, media_id=media_id)
            speech = "Sorry, I couldn't create the request. Please try again later."
            return handler_input.response_builder.speak(speech).response

        return (
            handler_input.response_builder
            .speak(speech)
            .set_card(SimpleCard("Overtalkerr", speech))
            .set_should_end_session(True)
            .response
        )


class NoIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.NoIntent - shows next result"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        session_id = get_session_id(handler_input)

        log_request("NoIntent", user_id)

        state = load_state(user_id, session_id)

        if not state:
            speech = "Please tell me the title. For example, say download the movie Jurassic World from 2015."
            return (
                handler_input.response_builder
                .speak(speech)
                .ask(speech)
                .response
            )

        idx = state.get('index', 0) + 1
        results = state.get('results', [])

        if idx >= len(results):
            speech = "That's all I could find. Would you like to search for something else?"
            return (
                handler_input.response_builder
                .speak(speech)
                .ask("What would you like to download?")
                .response
            )

        # Update state
        state['index'] = idx
        save_state(user_id, session_id, state)

        # Build response
        next_item = results[idx]
        speech = build_speech_for_next(next_item)

        return (
            handler_input.response_builder
            .speak(speech)
            .ask("Is that the one?")
            .set_card(SimpleCard("Overtalkerr", speech))
            .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.HelpIntent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech = (
            "You can say things like: download the movie Jurassic World from 2015, "
            "or download the upcoming TV show Robin Hood. "
            "You can also specify seasons for TV shows, like download season 2 of Breaking Bad. "
            "What would you like to download?"
        )

        return (
            handler_input.response_builder
            .speak(speech)
            .ask(speech)
            .set_card(SimpleCard("Overtalkerr Help", speech))
            .response
        )


class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.CancelIntent and AMAZON.StopIntent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return (
            is_intent_name("AMAZON.CancelIntent")(handler_input) or
            is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        speech = "Goodbye!"

        return (
            handler_input.response_builder
            .speak(speech)
            .set_should_end_session(True)
            .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.FallbackIntent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech = (
            "Sorry, I didn't understand that. You can say things like, "
            "download the movie Jurassic World from 2015. What would you like to download?"
        )

        return (
            handler_input.response_builder
            .speak(speech)
            .ask(speech)
            .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for session end"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        # Cleanup if needed
        logger.info("Session ended")
        return handler_input.response_builder.response


# ==========================================
# Exception Handlers
# ==========================================

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler"""

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        log_error("Unhandled exception in Alexa handler", exception)

        speech = "Sorry, I encountered an unexpected error. Please try again."

        return (
            handler_input.response_builder
            .speak(speech)
            .ask(speech)
            .response
        )


# ==========================================
# Skill Builder
# ==========================================

# Create skill builder
sb = SkillBuilder()

# Register request handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(DownloadIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handler
sb.add_exception_handler(CatchAllExceptionHandler())

# Build the skill
skill = sb.create()
