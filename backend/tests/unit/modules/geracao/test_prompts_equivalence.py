"""Verifies the equivalence guarantee of Secao 3.6.3 do TCC: prompts for different
experimental conditions must differ ONLY in the {context_block} — same system
instructions, same output instructions, same everything else."""

import pytest

from src.modules.geracao import prompts
from src.modules.geracao.schemas import CondicaoExperimental, FewShot
from src.modules.matriz_referencia.schemas import HabilidadeContexto, ObjetoConhecimentoRead

pytestmark = pytest.mark.unit

HABILIDADE = HabilidadeContexto(
    habilidade_codigo="CN-H17",
    habilidade_descricao="Relacionar informacoes apresentadas em diferentes formas de linguagem.",
    competencia_numero=5,
    competencia_descricao="Entender metodos e procedimentos proprios das ciencias naturais.",
    area_codigo="CN",
    area_nome="Ciencias da Natureza e suas Tecnologias",
    objetos_conhecimento=[
        ObjetoConhecimentoRead(codigo="CN-FIS-OC1", titulo="Conhecimentos basicos", descricao="Notacao cientifica."),
    ],
)

FEW_SHOTS = [
    FewShot(
        enunciado="Um exemplo de item real do ENEM.",
        alternativas={"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        gabarito="B",
    )
]


def _fixed_scaffolding_parts(prompt: str) -> tuple[str, str]:
    """Return (before_contexto, after_contexto) — everything except the context_block itself."""
    prefix_marker = "[CONTEXTO] "
    suffix_marker = "\n[INSTRUCOES]"
    prefix_end = prompt.index(prefix_marker) + len(prefix_marker)
    suffix_start = prompt.index(suffix_marker)
    return prompt[:prefix_end], prompt[suffix_start:]


@pytest.mark.parametrize(
    "condicao", [CondicaoExperimental.COM_GRAFO, CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO, CondicaoExperimental.SEM_GRAFO]
)
def test_prompt_contains_fixed_blocks(condicao: CondicaoExperimental) -> None:
    prompt = prompts.build_prompt(condicao, HABILIDADE, FEW_SHOTS)
    assert "[SISTEMA]" in prompt
    assert "[CONTEXTO]" in prompt
    assert "[INSTRUCOES]" in prompt
    assert "[SAIDA]" in prompt


def test_prompts_differ_only_in_context_block() -> None:
    prompt_grafo = prompts.build_prompt(CondicaoExperimental.COM_GRAFO, HABILIDADE, FEW_SHOTS)
    prompt_fewshot = prompts.build_prompt(CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO, HABILIDADE, FEW_SHOTS)
    prompt_sem_grafo = prompts.build_prompt(CondicaoExperimental.SEM_GRAFO, HABILIDADE, FEW_SHOTS)

    scaffolding = {_fixed_scaffolding_parts(p) for p in (prompt_grafo, prompt_fewshot, prompt_sem_grafo)}
    assert len(scaffolding) == 1, "SISTEMA/INSTRUCOES/SAIDA blocks must be identical across conditions"


def test_com_grafo_includes_objetos_de_conhecimento() -> None:
    context_block = prompts.build_context_block(CondicaoExperimental.COM_GRAFO, HABILIDADE, FEW_SHOTS)
    assert "Objetos de Conhecimento" in context_block
    assert "Notacao cientifica" in context_block
    assert "Exemplo 1" in context_block


def test_com_fewshot_sem_grafo_excludes_objetos_de_conhecimento_but_keeps_fewshots() -> None:
    context_block = prompts.build_context_block(CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO, HABILIDADE, FEW_SHOTS)
    assert "Objetos de Conhecimento" not in context_block
    assert "Notacao cientifica" not in context_block
    assert "Exemplo 1" in context_block


def test_sem_grafo_excludes_objetos_de_conhecimento_and_fewshots() -> None:
    context_block = prompts.build_context_block(CondicaoExperimental.SEM_GRAFO, HABILIDADE, FEW_SHOTS)
    assert "Objetos de Conhecimento" not in context_block
    assert "Exemplo" not in context_block
    assert HABILIDADE.habilidade_codigo in context_block
    assert HABILIDADE.habilidade_descricao in context_block


def test_all_three_context_blocks_are_distinct() -> None:
    blocks = {
        prompts.build_context_block(c, HABILIDADE, FEW_SHOTS)
        for c in (CondicaoExperimental.COM_GRAFO, CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO, CondicaoExperimental.SEM_GRAFO)
    }
    assert len(blocks) == 3
