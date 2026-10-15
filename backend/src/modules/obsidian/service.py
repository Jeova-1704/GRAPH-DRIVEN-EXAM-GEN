"""Obsidian Markdown export (Secao 3.5.4 / 3.10 do TCC): YAML frontmatter + wiki-links
per node, so the ENEM graph can be browsed in Obsidian's Graph View."""

from pathlib import Path

from ..matriz_referencia.schemas import HabilidadeContexto
from ..questoes.schemas import QuestaoRead


def _yaml_frontmatter(campos: dict[str, object]) -> str:
    linhas = "\n".join(f"{chave}: {valor}" for chave, valor in campos.items())
    return f"---\n{linhas}\n---\n"


class ObsidianService:
    def build_habilidade_markdown(self, habilidade: HabilidadeContexto) -> str:
        frontmatter = _yaml_frontmatter(
            {
                "codigo": habilidade.habilidade_codigo,
                "area": habilidade.area_codigo,
                "competencia": habilidade.competencia_numero,
            }
        )
        objetos = "\n".join(f"- **{oc.titulo}**: {oc.descricao}" for oc in habilidade.objetos_conhecimento) or ("(nenhum)")
        return (
            f"{frontmatter}\n"
            f"# {habilidade.habilidade_codigo}\n\n"
            f"{habilidade.habilidade_descricao}\n\n"
            f"Area: [[{habilidade.area_codigo}]]\n"
            f"Competencia {habilidade.competencia_numero}: {habilidade.competencia_descricao}\n\n"
            f"## Objetos de Conhecimento\n{objetos}\n"
        )

    def build_questao_markdown(self, questao: QuestaoRead) -> str:
        frontmatter = _yaml_frontmatter(
            {
                "id": questao.id,
                "origem": questao.origem.value,
                "gabarito": questao.gabarito,
                "validacao_estrutural_ok": questao.validacao_estrutural_ok,
            }
        )
        alternativas = "\n".join(f"- **{letra}**: {texto}" for letra, texto in sorted(questao.alternativas.items()))
        justificativa = f"\n\n**Justificativa**: {questao.justificativa}" if questao.justificativa else ""
        return (
            f"{frontmatter}\n"
            f"# Questao {questao.id}\n\n"
            f"{questao.enunciado}\n\n"
            f"{alternativas}\n\n"
            f"**Gabarito**: {questao.gabarito}"
            f"{justificativa}\n\n"
            f"Avalia: [[{questao.habilidade_codigo}]]\n"
        )

    def exportar_habilidade(self, diretorio: Path, habilidade: HabilidadeContexto) -> Path:
        diretorio.mkdir(parents=True, exist_ok=True)
        caminho = diretorio / f"{habilidade.habilidade_codigo}.md"
        caminho.write_text(self.build_habilidade_markdown(habilidade), encoding="utf-8")
        return caminho

    def exportar_questao(self, diretorio: Path, questao: QuestaoRead) -> Path:
        diretorio.mkdir(parents=True, exist_ok=True)
        caminho = diretorio / f"Questao-{questao.id}.md"
        caminho.write_text(self.build_questao_markdown(questao), encoding="utf-8")
        return caminho
