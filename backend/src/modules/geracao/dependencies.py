from typing import Annotated

from fastapi import Depends

from .service import GeracaoService


def get_geracao_service() -> GeracaoService:
    return GeracaoService()


GeracaoServiceDep = Annotated[GeracaoService, Depends(get_geracao_service)]
