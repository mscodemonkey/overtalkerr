import os
import datetime as dt
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config import Config
from logger import logger, log_error, log_overseerr_call
from media_backends import get_backend, MediaBackendError, MediaBackendConnectionError, MediaBackendAuthError

# Use configuration instead of direct env vars
BASE = Config.MEDIA_BACKEND_URL.rstrip("/")
API_KEY = Config.MEDIA_BACKEND_API_KEY
MOCK = Config.MOCK_BACKEND

HEADERS = {
    "X-Api-Key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Request timeout settings (connect timeout, read timeout)
TIMEOUT = (5, 30)

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,  # Wait 1s, 2s, 4s between retries
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
)

# Create session with retry adapter
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Get backend instance (auto-detects Overseerr/Jellyseerr/Ombi)
_backend = get_backend()

# Helper: normalize release date for movie/tv

def normalize_release_date(item: Dict[str, Any]) -> Optional[str]:
    # Overseerr returns either releaseDate (movies) or firstAirDate (tv)
    date = item.get("releaseDate") or item.get("firstAirDate")
    return date


def parse_date(date_str: Optional[str]) -> Optional[dt.date]:
    if not date_str:
        return None
    try:
        return dt.date.fromisoformat(date_str[:10])
    except Exception:
        return None


class OverseerrError(MediaBackendError):
    """Base exception for Overseerr API errors (alias for MediaBackendError)"""
    pass


class OverseerrConnectionError(MediaBackendConnectionError):
    """Raised when unable to connect to Overseerr (alias for MediaBackendConnectionError)"""
    pass


class OverseerrAuthError(MediaBackendAuthError):
    """Raised when authentication fails (alias for MediaBackendAuthError)"""
    pass


class OverseerrNotFoundError(OverseerrError):
    """Raised when requested resource not found"""
    pass


