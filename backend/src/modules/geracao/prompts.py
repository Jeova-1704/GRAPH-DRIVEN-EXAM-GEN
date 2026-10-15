"""PROMPT_BASE and per-condition context_block construction (Secao 3.6 do TCC).

The template has four fixed blocks; only {context_block} varies between the three
experimental conditions (Secao 3.6.2/3.6.3) — everything else must be byte-identical
across conditions so that observed differences in output are attributable only to the
curricular context, not to prompt wording. `build_prompt` guarantees this by
interpolating context_block into one fixed template; `test_prompts_equivalence.py`
verifies it holds.
"""

from ..matriz_referencia.schemas import HabilidadeContexto
from .schemas import CondicaoExperimental, FewShot

_INSTRUCAO_SISTEMA = (
    "[SISTEMA] Voce e especialista em elaboracao de questoes ENEM.\n"
    "Gere um item de multipla escolha alinhado a habilidade informada.\n"
    "Responda exclusivamente em JSON, sem texto adicional."
)

_INSTRUCOES_SAIDA = (
    "[INSTRUCOES] Enunciado situacional (nao pode ser definicao direta).\n"
    "5 alternativas A-E. Gabarito unico. Sem LaTeX. Linguagem Ensino Medio.\n"
    "Justificativa com vinculo explicito a habilidade-alvo.\n"
    '[SAIDA] {"enunciado":"...","alternativas":{"A":"...","B":"...",'
    '"C":"...","D":"...","E":"..."},"gabarito":"X","justificativa":"..."}'
)


def _formatar_few_shots(few_shots: list[FewShot]) -> str:
    blocos = []
    for i, fs in enumerate(few_shots, start=1):
        alternativas = "; ".join(f"{letra}) {texto}" for letra, texto in sorted(fs.alternativas.items()))
        blocos.append(f"Exemplo {i}: {fs.enunciado} [{alternativas}] Gabarito: {fs.gabarito}")
    return "\n".join(blocos)


def build_context_block(
    condicao: CondicaoExperimental,
    habilidade: HabilidadeContexto,
    few_shots: list[FewShot],
) -> str:
    """Build the {context_block} for one experimental condition (Secao 3.6.2 do TCC)."""
    if condicao == CondicaoExperimental.COM_GRAFO:
        ocs = "; ".join(f"{oc.titulo}: {oc.descricao}" for oc in habilidade.objetos_conhecimento)
        return (
            f"Area: {habilidade.area_nome} ({habilidade.area_codigo})\n"
            f"Competencia {habilidade.competencia_numero}: {habilidade.competencia_descricao}\n"
            f"Habilidade {habilidade.habilidade_codigo}: {habilidade.habilidade_descricao}\n"
            f"Objetos de Conhecimento: {ocs}\n"
            f"Exemplos:\n{_formatar_few_shots(few_shots)}"
        )

    if condicao == CondicaoExperimental.COM_FEWSHOT_SEM_GRAFO:
        return (
            f"Habilidade {habilidade.habilidade_codigo}: {habilidade.habilidade_descricao}\n"
            f"Exemplos:\n{_formatar_few_shots(few_shots)}"
        )

    # SEM_GRAFO: apenas codigo + descricao da habilidade, sem OCs e sem few-shots
    return f"Habilidade {habilidade.habilidade_codigo}: {habilidade.habilidade_descricao}"


def build_prompt(
    condicao: CondicaoExperimental,
    habilidade: HabilidadeContexto,
    few_shots: list[FewShot],
) -> str:
    """Assemble the full PROMPT_BASE for one (habilidade, condicao) pair."""
    context_block = build_context_block(condicao, habilidade, few_shots)
    return f"{_INSTRUCAO_SISTEMA}\n[CONTEXTO] {context_block}\n{_INSTRUCOES_SAIDA}"
