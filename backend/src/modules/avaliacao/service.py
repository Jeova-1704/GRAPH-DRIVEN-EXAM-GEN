import json

from ...infrastructure.llm.glm_client import GLMClient
from ..common.exceptions import AvaliacaoError
from ..common.utils.llm_json import parse_json_response
from ..matriz_referencia.schemas import HabilidadeContexto
from ..validacao.schemas import ItemGerado
from . import nlp
from .judge_prompt import build_judge_prompt
from .schemas import JulgamentoLLM, MetricasNLP


class AvaliacaoService:
    """Two-layer quality evaluation protocol (Secao 3.9 do TCC):
    Camada B (automatic NLP metrics) and Camada A (LLM-as-Judge)."""

    def calcular_metricas_nlp(
        self,
        item: ItemGerado,
        habilidade: HabilidadeContexto,
        tokens_outras_habilidades: list[list[str]] | None = None,
        embedding_item: list[float] | None = None,
        embedding_habilidade: list[float] | None = None,
    ) -> MetricasNLP:
        texto_item = item.enunciado + " " + " ".join(item.alternativas.values())
        tokens_item = nlp.tokenizar(texto_item)

        tokens_oc = nlp.tokenizar(" ".join(f"{oc.titulo} {oc.descricao}" for oc in habilidade.objetos_conhecimento))
        cobertura = nlp.cobertura_lexical(tokens_item, tokens_oc)

        especificidade = None
        if tokens_outras_habilidades is not None:
            coberturas_outras = [nlp.cobertura_lexical(tokens_item, t) for t in tokens_outras_habilidades]
            especificidade = nlp.especificidade_curricular(cobertura, coberturas_outras)

        similaridade = None
        if embedding_item is not None and embedding_habilidade is not None:
            similaridade = nlp.similaridade_cosseno(embedding_item, embedding_habilidade)

        return MetricasNLP(
            cobertura_lexical=cobertura,
            especificidade_curricular=especificidade,
            similaridade_semantica=similaridade,
            ttr=nlp.diversidade_lexical_ttr(tokens_item),
            fkgl=nlp.legibilidade_fkgl(texto_item),
        )

    async def julgar(self, glm_client: GLMClient, item: ItemGerado, habilidade: HabilidadeContexto) -> JulgamentoLLM:
        prompt = build_judge_prompt(item, habilidade)
        resposta_bruta = await glm_client.judge(prompt)

        try:
            payload = parse_json_response(resposta_bruta)
        except json.JSONDecodeError as exc:
            raise AvaliacaoError(f"Resposta do juiz nao e um JSON valido: {exc}") from exc

        try:
            return JulgamentoLLM(
                d1_alinhamento_habilidade=payload["d1"],
                d2_adequacao_objetos_conhecimento=payload["d2"],
                d3_plausibilidade_distratores=payload["d3"],
                d4_nivel_escolaridade=payload["d4"],
                d5_aderencia_formato_enem=payload["d5"],
                justificativa=payload["justificativa"],
            )
        except Exception as exc:
            raise AvaliacaoError(f"JSON do juiz nao corresponde ao schema esperado: {exc}") from exc
