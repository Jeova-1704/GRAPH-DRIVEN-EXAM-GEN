"""Statistical analysis of Camada A with the judge distinct from the generator.

Reads data/julgamento_<modelo>.jsonl (written by scripts/rejulgar_juiz_distinto.py) and the
original export (glm-4.5 self-judgement), and reports, per dimension D1-D5 and mean score:

1. Descriptives per condition (mean, median, share of maximum score).
2. Kruskal-Wallis across conditions, Mann-Whitney U post-hoc (Bonferroni, alpha=0.0167),
   Holm across the six judge tests, Cliff's delta with skill-clustered bootstrap CI.
3. Skill-level paired analysis (Friedman + Wilcoxon) over the 120 habilidades.
4. Agreement between the distinct judge and the original self-judge: exact agreement,
   quadratic weighted kappa and mean difference (self-judge minus distinct judge).
5. Token usage of the distinct judge.

Usage (from backend/): uv run python -m scripts.analisar_juiz_distinto --modelo glm-4-plus
"""
# ruff: noqa: E501

import argparse
import json
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

DATA = Path(__file__).parent.parent / "data"
CONDICOES = ["com_grafo", "com_fewshot_sem_grafo", "sem_grafo"]
PARES = list(combinations(CONDICOES, 2))
DIMS = ["d1", "d2", "d3", "d4", "d5"]
CAMPOS_ORIGINAIS = {
    "d1": "judge_d1_alinhamento_habilidade",
    "d2": "judge_d2_adequacao_objetos_conhecimento",
    "d3": "judge_d3_plausibilidade_distratores",
    "d4": "judge_d4_nivel_escolaridade",
    "d5": "judge_d5_aderencia_formato_enem",
}
N_BOOT = 1000
RNG = np.random.default_rng(42)


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    ranks = stats.rankdata(np.concatenate([a, b]))
    u1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    return float(2 * u1 / (n1 * n2) - 1)


def kappa_quadratico(x: list[int], y: list[int], k: int = 5) -> float:
    obs = np.zeros((k, k))
    for a, b in zip(x, y, strict=True):
        obs[a - 1, b - 1] += 1
    obs /= obs.sum()
    esp = np.outer(obs.sum(axis=1), obs.sum(axis=0))
    i, j = np.indices((k, k))
    pesos = (i - j) ** 2 / (k - 1) ** 2
    return float(1 - (pesos * obs).sum() / (pesos * esp).sum())


