"""Build data/questoes_geradas.xlsx: the full 1,788-item corpus with NLP metrics and the
scores of both LLM judges (principal: glm-4-plus, from data/julgamento_glm-4-plus.jsonl;
secondary: glm-4.5, the generator itself, from data/questoes_export.json).

Usage (from backend/):
    uv run --with openpyxl python -m scripts.build_xlsx
"""

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

DATA_DIR = Path(__file__).parent.parent / "data"
registros = json.loads((DATA_DIR / "questoes_export.json").read_text(encoding="utf-8"))

juiz_principal: dict[str, dict] = {}
with (DATA_DIR / "julgamento_glm-4-plus.jsonl").open(encoding="utf-8") as f:
    for linha in f:
        if linha.strip():
            j = json.loads(linha)
            juiz_principal[j["id"]] = j

DIMS_SECUNDARIO = [
    "judge_d1_alinhamento_habilidade",
    "judge_d2_adequacao_objetos_conhecimento",
    "judge_d3_plausibilidade_distratores",
    "judge_d4_nivel_escolaridade",
    "judge_d5_aderencia_formato_enem",
]


def media(valores: list) -> float | None:
    return sum(valores) / len(valores) if valores and all(v is not None for v in valores) else None


colunas = [
    ("id", "ID", 24),
    ("origem", "Condicao", 20),
    ("area_codigo", "Area (codigo)", 10),
    ("area_nome", "Area (nome)", 22),
    ("competencia_numero", "Competencia", 10),
    ("habilidade_codigo", "Habilidade", 12),
    ("habilidade_descricao", "Habilidade (descricao)", 40),
    ("enunciado", "Enunciado", 60),
    ("alternativa_a", "Alternativa A", 30),
    ("alternativa_b", "Alternativa B", 30),
    ("alternativa_c", "Alternativa C", 30),
    ("alternativa_d", "Alternativa D", 30),
    ("alternativa_e", "Alternativa E", 30),
    ("gabarito", "Gabarito", 8),
    ("justificativa", "Justificativa (gerador)", 40),
    ("validacao_estrutural_ok", "Validacao estrutural OK", 12),
    ("cobertura_lexical", "Cobertura lexical C(i,h)", 14),
    ("especificidade_curricular", "Especificidade curricular E(i,h)", 16),
    ("ttr", "TTR", 10),
    ("fkgl", "FKGL", 10),
    ("p_media", "Juiz principal (glm-4-plus) - media", 14),
    ("p_d1", "Principal D1 - Alinhamento a habilidade", 12),
    ("p_d2", "Principal D2 - Adequacao dos OCs", 12),
    ("p_d3", "Principal D3 - Plausibilidade dos distratores", 12),
    ("p_d4", "Principal D4 - Nivel de escolaridade", 12),
    ("p_d5", "Principal D5 - Formato ENEM", 12),
    ("p_justificativa", "Principal - justificativa", 40),
    ("s_media", "Juiz secundario (glm-4.5) - media", 14),
    ("s_d1", "Secundario D1", 10),
    ("s_d2", "Secundario D2", 10),
    ("s_d3", "Secundario D3", 10),
    ("s_d4", "Secundario D4", 10),
    ("s_d5", "Secundario D5", 10),
    ("s_justificativa", "Secundario - justificativa", 40),
]
LETRA = {chave: get_column_letter(i + 1) for i, (chave, _, _) in enumerate(colunas)}

wb = Workbook()

# --- Planilha 1: Resumo ---
resumo = wb.active
resumo.title = "Resumo"
resumo["A1"] = "Graph-Driven Exam Gen - Corpus de itens gerados (1.788 itens, 120 habilidades, 3 condicoes)"
resumo["A1"].font = Font(bold=True, size=14)
resumo["A3"] = "Total de itens"
resumo["B3"] = f"=COUNTA(Questoes!{LETRA['id']}2:{LETRA['id']}100000)"
resumo["A4"] = "Itens validos estruturalmente"
resumo["B4"] = f"=COUNTIF(Questoes!{LETRA['validacao_estrutural_ok']}2:{LETRA['validacao_estrutural_ok']}100000,TRUE)"

