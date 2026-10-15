"""Run the full experimental corpus generation (Objetivo D, Secao 3.7 do TCC):
120 habilidades x 3 condicoes x N itens por condicao (GERACAO_ITENS_POR_CONDICAO,
default 5) = 1800 itens.

For each habilidade, the three conditions are generated in randomized order
(Secao 3.7.2) while temperature/model/max_tokens stay constant (Secao 3.7.2 /
GLMSettings). Every item is validated structurally, persisted regardless of
outcome (Secao 3.8.1 — failures are kept for audit, not silently dropped), and
run through Camada B (NLP metrics) before Camada A (LLM-as-Judge) is applied
separately (see executar_avaliacao.py) once the whole corpus exists.

Usage (from backend/):
    uv run python -m scripts.executar_experimento [--habilidades CN-H17,CN-H18] [--limite N]

Requires NEO4J_ENABLED=true, a populated graph (scripts/load_matriz_referencia.py)
and a valid GLM_API_KEY. Each run creates fresh Questao nodes (new UUIDs) — re-running
adds another batch rather than overwriting a previous one, so start with --limite on
a small pilot before committing to the full 120-habilidade run (see Fase 4 no roadmap:
API/latency cost scales with 120 x 3 x GERACAO_ITENS_POR_CONDICAO calls).
"""

import argparse
import asyncio
import random
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from neo4j import AsyncSession as Neo4jAsyncSession  # noqa: E402

from src.infrastructure.config.settings import settings  # noqa: E402
from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.llm.glm_client import GLMClient, get_glm_client  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.avaliacao.service import AvaliacaoService  # noqa: E402
from src.modules.geracao.schemas import CondicaoExperimental  # noqa: E402
from src.modules.geracao.service import GeracaoService  # noqa: E402
from src.modules.matriz_referencia.service import MatrizReferenciaService  # noqa: E402
from src.modules.questoes.schemas import OrigemQuestao, QuestaoCreate  # noqa: E402
from src.modules.questoes.service import QuestoesService  # noqa: E402

logger = get_logger()

CONDICOES = [CondicaoExperimental.COM_GRAFO, CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO, CondicaoExperimental.SEM_GRAFO]


async def gerar_para_habilidade(
    habilidade_codigo: str,
    matriz_service: MatrizReferenciaService,
    geracao_service: GeracaoService,
    avaliacao_service: AvaliacaoService,
    questoes_service: QuestoesService,
    session: Neo4jAsyncSession,
    glm_client: GLMClient,
) -> int:
    habilidade = await matriz_service.get_habilidade_contexto(session, habilidade_codigo)
    fewshots = await questoes_service.get_fewshots(session, habilidade_codigo, limite=settings.GERACAO_FEWSHOTS_POR_HABILIDADE)

    condicoes_embaralhadas = list(CONDICOES)
    random.shuffle(condicoes_embaralhadas)

    total_gerado = 0
    for condicao in condicoes_embaralhadas:
        fewshots_condicao = fewshots if condicao != CondicaoExperimental.SEM_GRAFO else []
        for _ in range(settings.GERACAO_ITENS_POR_CONDICAO):
            try:
                item, validacao = await geracao_service.gerar_item(glm_client, habilidade, condicao, fewshots_condicao)
            except Exception:
                logger.exception("Falha ao gerar item para %s / %s", habilidade_codigo, condicao.value)
                continue

            questao_id = await questoes_service.criar(
                session,
                QuestaoCreate(
                    habilidade_codigo=habilidade_codigo,
                    enunciado=item.enunciado,
                    alternativas=item.alternativas,
                    gabarito=item.gabarito,
                    justificativa=item.justificativa,
                    origem=OrigemQuestao(condicao.value),
                    validacao_estrutural_ok=validacao.ok,
                ),
            )

            metricas = avaliacao_service.calcular_metricas_nlp(item, habilidade)
            await questoes_service.salvar_metricas(
                session,
                questao_id,
                cobertura_lexical=metricas.cobertura_lexical,
                especificidade_curricular=metricas.especificidade_curricular,
                similaridade_semantica=metricas.similaridade_semantica,
                ttr=metricas.ttr,
                fkgl=metricas.fkgl,
            )
            total_gerado += 1
            logger.info(
                "Gerado %s [%s] validacao_ok=%s cobertura=%.3f",
                questao_id,
                condicao.value,
                validacao.ok,
                metricas.cobertura_lexical,
            )

    return total_gerado


async def main(habilidades_filtro: list[str] | None, limite: int | None) -> None:
    matriz_service = MatrizReferenciaService()
    geracao_service = GeracaoService()
    avaliacao_service = AvaliacaoService()
    questoes_service = QuestoesService()
    glm_client = get_glm_client()

    async for session in graph_session():
        if habilidades_filtro:
            habilidades = habilidades_filtro
        else:
            habilidades = []
            for area in await matriz_service.get_areas(session):
                por_area = await matriz_service.get_habilidades_por_area(session, area.codigo)
                habilidades.extend(h.codigo for h in por_area)

        if limite:
            habilidades = habilidades[:limite]

        logger.info("Executando experimento para %d habilidades", len(habilidades))
        total = 0
        for habilidade_codigo in habilidades:
            total += await gerar_para_habilidade(
                habilidade_codigo, matriz_service, geracao_service, avaliacao_service, questoes_service, session, glm_client
            )
        logger.info("Experimento concluido: %d itens gerados", total)

    await close_driver()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--habilidades", type=str, default=None, help="Codigos separados por virgula (ex: CN-H17,CN-H18)")
    parser.add_argument("--limite", type=int, default=None, help="Limitar a N habilidades (piloto)")
    args = parser.parse_args()

    filtro = args.habilidades.split(",") if args.habilidades else None
    asyncio.run(main(filtro, args.limite))
