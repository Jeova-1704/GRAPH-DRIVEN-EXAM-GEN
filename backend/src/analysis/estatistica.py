"""Statistical analysis pipeline (Secao 3.11 do TCC / Objetivo F, Secao 4.6):
Shapiro-Wilk normality test -> Kruskal-Wallis -> post-hoc Mann-Whitney U with
Bonferroni correction, comparing the three experimental conditions.

Not a FastAPI module — this runs offline over the exported corpus (see
scripts/analisar_corpus.py), so it lives alongside interfaces/infrastructure/modules
rather than inside modules/.
"""

from dataclasses import dataclass
from itertools import combinations

from scipy import stats


@dataclass
class ResultadoShapiroWilk:
    estatistica: float
    p_valor: float
    normal: bool


@dataclass
class ResultadoKruskalWallis:
    estatistica: float
    p_valor: float
    significativo: bool


@dataclass
class ResultadoMannWhitney:
    grupo_a: str
    grupo_b: str
    estatistica: float
    p_valor: float
    significativo: bool


@dataclass
class AnaliseIndicador:
    """Full pipeline result for one automatic indicator (e.g. cobertura_lexical, D1, TTR...)."""

    nome_indicador: str
    normalidade_por_grupo: dict[str, ResultadoShapiroWilk]
    kruskal_wallis: ResultadoKruskalWallis
    post_hoc: list[ResultadoMannWhitney]


def testar_normalidade(dados: list[float], alpha: float = 0.05) -> ResultadoShapiroWilk:
    """Shapiro-Wilk (Secao 3.11.1 do TCC). Requires at least 3 observations."""
    if len(dados) < 3:
        raise ValueError("Shapiro-Wilk requer pelo menos 3 observacoes")
    estatistica, p_valor = stats.shapiro(dados)
    return ResultadoShapiroWilk(estatistica=float(estatistica), p_valor=float(p_valor), normal=bool(p_valor > alpha))


def kruskal_wallis(grupos: dict[str, list[float]], alpha: float = 0.05) -> ResultadoKruskalWallis:
    """Kruskal-Wallis comparing all conditions at once (Secao 3.11.2 do TCC)."""
    if len(grupos) < 2:
        raise ValueError("Kruskal-Wallis requer pelo menos 2 grupos")
    estatistica, p_valor = stats.kruskal(*grupos.values())
    return ResultadoKruskalWallis(estatistica=float(estatistica), p_valor=float(p_valor), significativo=bool(p_valor <= alpha))


def mann_whitney_post_hoc(grupos: dict[str, list[float]], alpha_bonferroni: float = 0.0167) -> list[ResultadoMannWhitney]:
    """Pairwise Mann-Whitney U with a pre-adjusted Bonferroni alpha (Secao 3.11.2 do TCC).

    alpha_bonferroni defaults to 0.0167 = 0.05/3, matching the TCC's three pairwise
    comparisons among com_grafo / com_fewshot_sem_grafo / sem_grafo.
    """
    resultados = []
    for (nome_a, dados_a), (nome_b, dados_b) in combinations(grupos.items(), 2):
        estatistica, p_valor = stats.mannwhitneyu(dados_a, dados_b, alternative="two-sided")
        resultados.append(
            ResultadoMannWhitney(
                grupo_a=nome_a,
                grupo_b=nome_b,
                estatistica=float(estatistica),
                p_valor=float(p_valor),
                significativo=bool(p_valor <= alpha_bonferroni),
            )
        )
    return resultados


def analisar_indicador(
    nome_indicador: str,
    grupos: dict[str, list[float]],
    alpha: float = 0.05,
    alpha_bonferroni: float = 0.0167,
) -> AnaliseIndicador:
    """Run the full three-step pipeline for one indicator across all conditions."""
    normalidade = {nome: testar_normalidade(dados, alpha) for nome, dados in grupos.items()}
    kw = kruskal_wallis(grupos, alpha)
    post_hoc = mann_whitney_post_hoc(grupos, alpha_bonferroni) if kw.significativo else []
    return AnaliseIndicador(
        nome_indicador=nome_indicador,
        normalidade_por_grupo=normalidade,
        kruskal_wallis=kw,
        post_hoc=post_hoc,
    )
