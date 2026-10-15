from enum import StrEnum

from pydantic import BaseModel

from ..validacao.schemas import ItemGerado, ValidacaoResultado


class CondicaoExperimental(StrEnum):
    """The three parallel experimental conditions (Secao 3.6.2 / 3.7 do TCC)."""

    COM_GRAFO = "com_grafo"
    COM_FEWSHOT_SEM_GRAFO = "com_fewshot_sem_grafo"
    SEM_GRAFO = "sem_grafo"


class FewShot(BaseModel):
    """A real ENEM item used as a few-shot example."""

    enunciado: str
    alternativas: dict[str, str]
    gabarito: str


class GeracaoRequest(BaseModel):
    habilidade_codigo: str
    condicao: CondicaoExperimental
    few_shots: list[FewShot] = []


class GeracaoResponse(BaseModel):
    item: ItemGerado
    validacao: ValidacaoResultado
