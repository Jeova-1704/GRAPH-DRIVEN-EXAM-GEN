from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from neo4j import AsyncSession as Neo4jAsyncSession
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.dependencies import get_current_superuser, get_current_user, get_optional_user
from .database.session import async_session
from .graph.session import graph_session
from .llm.glm_client import GLMClient, get_glm_client

# Database
AsyncSessionDep = Annotated[AsyncSession, Depends(async_session)]

# Graph database (ENEM Reference Matrix + Questao)
GraphSessionDep = Annotated[Neo4jAsyncSession, Depends(graph_session)]

# GLM (Zhipu AI) client
GLMClientDep = Annotated[GLMClient, Depends(get_glm_client)]

# Users (dict-compat, resolved by crudauth)
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
CurrentSuperUserDep = Annotated[dict[str, Any], Depends(get_current_superuser)]
OptionalUserDep = Annotated[dict[str, Any] | None, Depends(get_optional_user)]

# Auth form
OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
