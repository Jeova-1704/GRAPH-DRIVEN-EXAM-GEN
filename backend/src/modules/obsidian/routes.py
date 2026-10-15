from pathlib import Path

from fastapi import APIRouter, HTTPException

from ...infrastructure.dependencies import CurrentSuperUserDep, GraphSessionDep
from ..common.utils.error_handler import handle_exception
from ..matriz_referencia.dependencies import MatrizReferenciaServiceDep
from ..questoes.dependencies import QuestoesServiceDep
from ..questoes.schemas import OrigemQuestao
from .dependencies import ObsidianServiceDep
from .schemas import ExportarRequest, ExportarResultado

router = APIRouter(tags=["Obsidian"])


@router.post(
    "/exportar",
    response_model=ExportarResultado,
    summary="Export the whole graph (Habilidades + Questoes) to Obsidian Markdown",
)
async def exportar(
    request: ExportarRequest,
    db: GraphSessionDep,
    matriz_service: MatrizReferenciaServiceDep,
    questoes_service: QuestoesServiceDep,
    obsidian_service: ObsidianServiceDep,
    _: CurrentSuperUserDep,
) -> ExportarResultado:
    try:
        diretorio = Path(request.diretorio)

        n_habilidades = 0
        for area in await matriz_service.get_areas(db):
            for habilidade_summary in await matriz_service.get_habilidades_por_area(db, area.codigo):
                habilidade = await matriz_service.get_habilidade_contexto(db, habilidade_summary.codigo)
                obsidian_service.exportar_habilidade(diretorio, habilidade)
                n_habilidades += 1

        n_questoes = 0
        for origem in OrigemQuestao:
            for questao in await questoes_service.get_por_origem(db, origem):
                obsidian_service.exportar_questao(diretorio, questao)
                n_questoes += 1

        return ExportarResultado(
            diretorio=str(diretorio),
            habilidades_exportadas=n_habilidades,
            questoes_exportadas=n_questoes,
        )
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
