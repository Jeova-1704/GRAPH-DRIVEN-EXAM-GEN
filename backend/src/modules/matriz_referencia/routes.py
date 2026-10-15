from fastapi import APIRouter, HTTPException

from ...infrastructure.dependencies import CurrentSuperUserDep, GraphSessionDep
from ..common.utils.error_handler import handle_exception
from .dependencies import MatrizReferenciaServiceDep
from .schemas import AreaRead, CargaResultado, HabilidadeContexto, HabilidadeSummary, IntegridadeRelatorio

router = APIRouter(tags=["Matriz de Referencia"])


@router.get("/areas", response_model=list[AreaRead], summary="List ENEM knowledge areas")
async def get_areas(db: GraphSessionDep, service: MatrizReferenciaServiceDep) -> list[AreaRead]:
    try:
        return await service.get_areas(db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get(
    "/areas/{area_codigo}/habilidades",
    response_model=list[HabilidadeSummary],
    summary="List the Habilidades of a knowledge area",
)
async def get_habilidades_por_area(
    area_codigo: str, db: GraphSessionDep, service: MatrizReferenciaServiceDep
) -> list[HabilidadeSummary]:
    try:
        return await service.get_habilidades_por_area(db, area_codigo)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get(
    "/habilidades/{codigo}",
    response_model=HabilidadeContexto,
    summary="Get a Habilidade with its full curricular context (GraphRAG context_block source)",
)
async def get_habilidade(codigo: str, db: GraphSessionDep, service: MatrizReferenciaServiceDep) -> HabilidadeContexto:
    try:
        return await service.get_habilidade_contexto(db, codigo)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get(
    "/integridade",
    response_model=IntegridadeRelatorio,
    summary="Structural verification report",
)
async def get_integridade(
    db: GraphSessionDep,
    service: MatrizReferenciaServiceDep,
    _: CurrentSuperUserDep,
) -> IntegridadeRelatorio:
    try:
        return await service.verificar_integridade(db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post(
    "/carregar",
    response_model=CargaResultado,
    summary="Idempotently (re)load the bundled Matriz de Referencia JSON into the graph",
)
async def carregar_matriz(
    db: GraphSessionDep,
    service: MatrizReferenciaServiceDep,
    _: CurrentSuperUserDep,
) -> CargaResultado:
    try:
        return await service.carregar_de_arquivo(db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
