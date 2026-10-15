import json
from pathlib import Path
from typing import Any

from neo4j import AsyncSession as Neo4jAsyncSession

from ..common.exceptions import ResourceNotFoundError
from . import cypher
from .schemas import (
    AreaRead,
    CargaResultado,
    HabilidadeContexto,
    HabilidadeSummary,
    IntegridadeRelatorio,
    ObjetoConhecimentoRead,
)

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "matriz_referencia.json"


class MatrizReferenciaService:
    """Loads and queries the ENEM Reference Matrix property graph (Secao 3.4 do TCC)."""

    async def carregar_de_arquivo(self, session: Neo4jAsyncSession, path: Path = DEFAULT_DATA_PATH) -> CargaResultado:
        """Idempotently load Areas/Competencias/Habilidades/ObjetosConhecimento from the JSON dataset."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return await self.carregar_de_dados(session, data)

    async def carregar_de_dados(self, session: Neo4jAsyncSession, data: dict[str, Any]) -> CargaResultado:
        for statement in cypher.CONSTRAINTS:
            await session.run(statement)

        n_areas = n_competencias = n_habilidades = n_ocs = 0

        for area in data["areas"]:
            await session.run(cypher.MERGE_AREA, codigo=area["codigo"], nome=area["nome"])
            n_areas += 1

            for oc in area["objetos_conhecimento"]:
                await session.run(
                    cypher.MERGE_OBJETO_CONHECIMENTO,
                    area_codigo=area["codigo"],
                    codigo=oc["codigo"],
                    titulo=oc["titulo"],
                    descricao=oc["descricao"],
                )
                n_ocs += 1

            for competencia in area["competencias"]:
                await session.run(
                    cypher.MERGE_COMPETENCIA,
                    area_codigo=area["codigo"],
                    numero=competencia["numero"],
                    descricao=competencia["descricao"],
                )
                n_competencias += 1

                for habilidade in competencia["habilidades"]:
                    await session.run(
                        cypher.MERGE_HABILIDADE,
                        area_codigo=area["codigo"],
                        competencia_numero=competencia["numero"],
                        codigo=habilidade["codigo"],
                        descricao=habilidade["descricao"],
                    )
                    n_habilidades += 1

                    for oc_codigo in competencia["objetos_conhecimento"]:
                        await session.run(
                            cypher.MERGE_HABILIDADE_ABRANGE_OC,
                            habilidade_codigo=habilidade["codigo"],
                            oc_codigo=oc_codigo,
                        )

        return CargaResultado(
            areas_carregadas=n_areas,
            competencias_carregadas=n_competencias,
            habilidades_carregadas=n_habilidades,
            objetos_conhecimento_carregados=n_ocs,
        )

    async def get_areas(self, session: Neo4jAsyncSession) -> list[AreaRead]:
        result = await session.run(cypher.GET_AREAS)
        return [AreaRead(codigo=r["codigo"], nome=r["nome"]) async for r in result]

    async def get_habilidades_por_area(self, session: Neo4jAsyncSession, area_codigo: str) -> list[HabilidadeSummary]:
        result = await session.run(cypher.GET_HABILIDADES_POR_AREA, area_codigo=area_codigo)
        return [HabilidadeSummary(codigo=r["codigo"], descricao=r["descricao"]) async for r in result]

    async def get_habilidade_contexto(self, session: Neo4jAsyncSession, codigo: str) -> HabilidadeContexto:
        """Fetch the full curricular context for a Habilidade — the raw material for the
        GraphRAG context_block (Secao 3.6 do TCC): Area, Competencia and its ObjetosConhecimento.
        """
        result = await session.run(cypher.GET_HABILIDADE_COM_CONTEXTO, codigo=codigo)
        record = await result.single()
        if record is None:
            raise ResourceNotFoundError(f"Habilidade {codigo} not found")

        objetos = [ObjetoConhecimentoRead(**oc) for oc in record["objetos_conhecimento"] if oc["codigo"] is not None]
        return HabilidadeContexto(
            habilidade_codigo=record["habilidade_codigo"],
            habilidade_descricao=record["habilidade_descricao"],
            competencia_numero=record["competencia_numero"],
            competencia_descricao=record["competencia_descricao"],
            area_codigo=record["area_codigo"],
            area_nome=record["area_nome"],
            objetos_conhecimento=objetos,
        )

    async def verificar_integridade(self, session: Neo4jAsyncSession) -> IntegridadeRelatorio:
        """Structural verification queries (Secao 3.4.4 / Objetivo A, Secao 4.1 do TCC)."""

        async def count_label(label: str) -> int:
            result = await session.run(cypher.COUNT_NODES_BY_LABEL, label=label)
            record = await result.single()
            return int(record["total"]) if record else 0

        async def count_query(query: str) -> int:
            result = await session.run(query)
            record = await result.single()
            return int(record["total"]) if record else 0

        return IntegridadeRelatorio(
            total_areas=await count_label("Area"),
            total_competencias=await count_label("Competencia"),
            total_habilidades=await count_label("Habilidade"),
            total_objetos_conhecimento=await count_label("ObjetoConhecimento"),
            habilidades_sem_objeto_conhecimento=await count_query(cypher.COUNT_HABILIDADES_SEM_OC),
            habilidades_sem_competencia=await count_query(cypher.COUNT_HABILIDADES_SEM_COMPETENCIA),
            competencias_sem_area=await count_query(cypher.COUNT_COMPETENCIAS_SEM_AREA),
        )
