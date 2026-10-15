from enum import StrEnum

from pydantic import BaseModel, Field


class OrigemQuestao(StrEnum):
    """Matches the :Questao.origem property (Secao 3.1/3.2 do artigo aprovado):
    ENEM for real official items (few-shot source), or one of the three
    experimental conditions for LLM-generated items."""

    ENEM = "ENEM"
    COM_GRAFO = "com_grafo"
    COM_FEWSHOT_SEM_GRAFO = "com_fewshot_sem_grafo"
    SEM_GRAFO = "sem_grafo"


class QuestaoCreate(BaseModel):
    habilidade_codigo: str
    enunciado: str
    alternativas: dict[str, str]
    gabarito: str
    justificativa: str | None = None
    origem: OrigemQuestao
    ano_origem: int | None = None
    validacao_estrutural_ok: bool = True


class QuestaoMetricas(BaseModel):
    """NLP indicators computed by modules/avaliacao (Camada B, Secao 3.9.1 do TCC)."""

    cobertura_lexical: float | None = None
    especificidade_curricular: float | None = None
    similaridade_semantica: float | None = None
    ttr: float | None = None
    fkgl: float | None = None


class QuestaoJulgamento(BaseModel):
    """LLM-as-Judge scores (Camada A, Secao 3.9.2 do TCC)."""

    d1_alinhamento_habilidade: int | None = None
    d2_adequacao_objetos_conhecimento: int | None = None
    d3_plausibilidade_distratores: int | None = None
    d4_nivel_escolaridade: int | None = None
    d5_aderencia_formato_enem: int | None = None
    justificativa: str | None = None


class QuestaoRead(BaseModel):
    id: str
    habilidade_codigo: str
    enunciado: str
    alternativas: dict[str, str]
    gabarito: str
    justificativa: str | None
    origem: OrigemQuestao
    ano_origem: int | None
    validacao_estrutural_ok: bool
    metricas: QuestaoMetricas = Field(default_factory=QuestaoMetricas)
    julgamento: QuestaoJulgamento = Field(default_factory=QuestaoJulgamento)
