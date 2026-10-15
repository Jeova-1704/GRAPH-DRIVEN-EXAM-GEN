from typing import Any

import pytest

from src.modules.config_experimento.schemas import ConfigExperimentoUpdate
from src.modules.config_experimento.service import ConfigExperimentoService

pytestmark = pytest.mark.unit


class FakeResult:
    def __init__(self, record: dict[str, Any] | None) -> None:
        self._record = record

    async def single(self) -> dict[str, Any] | None:
        return self._record


class FakeSession:
    def __init__(self, existing_config: dict[str, Any] | None = None) -> None:
        self._existing_config = existing_config
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def run(self, query: str, **params: Any) -> FakeResult:
        self.calls.append((query, params))
        if "campos" in params:
            # simulate MERGE ... SET c += $campos
            self._existing_config = {**(self._existing_config or {}), **params["campos"]}
            return FakeResult({"c": self._existing_config})
        if self._existing_config is None:
            return FakeResult(None)
        return FakeResult({"c": self._existing_config})


async def test_get_falls_back_to_settings_defaults_when_no_config_node() -> None:
    session = FakeSession(existing_config=None)
    service = ConfigExperimentoService()

    config = await service.get(session)

    assert config.glm_generation_model  # comes from settings default, non-empty
    assert config.geracao_itens_por_condicao == 5


async def test_get_returns_saved_values_over_defaults() -> None:
    session = FakeSession(existing_config={"glm_generation_model": "glm-4.5-custom"})
    service = ConfigExperimentoService()

    config = await service.get(session)

    assert config.glm_generation_model == "glm-4.5-custom"


async def test_atualizar_merges_only_provided_fields() -> None:
    session = FakeSession(existing_config=None)
    service = ConfigExperimentoService()

    config = await service.atualizar(session, ConfigExperimentoUpdate(geracao_itens_por_condicao=10))

    assert config.geracao_itens_por_condicao == 10
    assert config.glm_judge_model  # untouched field still falls back to default


async def test_atualizar_with_no_fields_does_not_call_merge() -> None:
    session = FakeSession(existing_config=None)
    service = ConfigExperimentoService()

    await service.atualizar(session, ConfigExperimentoUpdate())

    assert all("MERGE" not in query for query, _ in session.calls)
