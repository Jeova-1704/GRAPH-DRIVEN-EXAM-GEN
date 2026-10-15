from typing import Annotated

from fastapi import Depends

from .service import QuestoesService


def get_questoes_service() -> QuestoesService:
    return QuestoesService()


QuestoesServiceDep = Annotated[QuestoesService, Depends(get_questoes_service)]
