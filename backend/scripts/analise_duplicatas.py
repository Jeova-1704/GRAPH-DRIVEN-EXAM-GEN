"""Robustness to duplicated items (TCC, Apendice D.4): within each cell (habilidade x condicao),
40 items repeat verbatim the stem of another item of the same cell, despite temperature 0.
Re-runs the C(i,h) and E(i,h) comparisons with and without them (Kruskal-Wallis, Mann-Whitney U
with Bonferroni, Cliff's delta with a 95% CI from a cluster bootstrap over habilidades).

Usage (from backend/):
    uv run python -m scripts.analise_duplicatas
Writes data/resultado_robustez_duplicatas.json.
"""

import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

DATA_DIR = Path(__file__).parent.parent / "data"
CONDICOES = ["com_grafo", "com_fewshot_sem_grafo", "sem_grafo"]
PARES = [("com_grafo", "com_fewshot_sem_grafo"), ("com_grafo", "sem_grafo"), ("com_fewshot_sem_grafo", "sem_grafo")]
INDICADORES = ["cobertura_lexical", "especificidade_curricular"]
N_BOOT = 2000
SEMENTE = 42


def sem_duplicatas(itens: list[dict]) -> list[dict]:
    """Keep the first occurrence of each verbatim stem within a cell (habilidade x condicao)."""
    vistos: set[tuple[str, str, str]] = set()
    unicos = []
    for q in itens:
        chave = (q["habilidade_codigo"], q["origem"], q["enunciado"].strip())
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(q)
    return unicos


def cliffs_delta(a: list[float], b: list[float]) -> float:
    xa, xb = np.asarray(a), np.asarray(b)
    maior = (xa[:, None] > xb[None, :]).sum()
    menor = (xa[:, None] < xb[None, :]).sum()
    return float((maior - menor) / (len(xa) * len(xb)))


def analisar(itens: list[dict]) -> dict:
    por_hab: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for q in itens:
        por_hab[q["habilidade_codigo"]][q["origem"]].append(q)
    habilidades = sorted(por_hab)
    resultado: dict = {"n": len(itens), "n_por_condicao": {c: sum(q["origem"] == c for q in itens) for c in CONDICOES}}
    for ind in INDICADORES:
        grupos = {c: [q[ind] for q in itens if q["origem"] == c] for c in CONDICOES}
        h, p = stats.kruskal(*grupos.values())
        pares = {}
        for a, b in PARES:
            _, p_mw = stats.mannwhitneyu(grupos[a], grupos[b], alternative="two-sided")
            rng = random.Random(SEMENTE)
            boots = []
            for _ in range(N_BOOT):
                amostra = [rng.choice(habilidades) for _ in habilidades]
                xa = [q[ind] for hab in amostra for q in por_hab[hab][a]]
                xb = [q[ind] for hab in amostra for q in por_hab[hab][b]]
                boots.append(cliffs_delta(xa, xb))
            lo, hi = np.percentile(boots, [2.5, 97.5])
            pares[f"{a}__vs__{b}"] = {
                "p_mann_whitney": float(p_mw),
                "p_bonferroni": float(min(p_mw * 3, 1.0)),
                "cliffs_delta": cliffs_delta(grupos[a], grupos[b]),
                "ic95_cluster_bootstrap": [float(lo), float(hi)],
            }
        resultado[ind] = {"kruskal_wallis": {"H": float(h), "p": float(p)}, "pares": pares}
    return resultado


def main() -> None:
    registros = json.loads((DATA_DIR / "questoes_export.json").read_text(encoding="utf-8"))
    unicos = sem_duplicatas(registros)
    saida = {
        "descricao": "C(i,h) e E(i,h) com e sem itens de enunciado repetido na mesma celula (habilidade x condicao)",
        "itens_removidos": len(registros) - len(unicos),
        "n_boot": N_BOOT,
        "semente": SEMENTE,
        "corpus_completo": analisar(registros),
        "sem_duplicatas": analisar(unicos),
    }
    caminho = DATA_DIR / "resultado_robustez_duplicatas.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Salvo em {caminho} (removidos: {saida['itens_removidos']})")


if __name__ == "__main__":
    main()
