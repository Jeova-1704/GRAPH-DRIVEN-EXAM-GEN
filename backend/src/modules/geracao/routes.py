from fastapi import APIRouter, HTTPException

from ...infrastructure.dependencies import CurrentSuperUserDep, GLMClientDep, GraphSessionDep
from ..common.utils.error_handler import handle_exception
from ..matriz_referencia.dependencies import MatrizReferenciaServiceDep
from .dependencies import GeracaoServiceDep
from .schemas import GeracaoRequest, GeracaoResponse

router = APIRouter(tags=["Geracao"])


@router.post(
    "/item",
    response_model=GeracaoResponse,
    summary="Generate one item for a Habilidade under one experimental condition",
)
async def gerar_item(
    request: GeracaoRequest,
    db: GraphSessionDep,
    glm_client: GLMClientDep,
    matriz_service: MatrizReferenciaServiceDep,
    geracao_service: GeracaoServiceDep,
    _: CurrentSuperUserDep,
) -> GeracaoResponse:
    try:
        habilidade = await matriz_service.get_habilidade_contexto(db, request.habilidade_codigo)
        item, validacao = await geracao_service.gerar_item(glm_client, habilidade, request.condicao, request.few_shots)
        return GeracaoResponse(item=item, validacao=validacao)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
