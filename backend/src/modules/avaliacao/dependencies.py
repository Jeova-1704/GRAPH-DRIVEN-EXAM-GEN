from typing import Annotated

from fastapi import Depends

from .service import AvaliacaoService


def get_avaliacao_service() -> AvaliacaoService:
    return AvaliacaoService()


AvaliacaoServiceDep = Annotated[AvaliacaoService, Depends(get_avaliacao_service)]
