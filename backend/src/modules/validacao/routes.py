from fastapi import APIRouter

from .dependencies import ValidacaoServiceDep
from .schemas import ItemGerado, ValidacaoResultado

router = APIRouter(tags=["Validacao"])


@router.post(
    "/verificar",
    response_model=ValidacaoResultado,
    summary="Check an item against the five structural criteria C1-C5",
)
async def verificar_item(item: ItemGerado, service: ValidacaoServiceDep) -> ValidacaoResultado:
    return service.validar(item)
