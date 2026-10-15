from typing import Annotated

from fastapi import Depends

from .service import ObsidianService


def get_obsidian_service() -> ObsidianService:
    return ObsidianService()


ObsidianServiceDep = Annotated[ObsidianService, Depends(get_obsidian_service)]
