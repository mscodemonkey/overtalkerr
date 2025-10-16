"""
Overtalkerr - Multi-platform voice assistant for Overseerr

Supports:
- Amazon Alexa (ask-sdk-python)
- Google Assistant (Dialogflow)
- Siri Shortcuts (webhook)
- Web-based test harness

This replaces the deprecated Flask-Ask framework with modern, production-ready code.
"""
import json
import os
import re
import datetime as dt
import base64
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify, send_from_directory, Response
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response as AlexaResponse
from ask_sdk_model.ui import SimpleCard

from config import Config
from logger import logger, log_request, log_error
from db import db_session, SessionState, cleanup_old_sessions
import overseerr
from overseerr import OverseerrError, OverseerrConnectionError
from voice_assistant_adapter import router, VoiceResponse, VoiceAssistantPlatform
from unified_voice_handler import unified_handler, load_state, save_state

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Static directory for test UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

logger.info("Overtalkerr starting up...")

# Check backend connectivity on startup
if not Config.MOCK_BACKEND:
    Config.check_connectivity()

# ========================================
# ALEXA SKILL (ask-sdk-python)
# ========================================

# Import Alexa handlers from dedicated module
from alexa_handlers import skill as alexa_skill

# ========================================
# DASHBOARD / LANDING PAGE
# ========================================

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return send_from_directory('static', 'dashboard.html')


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        from db import SessionState, db_session
        from datetime import datetime, timedelta
        from media_backends import get_backend, BackendFactory

        stats = {}

        # Backend status
        # Check if backend is configured
        if not Config.MEDIA_BACKEND_URL or Config.MEDIA_BACKEND_URL == 'http://your-backend-url:5055':
            stats['backend_connected'] = False
            stats['backend_type'] = 'Not Configured'
            stats['backend_configured'] = False
        else:
            stats['backend_configured'] = True

            # Try to get backend info
            try:
                backend = get_backend()
                stats['backend_type'] = backend.__class__.__name__.replace('Backend', '')
                stats['backend_connected'] = True
            except Exception as e:
                # Couldn't initialize backend, but still show what we know
                logger.warning(f"Could not initialize backend: {e}")
                stats['backend_connected'] = False

                # Try to guess backend type from URL or just show as configured
                try:
                    detected_type = BackendFactory.detect_backend_type(Config.MEDIA_BACKEND_URL, Config.MEDIA_BACKEND_API_KEY)
                    stats['backend_type'] = detected_type.value.title()
                except:
                    # Can't detect, use generic name
                    stats['backend_type'] = 'Backend'

        # Database stats
        with db_session() as session:
            # Total requests (approximate by unique media titles in session state)
            total_count = session.query(SessionState).count()
            stats['total_requests'] = total_count

            # Recent activity (last 10)
            recent = session.query(SessionState).order_by(
                SessionState.updated_at.desc()
            ).limit(10).all()

            stats['recent_activity'] = []
            for s in recent:
                if s.session_data and 'chosen_result' in s.session_data:
                    result = s.session_data['chosen_result']
                    stats['recent_activity'].append({
                        'title': result.get('title', 'Unknown'),
                        'year': result.get('year'),
                        'media_type': result.get('mediaType', 'unknown'),
                        'timestamp': s.updated_at.isoformat() if s.updated_at else None
                    })

            # Today's requests
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = session.query(SessionState).filter(
                SessionState.updated_at >= today
            ).count()
            stats['requests_today'] = today_count

            # This week's requests
            week_ago = datetime.now() - timedelta(days=7)
            week_count = session.query(SessionState).filter(
                SessionState.updated_at >= week_ago
            ).count()
            stats['requests_this_week'] = week_count

        # Configuration status
        stats['config_complete'] = bool(
            Config.MEDIA_BACKEND_URL and
            Config.MEDIA_BACKEND_API_KEY and
            Config.PUBLIC_BASE_URL
        )

        stats['public_url'] = Config.PUBLIC_BASE_URL or 'Not configured'
        stats['backend_url'] = Config.MEDIA_BACKEND_URL or 'Not configured'

        return jsonify(stats)

    except Exception as e:
        log_error("Failed to get stats", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/version')
def get_version():
    """Get current version and check for updates from GitHub"""
    import os
    import requests
    from datetime import datetime, timedelta

    try:
        # Read current version
        version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
        with open(version_file, 'r') as f:
            current_version = f.read().strip()

        response_data = {
            'current_version': current_version,
            'update_available': False,
            'latest_version': None,
            'release_url': None,
            'release_notes': None,
            'checked_at': datetime.utcnow().isoformat()
        }

        # Check GitHub for latest release
        try:
            github_api = 'https://api.github.com/repos/mscodemonkey/overtalkerr/releases/latest'
            headers = {'Accept': 'application/vnd.github.v3+json'}

            gh_response = requests.get(github_api, headers=headers, timeout=5)

            if gh_response.status_code == 200:
                release_data = gh_response.json()
                latest_version = release_data.get('tag_name', '').lstrip('v')

                response_data['latest_version'] = latest_version
                response_data['release_url'] = release_data.get('html_url')
                response_data['release_notes'] = release_data.get('body', '')
                response_data['published_at'] = release_data.get('published_at')

                # Simple version comparison (works for semver like 1.0.0)
                if latest_version and latest_version != current_version:
                    # Remove -beta, -alpha suffixes for comparison
                    current_clean = current_version.split('-')[0]
                    latest_clean = latest_version.split('-')[0]

                    current_parts = [int(x) for x in current_clean.split('.')]
                    latest_parts = [int(x) for x in latest_clean.split('.')]

                    if latest_parts > current_parts:
                        response_data['update_available'] = True
                        logger.info(f"Update available: {current_version} -> {latest_version}")

        except Exception as e:
            logger.warning(f"Could not check for updates: {e}")
            response_data['check_error'] = str(e)

        return jsonify(response_data)

    except Exception as e:
        log_error("Failed to get version info", e)
        return jsonify({"error": str(e)}), 500


# ========================================
# ALEXA ENDPOINT
# ========================================

@app.route('/alexa', methods=['POST'])
def alexa_webhook():
    """
    Alexa skill endpoint for handling voice requests.

    This endpoint handles all Alexa skill requests with proper verification.
    """
    try:
        # Get request data
        request_data = request.get_json()

        logger.debug("Received Alexa request", extra={"request_type": request_data.get('request', {}).get('type')})

        # Process with ask-sdk-python skill
        response = alexa_skill.invoke(request_envelope=request_data, context=None)

        return jsonify(response)

    except Exception as e:
        log_error("Error processing Alexa request", e)
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Sorry, I encountered an error processing your request."
                },
                "shouldEndSession": True
            }
        }), 500


