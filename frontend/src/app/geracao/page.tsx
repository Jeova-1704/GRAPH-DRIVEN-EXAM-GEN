"use client";

import { useEffect, useState } from "react";
import {
  Area,
  CondicaoExperimental,
  GeracaoResponse,
  HabilidadeSummary,
  getAreas,
  getHabilidadesPorArea,
  gerarItem,
} from "@/lib/api";

const CONDICOES: { valor: CondicaoExperimental; rotulo: string }[] = [
  { valor: "com_grafo", rotulo: "Com grafo (hierarquia completa + few-shots)" },
  { valor: "com_fewshot_sem_grafo", rotulo: "Com few-shot, sem grafo" },
  { valor: "sem_grafo", rotulo: "Sem grafo (baseline)" },
];

export default function GeracaoPage() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [areaSelecionada, setAreaSelecionada] = useState<string>("");
  const [habilidades, setHabilidades] = useState<HabilidadeSummary[]>([]);
  const [habilidadeSelecionada, setHabilidadeSelecionada] = useState<string>("");
  const [condicao, setCondicao] = useState<CondicaoExperimental>("com_grafo");
  const [resultado, setResultado] = useState<GeracaoResponse | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    getAreas()
      .then((data) => {
        setAreas(data);
        if (data.length > 0) setAreaSelecionada(data[0].codigo);
      })
      .catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    if (!areaSelecionada) return;
    getHabilidadesPorArea(areaSelecionada)
      .then((data) => {
        setHabilidades(data);
        if (data.length > 0) setHabilidadeSelecionada(data[0].codigo);
      })
      .catch((e) => setErro(String(e)));
  }, [areaSelecionada]);

  async function handleGerar() {
    setCarregando(true);
    setErro(null);
    setResultado(null);
    try {
      const resposta = await gerarItem(habilidadeSelecionada, condicao);
      setResultado(resposta);
    } catch (e) {
      setErro(String(e));
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div>
      <h1>Geracao de Itens</h1>
      <p>Pipeline GraphRAG — gera um item para a habilidade e condicao escolhidas.</p>

      <div className="card">
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <label>
            Area:{" "}
            <select value={areaSelecionada} onChange={(e) => setAreaSelecionada(e.target.value)}>
              {areas.map((a) => (
                <option key={a.codigo} value={a.codigo}>
                  {a.codigo} — {a.nome}
                </option>
              ))}
            </select>
          </label>

          <label>
            Habilidade:{" "}
            <select value={habilidadeSelecionada} onChange={(e) => setHabilidadeSelecionada(e.target.value)}>
              {habilidades.map((h) => (
                <option key={h.codigo} value={h.codigo}>
                  {h.codigo}
                </option>
              ))}
            </select>
          </label>

          <label>
            Condicao:{" "}
            <select value={condicao} onChange={(e) => setCondicao(e.target.value as CondicaoExperimental)}>
              {CONDICOES.map((c) => (
                <option key={c.valor} value={c.valor}>
                  {c.rotulo}
                </option>
              ))}
            </select>
          </label>

          <button onClick={handleGerar} disabled={carregando || !habilidadeSelecionada}>
            {carregando ? "Gerando..." : "Gerar item"}
          </button>
        </div>
      </div>

      {erro && (
        <div className="card" style={{ borderColor: "#f87171", background: "#fef2f2" }}>
          Erro: {erro}
          <br />
          <small>Requer GLM_API_KEY configurada e o usuario autenticado como superusuario.</small>
        </div>
      )}

      {resultado && (
        <div className="card">
          <h2>
            Item gerado{" "}
            <span className={`badge ${resultado.validacao.validacao_estrutural_ok ? "badge-ok" : "badge-erro"}`}>
              {resultado.validacao.validacao_estrutural_ok ? "Validacao OK" : "Reprovado"}
            </span>
          </h2>
          <p>{resultado.item.enunciado}</p>
          <ul>
            {Object.entries(resultado.item.alternativas).map(([letra, texto]) => (
              <li key={letra}>
                <strong>{letra})</strong> {texto}
              </li>
            ))}
          </ul>
          <p>
            <strong>Gabarito:</strong> {resultado.item.gabarito}
          </p>
          <p>
            <strong>Justificativa:</strong> {resultado.item.justificativa}
          </p>
          {resultado.validacao.criterios_reprovados.length > 0 && (
            <p style={{ color: "#991b1b" }}>
              Criterios reprovados: {resultado.validacao.criterios_reprovados.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
