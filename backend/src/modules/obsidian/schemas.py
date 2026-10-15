from pydantic import BaseModel


class ExportarRequest(BaseModel):
    diretorio: str = "obsidian_vault"


class ExportarResultado(BaseModel):
    diretorio: str
    habilidades_exportadas: int
    questoes_exportadas: int
