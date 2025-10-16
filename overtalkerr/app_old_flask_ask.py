import json
import os
import re
import datetime as dt
from typing import Any, Dict, List, Optional

import base64
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_ask import Ask, statement, question, session
from dotenv import load_dotenv

from db import db_session, SessionState
import overseerr

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
ask = Ask(app, '/')

# Utilities

def _media_type_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    if 'tv' in t or 'show' in t or 'series' in t:
        return 'tv'
    if 'movie' in t or 'film' in t:
        return 'movie'
    return None


def _build_speech_for_item(item: Dict[str, Any], prefix: str) -> str:
    title = item.get('_title') or item.get('title') or item.get('name') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]
    type_word = 'movie' if mtype == 'movie' else 'tv show'
    if year:
        return f"{prefix} the {type_word} {title}, released in {year}, is that the one you want?"
    else:
        return f"{prefix} the {type_word} {title}, is that the one you want?"


def _build_speech_for_next(item: Dict[str, Any]) -> str:
    title = item.get('_title') or 'Unknown title'
    mtype = item.get('_mediaType') or 'title'
    year = None
    if item.get('_releaseDate'):
        year = item['_releaseDate'][:4]
    type_word = 'movie' if mtype == 'movie' else 'tv show'
    if year:
        return f"What about the {type_word} {title}, released in {year}?"
    else:
        return f"What about the {type_word} {title}?"


# Persistence helpers

def _save_state(user_id: str, conversation_id: str, state: Dict[str, Any]):
    with db_session() as s:
        existing = (
            s.query(SessionState)
            .filter(SessionState.user_id == user_id, SessionState.conversation_id == conversation_id)
            .one_or_none()
        )
        payload = json.dumps(state)
        if existing:
            existing.state_json = payload
        else:
            row = SessionState(user_id=user_id, conversation_id=conversation_id, state_json=payload)
            s.add(row)