# ========================================
# UNIVERSAL VOICE ENDPOINT
# ========================================

@app.route('/voice', methods=['POST'])
def universal_voice_webhook():
    """
    Universal endpoint for Google Assistant, Siri Shortcuts, and other platforms.

    Automatically detects the platform and routes appropriately.
    """
    try:
        request_data = request.get_json()

        # Parse request using platform adapter
        voice_request = router.parse_request(request_data)

        if voice_request is None:
            return jsonify({"error": "Could not parse request"}), 400

        logger.info(f"Processing {voice_request.platform.value} request: {voice_request.intent_name}")

        # Handle with unified handler
        voice_response = unified_handler.route_intent(voice_request)

        # Build platform-specific response
        platform_response = router.build_response(voice_response, voice_request.platform)

        return jsonify(platform_response)

    except Exception as e:
        log_error("Error processing voice request", e)
        return jsonify({
            "speech": "Sorry, I encountered an error processing your request."
        }), 500


# ========================================
# TEST HARNESS (Web UI)
# ========================================

def _is_local_ip(ip: str) -> bool:
    """Check if IP is from local network"""
    if not ip:
        return False
    return (
        ip.startswith('127.') or
        ip == '::1' or
        ip.startswith('192.168.') or
        ip.startswith('10.') or
        ip.startswith('172.16.') or
        ip.startswith('172.17.') or
        ip.startswith('172.18.') or
        ip.startswith('172.19.') or
        ip.startswith('172.2')
    )


def _needs_auth() -> bool:
    """Check if request needs authentication"""
    path = request.path or ''
    if not path.startswith('/test'):
        return False

    # Get client IP
    xff = request.headers.get('X-Forwarded-For', '')
    ip = (xff.split(',')[0].strip() if xff else request.remote_addr) or ''

    if _is_local_ip(ip):
        return False

    # Require auth only if credentials are configured
    return bool(Config.BASIC_AUTH_USER and Config.BASIC_AUTH_PASS)


