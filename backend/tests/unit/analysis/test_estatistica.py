"""Unit tests for the Secao 3.11 statistical pipeline (Objetivo F)."""

import pytest

from src.analysis import estatistica

pytestmark = pytest.mark.unit

# Three completely separated groups -> unambiguous significance in every test below.
COM_GRAFO = [8.0 + i * 0.1 for i in range(10)]
COM_FEWSHOT_SEM_GRAFO = [5.0 + i * 0.1 for i in range(10)]
SEM_GRAFO = [2.0 + i * 0.1 for i in range(10)]

GRUPOS_SEPARADOS = {
    "com_grafo": COM_GRAFO,
    "com_fewshot_sem_grafo": COM_FEWSHOT_SEM_GRAFO,
    "sem_grafo": SEM_GRAFO,
}

GRUPOS_IDENTICOS = {
    "com_grafo": [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9],
    "com_fewshot_sem_grafo": [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9],
    "sem_grafo": [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9],
}


def test_testar_normalidade_requires_at_least_three_observations() -> None:
    with pytest.raises(ValueError, match="pelo menos 3"):
        estatistica.testar_normalidade([1.0, 2.0])


def test_testar_normalidade_flags_extreme_skew_as_non_normal() -> None:
    dados = [1.0] * 9 + [1000.0]
    resultado = estatistica.testar_normalidade(dados)
    assert resultado.normal is False
    assert resultado.p_valor < 0.05


def test_testar_normalidade_returns_expected_shape() -> None:
    resultado = estatistica.testar_normalidade(COM_GRAFO)
    assert isinstance(resultado.estatistica, float)
    assert isinstance(resultado.p_valor, float)
    assert isinstance(resultado.normal, bool)


def test_kruskal_wallis_requires_at_least_two_groups() -> None:
    with pytest.raises(ValueError, match="pelo menos 2"):
        estatistica.kruskal_wallis({"unico": COM_GRAFO})


def test_kruskal_wallis_detects_significant_difference() -> None:
    resultado = estatistica.kruskal_wallis(GRUPOS_SEPARADOS)
    assert resultado.significativo is True
    assert resultado.p_valor < 0.05


def test_kruskal_wallis_no_difference_for_identical_groups() -> None:
    resultado = estatistica.kruskal_wallis(GRUPOS_IDENTICOS)
    assert resultado.significativo is False
    assert resultado.p_valor > 0.05


def test_mann_whitney_post_hoc_returns_all_pairs() -> None:
    resultados = estatistica.mann_whitney_post_hoc(GRUPOS_SEPARADOS)
    pares = {frozenset((r.grupo_a, r.grupo_b)) for r in resultados}
    assert len(resultados) == 3
    assert frozenset(("com_grafo", "sem_grafo")) in pares


def test_mann_whitney_post_hoc_all_pairs_significant_for_fully_separated_groups() -> None:
    resultados = estatistica.mann_whitney_post_hoc(GRUPOS_SEPARADOS, alpha_bonferroni=0.0167)
    assert all(r.significativo for r in resultados)


def test_mann_whitney_post_hoc_not_significant_for_identical_groups() -> None:
    resultados = estatistica.mann_whitney_post_hoc(GRUPOS_IDENTICOS, alpha_bonferroni=0.0167)
    assert all(not r.significativo for r in resultados)


def test_analisar_indicador_runs_full_pipeline_and_confirms_gradient() -> None:
    analise = estatistica.analisar_indicador("cobertura_lexical", GRUPOS_SEPARADOS)

    assert analise.nome_indicador == "cobertura_lexical"
    assert set(analise.normalidade_por_grupo.keys()) == set(GRUPOS_SEPARADOS.keys())
    assert analise.kruskal_wallis.significativo is True
    assert len(analise.post_hoc) == 3
    assert all(r.significativo for r in analise.post_hoc)


def test_analisar_indicador_skips_post_hoc_when_kruskal_not_significant() -> None:
    analise = estatistica.analisar_indicador("ttr", GRUPOS_IDENTICOS)

    assert analise.kruskal_wallis.significativo is False
    assert analise.post_hoc == []
