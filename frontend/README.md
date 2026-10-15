# Frontend — Graph-Driven Exam Gen

Next.js 16 (App Router) + React 19 + TypeScript, implementando as seis telas da Seção 3.5.1 do TCC: Dashboard, Geração, Avaliação, Grafo, Export Obsidian, Configuração.

Pinned originally to the versions the TCC methodology names (Next.js 14, React 18) — bumped to Next 16 / React 19 during setup because `npm audit` flagged critical vulnerabilities in the 14.x line. Next 16 ships an `AGENTS.md`/`CLAUDE.md` pair warning that its APIs may differ from an LLM's training data; this app only uses stable App Router basics (`page.tsx`, `layout.tsx`, `"use client"`, hooks) which built and ran cleanly.

## Rodando

```bash
cd implementação/frontend
npm install
cp .env.local.example .env.local   # aponta para o backend (default: http://localhost:8000/api/v1)
npm run dev                         # http://localhost:3000
```

Requer o backend rodando (`cd ../backend && uv run fastapi dev src/interfaces/main.py`), com Neo4j habilitado e a Matriz carregada (`uv run python -m scripts.load_matriz_referencia`) para as páginas mostrarem dados reais. Sem isso, as páginas carregam mas mostram mensagens de erro de conexão — comportamento esperado, não um bug.

## Build de produção

```bash
npm run build && npm start
```

Validado nesta sessão: `npm run build` compila e type-checa sem erros (todas as 6 rotas geradas como estáticas — o fetch de dados acontece no cliente via `src/lib/api.ts`, então a build não depende do backend estar no ar). `npm run dev` também testado (as 6 rotas respondem 200).

## Estrutura

```
src/
├── app/
│   ├── layout.tsx          # layout raiz + navegacao
│   ├── page.tsx            # Dashboard
│   ├── geracao/page.tsx    # Gerar item (Objetivo B/C)
│   ├── avaliacao/page.tsx  # Metricas NLP + LLM-as-Judge (Objetivo E)
│   ├── grafo/page.tsx      # Visualizacao Area->Competencia->Habilidade (ReactFlow)
│   ├── obsidian/page.tsx   # Dispara export Markdown
│   └── configuracao/page.tsx
├── components/Nav.tsx
└── lib/api.ts              # cliente axios tipado, espelha os schemas do backend
```

## O que falta para ficar "completo" no sentido do TCC

- Autenticação real no frontend (login/sessão) — hoje as chamadas a rotas de superusuário (`/geracao/item`, `/config` PUT, `/obsidian/exportar`, `/matriz/integridade`) vão falhar com 401/403 sem uma sessão autenticada; o backend já tem `crudauth` pronto, só falta a tela de login e o cookie de sessão sendo enviado (o cliente axios já usa `withCredentials: true`).
  - Além disso, como frontend (porta 3000) e backend (porta 8000) são origens diferentes, cookies de sessão só atravessam se `CORS_ORIGINS` no `backend/.env` listar `http://localhost:3000` explicitamente — o default `CORS_ORIGINS=*` não funciona com `withCredentials: true` (navegadores recusam `Access-Control-Allow-Origin: *` combinado com credenciais).
- Testes de frontend (Playwright/Vitest) — nada foi escrito ainda.
- Polimento visual — as páginas são funcionais mas propositalmente simples (CSS mínimo em `globals.css`), não uma interface refinada.
