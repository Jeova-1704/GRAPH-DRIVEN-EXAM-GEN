"use client";

import { useCallback, useEffect, useState } from "react";
import ReactFlow, { Background, Controls, Edge, Node } from "reactflow";
import "reactflow/dist/style.css";
import {
  Area,
  HabilidadeContexto,
  OrigemQuestao,
  Questao,
  getAreas,
  getHabilidade,
  getHabilidadesPorArea,
  getQuestoesPorOrigem,
} from "@/lib/api";

const CORES_ORIGEM: Record<OrigemQuestao, string> = {
  ENEM: "#7c3aed",
  com_grafo: "#16a34a",
  com_fewshot_sem_grafo: "#f59e0b",
  sem_grafo: "#ef4444",
};

const TODAS_ORIGENS: OrigemQuestao[] = ["ENEM", "com_grafo", "com_fewshot_sem_grafo", "sem_grafo"];

export default function GrafoPage() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [areaSelecionada, setAreaSelecionada] = useState<string>("");
  const [questoesPorHabilidade, setQuestoesPorHabilidade] = useState<Record<string, Questao[]>>({});
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [habilidadeSelecionada, setHabilidadeSelecionada] = useState<HabilidadeContexto | null>(null);
  const [questaoSelecionada, setQuestaoSelecionada] = useState<Questao | null>(null);
  const [apenasComItens, setApenasComItens] = useState(false);
  const [busca, setBusca] = useState("");

  useEffect(() => {
    getAreas().then((data) => {
      setAreas(data);
      if (data.length > 0) setAreaSelecionada(data[0].codigo);
    });

    Promise.all(TODAS_ORIGENS.map((o) => getQuestoesPorOrigem(o).catch(() => [] as Questao[]))).then((resultados) => {
      const mapa: Record<string, Questao[]> = {};
      resultados.flat().forEach((q) => {
        (mapa[q.habilidade_codigo] ||= []).push(q);
      });
      setQuestoesPorHabilidade(mapa);
    });
  }, []);

  useEffect(() => {
    if (!areaSelecionada) return;
    setCarregando(true);
    setHabilidadeSelecionada(null);
    setQuestaoSelecionada(null);

    (async () => {
      const habilidades = await getHabilidadesPorArea(areaSelecionada);
      const todosContextos = await Promise.all(habilidades.map((h) => getHabilidade(h.codigo)));
      const buscaLower = busca.trim().toLowerCase();
      const contextos = todosContextos.filter((ctx) => {
        if (apenasComItens && (questoesPorHabilidade[ctx.habilidade_codigo] || []).length === 0) return false;
        if (
          buscaLower &&
          !ctx.habilidade_codigo.toLowerCase().includes(buscaLower) &&
          !ctx.habilidade_descricao.toLowerCase().includes(buscaLower)
        )
          return false;
        return true;
      });

      const competenciasVistas = new Map<number, string>();
      const novosNodes: Node[] = [
        {
          id: `area-${areaSelecionada}`,
          data: { label: areaSelecionada },
          position: { x: 0, y: 300 },
          style: { background: "#1a1a1a", color: "#fff", borderRadius: 8 },
        },
      ];
      const novasEdges: Edge[] = [];
      const mapaHabilidades: Record<string, HabilidadeContexto> = {};
      const mapaQuestoes: Record<string, Questao> = {};

      let yHabilidade = 0;
      contextos.forEach((ctx) => {
        const compId = `comp-${ctx.competencia_numero}`;
        if (!competenciasVistas.has(ctx.competencia_numero)) {
          competenciasVistas.set(ctx.competencia_numero, compId);
          const yComp = competenciasVistas.size * 90;
          novosNodes.push({
            id: compId,
            data: { label: `C${ctx.competencia_numero}` },
            position: { x: 260, y: yComp },
            style: { background: "#2563eb", color: "#fff", borderRadius: 8, fontSize: 12 },
          });
          novasEdges.push({ id: `e-area-${compId}`, source: `area-${areaSelecionada}`, target: compId });
        }

        const habId = `hab-${ctx.habilidade_codigo}`;
        const questoesDaHabilidade = questoesPorHabilidade[ctx.habilidade_codigo] || [];
        novosNodes.push({
          id: habId,
          data: { label: `${ctx.habilidade_codigo} (${questoesDaHabilidade.length})` },
          position: { x: 540, y: yHabilidade },
          style: {
            fontSize: 11,
            padding: 4,
            border: questoesDaHabilidade.length > 0 ? "2px solid #16a34a" : undefined,
          },
        });
        novasEdges.push({ id: `e-${compId}-${habId}`, source: compId, target: habId });
        mapaHabilidades[habId] = ctx;

        questoesDaHabilidade.forEach((q, qi) => {
          const qId = `q-${q.id}`;
          novosNodes.push({
            id: qId,
            data: { label: q.origem },
            position: { x: 820 + (qi % 3) * 90, y: yHabilidade + Math.floor(qi / 3) * 26 },
            style: {
              fontSize: 9,
              padding: 3,
              background: CORES_ORIGEM[q.origem],
              color: "#fff",
              borderRadius: 999,
              width: 80,
              textAlign: "center",
            },
          });
          novasEdges.push({
            id: `e-avalia-${qId}`,
            source: qId,
            target: habId,
            label: "AVALIA",
            style: { stroke: CORES_ORIGEM[q.origem] },
          });
          mapaQuestoes[qId] = q;
        });

        yHabilidade += 40 + Math.ceil(questoesDaHabilidade.length / 3) * 26;
      });

      setNodes(novosNodes);
      setEdges(novasEdges);
      setCarregando(false);

      (window as unknown as { __habilidades?: Record<string, HabilidadeContexto> }).__habilidades = mapaHabilidades;
      (window as unknown as { __questoes?: Record<string, Questao> }).__questoes = mapaQuestoes;
    })();
  }, [areaSelecionada, questoesPorHabilidade, apenasComItens, busca]);

  const handleNodeClick = useCallback((_: unknown, node: Node) => {
    const habilidades = (window as unknown as { __habilidades?: Record<string, HabilidadeContexto> }).__habilidades;
    const questoes = (window as unknown as { __questoes?: Record<string, Questao> }).__questoes;
    if (habilidades && habilidades[node.id]) {
      setHabilidadeSelecionada(habilidades[node.id]);
      setQuestaoSelecionada(null);
    } else if (questoes && questoes[node.id]) {
      setQuestaoSelecionada(questoes[node.id]);
      setHabilidadeSelecionada(null);
    }
  }, []);

  const totalQuestoes = Object.values(questoesPorHabilidade).reduce((acc, qs) => acc + qs.length, 0);

  return (
    <div>
      <h1>Grafo da Matriz de Referencia</h1>
      <p>
        Area → Competencia → Habilidade → Questao. Clique em qualquer no para ver o detalhe — sem
        precisar escrever Cypher. Bordas verdes = habilidade ja tem itens gerados. {totalQuestoes} questoes no total
        carregadas no grafo.
      </p>

      <div className="card">
        <label>
          Area:{" "}
          <select value={areaSelecionada} onChange={(e) => setAreaSelecionada(e.target.value)}>
            {areas.map((a) => (
              <option key={a.codigo} value={a.codigo}>
                {a.codigo} — {a.nome}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Buscar habilidade:{" "}
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="codigo ou palavra-chave"
            style={{ width: 200 }}
          />
        </label>{" "}
        <label>
          <input type="checkbox" checked={apenasComItens} onChange={(e) => setApenasComItens(e.target.checked)} />{" "}
          Mostrar so habilidades com itens gerados
        </label>
        {carregando && <span style={{ marginLeft: 12 }}>Carregando grafo...</span>}
        <div style={{ marginTop: 8, fontSize: 12 }}>
          Legenda das Questoes:{" "}
          {TODAS_ORIGENS.map((o) => (
            <span key={o} style={{ marginRight: 12 }}>
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  borderRadius: 999,
                  background: CORES_ORIGEM[o],
                  marginRight: 4,
                }}
              />
              {o}
            </span>
          ))}
        </div>
      </div>

      <div className="card" style={{ height: 550, padding: 0 }}>
        <ReactFlow nodes={nodes} edges={edges} onNodeClick={handleNodeClick} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      {habilidadeSelecionada && (
        <div className="card">
          <h2>{habilidadeSelecionada.habilidade_codigo}</h2>
          <p>{habilidadeSelecionada.habilidade_descricao}</p>
          <p>
            <strong>Competencia {habilidadeSelecionada.competencia_numero}:</strong>{" "}
            {habilidadeSelecionada.competencia_descricao}
          </p>
          <h3>Objetos de Conhecimento</h3>
          <ul>
            {habilidadeSelecionada.objetos_conhecimento.map((oc) => (
              <li key={oc.codigo}>
                <strong>{oc.titulo}</strong>: {oc.descricao}
              </li>
            ))}
          </ul>
        </div>
      )}

      {questaoSelecionada && (
        <div className="card">
          <h2>
            Questao ({questaoSelecionada.origem}){" "}
            <span className={`badge ${questaoSelecionada.validacao_estrutural_ok ? "badge-ok" : "badge-erro"}`}>
              {questaoSelecionada.validacao_estrutural_ok ? "OK" : "Reprovado"}
            </span>
          </h2>
          <p>{questaoSelecionada.enunciado}</p>
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {Object.entries(questaoSelecionada.alternativas)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([letra, texto]) => (
                <li
                  key={letra}
                  style={{
                    padding: "4px 8px",
                    marginBottom: 4,
                    borderRadius: 4,
                    background: letra === questaoSelecionada.gabarito ? "#dcfce7" : "transparent",
                    fontWeight: letra === questaoSelecionada.gabarito ? 600 : 400,
                  }}
                >
                  <strong>{letra})</strong> {texto}
                </li>
              ))}
          </ul>
          {questaoSelecionada.justificativa && (
            <p>
              <strong>Justificativa:</strong> {questaoSelecionada.justificativa}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