def _load_state(user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    with db_session() as s:
        row = (
            s.query(SessionState)
            .filter(SessionState.user_id == user_id, SessionState.conversation_id == conversation_id)
            .one_or_none()
        )
        if row:
            try:
                return json.loads(row.state_json)
            except Exception:
                return None
        return None


# Intents

@ask.launch
def launched():
    return question("Hi. You can say, download the movie Jurassic World, or download the upcoming tv show.")


@ask.intent(
    'DownloadIntent',
    mapping={'MediaTitle': 'MediaTitle', 'Year': 'Year', 'MediaType': 'MediaType', 'Upcoming': 'Upcoming'},
)
def download_intent(MediaTitle: Optional[str], Year: Optional[str], MediaType: Optional[str], Upcoming: Optional[str]):
    if not MediaTitle:
        return question("Please tell me the title. For example, say download the movie Jurassic World from 2015.")

    # Normalize
    media_type = _media_type_from_text(MediaType)
    upcoming_only = False
    if Upcoming:
        upcoming_only = Upcoming.lower() in ['yes', 'true', '1', 'upcoming']
    # Also detect the word upcoming within the title phrase
    if MediaTitle and re.search(r"\bupcoming\b", MediaTitle, re.IGNORECASE):
        upcoming_only = True
        # remove the word upcoming from title
        MediaTitle = re.sub(r"\bupcoming\b", "", MediaTitle, flags=re.IGNORECASE).strip()

    # Year normalization: just 4 digits
    year = None
    if Year:
        m = re.search(r"(\d{4})", Year)
        if m:
            year = m.group(1)

    # Search Overseerr
    try:
        results = overseerr.search(MediaTitle, media_type)
    except Exception as e:
        return statement("Sorry, I couldn't reach the request server.")

    # Filter and sort
    ranked = overseerr.pick_best(results, upcoming_only=upcoming_only, year_filter=year)

    if not ranked:
        return statement("That's all I could find, sorry I couldn't help more")

    # Build state
    user_id = (session.user.userId if hasattr(session, 'user') and session.user else 'unknown')
    conv_id = session.sessionId

    state = {
        'query': MediaTitle,
        'media_type': media_type,  # 'movie'|'tv'|None
        'year': year,
        'upcoming_only': upcoming_only,
        'results': ranked,  # store list of dicts
        'index': 0,
    }

    _save_state(user_id, conv_id, state)

    first = ranked[0]
    speech = _build_speech_for_item(first, prefix="I found")
    return question(speech)


@ask.intent('AMAZON.YesIntent')
def yes_intent():
    user_id = (session.user.userId if hasattr(session, 'user') and session.user else 'unknown')
    conv_id = session.sessionId
    state = _load_state(user_id, conv_id)
    if not state:
        return question("Please say the title to start a download request.")

    idx = state.get('index', 0)
    results = state.get('results', [])
    if idx >= len(results):
        return statement("That's all I could find, sorry I couldn't help more")

    chosen = results[idx]
    media_id = chosen.get('id') or chosen.get('mediaId') or chosen.get('tmdbId')
    media_type = chosen.get('_mediaType') or state.get('media_type') or 'movie'

    if not media_id:
        return statement("Sorry, I couldn't determine the item ID.")

    try:
        overseerr.request_media(int(media_id), media_type)
    except Exception:
        return statement("Sorry, I couldn't create the request.")

    return statement("OK done")


@ask.intent('AMAZON.NoIntent')
def no_intent():
    user_id = (session.user.userId if hasattr(session, 'user') and session.user else 'unknown')
    conv_id = session.sessionId
    state = _load_state(user_id, conv_id)
    if not state:
        return question("Please tell me the title. For example, say download the movie Jurassic World from 2015.")

    idx = state.get('index', 0) + 1
    results = state.get('results', [])

    if idx >= len(results):
        return statement("That's all I could find, sorry I couldn't help more")

    state['index'] = idx
    _save_state(user_id, conv_id, state)

    nxt = results[idx]
    speech = _build_speech_for_next(nxt)
    return question(speech)


@ask.intent('AMAZON.HelpIntent')
def help_intent():
    return question("You can say: download the movie Jurassic World from 2015. Or: download the upcoming tv show Robin Hood.")


@ask.intent('AMAZON.FallbackIntent')
def fallback_intent():
    return question("Sorry, I didn't catch that. Try saying, download the movie Jurassic World from 2015.")


@ask.session_ended
def session_ended():
    return statement("Goodbye")


# ----------------------
# Test harness (no Alexa)
# ----------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


def _simulate_start(user_id: str, conv_id: str, title: str, year: Optional[str], media_type_text: Optional[str], upcoming: bool) -> Dict[str, Any]:
    media_type = _media_type_from_text(media_type_text)

    # Remove the word upcoming from title if present
    if re.search(r"\\bupcoming\\b", title, re.IGNORECASE):
        upcoming = True
        title = re.sub(r"\\bupcoming\\b", "", title, flags=re.IGNORECASE).strip()

    # year normalization: ensure 4 digits only
    if year:
        m = re.search(r"(\\d{4})", year)
        year = m.group(1) if m else None

    try:
        results = overseerr.search(title, media_type)
    except Exception:
        return {"speech": "Sorry, I couldn't reach the request server.", "end": True}

    ranked = overseerr.pick_best(results, upcoming_only=upcoming, year_filter=year)
    if not ranked:
        return {"speech": "That's all I could find, sorry I couldn't help more", "end": True}

    state = {
        'query': title,
        'media_type': media_type,
        'year': year,
        'upcoming_only': upcoming,
        'results': ranked,
        'index': 0,
    }
    _save_state(user_id, conv_id, state)

    first = ranked[0]
    speech = _build_speech_for_item(first, prefix="I found")
    return {"speech": speech, "index": 0, "total": len(ranked), "item": first}


def _is_local_ip(ip: str) -> bool:
    if not ip:
        return False
    return (
        ip.startswith('127.') or ip == '::1' or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.') or ip.startswith('172.17.') or ip.startswith('172.18.') or ip.startswith('172.19.') or ip.startswith('172.2')
    )


def _needs_auth() -> bool:
    # Only protect /test endpoints when request is not from local network
    path = request.path or ''
    if not path.startswith('/test'):
        return False
    # get client ip (consider X-Forwarded-For)
    xff = request.headers.get('X-Forwarded-For', '')
    ip = (xff.split(',')[0].strip() if xff else request.remote_addr) or ''
    if _is_local_ip(ip):
        return False
    # Require auth only if creds are configured
    return bool(os.getenv('BASIC_AUTH_USER') and os.getenv('BASIC_AUTH_PASS'))


def _check_basic_auth() -> Optional[Response]:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Basic '):
        return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Test"'})
    try:
        raw = base64.b64decode(auth.split(' ', 1)[1]).decode('utf-8')
        user, pwd = raw.split(':', 1)
    except Exception:
        return Response('Invalid auth header', 401, {'WWW-Authenticate': 'Basic realm="Test"'})
    if user == os.getenv('BASIC_AUTH_USER') and pwd == os.getenv('BASIC_AUTH_PASS'):
        return None
    return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Test"'})


@app.before_request
def _protect_test_endpoints():
    if _needs_auth():
        failure = _check_basic_auth()
        if failure is not None:
            return failure


@app.route('/test', methods=['GET'])
def test_ui():
    # Serve simple HTML UI
    return send_from_directory(STATIC_DIR, 'test_ui.html')


@app.route('/test/start', methods=['POST'])
def test_start():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId') or 'test-user'
    conv_id = data.get('conversationId') or f"conv-{int(dt.datetime.utcnow().timestamp())}"
    title = data.get('title') or ''
    year = data.get('year')
    media_type_text = data.get('mediaType')
    upcoming = bool(data.get('upcoming'))
    if not title:
        return jsonify({"error": "title is required"}), 400
    result = _simulate_start(user_id, conv_id, title, year, media_type_text, upcoming)
    result.update({"userId": user_id, "conversationId": conv_id})
    return jsonify(result)


@app.route('/test/yes', methods=['POST'])
def test_yes():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId') or 'test-user'
    conv_id = data.get('conversationId')
    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400
    state = _load_state(user_id, conv_id)
    if not state:
        return jsonify({"speech": "Please start a search first."}), 400
    idx = state.get('index', 0)
    results = state.get('results', [])
    if idx >= len(results):
        return jsonify({"speech": "That's all I could find, sorry I couldn't help more", "end": True})
    chosen = results[idx]
    media_id = chosen.get('id') or chosen.get('mediaId') or chosen.get('tmdbId')
    media_type = chosen.get('_mediaType') or state.get('media_type') or 'movie'
    if not media_id:
        return jsonify({"speech": "Sorry, I couldn't determine the item ID.", "end": True}), 500
    try:
        overseerr.request_media(int(media_id), media_type)
    except Exception as e:
        return jsonify({"speech": "Sorry, I couldn't create the request.", "error": str(e)}), 502
    return jsonify({"speech": "OK done", "requested": {"mediaId": media_id, "mediaType": media_type}})


@app.route('/test/no', methods=['POST'])
def test_no():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId') or 'test-user'
    conv_id = data.get('conversationId')
    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400
    state = _load_state(user_id, conv_id)
    if not state:
        return jsonify({"speech": "Please start a search first."}), 400
    idx = state.get('index', 0) + 1
    results = state.get('results', [])
    if idx >= len(results):
        return jsonify({"speech": "That's all I could find, sorry I couldn't help more", "end": True})
    state['index'] = idx
    _save_state(user_id, conv_id, state)
    nxt = results[idx]
    return jsonify({"speech": _build_speech_for_next(nxt), "index": idx, "total": len(results), "item": nxt})


@app.route('/test/state', methods=['GET'])
def test_state():
    user_id = request.args.get('userId', 'test-user')
    conv_id = request.args.get('conversationId', '')
    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400
    state = _load_state(user_id, conv_id)
    return jsonify({"state": state})


@app.route('/test/info', methods=['GET'])
def test_info():
    # Expose basic info for the UI
    return jsonify({
        "mock": bool(getattr(overseerr, 'MOCK', False)),
        "authProtected": _needs_auth(),
    })


@app.route('/test/reset', methods=['POST'])
def test_reset():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId') or 'test-user'
    conv_id = data.get('conversationId')
    if not conv_id:
        return jsonify({"error": "conversationId is required"}), 400
    with db_session() as s:
        q = s.query(SessionState).filter(SessionState.user_id == user_id, SessionState.conversation_id == conv_id)
        deleted = q.delete()
    return jsonify({"ok": True, "deleted": deleted})


@app.route('/test/purge', methods=['POST'])
def test_purge():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId')
    with db_session() as s:
        if user_id:
            q = s.query(SessionState).filter(SessionState.user_id == user_id)
            deleted = q.delete()
        else:
            deleted = s.query(SessionState).delete()
    return jsonify({"ok": True, "deleted": deleted})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
