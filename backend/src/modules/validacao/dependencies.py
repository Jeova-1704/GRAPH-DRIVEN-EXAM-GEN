from typing import Annotated

from fastapi import Depends

from .service import ValidacaoService


def get_validacao_service() -> ValidacaoService:
    return ValidacaoService()


ValidacaoServiceDep = Annotated[ValidacaoService, Depends(get_validacao_service)]
