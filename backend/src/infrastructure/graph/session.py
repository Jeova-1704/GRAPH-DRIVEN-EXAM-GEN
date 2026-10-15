from collections.abc import AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j import AsyncSession as Neo4jAsyncSession

from ..config.settings import settings

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    """Return the process-wide Neo4j async driver, creating it on first use."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
        )
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver. Call from the app lifespan shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def verify_connectivity() -> None:
    """Raise if Neo4j is unreachable. Call from the app lifespan startup."""
    await get_driver().verify_connectivity()


async def graph_session() -> AsyncGenerator[Neo4jAsyncSession, None]:
    """FastAPI dependency yielding a Neo4j async session scoped to the configured database."""
    session = get_driver().session(database=settings.NEO4J_DATABASE)
    try:
        yield session
    finally:
        await session.close()
