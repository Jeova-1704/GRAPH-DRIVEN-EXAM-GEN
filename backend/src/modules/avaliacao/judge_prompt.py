"""LLM-as-Judge prompt template (Secao 3.9.2 do TCC): a blind, independent judge model
scores a generated item on five pedagogical dimensions, 1-5 each, with justification."""

from ..matriz_referencia.schemas import HabilidadeContexto
from ..validacao.schemas import ItemGerado

_ESCALA_MIN = 1
_ESCALA_MAX = 5


def build_judge_prompt(item: ItemGerado, habilidade: HabilidadeContexto) -> str:
    alternativas = "\n".join(f"{letra}) {texto}" for letra, texto in sorted(item.alternativas.items()))
    ocs = "; ".join(oc.titulo for oc in habilidade.objetos_conhecimento) or "(nenhum objeto de conhecimento listado)"

    return (
        "[SISTEMA] Voce e um avaliador pedagogico independente e cego, especialista em itens ENEM.\n"
        "Avalie o item abaixo em relacao a habilidade-alvo, sem saber qual foi o metodo de geracao.\n"
        "Responda exclusivamente em JSON, sem texto adicional.\n"
        f"[HABILIDADE-ALVO] {habilidade.habilidade_codigo}: {habilidade.habilidade_descricao}\n"
        f"[OBJETOS DE CONHECIMENTO ESPERADOS] {ocs}\n"
        f"[ITEM] Enunciado: {item.enunciado}\n"
        f"Alternativas:\n{alternativas}\n"
        f"Gabarito: {item.gabarito}\n"
        f"Justificativa do gerador: {item.justificativa}\n"
        f"[INSTRUCOES] Atribua uma nota de {_ESCALA_MIN} a {_ESCALA_MAX} para cada dimensao:\n"
        "d1: alinhamento a habilidade-alvo.\n"
        "d2: adequacao dos objetos de conhecimento.\n"
        "d3: plausibilidade dos distratores.\n"
        "d4: adequacao ao nivel de escolaridade (Ensino Medio).\n"
        "d5: aderencia ao formato ENEM.\n"
        '[SAIDA] {"d1":X,"d2":X,"d3":X,"d4":X,"d5":X,"justificativa":"..."}'
    )
