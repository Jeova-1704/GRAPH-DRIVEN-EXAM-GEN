"""Export the generated corpus from Neo4j and run the Objetivo F statistical pipeline
(Secao 3.11 do TCC): Shapiro-Wilk -> Kruskal-Wallis -> Mann-Whitney U com Bonferroni,
comparando com_grafo / com_fewshot_sem_grafo / sem_grafo em cada indicador automatico.

Só itens com validacao_estrutural_ok=True entram na analise (itens reprovados na Fase C
foram mantidos no grafo so para auditoria, nao para comparação de qualidade). Indicadores
com dados insuficientes (ex.: similaridade_semantica antes do backfill de embeddings) sao
reportados como pulados em vez de derrubar o script inteiro.

Usage (from backend/):
    uv run python -m scripts.analisar_corpus
"""

import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Any

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.analysis.estatistica import AnaliseIndicador, analisar_indicador  # noqa: E402
from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.questoes.schemas import OrigemQuestao, QuestaoRead  # noqa: E402
from src.modules.questoes.service import QuestoesService  # noqa: E402

logger = get_logger()

CONDICOES = [OrigemQuestao.COM_GRAFO, OrigemQuestao.COM_FEWSHOT_SEM_GRAFO, OrigemQuestao.SEM_GRAFO]
MIN_OBSERVACOES_POR_GRUPO = 3

OUTPUT_PATH = backend_dir / "data" / "resultado_analise_estatistica.json"


def score_medio_judge(q: QuestaoRead) -> float | None:
    j = q.julgamento
    dims = [
        j.d1_alinhamento_habilidade,
        j.d2_adequacao_objetos_conhecimento,
        j.d3_plausibilidade_distratores,
        j.d4_nivel_escolaridade,
        j.d5_aderencia_formato_enem,
    ]
    if any(d is None for d in dims):
        return None
    return sum(dims) / 5  # type: ignore[arg-type]


INDICADORES: dict[str, Any] = {
    "cobertura_lexical": lambda q: q.metricas.cobertura_lexical,
    "especificidade_curricular": lambda q: q.metricas.especificidade_curricular,
    "similaridade_semantica": lambda q: q.metricas.similaridade_semantica,
    "ttr": lambda q: q.metricas.ttr,
    "fkgl": lambda q: q.metricas.fkgl,
    "d1_alinhamento_habilidade": lambda q: q.julgamento.d1_alinhamento_habilidade,
    "d2_adequacao_objetos_conhecimento": lambda q: q.julgamento.d2_adequacao_objetos_conhecimento,
    "d3_plausibilidade_distratores": lambda q: q.julgamento.d3_plausibilidade_distratores,
    "d4_nivel_escolaridade": lambda q: q.julgamento.d4_nivel_escolaridade,
    "d5_aderencia_formato_enem": lambda q: q.julgamento.d5_aderencia_formato_enem,
    "score_medio_judge": score_medio_judge,
}


def resultado_para_dict(analise: AnaliseIndicador) -> dict[str, Any]:
    return {
        "nome_indicador": analise.nome_indicador,
        "normalidade_por_grupo": {
            nome: {"estatistica": r.estatistica, "p_valor": r.p_valor, "normal": r.normal}
            for nome, r in analise.normalidade_por_grupo.items()
        },
        "kruskal_wallis": {
            "estatistica": analise.kruskal_wallis.estatistica,
            "p_valor": analise.kruskal_wallis.p_valor,
            "significativo": analise.kruskal_wallis.significativo,
        },
        "post_hoc": [
            {
                "grupo_a": r.grupo_a,
                "grupo_b": r.grupo_b,
                "estatistica": r.estatistica,
                "p_valor": r.p_valor,
                "significativo": r.significativo,
            }
            for r in analise.post_hoc
        ],
    }


async def main() -> None:
    questoes_service = QuestoesService()

    async for session in graph_session():
        questoes_por_condicao: dict[OrigemQuestao, list[QuestaoRead]] = {}
        for origem in CONDICOES:
            todas = await questoes_service.get_por_origem(session, origem)
            validas = [q for q in todas if q.validacao_estrutural_ok]
            questoes_por_condicao[origem] = validas
            logger.info(
                "Condicao %s: %d itens (%d validos estruturalmente, %d reprovados)",
                origem.value,
                len(todas),
                len(validas),
                len(todas) - len(validas),
            )

        resultados: dict[str, Any] = {}
        pulados: dict[str, str] = {}

        for nome_indicador, extrator in INDICADORES.items():
            grupos: dict[str, list[float]] = {}
            for origem, questoes in questoes_por_condicao.items():
                valores = [v for q in questoes if (v := extrator(q)) is not None]
                grupos[origem.value] = valores

            insuficientes = {nome: len(v) for nome, v in grupos.items() if len(v) < MIN_OBSERVACOES_POR_GRUPO}
            if insuficientes:
                motivo = f"dados insuficientes (< {MIN_OBSERVACOES_POR_GRUPO} observacoes): {insuficientes}"
                logger.warning("Pulando indicador %s: %s", nome_indicador, motivo)
                pulados[nome_indicador] = motivo
                continue

            descritivas = {
                nome: {
                    "n": len(valores),
                    "media": statistics.mean(valores),
                    "mediana": statistics.median(valores),
                    "desvio_padrao": statistics.stdev(valores) if len(valores) > 1 else 0.0,
                }
                for nome, valores in grupos.items()
            }

            analise = analisar_indicador(nome_indicador, grupos)
            resultado = resultado_para_dict(analise)
            resultado["descritivas"] = descritivas
            resultados[nome_indicador] = resultado
            logger.info(
                "%s: medianas %s | Kruskal-Wallis p=%.4f (significativo=%s)",
                nome_indicador,
                {nome: round(d["mediana"], 3) for nome, d in descritivas.items()},
                analise.kruskal_wallis.p_valor,
                analise.kruskal_wallis.significativo,
            )

        contagens = {origem.value: len(qs) for origem, qs in questoes_por_condicao.items()}
        payload = {"contagens_validas_por_condicao": contagens, "indicadores": resultados, "indicadores_pulados": pulados}

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Resultado salvo em %s", OUTPUT_PATH)

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
