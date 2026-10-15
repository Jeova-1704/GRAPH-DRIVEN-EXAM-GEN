"""Unit tests for GeracaoService, mocked at the GLM-client layer."""

import pytest

from src.modules.common.exceptions import GeracaoError
from src.modules.geracao.schemas import CondicaoExperimental
from src.modules.geracao.service import GeracaoService
from src.modules.matriz_referencia.schemas import HabilidadeContexto

pytestmark = pytest.mark.unit

HABILIDADE = HabilidadeContexto(
    habilidade_codigo="CN-H17",
    habilidade_descricao="Relacionar informacoes.",
    competencia_numero=5,
    competencia_descricao="Metodos.",
    area_codigo="CN",
    area_nome="Ciencias da Natureza",
    objetos_conhecimento=[],
)

VALID_JSON_RESPONSE = (
    '{"enunciado": "' + ("x" * 50) + '", '
    '"alternativas": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}, '
    '"gabarito": "A", '
    '"justificativa": "' + ("y" * 100) + '"}'
)


class FakeGLMClient:
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_prompt: str | None = None

    async def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


async def test_gerar_item_parses_valid_json_and_validates_structurally() -> None:
    service = GeracaoService()
    glm_client = FakeGLMClient(VALID_JSON_RESPONSE)

    item, resultado = await service.gerar_item(glm_client, HABILIDADE, CondicaoExperimental.SEM_GRAFO, [])

    assert item.gabarito == "A"
    assert resultado.ok is True
    assert glm_client.last_prompt is not None
    assert "[SISTEMA]" in glm_client.last_prompt


async def test_gerar_item_strips_markdown_code_fences() -> None:
    service = GeracaoService()
    glm_client = FakeGLMClient(f"```json\n{VALID_JSON_RESPONSE}\n```")

    item, _ = await service.gerar_item(glm_client, HABILIDADE, CondicaoExperimental.SEM_GRAFO, [])

    assert item.gabarito == "A"


async def test_gerar_item_raises_geracao_error_on_malformed_json() -> None:
    service = GeracaoService()
    glm_client = FakeGLMClient("isto nao e JSON")

    with pytest.raises(GeracaoError):
        await service.gerar_item(glm_client, HABILIDADE, CondicaoExperimental.SEM_GRAFO, [])


async def test_gerar_item_raises_geracao_error_on_json_missing_fields() -> None:
    service = GeracaoService()
    glm_client = FakeGLMClient('{"enunciado": "so isso"}')

    with pytest.raises(GeracaoError):
        await service.gerar_item(glm_client, HABILIDADE, CondicaoExperimental.SEM_GRAFO, [])


async def test_gerar_item_surfaces_structural_validation_failures() -> None:
    service = GeracaoService()
    bad_json = (
        '{"enunciado": "curto", '
        '"alternativas": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}, '
        '"gabarito": "A", "justificativa": "curta"}'
    )
    glm_client = FakeGLMClient(bad_json)

    item, resultado = await service.gerar_item(glm_client, HABILIDADE, CondicaoExperimental.SEM_GRAFO, [])

    assert resultado.ok is False
    assert "C4_enunciado_minimo" in resultado.criterios_reprovados
    assert "C5_justificativa_minima" in resultado.criterios_reprovados
