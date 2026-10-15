"""Unit tests for the five structural criteria C1-C5 (Tabela 4, Secao 3.8 do TCC)."""

import pytest

from src.modules.validacao.schemas import ItemGerado
from src.modules.validacao.service import ValidacaoService

pytestmark = pytest.mark.unit

ENUNCIADO_VALIDO = "x" * 50
JUSTIFICATIVA_VALIDA = "y" * 100


def make_item(**overrides: object) -> ItemGerado:
    base = {
        "enunciado": ENUNCIADO_VALIDO,
        "alternativas": {"A": "alt a", "B": "alt b", "C": "alt c", "D": "alt d", "E": "alt e"},
        "gabarito": "A",
        "justificativa": JUSTIFICATIVA_VALIDA,
    }
    base.update(overrides)
    return ItemGerado(**base)  # type: ignore[arg-type]


@pytest.fixture
def service() -> ValidacaoService:
    return ValidacaoService()


def test_item_valido_passa_em_todos_os_criterios(service: ValidacaoService) -> None:
    resultado = service.validar(make_item())
    assert resultado.ok is True
    assert resultado.criterios_reprovados == []


def test_c1_reprova_menos_de_cinco_alternativas(service: ValidacaoService) -> None:
    item = make_item(alternativas={"A": "a", "B": "b", "C": "c", "D": "d"})
    resultado = service.validar(item)
    assert "C1_cinco_alternativas" in resultado.criterios_reprovados


def test_c1_reprova_alternativa_vazia(service: ValidacaoService) -> None:
    item = make_item(alternativas={"A": "", "B": "b", "C": "c", "D": "d", "E": "e"})
    resultado = service.validar(item)
    assert "C1_cinco_alternativas" in resultado.criterios_reprovados


def test_c1_reprova_chave_fora_de_a_e(service: ValidacaoService) -> None:
    item = make_item(alternativas={"A": "a", "B": "b", "C": "c", "D": "d", "F": "f"})
    resultado = service.validar(item)
    assert "C1_cinco_alternativas" in resultado.criterios_reprovados


def test_c2_reprova_gabarito_invalido(service: ValidacaoService) -> None:
    item = make_item(gabarito="F")
    resultado = service.validar(item)
    assert "C2_gabarito_valido" in resultado.criterios_reprovados


@pytest.mark.parametrize("gabarito", ["A", "B", "C", "D", "E"])
def test_c2_aceita_qualquer_gabarito_valido(service: ValidacaoService, gabarito: str) -> None:
    resultado = service.validar(make_item(gabarito=gabarito))
    assert "C2_gabarito_valido" not in resultado.criterios_reprovados


def test_c3_reprova_alternativas_duplicadas_exatas(service: ValidacaoService) -> None:
    item = make_item(alternativas={"A": "mesmo texto", "B": "mesmo texto", "C": "c", "D": "d", "E": "e"})
    resultado = service.validar(item)
    assert "C3_sem_duplicatas" in resultado.criterios_reprovados


def test_c3_reprova_duplicata_case_insensitive(service: ValidacaoService) -> None:
    item = make_item(alternativas={"A": "Mesmo Texto", "B": "mesmo texto", "C": "c", "D": "d", "E": "e"})
    resultado = service.validar(item)
    assert "C3_sem_duplicatas" in resultado.criterios_reprovados


def test_c4_reprova_enunciado_curto(service: ValidacaoService) -> None:
    item = make_item(enunciado="muito curto")
    resultado = service.validar(item)
    assert "C4_enunciado_minimo" in resultado.criterios_reprovados


def test_c4_aceita_enunciado_no_limite_minimo(service: ValidacaoService) -> None:
    item = make_item(enunciado="x" * 50)
    resultado = service.validar(item)
    assert "C4_enunciado_minimo" not in resultado.criterios_reprovados


def test_c5_reprova_justificativa_curta(service: ValidacaoService) -> None:
    item = make_item(justificativa="muito curta")
    resultado = service.validar(item)
    assert "C5_justificativa_minima" in resultado.criterios_reprovados


def test_c5_aceita_justificativa_no_limite_minimo(service: ValidacaoService) -> None:
    item = make_item(justificativa="y" * 100)
    resultado = service.validar(item)
    assert "C5_justificativa_minima" not in resultado.criterios_reprovados


def test_multiplos_criterios_reprovados_simultaneamente(service: ValidacaoService) -> None:
    item = make_item(gabarito="Z", enunciado="curto", justificativa="curta")
    resultado = service.validar(item)
    assert resultado.ok is False
    assert set(resultado.criterios_reprovados) == {
        "C2_gabarito_valido",
        "C4_enunciado_minimo",
        "C5_justificativa_minima",
    }


def test_item_gerado_rejeita_payload_sem_campos_obrigatorios() -> None:
    with pytest.raises(Exception):
        ItemGerado(enunciado="apenas isso")  # type: ignore[call-arg]
