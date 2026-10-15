"""Load the ENEM Reference Matrix (data/matriz_referencia.json) into Neo4j.

Usage (from backend/):
    uv run python -m scripts.load_matriz_referencia

Requires NEO4J_ENABLED=true and a reachable Neo4j instance (see
../docker-compose.neo4j.yml). Safe to re-run — every write is a Cypher MERGE.
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.infrastructure.graph.session import close_driver, graph_session  # noqa: E402
from src.infrastructure.logging import get_logger  # noqa: E402
from src.modules.matriz_referencia.service import MatrizReferenciaService  # noqa: E402

logger = get_logger()


async def main() -> None:
    service = MatrizReferenciaService()

    async for session in graph_session():
        resultado = await service.carregar_de_arquivo(session)
        logger.info(
            "Matriz carregada: %d areas, %d competencias, %d habilidades, %d objetos de conhecimento",
            resultado.areas_carregadas,
            resultado.competencias_carregadas,
            resultado.habilidades_carregadas,
            resultado.objetos_conhecimento_carregados,
        )

        relatorio = await service.verificar_integridade(session)
        logger.info("Relatorio de integridade: %s", relatorio.model_dump())
        if not relatorio.integro:
            logger.error("Grafo carregado com inconsistencias estruturais — ver relatorio acima.")

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
