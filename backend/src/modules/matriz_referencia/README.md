# matriz_referencia

Loads and serves the ENEM Reference Matrix as a Neo4j property graph: `(:Area)-[:POSSUI]->(:Competencia)-[:REQUER]->(:Habilidade)-[:ABRANGE]->(:ObjetoConhecimento)`.

## Data source and modeling decision

`backend/data/matriz_referencia.json` is transcribed verbatim from `context/matriz_referencia.pdf` (the official INEP document): 4 areas, 30 competencias, 120 habilidades — matches the source exactly.

The TCC (Secao 3.3.1) reports "aproximadamente 720" Objetos de Conhecimento; this dataset models 41. The anexo of the official PDF lists Objetos de Conhecimento **per area** (not per habilidade) as prose blocks under bold headings — there is no ready per-habilidade mapping in the source. Two granularities were possible:

1. **Bullet-level** (adopted here): each bold heading in the anexo = one `ObjetoConhecimento` node, with the following prose as its `descricao`. Produces 8 (LC) + 5 (MT) + 23 (CN) + 5 (CH) = 41 nodes.
2. **Atomic-phrase-level**: split every heading's prose into individual sentences/topics as separate nodes. This is almost certainly how the thesis arrives at "~720" — but doing this well requires per-phrase judgment about which Habilidade(s) each atomic topic serves, which is a much larger curation effort.

Every `Competencia` was manually mapped to its relevant `ObjetoConhecimento` bullet(s) (see `objetos_conhecimento` arrays in the JSON), and every `Habilidade` inherits its Competencia's mapping — satisfying the "every Habilidade has >=1 ObjetoConhecimento" structural requirement (Secao 3.4.4 / Objetivo A). If finer granularity is later needed to match the thesis's exact OC count, split the bullet-level nodes into atomic-phrase nodes and re-run the per-Habilidade curation — the loader (`service.carregar_de_dados`) doesn't care about granularity, it just walks whatever `objetos_conhecimento` lists are in the JSON.

Also note: the TCC text (Secao 3.3.1) says "28 Competencias" — the actual official document has **30** (9 LC + 7 MT + 8 CN + 6 CH). Worth fixing in the TCC text.

## Running the loader

```bash
# 1. bring up Neo4j
cd ..  # implementação/
docker compose -f docker-compose.neo4j.yml up -d

# 2. set NEO4J_ENABLED=true (and NEO4J_PASSWORD if you changed it) in backend/.env

# 3. load the matrix (idempotent — safe to re-run)
cd backend
uv run python -m scripts.load_matriz_referencia
```

Or via the API once the app is running: `POST /api/v1/matriz/carregar` (superuser only).

Verify with `GET /api/v1/matriz/integridade` (superuser only) — checks node counts and that no Habilidade/Competencia is disconnected.
