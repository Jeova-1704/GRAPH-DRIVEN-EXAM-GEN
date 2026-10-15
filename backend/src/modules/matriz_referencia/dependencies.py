from typing import Annotated

from fastapi import Depends

from .service import MatrizReferenciaService


def get_matriz_referencia_service() -> MatrizReferenciaService:
    return MatrizReferenciaService()


MatrizReferenciaServiceDep = Annotated[MatrizReferenciaService, Depends(get_matriz_referencia_service)]
