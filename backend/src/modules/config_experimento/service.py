from neo4j import AsyncSession as Neo4jAsyncSession

from ...infrastructure.config.settings import settings
from . import cypher
from .schemas import ConfigExperimento, ConfigExperimentoUpdate


def _defaults() -> dict:
    return {
        "glm_generation_model": settings.GLM_GENERATION_MODEL,
        "glm_judge_model": settings.GLM_JUDGE_MODEL,
        "glm_temperature": settings.GLM_TEMPERATURE,
        "glm_max_tokens": settings.GLM_MAX_TOKENS,
        "geracao_itens_por_condicao": settings.GERACAO_ITENS_POR_CONDICAO,
        "geracao_fewshots_por_habilidade": settings.GERACAO_FEWSHOTS_POR_HABILIDADE,
        "validacao_enunciado_min_chars": settings.VALIDACAO_ENUNCIADO_MIN_CHARS,
        "validacao_justificativa_min_chars": settings.VALIDACAO_JUSTIFICATIVA_MIN_CHARS,
        "estatistica_alpha": settings.ESTATISTICA_ALPHA,
        "estatistica_alpha_bonferroni": settings.ESTATISTICA_ALPHA_BONFERRONI,
    }


class ConfigExperimentoService:
    """Runtime-editable parameters backed by the single :Config node (Secao 3.5.3 do TCC).
    Any field not yet saved falls back to the Settings/.env default.
    """

    async def get(self, session: Neo4jAsyncSession) -> ConfigExperimento:
        result = await session.run(cypher.GET_CONFIG)
        record = await result.single()
        salvo = dict(record["c"]) if record else {}
        return ConfigExperimento(**{**_defaults(), **salvo})

    async def atualizar(self, session: Neo4jAsyncSession, patch: ConfigExperimentoUpdate) -> ConfigExperimento:
        campos = {k: v for k, v in patch.model_dump().items() if v is not None}
        if campos:
            await session.run(cypher.MERGE_CONFIG, campos=campos)
        return await self.get(session)
