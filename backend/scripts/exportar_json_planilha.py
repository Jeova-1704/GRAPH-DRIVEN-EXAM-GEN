"""One-off dump of all generated Questoes (+ Area/Competencia context per Habilidade) to a
plain JSON file, as an intermediate step for the XLSX export (built separately with openpyxl
in an environment that has it, since this venv doesn't).

Usage (from backend/):
    uv run python -m scripts.exportar_json_planilha
"""

import asyncio
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.matriz_referencia.service import MatrizReferenciaService  # noqa: E402
from src.modules.questoes.schemas import OrigemQuestao  # noqa: E402
from src.modules.questoes.service import QuestoesService  # noqa: E402

logger = get_logger()

CONDICOES = [OrigemQuestao.COM_GRAFO, OrigemQuestao.COM_FEWSHOT_SEM_GRAFO, OrigemQuestao.SEM_GRAFO]
OUTPUT_PATH = backend_dir / "data" / "questoes_export.json"


async def main() -> None:
    matriz_service = MatrizReferenciaService()
    questoes_service = QuestoesService()

    async for session in graph_session():
        contexto_por_habilidade: dict[str, dict] = {}
        areas = await matriz_service.get_areas(session)
        for area in areas:
            habilidades = await matriz_service.get_habilidades_por_area(session, area.codigo)
            for h in habilidades:
                ctx = await matriz_service.get_habilidade_contexto(session, h.codigo)
                contexto_por_habilidade[h.codigo] = {
                    "area_codigo": ctx.area_codigo,
                    "area_nome": ctx.area_nome,
                    "competencia_numero": ctx.competencia_numero,
                    "habilidade_descricao": ctx.habilidade_descricao,
                }

        registros = []
        for origem in CONDICOES:
            questoes = await questoes_service.get_por_origem(session, origem)
            for q in questoes:
                ctx = contexto_por_habilidade.get(q.habilidade_codigo, {})
                registros.append(
                    {
                        "id": q.id,
                        "origem": q.origem.value,
                        "area_codigo": ctx.get("area_codigo"),
                        "area_nome": ctx.get("area_nome"),
                        "competencia_numero": ctx.get("competencia_numero"),
                        "habilidade_codigo": q.habilidade_codigo,
                        "habilidade_descricao": ctx.get("habilidade_descricao"),
                        "enunciado": q.enunciado,
                        "alternativa_a": q.alternativas.get("A", ""),
                        "alternativa_b": q.alternativas.get("B", ""),
                        "alternativa_c": q.alternativas.get("C", ""),
                        "alternativa_d": q.alternativas.get("D", ""),
                        "alternativa_e": q.alternativas.get("E", ""),
                        "gabarito": q.gabarito,
                        "justificativa": q.justificativa,
                        "validacao_estrutural_ok": q.validacao_estrutural_ok,
                        "cobertura_lexical": q.metricas.cobertura_lexical,
                        "especificidade_curricular": q.metricas.especificidade_curricular,
                        "similaridade_semantica": q.metricas.similaridade_semantica,
                        "ttr": q.metricas.ttr,
                        "fkgl": q.metricas.fkgl,
                        "judge_d1_alinhamento_habilidade": q.julgamento.d1_alinhamento_habilidade,
                        "judge_d2_adequacao_objetos_conhecimento": q.julgamento.d2_adequacao_objetos_conhecimento,
                        "judge_d3_plausibilidade_distratores": q.julgamento.d3_plausibilidade_distratores,
                        "judge_d4_nivel_escolaridade": q.julgamento.d4_nivel_escolaridade,
                        "judge_d5_aderencia_formato_enem": q.julgamento.d5_aderencia_formato_enem,
                        "judge_justificativa": q.julgamento.justificativa,
                    }
                )

        OUTPUT_PATH.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Exportados %d registros para %s", len(registros), OUTPUT_PATH)

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
