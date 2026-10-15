"use client";

import { Fragment, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { OrigemQuestao, Questao, getQuestoesPorOrigem } from "@/lib/api";

const CONDICOES: OrigemQuestao[] = ["com_grafo", "com_fewshot_sem_grafo", "sem_grafo"];

function media(valores: (number | null)[]): number {
  const validos = valores.filter((v): v is number => v !== null);
  if (validos.length === 0) return 0;
  return validos.reduce((a, b) => a + b, 0) / validos.length;
}

export default function AvaliacaoPage() {
  const [questoesPorCondicao, setQuestoesPorCondicao] = useState<Record<string, Questao[]>>({});
  const [condicaoSelecionada, setCondicaoSelecionada] = useState<OrigemQuestao>("com_grafo");
  const [erro, setErro] = useState<string | null>(null);
  const [expandidoId, setExpandidoId] = useState<string | null>(null);
  const [filtroHabilidade, setFiltroHabilidade] = useState<string>("todas");
  const [busca, setBusca] = useState<string>("");

  useEffect(() => {
    Promise.all(CONDICOES.map((c) => getQuestoesPorOrigem(c)))
      .then((resultados) => {
        const mapa: Record<string, Questao[]> = {};
        CONDICOES.forEach((c, i) => (mapa[c] = resultados[i]));
        setQuestoesPorCondicao(mapa);
      })
      .catch((e) => setErro(String(e)));
  }, []);

  const dadosGrafico = CONDICOES.map((condicao) => {
    const questoes = questoesPorCondicao[condicao] || [];
    return {
      condicao,
      cobertura_lexical: media(questoes.map((q) => q.metricas.cobertura_lexical)),
      ttr: media(questoes.map((q) => q.metricas.ttr)),
      score_medio_judge: media(
        questoes.map((q) => {
          const j = q.julgamento;
          const dims = [
            j.d1_alinhamento_habilidade,
            j.d2_adequacao_objetos_conhecimento,
            j.d3_plausibilidade_distratores,
            j.d4_nivel_escolaridade,
            j.d5_aderencia_formato_enem,
          ];
          if (dims.some((d) => d === null)) return null;
          return (dims as number[]).reduce((a, b) => a + b, 0) / 5;
        })
      ),
    };
  });

  const questoesDaCondicao = questoesPorCondicao[condicaoSelecionada] || [];
  const habilidadesDisponiveis = Array.from(new Set(questoesDaCondicao.map((q) => q.habilidade_codigo))).sort();
  const questoesExibidas = questoesDaCondicao.filter((q) => {
    if (filtroHabilidade !== "todas" && q.habilidade_codigo !== filtroHabilidade) return false;
    if (busca.trim() && !q.enunciado.toLowerCase().includes(busca.trim().toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <h1>Avaliacao de Qualidade</h1>
      <p>Camada B (metricas NLP) + Camada A (LLM-as-Judge).</p>

      {erro && (
        <div className="card" style={{ borderColor: "#f87171", background: "#fef2f2" }}>
          Erro ao carregar: {erro}
        </div>
      )}

      <div className="card">
        <h2>Comparativo entre condicoes</h2>
        <div style={{ width: "100%", height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={dadosGrafico}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="condicao" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="cobertura_lexical" fill="#2563eb" name="Cobertura lexical C(i,h)" />
              <Bar dataKey="ttr" fill="#16a34a" name="TTR" />
              <Bar dataKey="score_medio_judge" fill="#f59e0b" name="Score medio LLM-as-Judge" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p style={{ fontSize: 12, color: "#666" }}>
          Hipotese central: com_grafo &gt; com_fewshot_sem_grafo &gt; sem_grafo. Confirmacao
          estatistica formal via Kruskal-Wallis + Mann-Whitney (Objetivo F) roda offline —
          ver src/analysis/estatistica.py.
        </p>
      </div>

      <div className="card">
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <label>
            Condicao:{" "}
            <select
              value={condicaoSelecionada}
              onChange={(e) => {
                setCondicaoSelecionada(e.target.value as OrigemQuestao);
                setFiltroHabilidade("todas");
              }}
            >
              {CONDICOES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Habilidade:{" "}
            <select value={filtroHabilidade} onChange={(e) => setFiltroHabilidade(e.target.value)}>
              <option value="todas">Todas ({habilidadesDisponiveis.length})</option>
              {habilidadesDisponiveis.map((h) => (
                <option key={h} value={h}>
                  {h}
                </option>
              ))}
            </select>
          </label>
          <label>
            Buscar no enunciado:{" "}
            <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="ex: fotossintese" style={{ width: 200 }} />
          </label>
          <span>{questoesExibidas.length} itens</span>
        </div>

        <table>
          <thead>
            <tr>
              <th></th>
              <th>Habilidade</th>
              <th>Validacao</th>
              <th>Cobertura</th>
              <th>Especificidade</th>
              <th>TTR</th>
              <th>FKGL</th>
              <th>Score Judge</th>
            </tr>
          </thead>
          <tbody>
            {questoesExibidas.map((q) => {
              const j = q.julgamento;
              const dims = [
                j.d1_alinhamento_habilidade,
                j.d2_adequacao_objetos_conhecimento,
                j.d3_plausibilidade_distratores,
                j.d4_nivel_escolaridade,
                j.d5_aderencia_formato_enem,
              ];
              const scoreJudge = dims.every((d) => d !== null)
                ? ((dims as number[]).reduce((a, b) => a + b, 0) / 5).toFixed(2)
                : "—";
              const expandido = expandidoId === q.id;
              return (
                <Fragment key={q.id}>
                  <tr onClick={() => setExpandidoId(expandido ? null : q.id)} style={{ cursor: "pointer" }}>
                    <td>{expandido ? "▼" : "▶"}</td>
                    <td>{q.habilidade_codigo}</td>
                    <td>
                      <span className={`badge ${q.validacao_estrutural_ok ? "badge-ok" : "badge-erro"}`}>
                        {q.validacao_estrutural_ok ? "OK" : "Reprovado"}
                      </span>
                    </td>
                    <td>{q.metricas.cobertura_lexical?.toFixed(3) ?? "—"}</td>
                    <td>{q.metricas.especificidade_curricular?.toFixed(2) ?? "—"}</td>
                    <td>{q.metricas.ttr?.toFixed(3) ?? "—"}</td>
                    <td>{q.metricas.fkgl?.toFixed(1) ?? "—"}</td>
                    <td>{scoreJudge}</td>
                  </tr>
                  {expandido && (
                    <tr>
                      <td colSpan={8} style={{ background: "#fafafa", padding: 16 }}>
                        <p style={{ marginTop: 0 }}>
                          <strong>Enunciado:</strong> {q.enunciado}
                        </p>
                        <ul style={{ listStyle: "none", paddingLeft: 0 }}>
                          {Object.entries(q.alternativas)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([letra, texto]) => (
                              <li
                                key={letra}
                                style={{
                                  padding: "4px 8px",
                                  marginBottom: 4,
                                  borderRadius: 4,
                                  background: letra === q.gabarito ? "#dcfce7" : "transparent",
                                  fontWeight: letra === q.gabarito ? 600 : 400,
                                }}
                              >
                                <strong>{letra})</strong> {texto}
                                {letra === q.gabarito ? "  ✓ Gabarito" : ""}
                              </li>
                            ))}
                        </ul>
                        {q.justificativa && (
                          <p>
                            <strong>Justificativa:</strong> {q.justificativa}
                          </p>
                        )}
                        {q.julgamento.justificativa && (
                          <p style={{ fontSize: 13, color: "#555" }}>
                            <strong>Comentario do juiz LLM:</strong> {q.julgamento.justificativa}
                          </p>
                        )}
                        <p style={{ fontSize: 12, color: "#888" }}>
                          ID: {q.id} · Origem: {q.origem} · Ano origem: {q.ano_origem ?? "—"}
                        </p>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
