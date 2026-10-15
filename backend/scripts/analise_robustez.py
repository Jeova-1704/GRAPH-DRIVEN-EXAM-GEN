"""Robustness analyses complementing scripts/analisar_corpus.py (offline, from the exported JSON):

1. Nonparametric effect sizes (Cliff's delta / rank-biserial) with skill-clustered bootstrap CI.
2. Holm correction across the family of Kruskal-Wallis tests (all indicators).
3. Skill-level paired analysis (Friedman + Wilcoxon signed-rank), addressing the
   intra-habilidade dependence of the item-level tests.
4. Sensitivity of E(i,h) to its definition (zeros excluded, as implemented, vs. plain mean
   over the other habilidades, as in the predecessor paper).

Usage (from backend/): uv run python -m scripts.analise_robustez
"""
# ruff: noqa: E501

import json
import statistics
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.modules.avaliacao import nlp  # noqa: E402

DATA = backend_dir / "data"
CONDICOES = ["com_grafo", "com_fewshot_sem_grafo", "sem_grafo"]
PARES = list(combinations(CONDICOES, 2))
N_BOOT = 1000
RNG = np.random.default_rng(42)

registros = json.loads((DATA / "questoes_export.json").read_text(encoding="utf-8"))
matriz = json.loads((DATA / "matriz_referencia.json").read_text(encoding="utf-8"))


def score_medio(r):
    dims = [
        r["judge_d1_alinhamento_habilidade"],
        r["judge_d2_adequacao_objetos_conhecimento"],
        r["judge_d3_plausibilidade_distratores"],
        r["judge_d4_nivel_escolaridade"],
        r["judge_d5_aderencia_formato_enem"],
    ]
    return None if any(d is None for d in dims) else sum(dims) / 5


# --- Sensitivity: recompute C and E for every item against all 120 habilidades ---
tokens_oc: dict[str, list[str]] = {}
for area in matriz["areas"]:
    ocs = {oc["codigo"]: f"{oc['titulo']} {oc['descricao']}" for oc in area["objetos_conhecimento"]}
    for comp in area["competencias"]:
        texto = " ".join(ocs[c] for c in comp["objetos_conhecimento"])
        for hab in comp["habilidades"]:
            tokens_oc[hab["codigo"]] = nlp.tokenizar(texto)

max_diff_c = 0.0
max_diff_e = 0.0
for r in registros:
    tokens_item = nlp.tokenizar(r["enunciado"] + " " + " ".join(r[f"alternativa_{x}"] for x in "abcde"))
    h = r["habilidade_codigo"]
    c_alvo = nlp.cobertura_lexical(tokens_item, tokens_oc[h])
    c_outras = [nlp.cobertura_lexical(tokens_item, t) for k, t in tokens_oc.items() if k != h]
    e_impl = nlp.especificidade_curricular(c_alvo, c_outras)
    media_todas = sum(c_outras) / len(c_outras)
    r["_e_simples"] = None if media_todas == 0 else c_alvo / media_todas
    max_diff_c = max(max_diff_c, abs(c_alvo - r["cobertura_lexical"]))
    max_diff_e = max(max_diff_e, abs(e_impl - r["especificidade_curricular"]))

INDICADORES = {
    "cobertura_lexical": lambda r: r["cobertura_lexical"],
    "especificidade_curricular": lambda r: r["especificidade_curricular"],
    "ttr": lambda r: r["ttr"],
    "fkgl": lambda r: r["fkgl"],
    "d1_alinhamento_habilidade": lambda r: r["judge_d1_alinhamento_habilidade"],
    "d2_adequacao_objetos_conhecimento": lambda r: r["judge_d2_adequacao_objetos_conhecimento"],
    "d3_plausibilidade_distratores": lambda r: r["judge_d3_plausibilidade_distratores"],
    "d4_nivel_escolaridade": lambda r: r["judge_d4_nivel_escolaridade"],
    "d5_aderencia_formato_enem": lambda r: r["judge_d5_aderencia_formato_enem"],
    "score_medio_judge": score_medio,
    "especificidade_sensibilidade_media_simples": lambda r: r["_e_simples"],
}


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    ranks = stats.rankdata(np.concatenate([a, b]))
    u1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    return float(2 * u1 / (n1 * n2) - 1)


resultado: dict = {"verificacao_recalculo": {"max_dif_C": max_diff_c, "max_dif_E": max_diff_e}, "indicadores": {}}
kw_p: dict[str, float] = {}

