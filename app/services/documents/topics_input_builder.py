"""
Build the free-text input sent to Crisalid-taxi for a document.

Pure functions, no I/O: language selection, text assembly and hashing.
"""
import hashlib
import re
from dataclasses import dataclass

from app.models.literal import Literal

UNDETERMINED_LANGUAGES = frozenset({"und", Literal.UNDETERMINED_LANGUAGE})

_WHITESPACE = re.compile(r"\s+")


@dataclass
class TopicsInput:
    """Text sent to Crisalid-taxi for one document, with the language used and its hash."""

    text: str
    language: str
    input_hash: str


def _matches_language(literal: Literal, language: str) -> bool:
    if language in UNDETERMINED_LANGUAGES:
        return literal.language in UNDETERMINED_LANGUAGES
    return literal.language == language


def _clean(value: str | None) -> str:
    return _WHITESPACE.sub(" ", value or "").strip()


def select_language(titles: list[Literal], abstracts: list[Literal],
                    languages: list[str]) -> str | None:
    """
    Pick the language of the text sent to Crisalid-taxi.

    :param titles: document titles
    :param abstracts: document abstracts
    :param languages: accepted languages, in priority order
    :return: the first language of ``languages`` that has at least one title or abstract,
             else ``"und"`` if any title or abstract has an undetermined language, else None
    """
    literals = list(titles) + list(abstracts)
    for language in languages:
        if any(_matches_language(literal, language) for literal in literals):
            return language
    if any(literal.language in UNDETERMINED_LANGUAGES for literal in literals):
        return "und"
    return None


def build_topics_input(titles: list[Literal], abstracts: list[Literal],
                       pref_labels: list[Literal], languages: list[str],
                       min_input_length: int) -> TopicsInput | None:
    """
    Assemble the Crisalid-taxi input text from titles, abstracts and subject pref labels.

    Only literals in the selected language are used. Subject ``alt_labels`` must not be
    passed. The minimum length applies to titles + abstracts only.

    :return: a TopicsInput, or None when the document has no usable text
    """
    language = select_language(titles, abstracts, languages)
    if language is None:
        return None
    core_parts = [_clean(literal.value) for literal in list(titles) + list(abstracts)
                  if _matches_language(literal, language)]
    core_parts = [part for part in core_parts if part]
    core = ". ".join(core_parts)
    if len(core) < min_input_length:
        return None
    seen: set[str] = set()
    label_parts: list[str] = []
    for label in pref_labels:
        if not _matches_language(label, language):
            continue
        value = _clean(label.value)
        key = value.casefold()
        if not value or key in seen:
            continue
        seen.add(key)
        label_parts.append(value)
    text = ". ".join([core] + label_parts)
    input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return TopicsInput(text=text, language=language, input_hash=input_hash)
