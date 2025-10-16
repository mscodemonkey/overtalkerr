"""
Universal voice assistant adapter supporting multiple platforms:
- Amazon Alexa (ask-sdk-python)
- Google Assistant (Actions on Google / Dialogflow)
- Siri Shortcuts (webhook-based)

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
    GOOGLE = "google"
    SIRI = "siri"
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


class GoogleAssistantAdapter(VoiceAssistantAdapter):
    """Adapter for Google Assistant (Dialogflow) requests"""

    def detect_platform(self, request_data: Dict[str, Any]) -> bool:
        """Detect Google Assistant request"""
        return (
            'queryResult' in request_data or
            'responseId' in request_data or
            'originalDetectIntentRequest' in request_data
        )

    def parse_request(self, request_data: Dict[str, Any]) -> VoiceRequest:
        """Parse Google Assistant request"""
        query_result = request_data.get('queryResult', {})
        original_request = request_data.get('originalDetectIntentRequest', {})

        # Extract user ID from payload
        payload = original_request.get('payload', {})
        user = payload.get('user', {})
        user_id = user.get('userId', 'unknown')

        session = request_data.get('session', 'unknown')
        session_id = session.split('/')[-1] if session else 'unknown'

        # Extract intent and parameters
        intent = query_result.get('intent', {})
        intent_name = intent.get('displayName', 'Unknown')

        parameters = query_result.get('parameters', {})
        slots = {k: str(v) if v else None for k, v in parameters.items()}

        return VoiceRequest(
            platform=VoiceAssistantPlatform.GOOGLE,
            user_id=user_id,
            session_id=session_id,
            intent_name=intent_name,
            slots=slots,
            raw_request=request_data
        )

    def build_response(self, voice_response: VoiceResponse) -> Dict[str, Any]:
        """Build Google Assistant response"""
        response = {
            'fulfillmentText': voice_response.speech,
            'fulfillmentMessages': [
                {
                    'text': {
                        'text': [voice_response.speech]
                    }
                }
            ]
        }

        # Add suggestion chips if there's a reprompt
        if voice_response.reprompt and not voice_response.should_end_session:
            response['fulfillmentMessages'].append({
                'suggestions': {
                    'suggestions': [
                        {'title': 'Yes'},
                        {'title': 'No'}
                    ]
                }
            })

        # Add basic card if specified
        if voice_response.card_title and voice_response.card_text:
            response['fulfillmentMessages'].append({
                'card': {
                    'title': voice_response.card_title,
                    'subtitle': voice_response.card_text
                }
            })

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


class VoiceAssistantRouter:
    """Routes requests to appropriate adapter"""

    def __init__(self):
        self.adapters = [
            AlexaAdapter(),
            GoogleAssistantAdapter(),
            SiriShortcutsAdapter()
        ]

    def detect_platform(self, request_data: Dict[str, Any]) -> Tuple[VoiceAssistantPlatform, Optional[VoiceAssistantAdapter]]:
        """Detect which platform sent the request"""
        for adapter in self.adapters:
            if adapter.detect_platform(request_data):
                platform = None
                if isinstance(adapter, AlexaAdapter):
                    platform = VoiceAssistantPlatform.ALEXA
                elif isinstance(adapter, GoogleAssistantAdapter):
                    platform = VoiceAssistantPlatform.GOOGLE
                elif isinstance(adapter, SiriShortcutsAdapter):
                    platform = VoiceAssistantPlatform.SIRI

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
            elif isinstance(adapter, GoogleAssistantAdapter) and platform == VoiceAssistantPlatform.GOOGLE:
                return adapter.build_response(voice_response)
            elif isinstance(adapter, SiriShortcutsAdapter) and platform == VoiceAssistantPlatform.SIRI:
                return adapter.build_response(voice_response)

        # Fallback to basic response
        return {'speech': voice_response.speech}


# Global router instance
router = VoiceAssistantRouter()
