from pydantic import BaseModel


class ItemGerado(BaseModel):
    """The JSON shape produced by the generation LLM, per the [SAIDA] block of PROMPT_BASE (Secao 3.6.1/4.4)."""

    enunciado: str
    alternativas: dict[str, str]
    gabarito: str
    justificativa: str


class ValidacaoResultado(BaseModel):
    """Outcome of the five structural criteria C1-C5 (Tabela 4 do TCC)."""

    validacao_estrutural_ok: bool
    criterios_reprovados: list[str]

    @property
    def ok(self) -> bool:
        return self.validacao_estrutural_ok
