"""Audit data/matriz_referencia.json against the official INEP PDF (context/matriz_referencia.pdf).

For every Competencia and Habilidade description in the JSON, checks whether the normalized
text (lowercase, no accents, no punctuation, collapsed whitespace) occurs verbatim in the
normalized text of the PDF. Items not found verbatim get the best fuzzy match (difflib ratio
over a sliding window) so a human can inspect the divergence. Writes the report to
data/conferencia_extracao_matriz.json.

Usage (from backend/):
    python scripts/conferir_extracao_matriz.py   (needs pypdf; not a project dependency)
"""

import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

backend_dir = Path(__file__).parent.parent
DATA_DIR = backend_dir / "data"
PDF = backend_dir.parents[1] / "context" / "matriz_referencia.pdf"


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"-\s+", "", texto)  # hyphenation at line breaks
    texto = re.sub(r"[^a-z0-9 ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def melhor_trecho(alvo: str, corpus: str) -> tuple[float, str]:
    n = len(alvo)
    melhor = (0.0, "")
    passo = max(1, n // 8)
    for i in range(0, max(1, len(corpus) - n), passo):
        trecho = corpus[i : i + n]
        r = difflib.SequenceMatcher(None, alvo, trecho, autojunk=False).quick_ratio()
        if r > melhor[0]:
            melhor = (r, trecho)
    # refine the best window with the exact ratio
    return difflib.SequenceMatcher(None, alvo, melhor[1], autojunk=False).ratio(), melhor[1]


def main() -> None:
    pdf_texto = normalizar(" ".join(p.extract_text() or "" for p in PdfReader(str(PDF)).pages))
    pdf_sem_espacos = pdf_texto.replace(" ", "")
    matriz = json.loads((DATA_DIR / "matriz_referencia.json").read_text(encoding="utf-8"))

    registros = []
    for area in matriz["areas"]:
        for comp in area["competencias"]:
            alvos = [("competencia", f"{area['codigo']}-C{comp['numero']}", comp["descricao"])]
            alvos += [("habilidade", h["codigo"], h["descricao"]) for h in comp["habilidades"]]
            for tipo, codigo, descricao in alvos:
                alvo = normalizar(descricao)
                # PDF text extraction inserts spurious spaces inside words ("t ransformacao"),
                # so the verbatim check ignores whitespace altogether.
                exato = alvo.replace(" ", "") in pdf_sem_espacos
                registro = {"tipo": tipo, "codigo": codigo, "exato": exato}
                if not exato:
                    ratio, trecho = melhor_trecho(alvo, pdf_texto)
                    registro.update({"similaridade": round(ratio, 4), "json": alvo, "pdf": trecho})
                registros.append(registro)

    resumo = {}
    for tipo in ("competencia", "habilidade"):
        sub = [r for r in registros if r["tipo"] == tipo]
        resumo[tipo] = {"total": len(sub), "verbatim": sum(r["exato"] for r in sub)}
    relatorio = {"pdf": PDF.name, "resumo": resumo, "divergencias": [r for r in registros if not r["exato"]]}
    (DATA_DIR / "conferencia_extracao_matriz.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resumo, indent=2))
    for r in relatorio["divergencias"]:
        print(f"\n[{r['codigo']}] sim={r['similaridade']}\n  JSON: {r['json']}\n  PDF : {r['pdf']}")


if __name__ == "__main__":
    sys.exit(main())