def search(query: str, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for media using the configured backend (Overseerr/Jellyseerr/Ombi).

    Args:
        query: Search query string
        media_type: 'movie' or 'tv' or None for mixed

    Returns:
        List of search results with enriched fields

    Raises:
        OverseerrConnectionError: If unable to connect to backend
        OverseerrAuthError: If authentication fails
        OverseerrError: For other API errors
    """
    if MOCK:
        logger.info(f"Mock search: query='{query}', media_type={media_type}")
        # Fabricate a few plausible results for testing
        today = dt.date.today()
        future = today.replace(year=today.year + 1)
        items: List[Dict[str, Any]] = []

        def make_item(idx: int, title: str, mt: str, date: Optional[dt.date]) -> Dict[str, Any]:
            base: Dict[str, Any] = {
                "id": 1000 + idx,
                "mediaType": mt,
                "title": title if mt == "movie" else None,
                "name": title if mt == "tv" else None,
                "releaseDate": date.isoformat() if mt == "movie" and date else None,
                "firstAirDate": date.isoformat() if mt == "tv" and date else None,
            }
            # Enrich as the real code would
            rcopy = dict(base)
            rcopy["_releaseDate"] = normalize_release_date(rcopy)
            rcopy["_date"] = parse_date(rcopy.get("_releaseDate"))
            rcopy["_title"] = rcopy.get("title") or rcopy.get("name") or ""
            rcopy["_mediaType"] = mt
            return rcopy

        base_title = query.strip().title() if query else "Sample Title"
        candidates = [
            make_item(1, base_title, media_type or "movie", today.replace(year=max(2000, today.year - 10))),
            make_item(2, f"{base_title} Rebirth", media_type or "movie", today.replace(year=today.year)),
            make_item(3, base_title, media_type or "tv", future),
        ]
        # Filter by media_type if provided
        if media_type:
            candidates = [c for c in candidates if c.get("_mediaType") == media_type]

        log_overseerr_call("search", True, query=query, media_type=media_type, result_count=len(candidates))
        return candidates

    # Use the backend abstraction
    try:
        logger.debug(f"Searching backend: query='{query}', media_type={media_type}")
        results = _backend.search(query, media_type)

        log_overseerr_call("search", True, query=query, media_type=media_type, result_count=len(results))
        return results

    except MediaBackendAuthError as e:
        log_error("Backend authentication failed", e)
        raise OverseerrAuthError(str(e))
    except MediaBackendConnectionError as e:
        log_error("Backend connection failed", e, query=query)
        raise OverseerrConnectionError(str(e))
    except MediaBackendError as e:
        log_error("Backend error during search", e, query=query)
        raise OverseerrError(str(e))
    except Exception as e:
        log_error("Unexpected error during backend search", e, query=query)
        raise OverseerrError(f"Unexpected error: {str(e)}")


def pick_best(results: List[Dict[str, Any]], *, upcoming_only: bool, year_filter: Optional[tuple[int, int]]) -> List[Dict[str, Any]]:
    """Return results sorted according to rules.
    - Prioritizes intelligent match tier (_combined_score from fuzzy matching)
    - upcoming_only => release date in the future ranked first
    - year_filter => keep where year is in range (start_year, end_year) inclusive
    - otherwise, sort by match quality then by most recent release date desc
    """
    today = dt.date.today()

    # Apply year filter strictly (now supports year ranges)
    if year_filter:
        start_year, end_year = year_filter
        filtered = []
        for r in results:
            release_date = r.get("_releaseDate", "")
            if release_date:
                try:
                    year = int(release_date[:4])
                    if start_year <= year <= end_year:
                        filtered.append(r)
                except (ValueError, IndexError):
                    pass
        results = filtered

    def score(r: Dict[str, Any]) -> Tuple[int, int, int]:
        # Upcoming score: 1 if in future and upcoming_only requested
        rdate = r.get("_date")
        upcoming_score = 1 if upcoming_only and rdate and rdate > today else 0

        # Use intelligent match score if available (from fuzzy_match_results)
        # This respects exact matches, starts-with, contains, etc.
        match_quality = r.get("_combined_score", 0)

        # More recent is better (but less important than match quality)
        recency = rdate.toordinal() if rdate else 0

        return (upcoming_score, match_quality, recency)

    # Primary sort: upcoming score desc, match quality desc, then recency desc
    results_sorted = sorted(results, key=lambda r: score(r), reverse=True)
    return results_sorted


def get_media_details(media_id: int, media_type: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific media item including cast.

    Args:
        media_id: TMDB media ID
        media_type: 'movie' or 'tv'

    Returns:
        Dict with 'cast' (list of names), 'director' (str), 'genres' (list), or None if unavailable
    """
    try:
        logger.debug(f"Fetching details for {media_type} {media_id}")
        details = _backend.get_details(media_id, media_type)
        if details:
            logger.info(f"Got details for {media_type} {media_id}: {len(details.get('cast', []))} cast members")
        return details
    except Exception as e:
        logger.warning(f"Failed to fetch details for {media_type} {media_id}: {e}")
        return None


def request_media(media_id: int, media_type: str, season: Optional[int] = None) -> Dict[str, Any]:
    """
    Create a media request using the configured backend (Overseerr/Jellyseerr/Ombi).

    Args:
        media_id: TMDB media ID
        media_type: 'movie' or 'tv'
        season: For TV shows, specific season number (None = all seasons)

    Returns:
        Response dict from backend

    Raises:
        OverseerrConnectionError: If unable to connect to backend
        OverseerrAuthError: If authentication fails
        OverseerrError: For other API errors
    """
    if MOCK:
        logger.info(f"Mock request: media_id={media_id}, media_type={media_type}, season={season}")
        # Simulate a successful request
        result = {
            "requestId": 9999,
            "mediaId": media_id,
            "mediaType": media_type,
            "season": season,
            "status": "mocked"
        }
        log_overseerr_call("request_media", True, media_id=media_id, media_type=media_type, season=season)
        return result

    # Use the backend abstraction
    try:
        logger.debug(f"Creating backend request: media_id={media_id}, media_type={media_type}, season={season}")
        result = _backend.request_media(media_id, media_type, season)

        log_overseerr_call("request_media", True, media_id=media_id, media_type=media_type, season=season)
        return result

    except MediaBackendAuthError as e:
        log_error("Backend authentication failed during request creation", e)
        raise OverseerrAuthError(str(e))
    except MediaBackendConnectionError as e:
        log_error("Backend connection failed", e, media_id=media_id, media_type=media_type)
        raise OverseerrConnectionError(str(e))
    except MediaBackendError as e:
        log_error("Backend error during request", e, media_id=media_id)
        raise OverseerrError(str(e))
    except Exception as e:
        log_error("Unexpected error during backend request", e, media_id=media_id)
        raise OverseerrError(f"Unexpected error: {str(e)}")
