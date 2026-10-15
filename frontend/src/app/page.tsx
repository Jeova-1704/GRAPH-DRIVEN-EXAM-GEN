"use client";

import { useEffect, useState } from "react";
import {
  Area,
  ConfigExperimento,
  IntegridadeRelatorio,
  OrigemQuestao,
  getAreas,
  getConfig,
  getContagemPorOrigem,
  getIntegridade,
} from "@/lib/api";

const ORIGENS: OrigemQuestao[] = ["ENEM", "com_grafo", "com_fewshot_sem_grafo", "sem_grafo"];
const META_POR_CONDICAO = 120 * 5; // 120 habilidades x 5 itens (default GERACAO_ITENS_POR_CONDICAO)

export default function DashboardPage() {
  const [areas, setAreas] = useState<Area[] | null>(null);
  const [integridade, setIntegridade] = useState<IntegridadeRelatorio | null>(null);
  const [contagem, setContagem] = useState<Record<string, number> | null>(null);
  const [config, setConfig] = useState<ConfigExperimento | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    getAreas().then(setAreas).catch((e) => setErro(String(e)));
    getIntegridade().then(setIntegridade).catch(() => setIntegridade(null));
    getContagemPorOrigem().then(setContagem).catch(() => setContagem(null));
    getConfig().then(setConfig).catch(() => setConfig(null));
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Visao geral da plataforma Graph-Driven Exam Gen.</p>

      {erro && (
        <div className="card" style={{ borderColor: "#f87171", background: "#fef2f2" }}>
          Nao foi possivel conectar a API ({process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}).
          Verifique se o backend e o Neo4j estao rodando. Detalhe: {erro}
        </div>
      )}

      <div className="card">
        <h2>Matriz de Referencia (Objetivo A)</h2>
        {integridade ? (
          <div className="grid">
            <div className="stat">
              <div className="valor">{integridade.total_areas}</div>
              <div className="rotulo">Areas</div>
            </div>
            <div className="stat">
              <div className="valor">{integridade.total_competencias}</div>
              <div className="rotulo">Competencias</div>
            </div>
            <div className="stat">
              <div className="valor">{integridade.total_habilidades}</div>
              <div className="rotulo">Habilidades</div>
            </div>
            <div className="stat">
              <div className="valor">{integridade.total_objetos_conhecimento}</div>
              <div className="rotulo">Objetos de Conhecimento</div>
            </div>
            <div className="stat">
              <span className={`badge ${integridade.integro ? "badge-ok" : "badge-erro"}`}>
                {integridade.integro ? "Integro" : "Inconsistente"}
              </span>
            </div>
          </div>
        ) : (
          <p>Grafo nao carregado ainda, ou requer autenticacao de superusuario.</p>
        )}
      </div>

      <div className="card">
        <h2>Corpus experimental (Objetivo D)</h2>
        {contagem ? (
          <table>
            <thead>
              <tr>
                <th>Origem</th>
                <th>Itens</th>
                <th>Meta</th>
              </tr>
            </thead>
            <tbody>
              {ORIGENS.map((origem) => (
                <tr key={origem}>
                  <td>{origem}</td>
                  <td>{contagem[origem] ?? 0}</td>
                  <td>{origem === "ENEM" ? "~600 (few-shots)" : META_POR_CONDICAO}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>Carregando contagem do corpus...</p>
        )}
      </div>

      <div className="card">
        <h2>Areas do Conhecimento</h2>
        {areas ? (
          <ul>
            {areas.map((a) => (
              <li key={a.codigo}>
                <strong>{a.codigo}</strong> — {a.nome}
              </li>
            ))}
          </ul>
        ) : (
          <p>Carregando...</p>
        )}
      </div>

      <div className="card">
        <h2>Configuracao ativa</h2>
        {config ? (
          <ul>
            <li>Modelo de geracao: {config.glm_generation_model}</li>
            <li>Modelo de julgamento: {config.glm_judge_model}</li>
            <li>Itens por condicao: {config.geracao_itens_por_condicao}</li>
          </ul>
        ) : (
          <p>Carregando...</p>
        )}
      </div>
    </div>
  );
}
