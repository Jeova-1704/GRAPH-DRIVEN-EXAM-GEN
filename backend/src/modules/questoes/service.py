import json
import uuid
from typing import Any

from neo4j import AsyncSession as Neo4jAsyncSession

from ...modules.geracao.schemas import FewShot
from ..common.exceptions import ResourceNotFoundError
from . import cypher
from .schemas import OrigemQuestao, QuestaoCreate, QuestaoJulgamento, QuestaoMetricas, QuestaoRead


def _record_to_questao_read(record: Any) -> QuestaoRead:
    return QuestaoRead(
        id=record["id"],
        habilidade_codigo=record["habilidade_codigo"],
        enunciado=record["enunciado"],
        alternativas=json.loads(record["alternativas_json"]),
        gabarito=record["gabarito"],
        justificativa=record["justificativa"],
        origem=OrigemQuestao(record["origem"]),
        ano_origem=record["ano_origem"],
        validacao_estrutural_ok=record["validacao_estrutural_ok"],
        metricas=QuestaoMetricas(
            cobertura_lexical=record["cobertura_lexical"],
            especificidade_curricular=record["especificidade_curricular"],
            similaridade_semantica=record["similaridade_semantica"],
            ttr=record["ttr"],
            fkgl=record["fkgl"],
        ),
        julgamento=QuestaoJulgamento(
            d1_alinhamento_habilidade=record["judge_d1_alinhamento"],
            d2_adequacao_objetos_conhecimento=record["judge_d2_objetos_conhecimento"],
            d3_plausibilidade_distratores=record["judge_d3_distratores"],
            d4_nivel_escolaridade=record["judge_d4_escolaridade"],
            d5_aderencia_formato_enem=record["judge_d5_formato_enem"],
            justificativa=record["judge_justificativa"],
        ),
    )


class QuestoesService:
    """Persists and retrieves :Questao nodes — official ENEM items (few-shot source) and
    LLM-generated corpus items (Secao 3.4.2 / 3.7 do TCC).
    """

    async def criar(self, session: Neo4jAsyncSession, questao: QuestaoCreate, questao_id: str | None = None) -> str:
        for statement in cypher.CONSTRAINTS:
            await session.run(statement)

        questao_id = questao_id or str(uuid.uuid4())
        await session.run(
            cypher.MERGE_QUESTAO,
            id=questao_id,
            habilidade_codigo=questao.habilidade_codigo,
            enunciado=questao.enunciado,
            alternativas_json=json.dumps(questao.alternativas, ensure_ascii=False),
            gabarito=questao.gabarito,
            justificativa=questao.justificativa,
            origem=questao.origem.value,
            ano_origem=questao.ano_origem,
            validacao_estrutural_ok=questao.validacao_estrutural_ok,
        )
        return questao_id

    async def get_fewshots(self, session: Neo4jAsyncSession, habilidade_codigo: str, limite: int) -> list[FewShot]:
        """Real ENEM items for a Habilidade, used as few-shots in com_grafo/com_fewshot_sem_grafo."""
        result = await session.run(cypher.GET_FEWSHOTS_POR_HABILIDADE, habilidade_codigo=habilidade_codigo, limite=limite)
        return [
            FewShot(enunciado=r["enunciado"], alternativas=json.loads(r["alternativas_json"]), gabarito=r["gabarito"])
            async for r in result
        ]

    async def get_por_id(self, session: Neo4jAsyncSession, questao_id: str) -> QuestaoRead:
        result = await session.run(cypher.GET_QUESTAO, id=questao_id)
        record = await result.single()
        if record is None:
            raise ResourceNotFoundError(f"Questao {questao_id} not found")
        return _record_to_questao_read(record)

    async def get_por_origem(self, session: Neo4jAsyncSession, origem: OrigemQuestao) -> list[QuestaoRead]:
        result = await session.run(cypher.GET_QUESTOES_POR_ORIGEM, origem=origem.value)
        return [_record_to_questao_read(r) async for r in result]

    async def contar_por_origem(self, session: Neo4jAsyncSession, origem: OrigemQuestao) -> int:
        result = await session.run(cypher.COUNT_QUESTOES_POR_ORIGEM, origem=origem.value)
        record = await result.single()
        return int(record["total"]) if record else 0

    async def salvar_metricas(
        self,
        session: Neo4jAsyncSession,
        questao_id: str,
        *,
        cobertura_lexical: float | None = None,
        especificidade_curricular: float | None = None,
        similaridade_semantica: float | None = None,
        ttr: float | None = None,
        fkgl: float | None = None,
    ) -> None:
        await session.run(
            cypher.SET_METRICAS,
            id=questao_id,
            cobertura_lexical=cobertura_lexical,
            especificidade_curricular=especificidade_curricular,
            similaridade_semantica=similaridade_semantica,
            ttr=ttr,
            fkgl=fkgl,
        )

    async def salvar_metricas_extra(
        self,
        session: Neo4jAsyncSession,
        questao_id: str,
        *,
        especificidade_curricular: float | None,
        similaridade_semantica: float | None,
    ) -> None:
        """Backfills especificidade_curricular/similaridade_semantica without touching the
        other 3 metric fields already set during corpus generation (executar_experimento.py
        called calcular_metricas_nlp without the optional cross-habilidade/embedding args).
        """
        await session.run(
            cypher.SET_METRICAS_EXTRA,
            id=questao_id,
            especificidade_curricular=especificidade_curricular,
            similaridade_semantica=similaridade_semantica,
        )

    async def salvar_julgamento(
        self,
        session: Neo4jAsyncSession,
        questao_id: str,
        *,
        d1: int,
        d2: int,
        d3: int,
        d4: int,
        d5: int,
        justificativa: str,
    ) -> None:
        await session.run(
            cypher.SET_JULGAMENTO,
            id=questao_id,
            d1=d1,
            d2=d2,
            d3=d3,
            d4=d4,
            d5=d5,
            justificativa=justificativa,
        )
