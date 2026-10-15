import pytest

from src.modules.avaliacao.service import AvaliacaoService
from src.modules.common.exceptions import AvaliacaoError
from src.modules.matriz_referencia.schemas import HabilidadeContexto, ObjetoConhecimentoRead
from src.modules.validacao.schemas import ItemGerado

pytestmark = pytest.mark.unit

HABILIDADE = HabilidadeContexto(
    habilidade_codigo="CN-H20",
    habilidade_descricao="Caracterizar causas ou efeitos dos movimentos de corpos celestes.",
    competencia_numero=6,
    competencia_descricao="Apropriar-se de conhecimentos da fisica.",
    area_codigo="CN",
    area_nome="Ciencias da Natureza",
    objetos_conhecimento=[
        ObjetoConhecimentoRead(
            codigo="CN-FIS-OC4",
            titulo="A Mecanica e o funcionamento do Universo",
            descricao="Gravitacao universal, orbita, movimentos de corpos celestes.",
        )
    ],
)

ITEM = ItemGerado(
    enunciado="Um satelite em orbita ao redor da Terra sofre a acao da gravitacao universal. " + ("x" * 20),
    alternativas={"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
    gabarito="A",
    justificativa="y" * 100,
)


class FakeGLMClient:
    def __init__(self, response: str) -> None:
        self._response = response

    async def judge(self, prompt: str) -> str:
        return self._response


def test_calcular_metricas_nlp_returns_expected_shape() -> None:
    service = AvaliacaoService()
    metricas = service.calcular_metricas_nlp(ITEM, HABILIDADE)

    assert 0.0 <= metricas.cobertura_lexical <= 1.0
    assert metricas.especificidade_curricular is None  # not requested
    assert metricas.similaridade_semantica is None  # no embeddings passed
    assert 0.0 <= metricas.ttr <= 1.0
    assert isinstance(metricas.fkgl, float)


def test_calcular_metricas_nlp_picks_up_orbita_from_context() -> None:
    service = AvaliacaoService()
    metricas = service.calcular_metricas_nlp(ITEM, HABILIDADE)
    assert metricas.cobertura_lexical > 0.0  # "orbita"/"gravitacao" overlap with the OC text


def test_calcular_metricas_nlp_with_especificidade_and_similaridade() -> None:
    service = AvaliacaoService()
    metricas = service.calcular_metricas_nlp(
        ITEM,
        HABILIDADE,
        tokens_outras_habilidades=[["gato", "cachorro"], ["passaro", "peixe"]],
        embedding_item=[1.0, 0.0],
        embedding_habilidade=[1.0, 0.0],
    )
    assert metricas.especificidade_curricular is not None
    assert metricas.similaridade_semantica == pytest.approx(1.0)


async def test_julgar_parses_valid_response() -> None:
    service = AvaliacaoService()
    glm_client = FakeGLMClient('{"d1":5,"d2":4,"d3":3,"d4":5,"d5":4,"justificativa":"boa aderencia"}')

    julgamento = await service.julgar(glm_client, ITEM, HABILIDADE)

    assert julgamento.d1_alinhamento_habilidade == 5
    assert julgamento.score_medio == pytest.approx((5 + 4 + 3 + 5 + 4) / 5)


async def test_julgar_raises_avaliacao_error_on_malformed_json() -> None:
    service = AvaliacaoService()
    glm_client = FakeGLMClient("resposta invalida")

    with pytest.raises(AvaliacaoError):
        await service.julgar(glm_client, ITEM, HABILIDADE)


async def test_julgar_raises_avaliacao_error_on_missing_dimension() -> None:
    service = AvaliacaoService()
    glm_client = FakeGLMClient('{"d1":5,"d2":4,"justificativa":"incompleto"}')

    with pytest.raises(AvaliacaoError):
        await service.julgar(glm_client, ITEM, HABILIDADE)


async def test_julgar_strips_markdown_code_fences() -> None:
    service = AvaliacaoService()
    glm_client = FakeGLMClient('```json\n{"d1":1,"d2":1,"d3":1,"d4":1,"d5":1,"justificativa":"x"}\n```')

    julgamento = await service.julgar(glm_client, ITEM, HABILIDADE)

    assert julgamento.score_medio == 1.0
