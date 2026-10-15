from fastapi import APIRouter, HTTPException

from ...infrastructure.dependencies import GraphSessionDep
from ..common.utils.error_handler import handle_exception
from .dependencies import QuestoesServiceDep
from .schemas import OrigemQuestao, QuestaoRead

router = APIRouter(tags=["Questoes"])


@router.get("/", response_model=list[QuestaoRead], summary="List Questoes by origin (ENEM or an experimental condition)")
async def listar_por_origem(origem: OrigemQuestao, db: GraphSessionDep, service: QuestoesServiceDep) -> list[QuestaoRead]:
    try:
        return await service.get_por_origem(db, origem)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/contagem", summary="Count Questoes per origin (corpus progress)")
async def contar_por_origem(db: GraphSessionDep, service: QuestoesServiceDep) -> dict[str, int]:
    try:
        return {origem.value: await service.contar_por_origem(db, origem) for origem in OrigemQuestao}
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{questao_id}", response_model=QuestaoRead, summary="Get one Questao by id")
async def get_por_id(questao_id: str, db: GraphSessionDep, service: QuestoesServiceDep) -> QuestaoRead:
    try:
        return await service.get_por_id(db, questao_id)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
