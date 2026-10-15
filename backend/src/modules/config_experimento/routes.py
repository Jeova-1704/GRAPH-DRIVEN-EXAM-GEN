from fastapi import APIRouter, HTTPException

from ...infrastructure.dependencies import CurrentSuperUserDep, GraphSessionDep
from ..common.utils.error_handler import handle_exception
from .dependencies import ConfigExperimentoServiceDep
from .schemas import ConfigExperimento, ConfigExperimentoUpdate

router = APIRouter(tags=["Configuracao"])


@router.get("/", response_model=ConfigExperimento, summary="Get current experiment parameters")
async def get_config(db: GraphSessionDep, service: ConfigExperimentoServiceDep) -> ConfigExperimento:
    try:
        return await service.get(db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.put("/", response_model=ConfigExperimento, summary="Update experiment parameters")
async def atualizar_config(
    patch: ConfigExperimentoUpdate,
    db: GraphSessionDep,
    service: ConfigExperimentoServiceDep,
    _: CurrentSuperUserDep,
) -> ConfigExperimento:
    try:
        return await service.atualizar(db, patch)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
