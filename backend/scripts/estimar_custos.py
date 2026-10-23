"""Estimate the LLM API cost of the experiment (Secao 3.6.3 do TCC).

- Principal judge (glm-4-plus): exact token counts recorded per item in
  data/julgamento_glm-4-plus.jsonl.
- Generation and secondary judge (glm-4.5): token usage was not recorded, so it is estimated
  from the rebuilt prompts and the stored outputs (data/questoes_geradas.xlsx), converting
  characters to tokens with the median chars/token ratio observed in the principal judge's
  exact records. Reasoning ("thinking") tokens of glm-4.5 are billed as output but were not
  recorded and are NOT included; a scenario is reported separately.

Prices: official public list prices (CNY per million tokens) from docs.bigmodel.cn,
consulted on 2026-10-22: glm-4.5 from 0.8 (input) / 2 (output), lowest tier; glm-4-plus 5.

Usage (from backend/, needs openpyxl like build_xlsx.py): python scripts/estimar_custos.py
"""

import json
import statistics as st
from pathlib import Path

import openpyxl

DATA = Path(__file__).parent.parent / "data"
PRECO = {"glm-4.5": {"entrada": 0.8, "saida": 2.0}, "glm-4-plus": {"entrada": 5.0, "saida": 5.0}}
RACIOCINIO_POR_CHAMADA = 2500  # hypothetical scenario only


def main() -> None:
    wb = openpyxl.load_workbook(DATA / "questoes_geradas.xlsx", read_only=True)
    rows = wb["Questoes"].iter_rows(values_only=True)
    hdr = list(next(rows))
    ix = {h: i for i, h in enumerate(hdr)}

    r_in, r_out = [], []
    ger_in = ger_out = jz_in = jz_out = 0
    for r in rows:
        jp = r[ix["Prompt do juiz completo"]] or ""
        gp = r[ix["Prompt de geracao completo"]] or ""
        tin, tout = r[ix["Principal - tokens de entrada"]], r[ix["Principal - tokens de saida"]]
        bruta = r[ix["Principal - resposta bruta"]] or ""
        if tin and jp:
            r_in.append(len(jp) / tin)
        if tout and bruta:
            r_out.append(len(bruta) / tout)
        item = {
            "enunciado": r[ix["Enunciado"]],
            "alternativas": {k: r[ix[f"Alternativa {k}"]] for k in "ABCDE"},
            "gabarito": r[ix["Gabarito"]],
            "justificativa": r[ix["Justificativa (gerador)"]],
        }
        ger_in += len(gp)
        ger_out += len(json.dumps(item, ensure_ascii=False))
        jz_in += len(jp)
        jz_out += len(r[ix["Secundario - justificativa"]] or "") + 60

    cin, cout = st.median(r_in), st.median(r_out)
    principal = json.loads((DATA / "resultado_juiz_distinto_glm-4-plus.json").read_text(encoding="utf-8"))
    tok = principal["uso_tokens_total"]

    def custo(modelo, ent, sai):
        return ent / 1e6 * PRECO[modelo]["entrada"] + sai / 1e6 * PRECO[modelo]["saida"]

    etapas = {
        "geracao_glm-4.5": {
            "exato": False,
            "entrada": round(ger_in / cin),
            "saida_visivel": round(ger_out / cout),
            "chamadas": 1788,
        },
        "juiz_secundario_glm-4.5": {
            "exato": False,
            "entrada": round(jz_in / cin),
            "saida_visivel": round(jz_out / cout),
            "chamadas": 1787,
        },
        "juiz_principal_glm-4-plus": {
            "exato": True,
            "entrada": tok["prompt_tokens"],
            "saida_visivel": tok["completion_tokens"],
            "chamadas": 1788,
        },
    }
    for nome, e in etapas.items():
        modelo = "glm-4-plus" if "plus" in nome else "glm-4.5"
        e["custo_cny"] = round(custo(modelo, e["entrada"], e["saida_visivel"]), 2)
        if modelo == "glm-4.5":
            extra = e["chamadas"] * RACIOCINIO_POR_CHAMADA
            e["cenario_raciocinio_tokens"] = extra
            e["cenario_raciocinio_custo_cny"] = round(custo(modelo, e["entrada"], e["saida_visivel"] + extra), 2)

    total_min = sum(e["custo_cny"] for e in etapas.values())
    total_cen = sum(e.get("cenario_raciocinio_custo_cny", e["custo_cny"]) for e in etapas.values())
    out = {
        "precos_cny_por_milhao": PRECO,
        "chars_por_token": {"entrada": round(cin, 3), "saida": round(cout, 3)},
        "etapas": etapas,
        "total_tokens_minimo": sum(e["entrada"] + e["saida_visivel"] for e in etapas.values()),
        "total_custo_cny_minimo": round(total_min, 2),
        "total_custo_cny_cenario_raciocinio": round(total_cen, 2),
    }
    (DATA / "resultado_custos.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
