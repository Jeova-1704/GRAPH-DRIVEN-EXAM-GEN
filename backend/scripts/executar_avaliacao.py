"""Run Camada A (LLM-as-Judge, Secao 3.9.2 do TCC) over every generated Questao.

Separate from executar_experimento.py because judging is independent of generation
(the TCC's protocol requires the judge to be blind to the generation condition) and
because it's useful to re-run judging alone (e.g. after tuning GLM_JUDGE_MODEL)
without regenerating the corpus.

Safe to stop (Ctrl+C or kill the process) and re-run later: already-judged Questoes
(d1_alinhamento_habilidade already set) are skipped, so a re-run only judges what's
still pending.

Usage (from backend/):
    uv run python -m scripts.executar_avaliacao
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.llm.glm_client import get_glm_client  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.avaliacao.service import AvaliacaoService  # noqa: E402
from src.modules.matriz_referencia.service import MatrizReferenciaService  # noqa: E402
from src.modules.questoes.schemas import OrigemQuestao  # noqa: E402
from src.modules.questoes.service import QuestoesService  # noqa: E402
from src.modules.validacao.schemas import ItemGerado  # noqa: E402

logger = get_logger()

ORIGENS_GERADAS = [OrigemQuestao.COM_GRAFO, OrigemQuestao.COM_FEWSHOT_SEM_GRAFO, OrigemQuestao.SEM_GRAFO]


async def main() -> None:
    matriz_service = MatrizReferenciaService()
    avaliacao_service = AvaliacaoService()
    questoes_service = QuestoesService()
    glm_client = get_glm_client()

    async for session in graph_session():
        total_julgadas = 0
        for origem in ORIGENS_GERADAS:
            todas_questoes = await questoes_service.get_por_origem(session, origem)
            questoes = [q for q in todas_questoes if q.julgamento.d1_alinhamento_habilidade is None]
            ja_julgadas = len(todas_questoes) - len(questoes)
            logger.info(
                "Condicao %s: %d ja julgadas, %d pendentes", origem.value, ja_julgadas, len(questoes)
            )

            for questao in questoes:
                habilidade = await matriz_service.get_habilidade_contexto(session, questao.habilidade_codigo)
                item = ItemGerado(
                    enunciado=questao.enunciado,
                    alternativas=questao.alternativas,
                    gabarito=questao.gabarito,
                    justificativa=questao.justificativa or "",
                )
                try:
                    julgamento = await avaliacao_service.julgar(glm_client, item, habilidade)
                except Exception:
                    logger.exception("Falha ao julgar %s", questao.id)
                    continue

                await questoes_service.salvar_julgamento(
                    session,
                    questao.id,
                    d1=julgamento.d1_alinhamento_habilidade,
                    d2=julgamento.d2_adequacao_objetos_conhecimento,
                    d3=julgamento.d3_plausibilidade_distratores,
                    d4=julgamento.d4_nivel_escolaridade,
                    d5=julgamento.d5_aderencia_formato_enem,
                    justificativa=julgamento.justificativa,
                )
                total_julgadas += 1
                logger.info("Julgado %s score_medio=%.2f", questao.id, julgamento.score_medio)

        logger.info("Avaliacao concluida: %d itens julgados", total_julgadas)

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
