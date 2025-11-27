"""
Universal voice assistant adapter supporting multiple platforms:
- Amazon Alexa (ask-sdk-python)
- Siri Shortcuts (webhook-based)
- Home Assistant Assist (webhook-based conversation agent)

Note: Google Assistant (Dialogflow) support was removed as Google deprecated
Conversational Actions in June 2023. Use Home Assistant Assist with Google
Assistant integration as an alternative.

This module provides a unified interface for handling requests from different platforms.
"""
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass

from logger import logger


class VoiceAssistantPlatform(Enum):
    """Supported voice assistant platforms"""
    ALEXA = "alexa"
    SIRI = "siri"
    HOME_ASSISTANT = "homeassistant"
    UNKNOWN = "unknown"


@dataclass
class VoiceRequest:
    """Unified voice request structure"""
    platform: VoiceAssistantPlatform
    user_id: str
    session_id: str
    intent_name: str
    slots: Dict[str, Optional[str]]
    raw_request: Dict[str, Any]


@dataclass
class VoiceResponse:
    """Unified voice response structure"""
    speech: str
    reprompt: Optional[str] = None
    should_end_session: bool = False
    card_title: Optional[str] = None
    card_text: Optional[str] = None


class VoiceAssistantAdapter(ABC):
    """Base class for voice assistant adapters"""

    @abstractmethod
    def detect_platform(self, request_data: Dict[str, Any]) -> bool:
        """Detect if this adapter can handle the request"""
        pass

    @abstractmethod
    def parse_request(self, request_data: Dict[str, Any]) -> VoiceRequest:
        """Parse platform-specific request into unified format"""
        pass

    @abstractmethod
    def build_response(self, voice_response: VoiceResponse) -> Dict[str, Any]:
        """Build platform-specific response from unified format"""
        pass


class AlexaAdapter(VoiceAssistantAdapter):
    """Adapter for Amazon Alexa requests"""

    def detect_platform(self, request_data: Dict[str, Any]) -> bool:
        """Detect Alexa request by checking for version and session"""
        return (
            'version' in request_data and
            'session' in request_data and
            'request' in request_data
        )

    def parse_request(self, request_data: Dict[str, Any]) -> VoiceRequest:
        """Parse Alexa request"""
        session = request_data.get('session', {})
        request = request_data.get('request', {})

        user_id = session.get('user', {}).get('userId', 'unknown')
        session_id = session.get('sessionId', 'unknown')

        # Determine intent name
        request_type = request.get('type')
        if request_type == 'LaunchRequest':
            intent_name = 'LaunchIntent'
            slots = {}
        elif request_type == 'IntentRequest':
            intent = request.get('intent', {})
            intent_name = intent.get('name', 'Unknown')
            raw_slots = intent.get('slots', {})
            slots = {k: v.get('value') for k, v in raw_slots.items()}
        elif request_type == 'SessionEndedRequest':
            intent_name = 'SessionEndedRequest'
            slots = {}
        else:
            intent_name = 'Unknown'
            slots = {}

        return VoiceRequest(
            platform=VoiceAssistantPlatform.ALEXA,
            user_id=user_id,
            session_id=session_id,
            intent_name=intent_name,
            slots=slots,
            raw_request=request_data
        )

    def build_response(self, voice_response: VoiceResponse) -> Dict[str, Any]:
        """Build Alexa response"""
        response = {
            'version': '1.0',
            'response': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': voice_response.speech
                },
                'shouldEndSession': voice_response.should_end_session
            }
        }

        if voice_response.reprompt:
            response['response']['reprompt'] = {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': voice_response.reprompt
                }
            }

        if voice_response.card_title and voice_response.card_text:
            response['response']['card'] = {
                'type': 'Simple',
                'title': voice_response.card_title,
                'content': voice_response.card_text
            }

        return response


class SiriShortcutsAdapter(VoiceAssistantAdapter):
    """Adapter for Siri Shortcuts (webhook-based)"""

    def detect_platform(self, request_data: Dict[str, Any]) -> bool:
        """Detect Siri Shortcuts request by custom header or structure"""
        return request_data.get('platform') == 'siri' or request_data.get('shortcut') is not None

    def parse_request(self, request_data: Dict[str, Any]) -> VoiceRequest:
        """Parse Siri Shortcuts request"""
        # Siri Shortcuts sends simpler JSON structure
        user_id = request_data.get('userId', 'siri-user')
        session_id = request_data.get('sessionId', f"siri-{user_id}")

        intent_name = request_data.get('action', request_data.get('intent', 'DownloadIntent'))

        # Siri sends parameters directly
        slots = request_data.get('parameters', {})

        # Also check for direct slot mapping
        if not slots:
            slots = {
                'MediaTitle': request_data.get('title'),
                'Year': request_data.get('year'),
                'MediaType': request_data.get('mediaType'),
                'Season': request_data.get('season'),
                'Upcoming': request_data.get('upcoming')
            }

        # Remove None values
        slots = {k: v for k, v in slots.items() if v is not None}

        return VoiceRequest(
            platform=VoiceAssistantPlatform.SIRI,
            user_id=user_id,
            session_id=session_id,
            intent_name=intent_name,
            slots=slots,
            raw_request=request_data
        )

    def build_response(self, voice_response: VoiceResponse) -> Dict[str, Any]:
        """Build Siri Shortcuts response"""
        # Siri Shortcuts expects simple JSON
        response = {
            'speech': voice_response.speech,
            'text': voice_response.speech,
            'endSession': voice_response.should_end_session
        }

        if voice_response.card_title:
            response['title'] = voice_response.card_title

        if voice_response.reprompt:
            response['reprompt'] = voice_response.reprompt

        return response


