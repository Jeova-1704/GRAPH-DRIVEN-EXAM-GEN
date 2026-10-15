from pydantic import BaseModel


class ConfigExperimento(BaseModel):
    """Runtime-editable experiment parameters (Secao 3.5.3 do TCC), persisted on the
    single :Config node. Falls back to Settings defaults until first saved."""

    glm_generation_model: str
    glm_judge_model: str
    glm_temperature: float
    glm_max_tokens: int
    geracao_itens_por_condicao: int
    geracao_fewshots_por_habilidade: int
    validacao_enunciado_min_chars: int
    validacao_justificativa_min_chars: int
    estatistica_alpha: float
    estatistica_alpha_bonferroni: float


class ConfigExperimentoUpdate(BaseModel):
    """All fields optional — PATCH-style partial update."""

    glm_generation_model: str | None = None
    glm_judge_model: str | None = None
    glm_temperature: float | None = None
    glm_max_tokens: int | None = None
    geracao_itens_por_condicao: int | None = None
    geracao_fewshots_por_habilidade: int | None = None
    validacao_enunciado_min_chars: int | None = None
    validacao_justificativa_min_chars: int | None = None
    estatistica_alpha: float | None = None
    estatistica_alpha_bonferroni: float | None = None
