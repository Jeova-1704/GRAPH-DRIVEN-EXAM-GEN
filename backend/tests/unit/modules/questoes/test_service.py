import json
from typing import Any

import pytest

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.questoes.schemas import OrigemQuestao, QuestaoCreate
from src.modules.questoes.service import QuestoesService

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


def make_questao_create(**overrides: object) -> QuestaoCreate:
    base = {
        "habilidade_codigo": "CN-H17",
        "enunciado": "x" * 50,
        "alternativas": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        "gabarito": "A",
        "justificativa": "y" * 100,
        "origem": OrigemQuestao.COM_GRAFO,
    }
    base.update(overrides)
    return QuestaoCreate(**base)  # type: ignore[arg-type]


async def test_criar_persists_alternativas_as_json_and_returns_id() -> None:
    session = FakeSession()
    service = QuestoesService()

    questao_id = await service.criar(session, make_questao_create(), questao_id="fixed-id")

    assert questao_id == "fixed-id"
    merge_call = session.calls[-1]
    assert merge_call[1]["alternativas_json"] == json.dumps({"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"})
    assert merge_call[1]["origem"] == "com_grafo"


async def test_get_fewshots_deserializes_alternativas() -> None:
    record = {
        "enunciado": "Um item real",
        "alternativas_json": json.dumps({"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}),
        "gabarito": "B",
    }
    session = FakeSession(results_by_call=[[record]])
    service = QuestoesService()

    fewshots = await service.get_fewshots(session, "CN-H17", limite=5)

    assert len(fewshots) == 1
    assert fewshots[0].alternativas["A"] == "a"
    assert fewshots[0].gabarito == "B"


async def test_get_por_id_raises_when_not_found() -> None:
    session = FakeSession(results_by_call=[[]])
    service = QuestoesService()

    with pytest.raises(ResourceNotFoundError):
        await service.get_por_id(session, "nao-existe")


def make_questao_record(**overrides: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "q1",
        "habilidade_codigo": "CN-H17",
        "enunciado": "enunciado",
        "alternativas_json": json.dumps({"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}),
        "gabarito": "A",
        "justificativa": "justificativa",
        "origem": "com_grafo",
        "ano_origem": None,
        "validacao_estrutural_ok": True,
        "cobertura_lexical": None,
        "especificidade_curricular": None,
        "similaridade_semantica": None,
        "ttr": None,
        "fkgl": None,
        "judge_d1_alinhamento": None,
        "judge_d2_objetos_conhecimento": None,
        "judge_d3_distratores": None,
        "judge_d4_escolaridade": None,
        "judge_d5_formato_enem": None,
        "judge_justificativa": None,
    }
    base.update(overrides)
    return base


async def test_get_por_id_parses_record() -> None:
    session = FakeSession(results_by_call=[[make_questao_record()]])
    service = QuestoesService()

    questao = await service.get_por_id(session, "q1")

    assert questao.origem == OrigemQuestao.COM_GRAFO
    assert questao.alternativas["A"] == "a"
    assert questao.metricas.cobertura_lexical is None
    assert questao.julgamento.d1_alinhamento_habilidade is None


async def test_get_por_id_parses_metricas_e_julgamento_quando_presentes() -> None:
    record = make_questao_record(cobertura_lexical=0.42, judge_d1_alinhamento=5, judge_justificativa="boa aderencia")
    session = FakeSession(results_by_call=[[record]])
    service = QuestoesService()

    questao = await service.get_por_id(session, "q1")

    assert questao.metricas.cobertura_lexical == 0.42
    assert questao.julgamento.d1_alinhamento_habilidade == 5
    assert questao.julgamento.justificativa == "boa aderencia"


async def test_contar_por_origem_returns_total() -> None:
    session = FakeSession(results_by_call=[[{"total": 5}]])
    service = QuestoesService()

    total = await service.contar_por_origem(session, OrigemQuestao.ENEM)

    assert total == 5