for nome, extrator in INDICADORES.items():
    por_cond_hab: dict[str, dict[str, list[float]]] = {c: defaultdict(list) for c in CONDICOES}
    for r in registros:
        v = extrator(r)
        if v is not None:
            por_cond_hab[r["origem"]][r["habilidade_codigo"]].append(float(v))
    grupos = {c: np.array([v for vs in por_cond_hab[c].values() for v in vs]) for c in CONDICOES}

    h_stat, p_kw = stats.kruskal(*grupos.values())
    n_tot = sum(len(g) for g in grupos.values())
    eps2 = float((h_stat - len(CONDICOES) + 1) / (n_tot - len(CONDICOES)))
    kw_p[nome] = float(p_kw)

    efeitos = {}
    habilidades = sorted(set.intersection(*[set(por_cond_hab[c]) for c in CONDICOES]))
    for a, b in PARES:
        d = cliffs_delta(grupos[a], grupos[b])
        boots = []
        for _ in range(N_BOOT):
            amostra = RNG.choice(len(habilidades), size=len(habilidades), replace=True)
            va = np.concatenate([por_cond_hab[a][habilidades[i]] for i in amostra])
            vb = np.concatenate([por_cond_hab[b][habilidades[i]] for i in amostra])
            boots.append(cliffs_delta(va, vb))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        efeitos[f"{a}__vs__{b}"] = {"cliffs_delta": d, "ic95_cluster_bootstrap": [float(lo), float(hi)]}

    # skill-level paired analysis
    medias = {c: np.array([statistics.mean(por_cond_hab[c][h]) for h in habilidades]) for c in CONDICOES}
    friedman = stats.friedmanchisquare(*medias.values())
    pareado = {}
    for a, b in PARES:
        w = stats.wilcoxon(medias[a], medias[b])
        pareado[f"{a}__vs__{b}"] = {
            "p_wilcoxon": float(w.pvalue),
            "significativo_bonferroni_0_0167": bool(w.pvalue <= 0.0167),
            "mediana_diferenca": float(np.median(medias[a] - medias[b])),
            "habilidades_a_maior": int((medias[a] > medias[b]).sum()),
            "habilidades_b_maior": int((medias[a] < medias[b]).sum()),
            "n_habilidades": len(habilidades),
        }

    resultado["indicadores"][nome] = {
        "n_por_condicao": {c: int(len(g)) for c, g in grupos.items()},
        "kruskal_wallis": {"H": float(h_stat), "p": float(p_kw), "epsilon2": eps2},
        "efeitos_pareados": efeitos,
        "nivel_habilidade": {"friedman_p": float(friedman.pvalue), "pareado": pareado},
    }

# Holm across the family of KW tests (excluding the sensitivity variant)
familia = [n for n in kw_p if not n.startswith("especificidade_sensibilidade")]
ordenados = sorted(familia, key=lambda n: kw_p[n])
m = len(ordenados)
rodando_max = 0.0
for i, n in enumerate(ordenados):
    p_ajust = min(1.0, (m - i) * kw_p[n])
    rodando_max = max(rodando_max, p_ajust)
    resultado["indicadores"][n]["kruskal_wallis"]["p_holm"] = rodando_max
    resultado["indicadores"][n]["kruskal_wallis"]["significativo_holm_0_05"] = bool(rodando_max <= 0.05)

out = DATA / "resultado_robustez.json"
out.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Verificacao recalculo: max|dC|={max_diff_c:.2e} max|dE|={max_diff_e:.2e}")
for n, r in resultado["indicadores"].items():
    kw = r["kruskal_wallis"]
    print(f"\n{n}: H={kw['H']:.2f} p={kw['p']:.2e} eps2={kw['epsilon2']:.4f} p_holm={kw.get('p_holm', float('nan')):.2e}")
    for par, e in r["efeitos_pareados"].items():
        print(
            f"   delta {par}: {e['cliffs_delta']:+.3f} IC95 [{e['ic95_cluster_bootstrap'][0]:+.3f}, {e['ic95_cluster_bootstrap'][1]:+.3f}]"
        )
    nh = r["nivel_habilidade"]
    print(f"   nivel-habilidade: Friedman p={nh['friedman_p']:.2e}")
    for par, e in nh["pareado"].items():
        print(
            f"      {par}: p_wilcoxon={e['p_wilcoxon']:.2e} sig={e['significativo_bonferroni_0_0167']} mediana_dif={e['mediana_diferenca']:+.4f} a>b em {e['habilidades_a_maior']}/{e['n_habilidades']}"
        )
print("\nSalvo em", out)