class HomeAssistantAdapter(VoiceAssistantAdapter):
    """Adapter for Home Assistant Assist (webhook-based conversation agent)"""

    def detect_platform(self, request_data: Dict[str, Any]) -> bool:
        """
        Detect Home Assistant request by checking for webhook-conversation structure.
        Home Assistant sends: conversation_id, user_id, language, query, exposed_entities, etc.
        """
        return (
            'conversation_id' in request_data and
            'query' in request_data and
            ('exposed_entities' in request_data or 'agent_id' in request_data)
        )

    def parse_request(self, request_data: Dict[str, Any]) -> VoiceRequest:
        """
        Parse Home Assistant webhook-conversation request.

        Expected format:
        {
            "conversation_id": "abc123",
            "user_id": "user_xyz",
            "language": "en",
            "agent_id": "conversation.overtalkerr",
            "query": "I want to download Inception",
            "messages": [...],  # conversation history
            "exposed_entities": {...}  # available smart home entities
        }
        """
        user_id = request_data.get('user_id', 'ha-user')
        session_id = request_data.get('conversation_id', f"ha-{user_id}")
        query = request_data.get('query', '')

        # Parse the query to extract intent and slots
        # For now, we'll use a simple heuristic:
        # - If query starts with launch-type words: LaunchIntent
        # - If contains "yes", "yeah", "yep", etc: YesIntent
        # - If contains "no", "nope", "nah", etc: NoIntent
        # - If contains "help": HelpIntent
        # - If contains "cancel", "stop", "exit": CancelIntent
        # - Otherwise: DownloadIntent with the query as MediaTitle

        query_lower = query.lower().strip()

        # Detect intent from query
        if not query_lower or query_lower in ['open overtalkerr', 'start overtalkerr', 'launch overtalkerr', 'hey overtalkerr']:
            intent_name = 'LaunchIntent'
            slots = {}
        elif query_lower in ['yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'correct', 'right', 'that one']:
            intent_name = 'YesIntent'
            slots = {}
        elif query_lower in ['no', 'nope', 'nah', 'not that one', 'wrong', 'next', 'next one', 'another', 'different']:
            intent_name = 'NoIntent'
            slots = {}
        elif 'help' in query_lower:
            intent_name = 'HelpIntent'
            slots = {}
        elif any(word in query_lower for word in ['cancel', 'stop', 'exit', 'quit', 'nevermind', 'never mind']):
            intent_name = 'CancelIntent'
            slots = {}
        else:
            # Default to DownloadIntent - parse media request
            intent_name = 'DownloadIntent'
            slots = self._extract_slots_from_query(query)

        return VoiceRequest(
            platform=VoiceAssistantPlatform.HOME_ASSISTANT,
            user_id=user_id,
            session_id=session_id,
            intent_name=intent_name,
            slots=slots,
            raw_request=request_data
        )

    def _extract_slots_from_query(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extract media request slots from natural language query.

        Examples:
        - "download Inception" -> {"MediaTitle": "Inception"}
        - "I want to watch The Office season 3" -> {"MediaTitle": "The Office", "Season": "3"}
        - "find movies from 2020" -> {"Year": "2020"}
        - "upcoming movie called Dune" -> {"MediaTitle": "Dune", "Upcoming": "true"}
        """
        slots = {}
        query_lower = query.lower()

        # Remove common prefixes
        prefixes = [
            'download ', 'request ', 'i want to download ', 'i want to watch ',
            'i want to see ', 'find ', 'search for ', 'get ', 'add ',
            'can you download ', 'can you find ', 'can you get ',
            'please download ', 'please find ', 'please get '
        ]

        cleaned_query = query
        for prefix in prefixes:
            if query_lower.startswith(prefix):
                cleaned_query = query[len(prefix):].strip()
                break

        # Detect media type (including patterns like "the movie" or "the tv show")
        if any(word in query_lower for word in ['the tv show', 'the show', 'the series', ' show', ' series', ' tv ', ' season', ' episode']):
            slots['MediaType'] = 'tv'
        elif any(word in query_lower for word in ['the movie', 'the film', ' movie', ' film']):
            slots['MediaType'] = 'movie'

        # Extract season number
        import re
        season_match = re.search(r'season\s+(\d+)', query_lower)
        if season_match:
            slots['Season'] = season_match.group(1)
            # Remove season mention from title
            cleaned_query = re.sub(r'\s*season\s+\d+', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Extract year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', query)
        if year_match:
            slots['Year'] = year_match.group(1)
            # Remove year from title
            cleaned_query = cleaned_query.replace(year_match.group(0), '').strip()

        # Detect upcoming
        if any(word in query_lower for word in ['upcoming', 'unreleased', 'not out yet', 'coming soon']):
            slots['Upcoming'] = 'true'
            # Remove upcoming mentions
            cleaned_query = re.sub(r'\b(upcoming|unreleased|not out yet|coming soon)\b', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Remove media type phrases (including "the movie", "a movie called", etc.)
        # Order matters - remove longer phrases first
        cleaned_query = re.sub(r'\b(the|a|an)\s+(movie|film|tv\s+show|show|series)\s+(called|named|titled)\b', '', cleaned_query, flags=re.IGNORECASE).strip()
        cleaned_query = re.sub(r'\b(the|a|an)\s+(movie|film|tv\s+show|show|series)\b', '', cleaned_query, flags=re.IGNORECASE).strip()
        cleaned_query = re.sub(r'\b(movie|film|show|series|tv)\b', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Remove remaining "called/named/titled" if still present
        cleaned_query = re.sub(r'\b(called|named|titled)\b', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Remove "from" when used with year
        cleaned_query = re.sub(r'\bfrom\b', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Clean up multiple spaces
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()

        # The remaining text is the media title
        if cleaned_query:
            slots['MediaTitle'] = cleaned_query

        return slots

    def build_response(self, voice_response: VoiceResponse) -> Dict[str, Any]:
        """
        Build Home Assistant webhook-conversation response.

        Expected response format:
        {
            "output": "The response text that will be spoken"
        }

        For streaming responses (not currently implemented):
        {"type": "item", "content": "text chunk"}
        {"type": "end"}
        """
        # Home Assistant webhook-conversation expects ONLY the "output" field
        # Extra fields may cause parsing errors in some versions
        response = {
            'output': voice_response.speech
        }

        return response


class VoiceAssistantRouter:
    """Routes requests to appropriate adapter"""

    def __init__(self):
        self.adapters = [
            AlexaAdapter(),
            SiriShortcutsAdapter(),
            HomeAssistantAdapter()
        ]

    def detect_platform(self, request_data: Dict[str, Any]) -> Tuple[VoiceAssistantPlatform, Optional[VoiceAssistantAdapter]]:
        """Detect which platform sent the request"""
        for adapter in self.adapters:
            if adapter.detect_platform(request_data):
                platform = None
                if isinstance(adapter, AlexaAdapter):
                    platform = VoiceAssistantPlatform.ALEXA
                elif isinstance(adapter, SiriShortcutsAdapter):
                    platform = VoiceAssistantPlatform.SIRI
                elif isinstance(adapter, HomeAssistantAdapter):
                    platform = VoiceAssistantPlatform.HOME_ASSISTANT

                logger.info(f"Detected platform: {platform.value if platform else 'unknown'}")
                return platform, adapter

        logger.warning("Could not detect voice assistant platform")
        return VoiceAssistantPlatform.UNKNOWN, None

    def parse_request(self, request_data: Dict[str, Any]) -> Optional[VoiceRequest]:
        """Parse request using appropriate adapter"""
        platform, adapter = self.detect_platform(request_data)

        if adapter is None:
            logger.error("No adapter found for request")
            return None

        try:
            return adapter.parse_request(request_data)
        except Exception as e:
            logger.error(f"Failed to parse {platform.value} request: {e}")
            return None

    def build_response(self, voice_response: VoiceResponse, platform: VoiceAssistantPlatform) -> Dict[str, Any]:
        """Build response for specific platform"""
        for adapter in self.adapters:
            if isinstance(adapter, AlexaAdapter) and platform == VoiceAssistantPlatform.ALEXA:
                return adapter.build_response(voice_response)
            elif isinstance(adapter, SiriShortcutsAdapter) and platform == VoiceAssistantPlatform.SIRI:
                return adapter.build_response(voice_response)
            elif isinstance(adapter, HomeAssistantAdapter) and platform == VoiceAssistantPlatform.HOME_ASSISTANT:
                return adapter.build_response(voice_response)

        # Fallback to basic response
        return {'speech': voice_response.speech}


# Global router instance
router = VoiceAssistantRouter()
