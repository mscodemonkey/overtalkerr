"""
Enhanced search capabilities for Overtalkerr.

Features:
- Fuzzy matching for typos and speech recognition errors
- Actor/director/cast search
- Genre filtering
- Natural language date parsing
- Trending/popular content discovery
- Smart query parsing
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process
import dateparser
from logger import logger


class SearchEnhancer:
    """Enhances search queries with fuzzy matching and NLP"""

    # Common speech recognition errors
    COMMON_SUBSTITUTIONS = {
        'jurrasic': 'jurassic',
        'harry potter': 'harry potter',
        'lord of the rings': 'lord of the rings',
        'game of thrones': 'game of thrones',
        'breaking bad': 'breaking bad',
        'the office': 'the office',
        'stranger things': 'stranger things',
        'the mandalorian': 'the mandalorian',
        'wandavision': 'wandavision',
        'the witcher': 'the witcher',
    }

    # Genre keywords
    GENRE_KEYWORDS = {
        'action': ['action', 'adventure', 'thriller'],
        'comedy': ['comedy', 'funny', 'humor'],
        'drama': ['drama', 'dramatic'],
        'horror': ['horror', 'scary', 'frightening'],
        'scifi': ['sci-fi', 'science fiction', 'scifi', 'sci fi'],
        'fantasy': ['fantasy', 'magical'],
        'romance': ['romance', 'romantic', 'love story'],
        'documentary': ['documentary', 'docuseries'],
        'animation': ['animated', 'animation', 'cartoon'],
        'crime': ['crime', 'detective', 'mystery'],
        'superhero': ['superhero', 'marvel', 'dc', 'comic'],
    }

    # Actor/director indicators
    CAST_INDICATORS = [
        'with', 'starring', 'by', 'directed by',
        'featuring', 'actor', 'actress', 'director'
    ]

    # Temporal keywords
    TEMPORAL_KEYWORDS = {
        'recent': 90,  # Last 90 days
        'new': 180,   # Last 6 months
        'latest': 90,
        'upcoming': -90,  # Next 90 days
        'coming soon': -60,
        'this year': 'current_year',
        'last year': 'last_year',
    }

    @staticmethod
    def correct_common_typos(query: str) -> str:
        """Correct common typos and speech recognition errors"""
        query_lower = query.lower()

        for wrong, correct in SearchEnhancer.COMMON_SUBSTITUTIONS.items():
            if wrong in query_lower:
                query = re.sub(re.escape(wrong), correct, query, flags=re.IGNORECASE)
                logger.debug(f"Corrected typo: '{wrong}' -> '{correct}'")

        return query

    @staticmethod
    def extract_cast_info(query: str) -> Tuple[str, Optional[str]]:
        """
        Extract actor/director info from query.

        Returns:
            (cleaned_query, cast_member_name)
        """
        for indicator in SearchEnhancer.CAST_INDICATORS:
            pattern = rf'\b{re.escape(indicator)}\s+([a-zA-Z\s]+?)(?:\s|$)'
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                cast_name = match.group(1).strip()
                cleaned_query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
                logger.info(f"Extracted cast: '{cast_name}' from query")
                return cleaned_query, cast_name

        return query, None

    @staticmethod
    def extract_genre(query: str) -> Tuple[str, Optional[str]]:
        """
        Extract genre from query.

        Returns:
            (cleaned_query, genre)
        """
        query_lower = query.lower()

        for genre, keywords in SearchEnhancer.GENRE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Remove genre keyword from query
                    cleaned = re.sub(rf'\b{re.escape(keyword)}\b', '', query, flags=re.IGNORECASE)
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                    logger.info(f"Extracted genre: '{genre}' from keyword '{keyword}'")
                    return cleaned, genre

        return query, None

    @staticmethod
    def extract_temporal_info(query: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Extract temporal information from query.

        Returns:
            (cleaned_query, temporal_filter)
            temporal_filter: {'type': 'relative', 'days': 90} or {'type': 'year', 'year': 2023}
        """
        query_lower = query.lower()

        # Check for temporal keywords
        for keyword, value in SearchEnhancer.TEMPORAL_KEYWORDS.items():
            if keyword in query_lower:
                cleaned = re.sub(rf'\b{re.escape(keyword)}\b', '', query, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()

                if isinstance(value, int):
                    temporal_filter = {'type': 'relative', 'days': value}
                elif value == 'current_year':
                    from datetime import datetime
                    temporal_filter = {'type': 'year', 'year': datetime.now().year}
                elif value == 'last_year':
                    from datetime import datetime
                    temporal_filter = {'type': 'year', 'year': datetime.now().year - 1}

                logger.info(f"Extracted temporal filter: {temporal_filter}")
                return cleaned, temporal_filter

        # Try natural language date parsing
        date_match = re.search(r'from\s+(\d{4})', query, re.IGNORECASE)
        if date_match:
            year = int(date_match.group(1))
            cleaned = re.sub(r'from\s+\d{4}', '', query, flags=re.IGNORECASE).strip()
            temporal_filter = {'type': 'year', 'year': year}
            logger.info(f"Extracted year filter: {year}")
            return cleaned, temporal_filter

        return query, None

    @staticmethod
    def parse_enhanced_query(query: str) -> Dict[str, Any]:
        """
        Parse query with all enhancements.

        Returns dict with:
        - cleaned_query: The search term
        - cast: Actor/director name if found
        - genre: Genre if found
        - temporal: Temporal filter if found
        - original: Original query
        """
        original = query

        # Step 1: Correct typos
        query = SearchEnhancer.correct_common_typos(query)

        # Step 2: Extract cast
        query, cast = SearchEnhancer.extract_cast_info(query)

        # Step 3: Extract genre
        query, genre = SearchEnhancer.extract_genre(query)

        # Step 4: Extract temporal info
        query, temporal = SearchEnhancer.extract_temporal_info(query)

        # Clean up extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()

        result = {
            'cleaned_query': query,
            'cast': cast,
            'genre': genre,
            'temporal': temporal,
            'original': original
        }

        logger.info(f"Enhanced query parsing: {result}")
        return result

    @staticmethod
    def fuzzy_match_results(query: str, results: List[Dict[str, Any]], threshold: int = 70) -> List[Dict[str, Any]]:
        """
        Re-rank results using fuzzy matching.

        Args:
            query: Search query
            results: List of search results from Overseerr
            threshold: Minimum similarity score (0-100)

        Returns:
            Re-ranked results with similarity scores
        """
        if not results:
            return results

        scored_results = []

        for result in results:
            title = result.get('_title', result.get('title', result.get('name', '')))

            # Calculate multiple similarity scores
            ratio = fuzz.ratio(query.lower(), title.lower())
            partial = fuzz.partial_ratio(query.lower(), title.lower())
            token_sort = fuzz.token_sort_ratio(query.lower(), title.lower())
            token_set = fuzz.token_set_ratio(query.lower(), title.lower())

            # Use the best score
            best_score = max(ratio, partial, token_sort, token_set)

            if best_score >= threshold:
                result_copy = result.copy()
                result_copy['_fuzzy_score'] = best_score
                scored_results.append(result_copy)

        # Sort by fuzzy score descending
        scored_results.sort(key=lambda x: x.get('_fuzzy_score', 0), reverse=True)

        logger.info(f"Fuzzy matching: {len(scored_results)} results above threshold {threshold}")

        return scored_results

    @staticmethod
    def suggest_alternatives(query: str, known_titles: List[str], limit: int = 5) -> List[Tuple[str, int]]:
        """
        Suggest alternative titles based on fuzzy matching.

        Args:
            query: User's search query
            known_titles: List of known titles to match against
            limit: Maximum number of suggestions

        Returns:
            List of (title, score) tuples
        """
        if not known_titles:
            return []

        # Use rapidfuzz to find best matches
        matches = process.extract(
            query,
            known_titles,
            scorer=fuzz.WRatio,
            limit=limit
        )

        # Filter out low scores
        suggestions = [(match[0], match[1]) for match in matches if match[1] >= 60]

        logger.info(f"Generated {len(suggestions)} suggestions for query '{query}'")

        return suggestions

    @staticmethod
    def filter_by_genre(results: List[Dict[str, Any]], genre: str) -> List[Dict[str, Any]]:
        """
        Filter results by genre.

        Note: This requires Overseerr API to return genre information.
        If not available, this returns all results.
        """
        # Check if results have genre info
        if not results or 'genres' not in results[0] and 'genre_ids' not in results[0]:
            logger.warning("Genre filtering requested but genre data not available in results")
            return results

        # TODO: Implement genre ID mapping when Overseerr provides genre data
        logger.info(f"Genre filtering for '{genre}' - implementation pending genre data from API")
        return results

    @staticmethod
    def filter_by_cast(results: List[Dict[str, Any]], cast_name: str) -> List[Dict[str, Any]]:
        """
        Filter results by actor/director.

        Note: This would require additional API calls to TMDB for cast info.
        Consider implementing if needed.
        """
        logger.info(f"Cast filtering for '{cast_name}' - requires TMDB API integration")
        return results

    @staticmethod
    def build_smart_query_explanation(parsed: Dict[str, Any]) -> str:
        """Build a human-readable explanation of what was understood"""
        parts = []

        if parsed['cleaned_query']:
            parts.append(f"searching for '{parsed['cleaned_query']}'")

        if parsed['cast']:
            parts.append(f"with {parsed['cast']}")

        if parsed['genre']:
            parts.append(f"in the {parsed['genre']} genre")

        if parsed['temporal']:
            if parsed['temporal']['type'] == 'year':
                parts.append(f"from {parsed['temporal']['year']}")
            elif parsed['temporal']['type'] == 'relative':
                days = abs(parsed['temporal']['days'])
                if parsed['temporal']['days'] > 0:
                    parts.append(f"from the last {days} days")
                else:
                    parts.append(f"coming in the next {days} days")

        if len(parts) > 1:
            return "I'm " + ", ".join(parts[:-1]) + " and " + parts[-1]
        elif parts:
            return "I'm " + parts[0]
        else:
            return "I'm searching for that"


# Singleton instance
search_enhancer = SearchEnhancer()
