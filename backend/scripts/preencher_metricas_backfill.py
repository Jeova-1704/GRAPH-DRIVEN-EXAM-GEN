"""Backfill especificidade_curricular E(i,h) and similaridade_semantica for every generated
Questao (Secao 3.9.1 do TCC).

executar_experimento.py called calcular_metricas_nlp() without the optional
tokens_outras_habilidades/embedding args, so cobertura_lexical/ttr/fkgl were computed for
all 1788 items but these two metrics were left None. This script fills only those two,
without touching the other three (see QuestoesService.salvar_metricas_extra).

especificidade_curricular needs the item's lexical coverage against all OTHER 119
habilidades' Objetos de Conhecimento — pure local token processing, no API cost.
similaridade_semantica needs GLM embeddings (embedding-2): one per Habilidade (cached,
~120 calls total) plus one per item (~1788 calls).

Safe to stop and re-run: items where both fields are already set are skipped.

Usage (from backend/):
    uv run python -m scripts.preencher_metricas_backfill
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.llm.glm_client import get_glm_client  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.avaliacao import nlp  # noqa: E402
from src.modules.matriz_referencia.service import MatrizReferenciaService  # noqa: E402
from src.modules.questoes.schemas import OrigemQuestao  # noqa: E402
from src.modules.questoes.service import QuestoesService  # noqa: E402

logger = get_logger()

ORIGENS_GERADAS = [OrigemQuestao.COM_GRAFO, OrigemQuestao.COM_FEWSHOT_SEM_GRAFO, OrigemQuestao.SEM_GRAFO]
AVISO_A_CADA = 50


async def main() -> None:
    matriz_service = MatrizReferenciaService()
    questoes_service = QuestoesService()
    glm_client = get_glm_client()

    async for session in graph_session():
        logger.info("Carregando tokens de Objetos de Conhecimento de todas as habilidades...")
        tokens_por_habilidade: dict[str, list[str]] = {}
        areas = await matriz_service.get_areas(session)
        for area in areas:
            habilidades = await matriz_service.get_habilidades_por_area(session, area.codigo)
            for h in habilidades:
                ctx = await matriz_service.get_habilidade_contexto(session, h.codigo)
                texto_oc = " ".join(f"{oc.titulo} {oc.descricao}" for oc in ctx.objetos_conhecimento)
                tokens_por_habilidade[h.codigo] = nlp.tokenizar(texto_oc)
        logger.info("Tokens carregados para %d habilidades", len(tokens_por_habilidade))

        embeddings_habilidade: dict[str, list[float]] = {}

        embeddings_disponiveis = True
        try:
            await glm_client.get_embedding("teste de disponibilidade do modelo de embedding")
        except Exception as exc:
            embeddings_disponiveis = False
            logger.warning(
                "Modelo de embedding (%s) indisponivel para esta chave de API — pulando "
                "similaridade_semantica nesta rodada, preenchendo so especificidade_curricular. "
                "Erro: %s",
                "GLM_EMBEDDING_MODEL",
                exc,
            )

        total_processadas = 0
        total_falhas = 0

        for origem in ORIGENS_GERADAS:
            todas_questoes = await questoes_service.get_por_origem(session, origem)
            pendentes = [
                q
                for q in todas_questoes
                if q.metricas.especificidade_curricular is None or q.metricas.similaridade_semantica is None
            ]
            logger.info(
                "Condicao %s: %d ja preenchidas, %d pendentes",
                origem.value,
                len(todas_questoes) - len(pendentes),
                len(pendentes),
            )

            for questao in pendentes:
                tokens_alvo = tokens_por_habilidade.get(questao.habilidade_codigo)
                if tokens_alvo is None:
                    logger.warning("Habilidade %s sem tokens carregados, pulando %s", questao.habilidade_codigo, questao.id)
                    continue

                texto_item = questao.enunciado + " " + " ".join(questao.alternativas.values())
                tokens_item = nlp.tokenizar(texto_item)

                cobertura_alvo = nlp.cobertura_lexical(tokens_item, tokens_alvo)
                coberturas_outras = [
                    nlp.cobertura_lexical(tokens_item, tokens)
                    for codigo, tokens in tokens_por_habilidade.items()
                    if codigo != questao.habilidade_codigo
                ]
                especificidade = nlp.especificidade_curricular(cobertura_alvo, coberturas_outras)

                # similaridade_semantica depende de embeddings GLM, que podem estar
                # indisponiveis (conta sem esse produto habilitado) sem bloquear a
                # especificidade_curricular, que e so processamento local.
                similaridade = questao.metricas.similaridade_semantica
                if embeddings_disponiveis:
                    try:
                        if questao.habilidade_codigo not in embeddings_habilidade:
                            texto_habilidade = " ".join(tokens_alvo)
                            embeddings_habilidade[questao.habilidade_codigo] = await glm_client.get_embedding(
                                texto_habilidade
                            )
                        embedding_habilidade = embeddings_habilidade[questao.habilidade_codigo]
                        embedding_item = await glm_client.get_embedding(texto_item)
                        similaridade = nlp.similaridade_cosseno(embedding_item, embedding_habilidade)
                    except Exception as exc:
                        logger.warning("Falha ao obter embedding para %s: %s", questao.id, exc)
                        total_falhas += 1

                await questoes_service.salvar_metricas_extra(
                    session,
                    questao.id,
                    especificidade_curricular=especificidade,
                    similaridade_semantica=similaridade,
                )
                total_processadas += 1
                if total_processadas % AVISO_A_CADA == 0:
                    logger.info("Progresso: %d itens preenchidos (%d falhas)", total_processadas, total_falhas)

        logger.info("Backfill concluido: %d itens preenchidos, %d falhas", total_processadas, total_falhas)

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
