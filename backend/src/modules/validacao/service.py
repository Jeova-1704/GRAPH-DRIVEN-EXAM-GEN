from ...infrastructure.config.settings import settings
from .schemas import ItemGerado, ValidacaoResultado

ALTERNATIVAS_ESPERADAS = {"A", "B", "C", "D", "E"}


class ValidacaoService:
    """Structural validation (Secao 3.8 do TCC): five mandatory criteria (C1-C5, Tabela 4)
    that mirror ENEM's formal item requirements. Runs before an item is persisted as part
    of the experimental corpus — items that fail are flagged but preserved for audit
    (Secao 3.8.1), never silently dropped.
    """

    def validar(self, item: ItemGerado) -> ValidacaoResultado:
        criterios_reprovados: list[str] = []

        # C1: exactly five non-empty alternatives, keyed A-E
        chaves = set(item.alternativas.keys())
        if chaves != ALTERNATIVAS_ESPERADAS or any(not v.strip() for v in item.alternativas.values()):
            criterios_reprovados.append("C1_cinco_alternativas")

        # C2: gabarito valido (A-E)
        if item.gabarito not in ALTERNATIVAS_ESPERADAS:
            criterios_reprovados.append("C2_gabarito_valido")

        # C3: sem alternativas duplicadas
        valores = list(item.alternativas.values())
        if len(set(v.strip().lower() for v in valores)) != len(valores):
            criterios_reprovados.append("C3_sem_duplicatas")

        # C4: enunciado com tamanho minimo
        if len(item.enunciado.strip()) < settings.VALIDACAO_ENUNCIADO_MIN_CHARS:
            criterios_reprovados.append("C4_enunciado_minimo")

        # C5: justificativa com tamanho minimo
        if len(item.justificativa.strip()) < settings.VALIDACAO_JUSTIFICATIVA_MIN_CHARS:
            criterios_reprovados.append("C5_justificativa_minima")

        return ValidacaoResultado(
            validacao_estrutural_ok=not criterios_reprovados,
            criterios_reprovados=criterios_reprovados,
        )
