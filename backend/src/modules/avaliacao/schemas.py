from pydantic import BaseModel, computed_field


class MetricasNLP(BaseModel):
    """Camada B (Secao 3.9.1 do TCC)."""

    cobertura_lexical: float
    especificidade_curricular: float | None
    similaridade_semantica: float | None
    ttr: float
    fkgl: float


class JulgamentoLLM(BaseModel):
    """Camada A - LLM-as-Judge, cinco dimensoes em escala 1-5 (Secao 3.9.2 do TCC)."""

    d1_alinhamento_habilidade: int
    d2_adequacao_objetos_conhecimento: int
    d3_plausibilidade_distratores: int
    d4_nivel_escolaridade: int
    d5_aderencia_formato_enem: int
    justificativa: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def score_medio(self) -> float:
        return (
            self.d1_alinhamento_habilidade
            + self.d2_adequacao_objetos_conhecimento
            + self.d3_plausibilidade_distratores
            + self.d4_nivel_escolaridade
            + self.d5_aderencia_formato_enem
        ) / 5
