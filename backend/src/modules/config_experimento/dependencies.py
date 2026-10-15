from typing import Annotated

from fastapi import Depends

from .service import ConfigExperimentoService


def get_config_experimento_service() -> ConfigExperimentoService:
    return ConfigExperimentoService()


ConfigExperimentoServiceDep = Annotated[ConfigExperimentoService, Depends(get_config_experimento_service)]
