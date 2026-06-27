"""
Shared name-matching helpers (normalization + fuzzy distance).

Extracted so that both the source-record contributor mapping
(:class:`SourceContributorMappingService`) and the user-driven contribution
update path (:class:`ContributionUpdateService`) rely on the exact same
name-similarity logic instead of duplicating it.
"""
import re
import unicodedata

from rapidfuzz import fuzz


def normalize_name(input_string: str) -> str:
    """
    Normalize a name for comparison: lowercase, strip diacritics, keep letters
    only and collapse whitespace.

    :param input_string: raw name
    :return: normalized name (may be empty)
    """
    normalized = (input_string or "").lower()

    # Replace accented characters with their ASCII equivalents
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

    # Replace all non-letter characters with spaces
    normalized = re.sub(r'[^a-z]', ' ', normalized)

    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def fuzz_distance(name1: str, name2: str) -> float:
    """
    Token-sort similarity ratio (0-100) between two names, computed on their
    normalized forms.

    :param name1: first name
    :param name2: second name
    :return: similarity ratio in [0, 100]
    """
    return fuzz.token_sort_ratio(name1, name2, processor=normalize_name)
