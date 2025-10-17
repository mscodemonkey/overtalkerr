"""
Alexa skill handlers using ask-sdk-python (modern Alexa SDK).

This module contains all Alexa intent handlers, replacing the deprecated Flask-Ask framework.
"""
import re
import datetime
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
from voice_assistant_adapter import router, VoiceRequest, VoiceAssistantPlatform
from unified_voice_handler import unified_handler


# ==========================================
# JSON Encoder for Date Objects
# ==========================================

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date and datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


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

        # Build VoiceRequest using the adapter
        voice_request = VoiceRequest(
            platform=VoiceAssistantPlatform.ALEXA,
            user_id=user_id,
            session_id=session_id,
            intent="DownloadIntent",
            slots={
                'MediaTitle': media_title,
                'Year': year,
                'MediaType': media_type_text,
                'Upcoming': upcoming_text,
                'Season': season_text
            }
        )

        # Use unified handler for consistent behavior across platforms
        voice_response = unified_handler.handle_download(voice_request)

        # Build Alexa response
        response_builder = handler_input.response_builder.speak(voice_response.speech)

        if voice_response.reprompt:
            response_builder = response_builder.ask(voice_response.reprompt)

        if voice_response.card_text:
            response_builder = response_builder.set_card(
                SimpleCard("Overtalkerr", voice_response.card_text)
            )

        if voice_response.should_end_session:
            response_builder = response_builder.set_should_end_session(True)

        return response_builder.response


class YesIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.YesIntent - confirms selection"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        session_id = get_session_id(handler_input)

        # Build VoiceRequest
        voice_request = VoiceRequest(
            platform=VoiceAssistantPlatform.ALEXA,
            user_id=user_id,
            session_id=session_id,
            intent="YesIntent",
            slots={}
        )

        # Use unified handler
        voice_response = unified_handler.handle_yes(voice_request)

        # Build Alexa response
        response_builder = handler_input.response_builder.speak(voice_response.speech)

        if voice_response.reprompt:
            response_builder = response_builder.ask(voice_response.reprompt)

        if voice_response.card_text:
            response_builder = response_builder.set_card(
                SimpleCard("Overtalkerr", voice_response.card_text)
            )

        if voice_response.should_end_session:
            response_builder = response_builder.set_should_end_session(True)

        return response_builder.response


class NoIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.NoIntent - shows next result"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = get_user_id(handler_input)
        session_id = get_session_id(handler_input)

        # Build VoiceRequest
        voice_request = VoiceRequest(
            platform=VoiceAssistantPlatform.ALEXA,
            user_id=user_id,
            session_id=session_id,
            intent="NoIntent",
            slots={}
        )

        # Use unified handler
        voice_response = unified_handler.handle_no(voice_request)

        # Build Alexa response
        response_builder = handler_input.response_builder.speak(voice_response.speech)

        if voice_response.reprompt:
            response_builder = response_builder.ask(voice_response.reprompt)

        if voice_response.card_text:
            response_builder = response_builder.set_card(
                SimpleCard("Overtalkerr", voice_response.card_text)
            )

        if voice_response.should_end_session:
            response_builder = response_builder.set_should_end_session(True)

        return response_builder.response


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