def _check_basic_auth() -> Optional[Response]:
    """Verify Basic Auth credentials"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Basic '):
        return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Test"'})

    try:
        raw = base64.b64decode(auth.split(' ', 1)[1]).decode('utf-8')
        user, pwd = raw.split(':', 1)
    except Exception:
        return Response('Invalid auth header', 401, {'WWW-Authenticate': 'Basic realm="Test"'})

    if user == Config.BASIC_AUTH_USER and pwd == Config.BASIC_AUTH_PASS:
        return None

    return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Test"'})


@app.before_request
def protect_test_endpoints():
    """Protect test endpoints with Basic Auth if configured"""
    if _needs_auth():
        failure = _check_basic_auth()
        if failure is not None:
            return failure


@app.route('/test', methods=['GET'])
def test_ui():
    """Serve test harness UI"""
    return send_from_directory(STATIC_DIR, 'test_ui.html')


@app.route('/test/info', methods=['GET'])
def test_info():
    """Get environment info for test UI"""
    return jsonify({
        "mock": Config.MOCK_BACKEND,
        "authProtected": _needs_auth(),
        "platform": "multi-platform",
        "version": "2.0.0"
    })


@app.route('/test/start', methods=['POST'])
def test_start():
    """Start a new search (test harness)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'test-user')
    conv_id = data.get('conversationId') or f"test-{int(dt.datetime.utcnow().timestamp())}"
    title = data.get('title', '')
    year = data.get('year')
    media_type_text = data.get('mediaType')
    upcoming = bool(data.get('upcoming'))
    season_text = data.get('season')

    if not title:
        return jsonify({"error": "title is required"}), 400

    # Build voice request
    voice_request = router.parse_request({
        "platform": "siri",  # Use Siri adapter for test harness
        "userId": user_id,
        "sessionId": conv_id,
        "action": "DownloadIntent",
        "parameters": {
            "MediaTitle": title,
            "Year": year,
            "MediaType": media_type_text,
            "Upcoming": "yes" if upcoming else "no",
            "Season": season_text
        }
    })

    # Handle request
    voice_response = unified_handler.handle_download(voice_request)

    # Load state to get result count
    state = load_state(user_id, conv_id)

    result = {
        "userId": user_id,
        "conversationId": conv_id,
        "speech": voice_response.speech,
        "end": voice_response.should_end_session
    }

    if state:
        result["index"] = state.get('index', 0)
        result["total"] = len(state.get('results', []))
        if state.get('results'):
            result["item"] = state['results'][state.get('index', 0)]

    return jsonify(result)


@app.route('/test/yes', methods=['POST'])
def test_yes():
    """Confirm selection (test harness)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'test-user')
    conv_id = data.get('conversationId')

    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400

    # Build voice request
    voice_request = router.parse_request({
        "platform": "siri",
        "userId": user_id,
        "sessionId": conv_id,
        "action": "AMAZON.YesIntent",
        "parameters": {}
    })

    # Handle request
    voice_response = unified_handler.handle_yes(voice_request)

    result = {
        "speech": voice_response.speech,
        "end": voice_response.should_end_session,
        "conversationId": conv_id
    }

    # Check if request was created
    if "requested" in voice_response.speech.lower() or "okay" in voice_response.speech.lower():
        state = load_state(user_id, conv_id)
        if state and state.get('results'):
            chosen = state['results'][state.get('index', 0)]
            result["requested"] = {
                "mediaId": chosen.get('id'),
                "mediaType": chosen.get('_mediaType')
            }

    return jsonify(result)


@app.route('/test/no', methods=['POST'])
def test_no():
    """Move to next result (test harness)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'test-user')
    conv_id = data.get('conversationId')

    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400

    # Build voice request
    voice_request = router.parse_request({
        "platform": "siri",
        "userId": user_id,
        "sessionId": conv_id,
        "action": "AMAZON.NoIntent",
        "parameters": {}
    })

    # Handle request
    voice_response = unified_handler.handle_no(voice_request)

    # Load updated state
    state = load_state(user_id, conv_id)

    result = {
        "speech": voice_response.speech,
        "end": voice_response.should_end_session,
        "conversationId": conv_id
    }

    if state:
        result["index"] = state.get('index', 0)
        result["total"] = len(state.get('results', []))
        if state.get('results') and state.get('index', 0) < len(state['results']):
            result["item"] = state['results'][state['index']]

    return jsonify(result)


@app.route('/test/state', methods=['GET'])
def test_state():
    """Get conversation state (test harness)"""
    user_id = request.args.get('userId', 'test-user')
    conv_id = request.args.get('conversationId', '')

    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400

    state = load_state(user_id, conv_id)
    return jsonify({"state": state})


@app.route('/test/reset', methods=['POST'])
def test_reset():
    """Reset conversation state (test harness)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'test-user')
    conv_id = data.get('conversationId')

    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400

    with db_session() as s:
        q = s.query(SessionState).filter(
            SessionState.user_id == user_id,
            SessionState.conversation_id == conv_id
        )
        deleted = q.delete()

    return jsonify({"ok": True, "deleted": deleted})


@app.route('/test/purge', methods=['POST'])
def test_purge():
    """Purge all or user-specific state (test harness)"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId')

    with db_session() as s:
        if user_id:
            q = s.query(SessionState).filter(SessionState.user_id == user_id)
            deleted = q.delete()
        else:
            deleted = s.query(SessionState).delete()

    return jsonify({"ok": True, "deleted": deleted})


