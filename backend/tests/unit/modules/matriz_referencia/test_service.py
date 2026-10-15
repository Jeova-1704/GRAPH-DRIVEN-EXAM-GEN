"""Unit tests for MatrizReferenciaService, mocked at the graph-session layer
(the equivalent of mocking at the CRUD layer for a relational module)."""

from typing import Any

import pytest

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.matriz_referencia import cypher
from src.modules.matriz_referencia.service import MatrizReferenciaService

pytestmark = pytest.mark.unit


class FakeResult:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    async def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __aiter__(self) -> "FakeResult":
        self._iter = iter(self._records)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


class FakeSession:
    """Records every Cypher statement it's asked to run and returns scripted results."""

    def __init__(self, results_by_call: list[list[dict[str, Any]]] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._results_by_call = results_by_call or []
        self._call_index = 0

    async def run(self, query: str, **params: Any) -> FakeResult:
        self.calls.append((query, params))
        if self._call_index < len(self._results_by_call):
            records = self._results_by_call[self._call_index]
        else:
            records = []
        self._call_index += 1
        return FakeResult(records)


MINI_DATASET = {
    "areas": [
        {
            "codigo": "LC",
            "nome": "Linguagens",
            "objetos_conhecimento": [{"codigo": "LC-OC1", "titulo": "T1", "descricao": "D1"}],
            "competencias": [
                {
                    "numero": 1,
                    "descricao": "Competencia 1",
                    "objetos_conhecimento": ["LC-OC1"],
                    "habilidades": [
                        {"codigo": "LC-H1", "descricao": "Habilidade 1"},
                        {"codigo": "LC-H2", "descricao": "Habilidade 2"},
                    ],
                }
            ],
        }
    ]
}


async def test_carregar_de_dados_runs_expected_cypher_statements() -> None:
    session = FakeSession()
    service = MatrizReferenciaService()

    resultado = await service.carregar_de_dados(session, MINI_DATASET)

    assert resultado.areas_carregadas == 1
    assert resultado.competencias_carregadas == 1
    assert resultado.habilidades_carregadas == 2
    assert resultado.objetos_conhecimento_carregados == 1

    # constraints + 1 area + 1 oc + 1 competencia + 2 habilidades + 2 ABRANGE merges
    n_constraints = len(cypher.CONSTRAINTS)
    assert len(session.calls) == n_constraints + 1 + 1 + 1 + 2 + 2


async def test_get_habilidade_contexto_raises_when_not_found() -> None:
    session = FakeSession(results_by_call=[[]])
    service = MatrizReferenciaService()

    with pytest.raises(ResourceNotFoundError):
        await service.get_habilidade_contexto(session, "LC-H999")


async def test_get_habilidade_contexto_parses_record() -> None:
    record = {
        "habilidade_codigo": "LC-H1",
        "habilidade_descricao": "Habilidade 1",
        "competencia_numero": 1,
        "competencia_descricao": "Competencia 1",
        "area_codigo": "LC",
        "area_nome": "Linguagens",
        "objetos_conhecimento": [{"codigo": "LC-OC1", "titulo": "T1", "descricao": "D1"}],
    }
    session = FakeSession(results_by_call=[[record]])
    service = MatrizReferenciaService()

    contexto = await service.get_habilidade_contexto(session, "LC-H1")

    assert contexto.habilidade_codigo == "LC-H1"
    assert contexto.objetos_conhecimento[0].codigo == "LC-OC1"


async def test_verificar_integridade_reports_success_when_all_zero() -> None:
    # count_label is called 4x, then 3 count_query calls, all returning total=0
    session = FakeSession(results_by_call=[[{"total": n}] for n in [4, 30, 120, 41, 0, 0, 0]])
    service = MatrizReferenciaService()

    relatorio = await service.verificar_integridade(session)

    assert relatorio.total_areas == 4
    assert relatorio.total_habilidades == 120
    assert relatorio.integro is True


async def test_verificar_integridade_flags_habilidades_sem_oc() -> None:
    session = FakeSession(results_by_call=[[{"total": n}] for n in [4, 30, 120, 41, 3, 0, 0]])
    service = MatrizReferenciaService()

    relatorio = await service.verificar_integridade(session)

    assert relatorio.habilidades_sem_objeto_conhecimento == 3
    assert relatorio.integro is False
