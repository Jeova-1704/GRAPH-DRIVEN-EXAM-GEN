"""Structural verification of the bundled Matriz de Referencia dataset (Secao 3.4.4 do TCC).

These checks run against the raw JSON, before anything touches Neo4j, so they run in
every environment (no Docker / no live graph needed) and catch data-entry mistakes early.
"""

import json

import pytest

from src.modules.matriz_referencia.service import DEFAULT_DATA_PATH

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def matriz() -> dict:
    return json.loads(DEFAULT_DATA_PATH.read_text(encoding="utf-8"))


def test_has_four_areas(matriz: dict) -> None:
    codigos = {area["codigo"] for area in matriz["areas"]}
    assert codigos == {"LC", "MT", "CN", "CH"}


def test_total_habilidades_is_120(matriz: dict) -> None:
    total = sum(len(c["habilidades"]) for area in matriz["areas"] for c in area["competencias"])
    assert total == 120


def test_each_area_has_30_habilidades(matriz: dict) -> None:
    for area in matriz["areas"]:
        total = sum(len(c["habilidades"]) for c in area["competencias"])
        assert total == 30, f"{area['codigo']} has {total} habilidades, expected 30"


def test_habilidade_codes_are_unique_and_prefixed_by_area(matriz: dict) -> None:
    seen: set[str] = set()
    for area in matriz["areas"]:
        for competencia in area["competencias"]:
            for habilidade in competencia["habilidades"]:
                codigo = habilidade["codigo"]
                assert codigo.startswith(f"{area['codigo']}-H"), codigo
                assert codigo not in seen, f"duplicate habilidade code: {codigo}"
                seen.add(codigo)


def test_every_competencia_references_at_least_one_objeto_conhecimento(matriz: dict) -> None:
    for area in matriz["areas"]:
        for competencia in area["competencias"]:
            assert competencia["objetos_conhecimento"], (
                f"{area['codigo']} competencia {competencia['numero']} has no ObjetoConhecimento"
            )


def test_every_referenced_objeto_conhecimento_exists_in_its_area(matriz: dict) -> None:
    for area in matriz["areas"]:
        oc_codes = {oc["codigo"] for oc in area["objetos_conhecimento"]}
        for competencia in area["competencias"]:
            for oc_codigo in competencia["objetos_conhecimento"]:
                assert oc_codigo in oc_codes, f"{oc_codigo} not defined in area {area['codigo']}"


def test_objeto_conhecimento_codes_are_unique_within_area(matriz: dict) -> None:
    for area in matriz["areas"]:
        codes = [oc["codigo"] for oc in area["objetos_conhecimento"]]
        assert len(codes) == len(set(codes)), f"duplicate ObjetoConhecimento codes in {area['codigo']}"


def test_habilidade_and_competencia_descriptions_are_non_empty(matriz: dict) -> None:
    for area in matriz["areas"]:
        for competencia in area["competencias"]:
            assert competencia["descricao"].strip()
            for habilidade in competencia["habilidades"]:
                assert habilidade["descricao"].strip()