# ========================================
# MAINTENANCE ENDPOINTS
# ========================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database
        with db_session() as s:
            count = s.query(SessionState).count()

        # Check backend (if not in mock mode)
        overseerr_status = "mock" if Config.MOCK_BACKEND else "connected"
        if not Config.MOCK_BACKEND:
            try:
                # Quick connectivity check
                overseerr_status = "connected" if Config.check_connectivity() else "unreachable"
            except:
                overseerr_status = "error"

        return jsonify({
            "status": "healthy",
            "database": "ok",
            "sessions": count,
            "overseerr": overseerr_status,
            "version": "2.0.0"
        })

    except Exception as e:
        log_error("Health check failed", e)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route('/cleanup', methods=['POST'])
def cleanup_endpoint():
    """Manually trigger cleanup of old sessions"""
    try:
        hours = request.args.get('hours', Config.SESSION_TTL_HOURS, type=int)
        deleted = cleanup_old_sessions(hours=hours)

        logger.info(f"Cleanup completed: {deleted} sessions deleted")

        return jsonify({
            "ok": True,
            "deleted": deleted,
            "hours": hours
        })

    except Exception as e:
        log_error("Cleanup failed", e)
        return jsonify({"error": str(e)}), 500


# ========================================
# CONFIGURATION MANAGEMENT ENDPOINTS
# ========================================

@app.route('/config')
def config_ui():
    """Serve the configuration management UI"""
    return send_from_directory('static', 'config_ui.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive values in production)"""
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()
        config = cm.read_config()

        # In production, mask sensitive values for display
        if Config.FLASK_ENV == 'production':
            # Show only last 4 characters of API key
            if 'MEDIA_BACKEND_API_KEY' in config and config['MEDIA_BACKEND_API_KEY']:
                api_key = config['MEDIA_BACKEND_API_KEY']
                if len(api_key) > 8:
                    config['MEDIA_BACKEND_API_KEY'] = '*' * (len(api_key) - 4) + api_key[-4:]

        return jsonify(config)

    except Exception as e:
        log_error("Failed to read config", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration to .env file"""
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()

        new_config = request.get_json()
        if not new_config:
            return jsonify({"error": "No configuration data provided"}), 400

        # Clean up API key
        if 'MEDIA_BACKEND_API_KEY' in new_config:
            api_key = new_config['MEDIA_BACKEND_API_KEY']

            # Check if API key is masked (all asterisks except last 4 chars)
            # If so, restore the original value from the .env file
            if api_key and api_key.startswith('*'):
                # This is a masked value, restore original
                existing_config = cm.read_config()
                if 'MEDIA_BACKEND_API_KEY' in existing_config:
                    new_config['MEDIA_BACKEND_API_KEY'] = existing_config['MEDIA_BACKEND_API_KEY']

            # Add base64 padding to API key if missing (Overseerr API requires it, but UI doesn't show it)
            elif api_key and not api_key.endswith('='):
                # Check if it looks like a base64 string that needs padding
                if len(api_key) % 4 != 0:
                    # Add padding to make it a multiple of 4
                    padding = '=' * (4 - (len(api_key) % 4))
                    new_config['MEDIA_BACKEND_API_KEY'] = api_key + padding
                    logger.info(f"Added base64 padding to API key (Overseerr API requirement)")

        # Validate configuration
        is_valid, error_message = cm.validate_config(new_config)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        # Write configuration
        cm.write_config(new_config)

        logger.info("Configuration updated via web UI")

        return jsonify({
            "success": True,
            "message": "Configuration saved. Restart the service to apply changes."
        })

    except Exception as e:
        log_error("Failed to save config", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/config/test-backend', methods=['POST'])
def test_backend_connection():
    """Test connection to media backend"""
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()

        data = request.get_json()
        if not data or 'url' not in data or 'apiKey' not in data:
            return jsonify({"error": "URL and API key required"}), 400

        result = cm.test_backend_connection(data['url'], data['apiKey'])
        return jsonify(result)

    except Exception as e:
        log_error("Backend test failed", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/config/restart', methods=['POST'])
def restart_service():
    """Restart the Overtalkerr service"""
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()

        success, message = cm.restart_service()

        if success:
            logger.info("Service restart initiated via web UI")
            return jsonify({
                "success": True,
                "message": message
            })
        else:
            logger.error(f"Failed to restart service: {message}")
            return jsonify({
                "success": False,
                "error": message
            }), 500

    except Exception as e:
        log_error("Restart failed", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========================================
# APPLICATION STARTUP
# ========================================

if __name__ == '__main__':
    # Run cleanup on startup
    try:
        deleted = cleanup_old_sessions(hours=Config.SESSION_TTL_HOURS)
        if deleted > 0:
            logger.info(f"Startup cleanup: removed {deleted} old sessions")
    except Exception as e:
        log_error("Startup cleanup failed", e)

    # Start Flask app
    debug_mode = Config.FLASK_ENV == 'development'
    logger.info(f"Starting Overtalkerr in {Config.FLASK_ENV} mode")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode
    )