cab = [
    "Condicao",
    "Qtd. itens",
    "C(i,h) media",
    "E(i,h) media",
    "TTR media",
    "FKGL media",
    "Juiz principal (glm-4-plus) media",
    "Juiz secundario (glm-4.5) media",
]
chaves = [None, None, "cobertura_lexical", "especificidade_curricular", "ttr", "fkgl", "p_media", "s_media"]
for j, texto in enumerate(cab):
    c = resumo.cell(row=6, column=j + 1, value=texto)
    c.font = Font(bold=True)
    c.alignment = Alignment(wrap_text=True)
    resumo.column_dimensions[get_column_letter(j + 1)].width = 24 if j == 0 else 18
cond_col = LETRA["origem"]
for i, cond in enumerate(["com_grafo", "com_fewshot_sem_grafo", "sem_grafo"]):
    row = 7 + i
    resumo.cell(row=row, column=1, value=cond)
    resumo.cell(row=row, column=2, value=f'=COUNTIF(Questoes!{cond_col}2:{cond_col}100000,"{cond}")')
    for j, chave in enumerate(chaves[2:], start=3):
        col = LETRA[chave]
        resumo.cell(
            row=row, column=j, value=f'=AVERAGEIF(Questoes!{cond_col}2:{cond_col}100000,"{cond}",Questoes!{col}2:{col}100000)'
        )

notas = [
    "Notas",
    "Juiz principal: glm-4-plus, distinto do gerador (julgamento em 02/10/2026). Juiz secundario: glm-4.5, o proprio "
    "gerador (execucao original). Notas de 1 a 5 em cada dimensao; a media e a media simples das cinco dimensoes.",
    "Similaridade semantica nao calculada: a chave de API utilizada nao tinha acesso a modelos de embedding.",
    "Respostas brutas, consumo de tokens e horario de cada julgamento do juiz principal: data/julgamento_glm-4-plus.jsonl.",
]
for k, texto in enumerate(notas):
    c = resumo.cell(row=11 + k, column=1, value=texto)
    c.font = Font(bold=(k == 0))
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if k:
        resumo.merge_cells(start_row=11 + k, start_column=1, end_row=11 + k, end_column=8)
        resumo.row_dimensions[11 + k].height = 32

# --- Planilha 2: Questoes ---
ws = wb.create_sheet("Questoes")
ws.append([rotulo for _, rotulo, _ in colunas])
for cell in ws[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", start_color="1F4E78")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws.freeze_panes = "A2"

sem_principal = 0
for r in registros:
    p = juiz_principal.get(r["id"])
    if p is None:
        sem_principal += 1
    dims_p = [p.get(f"d{k}") for k in range(1, 6)] if p else [None] * 5
    dims_s = [r.get(k) for k in DIMS_SECUNDARIO]
    extra = {
        "p_media": media(dims_p),
        **{f"p_d{k}": dims_p[k - 1] for k in range(1, 6)},
        "p_justificativa": p.get("justificativa") if p else None,
        "s_media": media(dims_s),
        **{f"s_d{k}": dims_s[k - 1] for k in range(1, 6)},
        "s_justificativa": r.get("judge_justificativa"),
    }
    ws.append([extra[chave] if chave in extra else r.get(chave) for chave, _, _ in colunas])

for chave, _, largura in colunas:
    ws.column_dimensions[LETRA[chave]].width = largura
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)

tabela = Table(displayName="TabelaQuestoes", ref=f"A1:{get_column_letter(len(colunas))}{len(registros) + 1}")
tabela.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False)
ws.add_table(tabela)

out_path = DATA_DIR / "questoes_geradas.xlsx"
wb.save(out_path)
print(f"Salvo em {out_path} ({len(registros)} linhas; sem julgamento principal: {sem_principal})")
