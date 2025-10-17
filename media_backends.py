"""
Abstraction layer for multiple media request backends.

Supports:
- Overseerr
- Jellyseerr (Overseerr fork - API compatible)
- Ombi

This allows Overtalkerr to work with any of these services with minimal configuration.
"""
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from enum import Enum
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config import Config
from logger import logger, log_error, log_overseerr_call


class BackendType(Enum):
    """Supported backend types"""
    OVERSEERR = "overseerr"
    JELLYSEERR = "jellyseerr"
    OMBI = "ombi"


class MediaBackendError(Exception):
    """Base exception for backend errors"""
    pass


class MediaBackendConnectionError(MediaBackendError):
    """Connection failed"""
    pass


class MediaBackendAuthError(MediaBackendError):
    """Authentication failed"""
    pass


class MediaBackend(ABC):
    """Abstract base class for media request backends"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.timeout = (5, 30)  # Connect, read timeout

    @abstractmethod
    def search(self, query: str, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for media"""
        pass

    @abstractmethod
    def request_media(self, media_id: int, media_type: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Request media to be downloaded"""
        pass

    @abstractmethod
    def get_details(self, media_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about media including cast"""
        pass

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        pass

    @abstractmethod
    def normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize result to common format"""
        pass


class OverseerrBackend(MediaBackend):
    """Overseerr backend implementation"""

    def get_headers(self) -> Dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search(self, query: str, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search Overseerr"""
        # Manually encode query to use %20 instead of + for spaces
        # Some Overseerr versions (especially develop builds) are strict about this
        encoded_query = quote(query, safe='')
        url = f"{self.base_url}/api/v1/search?query={encoded_query}"

        try:
            resp = self.session.get(url, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            # Log the response for debugging 400 errors
            if resp.status_code == 400:
                try:
                    error_body = resp.json()
                    logger.error(f"Overseerr 400 error: {error_body}")
                except:
                    logger.error(f"Overseerr 400 error (raw): {resp.text}")

            resp.raise_for_status()
            data = resp.json() or {}
            results = data.get("results", [])

            # Normalize and filter
            enriched = []
            for r in results:
                rtype = r.get("mediaType") or r.get("type")
                if media_type and rtype and rtype != media_type:
                    continue
                enriched.append(self.normalize_result(r))

            logger.info(f"Overseerr search: {len(enriched)} results for '{query}'")
            return enriched

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")
        except Exception as e:
            raise MediaBackendError(f"Search failed: {str(e)}")

    def request_media(self, media_id: int, media_type: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Request media in Overseerr"""
        url = f"{self.base_url}/api/v1/request"
        payload: Dict[str, Any] = {
            "mediaId": int(media_id),
            "mediaType": media_type,
        }

        if media_type == 'tv':
            if season is not None:
                # Request specific season
                payload["seasons"] = [season]
            else:
                # Request all seasons (using "all" keyword that Overseerr supports)
                # Note: This will request all available seasons
                payload["seasons"] = "all"

        try:
            resp = self.session.post(url, json=payload, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            if resp.status_code == 409:
                return {"message": "Media already requested", "mediaId": media_id, "mediaType": media_type}

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")
        except Exception as e:
            raise MediaBackendError(f"Request failed: {str(e)}")

    def get_details(self, media_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a movie or TV show including cast.

        Returns:
            Dict with 'cast' field containing list of actor names, or None if fetch fails
        """
        # Overseerr/TMDB provides detailed info at /api/v1/{movie|tv}/{tmdbId}
        endpoint = f"api/v1/{media_type}/{media_id}"
        url = f"{self.base_url}/{endpoint}"

        try:
            resp = self.session.get(url, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code == 404:
                logger.warning(f"Media details not found: {media_type} {media_id}")
                return None

            if resp.status_code in [401, 403]:
                logger.warning(f"Auth failed fetching details for {media_type} {media_id}")
                return None

            resp.raise_for_status()
            details = resp.json()

            # Extract cast from credits
            credits = details.get('credits', {})
            cast_list = credits.get('cast', [])

            # Get top 2-3 cast members
            cast_names = [person.get('name') for person in cast_list[:3] if person.get('name')]

            return {
                'cast': cast_names,
                'director': self._extract_director(credits),
                'genres': [g.get('name') for g in details.get('genres', [])],
            }

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching details for {media_type} {media_id}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error fetching details for {media_type} {media_id}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching details for {media_type} {media_id}: {e}")
            return None

    def _extract_director(self, credits: Dict[str, Any]) -> Optional[str]:
        """Extract director name from credits (movies only)"""
        crew = credits.get('crew', [])
        for person in crew:
            if person.get('job') == 'Director':
                return person.get('name')
        return None

    def normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Overseerr result with media status information"""
        from overseerr import normalize_release_date, parse_date

        rcopy = dict(result)
        rcopy["_releaseDate"] = normalize_release_date(rcopy)
        rcopy["_date"] = parse_date(rcopy.get("_releaseDate"))
        rcopy["_title"] = rcopy.get("title") or rcopy.get("name") or ""
        rcopy["_mediaType"] = rcopy.get("mediaType") or rcopy.get("type")

        # Extract media availability status
        # 1=UNKNOWN, 2=PENDING, 3=PROCESSING, 4=PARTIALLY_AVAILABLE, 5=AVAILABLE, 6=DELETED
        media_info = rcopy.get("mediaInfo", {})
        status = media_info.get("status", 1)  # Default to UNKNOWN

        rcopy["_mediaStatus"] = status
        rcopy["_isAvailable"] = status == 5  # AVAILABLE
        rcopy["_isPartiallyAvailable"] = status == 4  # PARTIALLY_AVAILABLE
        rcopy["_isPending"] = status == 2  # PENDING (requested but not approved)
        rcopy["_isProcessing"] = status == 3  # PROCESSING (downloading)
        rcopy["_hasRequests"] = len(media_info.get("requests", [])) > 0

        # For TV shows, extract available episode counts if partially available
        if rcopy.get("_mediaType") == "tv" and status == 4:
            # Count available episodes from seasons data in mediaInfo
            seasons = media_info.get("seasons", [])
            available_episodes = 0
            total_episodes = 0
            for season in seasons:
                # Skip season 0 (specials)
                if season.get("seasonNumber", 0) == 0:
                    continue
                # episodeFileCount = episodes actually available
                available_episodes += season.get("episodeFileCount", 0)
                total_episodes += season.get("episodeCount", 0)

            rcopy["_availableEpisodes"] = available_episodes if available_episodes > 0 else None
            rcopy["_totalEpisodes"] = total_episodes if total_episodes > 0 else None

        # Human-readable status
        status_map = {
            1: "unknown",
            2: "pending",
            3: "processing",
            4: "partially_available",
            5: "available",
            6: "deleted"
        }
        rcopy["_statusText"] = status_map.get(status, "unknown")

        return rcopy


class JellyseerrBackend(OverseerrBackend):
    """
    Jellyseerr backend (fork of Overseerr).

    API is nearly identical to Overseerr, so we inherit most functionality.
    """

    def search(self, query: str, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search Jellyseerr (uses Overseerr API)"""
        logger.info(f"Jellyseerr search for '{query}'")
        return super().search(query, media_type)

    def request_media(self, media_id: int, media_type: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Request media in Jellyseerr"""
        logger.info(f"Jellyseerr request: {media_type} {media_id}")
        return super().request_media(media_id, media_type, season)


class OmbiBackend(MediaBackend):
    """Ombi backend implementation"""

    def get_headers(self) -> Dict[str, str]:
        return {
            "ApiKey": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search(self, query: str, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search Ombi.

        Ombi has separate endpoints for movies and TV shows.
        """
        results = []

        # Search movies if not specifically looking for TV
        if media_type != 'tv':
            try:
                movie_results = self._search_movies(query)
                results.extend(movie_results)
            except Exception as e:
                logger.error(f"Ombi movie search failed: {e}")

        # Search TV if not specifically looking for movies
        if media_type != 'movie':
            try:
                tv_results = self._search_tv(query)
                results.extend(tv_results)
            except Exception as e:
                logger.error(f"Ombi TV search failed: {e}")

        logger.info(f"Ombi search: {len(results)} results for '{query}'")
        return results

    def _search_movies(self, query: str) -> List[Dict[str, Any]]:
        """Search Ombi for movies"""
        url = f"{self.base_url}/api/v1/Search/movie/{query}"

        try:
            resp = self.session.get(url, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            resp.raise_for_status()
            results = resp.json() or []

            return [self.normalize_result(r, 'movie') for r in results]

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")

    def _search_tv(self, query: str) -> List[Dict[str, Any]]:
        """Search Ombi for TV shows"""
        url = f"{self.base_url}/api/v1/Search/tv/{query}"

        try:
            resp = self.session.get(url, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            resp.raise_for_status()
            results = resp.json() or []

            return [self.normalize_result(r, 'tv') for r in results]

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")

    def request_media(self, media_id: int, media_type: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Request media in Ombi"""
        if media_type == 'movie':
            return self._request_movie(media_id)
        else:
            return self._request_tv(media_id, season)

    def _request_movie(self, media_id: int) -> Dict[str, Any]:
        """Request movie in Ombi"""
        url = f"{self.base_url}/api/v1/Request/movie"
        payload = {
            "theMovieDbId": media_id,
        }

        try:
            resp = self.session.post(url, json=payload, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            resp.raise_for_status()
            result = resp.json()

            logger.info(f"Ombi movie request: {media_id}")
            return result

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")

    def _request_tv(self, media_id: int, season: Optional[int] = None) -> Dict[str, Any]:
        """Request TV show in Ombi"""
        url = f"{self.base_url}/api/v1/Request/tv"

        # Ombi requires more details for TV requests
        # We need to fetch the show details first
        show_url = f"{self.base_url}/api/v1/Search/tv/moviedb/{media_id}"

        try:
            # Get show details
            show_resp = self.session.get(show_url, headers=self.get_headers(), timeout=self.timeout)
            show_resp.raise_for_status()
            show_data = show_resp.json()

            # Build request payload
            payload = {
                "tvDbId": show_data.get("id"),  # Ombi uses TVDB ID
                "requestAll": season is None,  # Request all seasons if no specific season
            }

            if season is not None:
                # Request specific season
                payload["latestSeason"] = False
                payload["requestAll"] = False
                payload["seasons"] = [{
                    "seasonNumber": season,
                    "episodes": []  # Empty = all episodes
                }]

            # Submit request
            resp = self.session.post(url, json=payload, headers=self.get_headers(), timeout=self.timeout)

            if resp.status_code in [401, 403]:
                raise MediaBackendAuthError("Invalid API key")

            resp.raise_for_status()
            result = resp.json()

            logger.info(f"Ombi TV request: {media_id}, season: {season}")
            return result

        except requests.exceptions.Timeout:
            raise MediaBackendConnectionError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise MediaBackendConnectionError("Connection failed")

    def get_details(self, media_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about media including cast.

        Note: Ombi doesn't have a built-in endpoint for detailed media info with cast,
        so this is a stub that returns None. Cast information won't be available for Ombi users.
        """
        logger.debug(f"Ombi doesn't support get_details for {media_type} {media_id}")
        return None

    def normalize_result(self, result: Dict[str, Any], media_type: str) -> Dict[str, Any]:
        """
        Normalize Ombi result to match Overseerr format with status information.

        Ombi uses different field names, so we need to map them.
        """
        from overseerr import parse_date

        # Ombi uses different field names
        normalized = {
            "id": result.get("id") or result.get("theMovieDbId"),
            "mediaType": media_type,
            "_mediaType": media_type,
        }

        if media_type == 'movie':
            normalized["title"] = result.get("title")
            normalized["_title"] = result.get("title")
            normalized["releaseDate"] = result.get("releaseDate")
            normalized["_releaseDate"] = result.get("releaseDate")
        else:  # TV
            normalized["name"] = result.get("title") or result.get("name")
            normalized["_title"] = result.get("title") or result.get("name")
            normalized["firstAirDate"] = result.get("firstAired") or result.get("releaseDate")
            normalized["_releaseDate"] = result.get("firstAired") or result.get("releaseDate")

        normalized["_date"] = parse_date(normalized.get("_releaseDate"))

        # Extract Ombi availability status
        # Ombi uses different field names: 'available', 'requested', 'approved', etc.
        is_available = result.get("available", False)
        is_requested = result.get("requested", False)
        is_approved = result.get("approved", False)

        # Map Ombi status to Overseerr-like status codes
        if is_available:
            status = 5  # AVAILABLE
            status_text = "available"
        elif is_approved:
            status = 3  # PROCESSING
            status_text = "processing"
        elif is_requested:
            status = 2  # PENDING
            status_text = "pending"
        else:
            status = 1  # UNKNOWN
            status_text = "unknown"

        normalized["_mediaStatus"] = status
        normalized["_isAvailable"] = is_available
        normalized["_isPartiallyAvailable"] = False  # Ombi doesn't have partial availability
        normalized["_isPending"] = is_requested and not is_approved
        normalized["_isProcessing"] = is_approved and not is_available
        normalized["_hasRequests"] = is_requested
        normalized["_statusText"] = status_text

        return normalized


class BackendFactory:
    """Factory for creating media backend instances"""

    @staticmethod
    def detect_backend_type(base_url: str, api_key: str) -> BackendType:
        """
        Auto-detect backend type by checking API endpoints.

        Returns:
            BackendType enum value
        """
        # Try Overseerr/Jellyseerr API (they use the same endpoints)
        try:
            headers = {"X-Api-Key": api_key}
            resp = requests.get(f"{base_url}/api/v1/status", headers=headers, timeout=5)

            if resp.ok:
                data = resp.json()
                # Check if it's Jellyseerr
                if "jellyseerr" in data.get("version", "").lower():
                    logger.info("Detected Jellyseerr backend")
                    return BackendType.JELLYSEERR
                else:
                    logger.info("Detected Overseerr backend")
                    return BackendType.OVERSEERR
        except:
            pass

        # Try Ombi API
        try:
            headers = {"ApiKey": api_key}
            resp = requests.get(f"{base_url}/api/v1/Status", headers=headers, timeout=5)

            if resp.ok:
                logger.info("Detected Ombi backend")
                return BackendType.OMBI
        except:
            pass

        # Default to Overseerr (most common)
        logger.warning("Could not detect backend type, defaulting to Overseerr")
        return BackendType.OVERSEERR

    @staticmethod
    def create(backend_type: Optional[BackendType] = None, base_url: Optional[str] = None, api_key: Optional[str] = None) -> MediaBackend:
        """
        Create a media backend instance.

        Args:
            backend_type: Specific backend type (auto-detected if None)
            base_url: API base URL (from config if None)
            api_key: API key (from config if None)

        Returns:
            MediaBackend instance
        """
        base_url = base_url or Config.MEDIA_BACKEND_URL
        api_key = api_key or Config.MEDIA_BACKEND_API_KEY

        # Auto-detect if not specified
        if backend_type is None:
            backend_type = BackendFactory.detect_backend_type(base_url, api_key)

        # Create appropriate backend
        if backend_type == BackendType.OVERSEERR:
            return OverseerrBackend(base_url, api_key)
        elif backend_type == BackendType.JELLYSEERR:
            return JellyseerrBackend(base_url, api_key)
        elif backend_type == BackendType.OMBI:
            return OmbiBackend(base_url, api_key)
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")


# Global backend instance (auto-detected)
_backend_instance = None


def get_backend() -> MediaBackend:
    """Get the configured media backend (singleton)"""
    global _backend_instance

    if _backend_instance is None:
        if Config.MOCK_BACKEND:
            logger.info("Mock mode enabled - using mock backend")
            # For mock mode, just use Overseerr backend (it handles mocking internally)
            _backend_instance = OverseerrBackend(Config.MEDIA_BACKEND_URL, Config.MEDIA_BACKEND_API_KEY)
        else:
            _backend_instance = BackendFactory.create()
            logger.info(f"Initialized {type(_backend_instance).__name__}")

    return _backend_instance
