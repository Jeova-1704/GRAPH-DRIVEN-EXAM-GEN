import json

from ...infrastructure.llm.glm_client import GLMClient
from ..common.exceptions import GeracaoError
from ..common.utils.llm_json import parse_json_response
from ..matriz_referencia.schemas import HabilidadeContexto
from ..validacao.schemas import ItemGerado, ValidacaoResultado
from ..validacao.service import ValidacaoService
from . import prompts
from .schemas import CondicaoExperimental, FewShot


def _parse_item(resposta_bruta: str) -> ItemGerado:
    """Parse the LLM's raw response into an ItemGerado, tolerating markdown code fences."""
    try:
        payload = parse_json_response(resposta_bruta)
    except json.JSONDecodeError as exc:
        raise GeracaoError(f"Resposta do LLM nao e um JSON valido: {exc}") from exc

    try:
        return ItemGerado(**payload)
    except Exception as exc:
        raise GeracaoError(f"JSON da resposta nao corresponde ao schema esperado: {exc}") from exc


class GeracaoService:
    """Orchestrates the GraphRAG generation pipeline (Secao 3.5.2/3.6 do TCC):
    build the condition-specific prompt, call the generation LLM, parse the JSON
    response and run it through structural validation before persistence.
    """

    def __init__(self, validacao_service: ValidacaoService | None = None) -> None:
        self._validacao_service = validacao_service or ValidacaoService()

    def montar_prompt(self, condicao: CondicaoExperimental, habilidade: HabilidadeContexto, few_shots: list[FewShot]) -> str:
        return prompts.build_prompt(condicao, habilidade, few_shots)

    async def gerar_item(
        self,
        glm_client: GLMClient,
        habilidade: HabilidadeContexto,
        condicao: CondicaoExperimental,
        few_shots: list[FewShot],
    ) -> tuple[ItemGerado, ValidacaoResultado]:
        prompt = self.montar_prompt(condicao, habilidade, few_shots)
        resposta_bruta = await glm_client.generate(prompt)
        item = _parse_item(resposta_bruta)
        resultado_validacao = self._validacao_service.validar(item)
        return item, resultado_validacao
