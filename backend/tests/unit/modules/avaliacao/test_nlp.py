"""Unit tests for Camada B automatic metrics (Secao 3.9.1 do TCC)."""

import pytest

from src.modules.avaliacao import nlp

pytestmark = pytest.mark.unit


def test_tokenizar_lowercases_and_strips_punctuation() -> None:
    tokens = nlp.tokenizar("Órbita, Microgravidade! (ISS)")
    assert "órbita" in tokens
    assert "microgravidade" in tokens
    assert "iss" in tokens


def test_tokenizar_removes_stopwords() -> None:
    tokens = nlp.tokenizar("a energia do corpo e a forca")
    assert "a" not in tokens
    assert "do" not in tokens
    assert "e" not in tokens
    assert "energia" in tokens
    assert "corpo" in tokens
    assert "forca" in tokens


def test_cobertura_lexical_full_overlap() -> None:
    assert nlp.cobertura_lexical(["gravitacao", "orbita"], ["gravitacao", "orbita"]) == 1.0


def test_cobertura_lexical_no_overlap() -> None:
    assert nlp.cobertura_lexical(["gato", "cachorro"], ["gravitacao", "orbita"]) == 0.0


def test_cobertura_lexical_partial_overlap() -> None:
    resultado = nlp.cobertura_lexical(["gravitacao", "gato", "cachorro", "passaro"], ["gravitacao"])
    assert resultado == pytest.approx(0.25)


def test_cobertura_lexical_empty_item_returns_zero() -> None:
    assert nlp.cobertura_lexical([], ["gravitacao"]) == 0.0


def test_especificidade_curricular_higher_for_more_specific_item() -> None:
    especifico = nlp.especificidade_curricular(0.5, [0.1, 0.1])
    generico = nlp.especificidade_curricular(0.1, [0.5, 0.5])
    assert especifico > generico


def test_especificidade_curricular_zero_when_target_coverage_is_zero() -> None:
    assert nlp.especificidade_curricular(0.0, [0.5, 0.3]) == 0.0


def test_especificidade_curricular_handles_all_zero_others() -> None:
    resultado = nlp.especificidade_curricular(0.5, [0.0, 0.0])
    assert resultado > 0  # denominator falls back to a small epsilon, not division by zero


def test_diversidade_lexical_ttr_all_unique() -> None:
    assert nlp.diversidade_lexical_ttr(["a", "b", "c"]) == 1.0


def test_diversidade_lexical_ttr_with_repeats() -> None:
    assert nlp.diversidade_lexical_ttr(["a", "a", "b", "b"]) == pytest.approx(0.5)


def test_diversidade_lexical_ttr_empty() -> None:
    assert nlp.diversidade_lexical_ttr([]) == 0.0


def test_legibilidade_fkgl_returns_a_float() -> None:
    resultado = nlp.legibilidade_fkgl("Esta e uma frase simples de teste.")
    assert isinstance(resultado, float)


def test_similaridade_cosseno_identical_vectors_is_one() -> None:
    assert nlp.similaridade_cosseno([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_similaridade_cosseno_orthogonal_vectors_is_zero() -> None:
    assert nlp.similaridade_cosseno([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_similaridade_cosseno_mismatched_lengths_returns_zero() -> None:
    assert nlp.similaridade_cosseno([1.0, 0.0], [1.0]) == 0.0


def test_similaridade_cosseno_zero_vector_returns_zero() -> None:
    assert nlp.similaridade_cosseno([0.0, 0.0], [1.0, 0.0]) == 0.0
