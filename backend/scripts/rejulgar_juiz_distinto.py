"""Re-run Camada A (LLM-as-Judge) with a judge model distinct from the generator.

The original judgement used glm-4.5 both to generate and to judge the items, which the
TCC review flagged as a self-evaluation bias threat. This script re-judges the exported
corpus (data/questoes_export.json) with another model, using exactly the same judge prompt
(modules/avaliacao/judge_prompt.py) and the same curricular context (each Habilidade
inherits the Objetos de Conhecimento of its Competencia, data/matriz_referencia.json).

It reads from the JSON export instead of Neo4j, so it runs without the graph database, and
writes one JSON line per item to data/julgamento_<modelo>.jsonl (model, timestamp, token
usage and raw answer included, for audit). Safe to stop and re-run: items already present
in the output file are skipped.

Usage (from backend/):
    uv run python -m scripts.rejulgar_juiz_distinto --modelo glm-4-plus --workers 4
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from dotenv import dotenv_values  # noqa: E402
from zhipuai import ZhipuAI  # noqa: E402

from src.modules.avaliacao.judge_prompt import build_judge_prompt  # noqa: E402
from src.modules.common.utils.llm_json import parse_json_response  # noqa: E402
from src.modules.matriz_referencia.schemas import HabilidadeContexto, ObjetoConhecimentoRead  # noqa: E402
from src.modules.validacao.schemas import ItemGerado  # noqa: E402

DATA_DIR = backend_dir / "data"
TEMPERATURA = 0.0
MAX_TOKENS = 2048
TENTATIVAS = 3
TIMEOUT_S = 120


def carregar_habilidades() -> dict[str, HabilidadeContexto]:
    matriz = json.loads((DATA_DIR / "matriz_referencia.json").read_text(encoding="utf-8"))
    habilidades: dict[str, HabilidadeContexto] = {}
    for area in matriz["areas"]:
        ocs = {oc["codigo"]: ObjetoConhecimentoRead(**oc) for oc in area["objetos_conhecimento"]}
        for comp in area["competencias"]:
            for hab in comp["habilidades"]:
                habilidades[hab["codigo"]] = HabilidadeContexto(
                    habilidade_codigo=hab["codigo"],
                    habilidade_descricao=hab["descricao"],
                    competencia_numero=comp["numero"],
                    competencia_descricao=comp["descricao"],
                    area_codigo=area["codigo"],
                    area_nome=area["nome"],
                    objetos_conhecimento=[ocs[c] for c in comp["objetos_conhecimento"]],
                )
    return habilidades


def item_de(questao: dict) -> ItemGerado:
    return ItemGerado(
        enunciado=questao["enunciado"],
        alternativas={letra: questao[f"alternativa_{letra.lower()}"] for letra in "ABCDE"},
        gabarito=questao["gabarito"],
        justificativa=questao["justificativa"] or "",
    )


async def julgar(cliente: ZhipuAI, modelo: str, prompt: str) -> tuple[dict, str, dict]:
    def _call():
        return cliente.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURA,
            max_tokens=MAX_TOKENS,
        )

    ultimo_erro: Exception | None = None
    for tentativa in range(TENTATIVAS):
        try:
            resposta = await asyncio.wait_for(asyncio.to_thread(_call), timeout=TIMEOUT_S)
            bruta = str(resposta.choices[0].message.content)
            payload = parse_json_response(bruta)
            notas = {d: int(payload[d]) for d in ("d1", "d2", "d3", "d4", "d5")}
            if not all(1 <= v <= 5 for v in notas.values()):
                raise ValueError(f"nota fora da escala 1-5: {notas}")
            notas["justificativa"] = str(payload.get("justificativa", ""))
            uso = resposta.usage.model_dump() if resposta.usage else {}
            return notas, bruta, uso
        except Exception as exc:  # noqa: BLE001 — retried, then reported by the caller
            ultimo_erro = exc
            await asyncio.sleep(2.0 * (tentativa + 1))
    assert ultimo_erro is not None
    raise ultimo_erro


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="glm-4-plus")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limite", type=int, default=0, help="julgar no maximo N itens (0 = todos)")
    args = parser.parse_args()

    cliente = ZhipuAI(api_key=dotenv_values(backend_dir / ".env")["GLM_API_KEY"])
    habilidades = carregar_habilidades()
    questoes = json.loads((DATA_DIR / "questoes_export.json").read_text(encoding="utf-8"))

    saida = DATA_DIR / f"julgamento_{args.modelo}.jsonl"
    feitos: set[str] = set()
    if saida.exists():
        feitos = {json.loads(linha)["id"] for linha in saida.read_text(encoding="utf-8").splitlines() if linha}
    pendentes = [q for q in questoes if q["id"] not in feitos]
    if args.limite:
        pendentes = pendentes[: args.limite]
    print(f"{len(feitos)} ja julgados, {len(pendentes)} pendentes, modelo={args.modelo}", flush=True)

    fila: asyncio.Queue[dict] = asyncio.Queue()
    for q in pendentes:
        fila.put_nowait(q)
    lock = asyncio.Lock()
    contagem = {"ok": 0, "falha": 0}

    async def worker() -> None:
        while not fila.empty():
            q = fila.get_nowait()
            prompt = build_judge_prompt(item_de(q), habilidades[q["habilidade_codigo"]])
            try:
                notas, bruta, uso = await julgar(cliente, args.modelo, prompt)
            except Exception as exc:  # noqa: BLE001
                contagem["falha"] += 1
                print(f"FALHA {q['id']}: {exc}", flush=True)
                continue
            registro = {
                "id": q["id"],
                "origem": q["origem"],
                "habilidade_codigo": q["habilidade_codigo"],
                "modelo_juiz": args.modelo,
                "temperatura": TEMPERATURA,
                "max_tokens": MAX_TOKENS,
                "julgado_em": datetime.now(UTC).isoformat(),
                **notas,
                "uso_tokens": uso,
                "resposta_bruta": bruta,
            }
            async with lock:
                with saida.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                contagem["ok"] += 1
                if contagem["ok"] % 50 == 0:
                    print(f"{contagem['ok']} julgados ({contagem['falha']} falhas)", flush=True)

    await asyncio.gather(*(worker() for _ in range(args.workers)))
    print(f"Concluido: {contagem['ok']} julgados, {contagem['falha']} falhas -> {saida.name}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
