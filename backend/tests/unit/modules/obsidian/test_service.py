from pathlib import Path

import pytest

from src.modules.matriz_referencia.schemas import HabilidadeContexto, ObjetoConhecimentoRead
from src.modules.obsidian.service import ObsidianService
from src.modules.questoes.schemas import OrigemQuestao, QuestaoRead

pytestmark = pytest.mark.unit

HABILIDADE = HabilidadeContexto(
    habilidade_codigo="CN-H17",
    habilidade_descricao="Relacionar informacoes apresentadas em diferentes formas de linguagem.",
    competencia_numero=5,
    competencia_descricao="Entender metodos e procedimentos proprios das ciencias naturais.",
    area_codigo="CN",
    area_nome="Ciencias da Natureza",
    objetos_conhecimento=[
        ObjetoConhecimentoRead(codigo="CN-FIS-OC1", titulo="Conhecimentos basicos", descricao="Notacao cientifica."),
    ],
)

QUESTAO = QuestaoRead(
    id="q-123",
    habilidade_codigo="CN-H17",
    enunciado="Enunciado de exemplo.",
    alternativas={"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
    gabarito="A",
    justificativa="Justificativa de exemplo.",
    origem=OrigemQuestao.COM_GRAFO,
    ano_origem=None,
    validacao_estrutural_ok=True,
)


def test_habilidade_markdown_has_yaml_frontmatter() -> None:
    md = ObsidianService().build_habilidade_markdown(HABILIDADE)
    assert md.startswith("---\n")
    assert "codigo: CN-H17" in md
    assert "area: CN" in md


def test_habilidade_markdown_has_wikilink_to_area() -> None:
    md = ObsidianService().build_habilidade_markdown(HABILIDADE)
    assert "[[CN]]" in md


def test_habilidade_markdown_lists_objetos_conhecimento() -> None:
    md = ObsidianService().build_habilidade_markdown(HABILIDADE)
    assert "Conhecimentos basicos" in md
    assert "Notacao cientifica" in md


def test_questao_markdown_has_wikilink_to_habilidade() -> None:
    md = ObsidianService().build_questao_markdown(QUESTAO)
    assert "[[CN-H17]]" in md


def test_questao_markdown_includes_gabarito_and_alternativas() -> None:
    md = ObsidianService().build_questao_markdown(QUESTAO)
    assert "Gabarito**: A" in md
    assert "**A**: a" in md


def test_exportar_habilidade_writes_file(tmp_path: Path) -> None:
    caminho = ObsidianService().exportar_habilidade(tmp_path, HABILIDADE)
    assert caminho.exists()
    assert caminho.name == "CN-H17.md"
    assert "CN-H17" in caminho.read_text(encoding="utf-8")


def test_exportar_questao_writes_file(tmp_path: Path) -> None:
    caminho = ObsidianService().exportar_questao(tmp_path, QUESTAO)
    assert caminho.exists()
    assert caminho.name == "Questao-q-123.md"