def analisar(nome: str, por_cond_hab: dict[str, dict[str, list[float]]]) -> dict:
    grupos = {c: np.array([v for vs in por_cond_hab[c].values() for v in vs]) for c in CONDICOES}
    desc = {
        c: {
            "n": int(len(g)),
            "media": float(g.mean()),
            "mediana": float(np.median(g)),
            "dp": float(g.std(ddof=1)),
            "prop_nota_maxima": float((g == 5).mean()),
        }
        for c, g in grupos.items()
    }
    if len(np.unique(np.concatenate(list(grupos.values())))) == 1:
        # every item got the same score: no test is defined (H is 0/0)
        return {"descritivas": desc, "sem_variancia": True, "kruskal_wallis": {"H": None, "p": 1.0, "epsilon2": None}}
    h_stat, p_kw = stats.kruskal(*grupos.values())
    n_tot = sum(len(g) for g in grupos.values())
    eps2 = float((h_stat - len(CONDICOES) + 1) / (n_tot - len(CONDICOES)))

    post_hoc, efeitos = {}, {}
    habilidades = sorted(set.intersection(*[set(por_cond_hab[c]) for c in CONDICOES]))
    for a, b in PARES:
        mw = stats.mannwhitneyu(grupos[a], grupos[b], alternative="two-sided")
        post_hoc[f"{a}__vs__{b}"] = {
            "U": float(mw.statistic),
            "p": float(mw.pvalue),
            "sig_bonferroni": bool(mw.pvalue <= 0.0167),
        }
        boots = []
        for _ in range(N_BOOT):
            amostra = RNG.choice(len(habilidades), size=len(habilidades), replace=True)
            va = np.concatenate([por_cond_hab[a][habilidades[i]] for i in amostra])
            vb = np.concatenate([por_cond_hab[b][habilidades[i]] for i in amostra])
            boots.append(cliffs_delta(va, vb))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        efeitos[f"{a}__vs__{b}"] = {"delta": cliffs_delta(grupos[a], grupos[b]), "ic95": [float(lo), float(hi)]}

    medias = {c: np.array([statistics.mean(por_cond_hab[c][h]) for h in habilidades]) for c in CONDICOES}
    try:
        friedman_p = float(stats.friedmanchisquare(*medias.values()).pvalue)
    except ValueError:
        friedman_p = float("nan")
    pareado = {}
    for a, b in PARES:
        dif = medias[a] - medias[b]
        p = float(stats.wilcoxon(medias[a], medias[b]).pvalue) if np.any(dif != 0) else 1.0
        pareado[f"{a}__vs__{b}"] = {
            "p_wilcoxon": p,
            "sig_bonferroni": bool(p <= 0.0167),
            "a_maior": int((dif > 0).sum()),
            "b_maior": int((dif < 0).sum()),
        }

    return {
        "descritivas": desc,
        "kruskal_wallis": {"H": float(h_stat), "p": float(p_kw), "epsilon2": eps2},
        "post_hoc_mann_whitney": post_hoc,
        "efeitos": efeitos,
        "nivel_habilidade": {"friedman_p": friedman_p, "pareado": pareado},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="glm-4-plus")
    args = parser.parse_args()

    novos = {}
    for linha in (DATA / f"julgamento_{args.modelo}.jsonl").read_text(encoding="utf-8").splitlines():
        if linha.strip():
            r = json.loads(linha)
            novos[r["id"]] = r
    originais = {r["id"]: r for r in json.loads((DATA / "questoes_export.json").read_text(encoding="utf-8"))}

    resultado: dict = {"modelo_juiz": args.modelo, "n_julgados": len(novos), "n_corpus": len(originais), "indicadores": {}}
    resultado["julgado_entre"] = [min(r["julgado_em"] for r in novos.values()), max(r["julgado_em"] for r in novos.values())]
    uso = defaultdict(int)
    for r in novos.values():
        for k, v in (r.get("uso_tokens") or {}).items():
            if isinstance(v, int):
                uso[k] += v
    resultado["uso_tokens_total"] = dict(uso)
    resultado["n_por_condicao"] = {c: sum(1 for r in novos.values() if r["origem"] == c) for c in CONDICOES}

    for nome in [*DIMS, "score_medio"]:
        por_cond_hab: dict[str, dict[str, list[float]]] = {c: defaultdict(list) for c in CONDICOES}
        for r in novos.values():
            v = statistics.mean(r[d] for d in DIMS) if nome == "score_medio" else r[nome]
            por_cond_hab[r["origem"]][r["habilidade_codigo"]].append(float(v))
        resultado["indicadores"][nome] = analisar(nome, por_cond_hab)

    ordenados = sorted(resultado["indicadores"], key=lambda n: resultado["indicadores"][n]["kruskal_wallis"]["p"])
    rodando = 0.0
    for i, n in enumerate(ordenados):
        rodando = max(rodando, min(1.0, (len(ordenados) - i) * resultado["indicadores"][n]["kruskal_wallis"]["p"]))
        resultado["indicadores"][n]["kruskal_wallis"]["p_holm"] = rodando

    concordancia = {}
    comuns = [i for i in novos if i in originais and originais[i][CAMPOS_ORIGINAIS["d1"]] is not None]
    for d in DIMS:
        x = [int(originais[i][CAMPOS_ORIGINAIS[d]]) for i in comuns]
        y = [int(novos[i][d]) for i in comuns]
        concordancia[d] = {
            "n": len(comuns),
            "concordancia_exata": float(np.mean(np.array(x) == np.array(y))),
            "kappa_ponderado_quadratico": kappa_quadratico(x, y),
            "media_auto_juiz": float(np.mean(x)),
            "media_juiz_distinto": float(np.mean(y)),
            "diferenca_media_auto_menos_distinto": float(np.mean(np.array(x) - np.array(y))),
            "prop_auto_maior": float(np.mean(np.array(x) > np.array(y))),
            "prop_auto_menor": float(np.mean(np.array(x) < np.array(y))),
            "wilcoxon_p": float(stats.wilcoxon(x, y).pvalue) if any(a != b for a, b in zip(x, y, strict=True)) else 1.0,
        }
    resultado["concordancia_com_auto_juiz_glm45"] = concordancia

    out = DATA / f"resultado_juiz_distinto_{args.modelo}.json"
    out.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Juiz {args.modelo}: {len(novos)}/{len(originais)} itens; por condicao {resultado['n_por_condicao']}")
    print(f"Periodo: {resultado['julgado_entre']}; tokens: {dict(uso)}")
    for n, r in resultado["indicadores"].items():
        kw = r["kruskal_wallis"]
        desc = "  ".join(
            f"{c[:8]}: m={v['media']:.3f} md={v['mediana']:.1f} max={v['prop_nota_maxima']:.3f}"
            for c, v in r["descritivas"].items()
        )
        if r.get("sem_variancia"):
            print(f"\n{n}: SEM VARIANCIA (todas as notas iguais)\n   {desc}")
            continue
        print(f"\n{n}: H={kw['H']:.2f} p={kw['p']:.2e} eps2={kw['epsilon2']:.4f} p_holm={kw['p_holm']:.2e}\n   {desc}")
        for par in r["efeitos"]:
            e, ph, nh = r["efeitos"][par], r["post_hoc_mann_whitney"][par], r["nivel_habilidade"]["pareado"][par]
            print(
                f"   {par}: MW p={ph['p']:.2e} delta={e['delta']:+.3f} [{e['ic95'][0]:+.3f};{e['ic95'][1]:+.3f}] | hab: {nh['a_maior']} vs {nh['b_maior']} p={nh['p_wilcoxon']:.2e}"
            )
        print(f"   Friedman p={r['nivel_habilidade']['friedman_p']:.2e}")
    print("\nConcordancia com o auto-juiz glm-4.5:")
    for d, c in concordancia.items():
        print(
            f"  {d}: n={c['n']} exata={c['concordancia_exata']:.3f} kappa_w={c['kappa_ponderado_quadratico']:.3f} media auto={c['media_auto_juiz']:.3f} distinto={c['media_juiz_distinto']:.3f} auto>dist={c['prop_auto_maior']:.3f} auto<dist={c['prop_auto_menor']:.3f} p={c['wilcoxon_p']:.2e}"
        )
    print("\nSalvo em", out)


if __name__ == "__main__":
    main()
