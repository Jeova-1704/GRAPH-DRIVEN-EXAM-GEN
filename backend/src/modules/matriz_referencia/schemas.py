from pydantic import BaseModel, computed_field


class AreaRead(BaseModel):
    codigo: str
    nome: str


class HabilidadeSummary(BaseModel):
    codigo: str
    descricao: str


class ObjetoConhecimentoRead(BaseModel):
    codigo: str
    titulo: str
    descricao: str


class HabilidadeContexto(BaseModel):
    """A Habilidade with its full curricular context, used to build the GraphRAG context_block (Secao 3.6)."""

    habilidade_codigo: str
    habilidade_descricao: str
    competencia_numero: int
    competencia_descricao: str
    area_codigo: str
    area_nome: str
    objetos_conhecimento: list[ObjetoConhecimentoRead]


class IntegridadeRelatorio(BaseModel):
    """Structural verification report (Secao 3.4.4 / 4.1 do TCC)."""

    total_areas: int
    total_competencias: int
    total_habilidades: int
    total_objetos_conhecimento: int
    habilidades_sem_objeto_conhecimento: int
    habilidades_sem_competencia: int
    competencias_sem_area: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def integro(self) -> bool:
        return (
            self.habilidades_sem_objeto_conhecimento == 0
            and self.habilidades_sem_competencia == 0
            and self.competencias_sem_area == 0
        )


class CargaResultado(BaseModel):
    """Result of loading the Matriz de Referencia JSON into Neo4j."""

    areas_carregadas: int
    competencias_carregadas: int
    habilidades_carregadas: int
    objetos_conhecimento_carregados: int
