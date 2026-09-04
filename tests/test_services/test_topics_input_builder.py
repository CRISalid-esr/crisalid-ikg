from app.models.literal import Literal
from app.models.text_literal import TextLiteral
from app.services.documents.topics_input_builder import build_topics_input, select_language

LANGS = ["en", "fr"]
EN_TITLE = Literal(value="Machine learning for quantum computing", language="en")
FR_TITLE = Literal(value="Apprentissage automatique pour l'informatique quantique", language="fr")
UND_TITLE = Literal(value="A title without any language information at all", language="ul")
FR_ABSTRACT = TextLiteral(value="Un long résumé en français " * 5, language="fr")


def test_select_language_priority_order():
    assert select_language([FR_TITLE, EN_TITLE], [FR_ABSTRACT], LANGS) == "en"
    assert select_language([FR_TITLE], [FR_ABSTRACT], LANGS) == "fr"
    assert select_language([], [FR_ABSTRACT], LANGS) == "fr"


def test_select_language_und_fallback_only_when_no_listed_language():
    assert select_language([UND_TITLE], [], LANGS) == "und"
    assert select_language([UND_TITLE, FR_TITLE], [], LANGS) == "fr"
    assert select_language([Literal(value="Ein Titel", language="de")], [], LANGS) is None


def test_build_input_uses_only_selected_language():
    result = build_topics_input([FR_TITLE, EN_TITLE], [FR_ABSTRACT], [], LANGS, 25)
    assert result is not None
    assert result.language == "en"
    assert result.text == EN_TITLE.value
    assert "français" not in result.text


def test_build_input_too_short_even_with_subjects():
    labels = [Literal(value="Quantum computing", language="en")] * 10
    result = build_topics_input([Literal(value="Short", language="en")], [], labels, LANGS, 25)
    assert result is None


def test_build_input_returns_none_without_usable_language():
    assert build_topics_input([Literal(value="Ein sehr langer deutscher Titel", language="de")],
                              [], [], LANGS, 25) is None


def test_build_input_pref_labels_deduplicated_and_language_filtered():
    labels = [
        Literal(value="Quantum computing", language="en"),
        Literal(value="quantum Computing ", language="en"),
        Literal(value="Informatique quantique", language="fr"),
        Literal(value="  Machine   learning ", language="en"),
    ]
    result = build_topics_input([EN_TITLE], [], labels, LANGS, 25)
    assert result.text == f"{EN_TITLE.value}. Quantum computing. Machine learning"


def test_build_input_und_labels_used_with_und_fallback():
    labels = [Literal(value="Some subject", language="ul"),
              Literal(value="Sujet", language="fr")]
    result = build_topics_input([UND_TITLE], [], labels, LANGS, 25)
    assert result.language == "und"
    assert result.text == f"{UND_TITLE.value}. Some subject"


def test_build_input_hash_is_stable_and_content_sensitive():
    first = build_topics_input([EN_TITLE], [FR_ABSTRACT], [], LANGS, 25)
    second = build_topics_input([EN_TITLE], [FR_ABSTRACT], [], LANGS, 25)
    changed = build_topics_input([Literal(value=EN_TITLE.value + "!", language="en")],
                                 [FR_ABSTRACT], [], LANGS, 25)
    assert first.input_hash == second.input_hash
    assert len(first.input_hash) == 64
    assert first.input_hash != changed.input_hash
