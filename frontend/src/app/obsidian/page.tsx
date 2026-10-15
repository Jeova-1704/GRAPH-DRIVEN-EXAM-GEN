"use client";

import { useState } from "react";
import { ExportarObsidianResultado, exportarObsidian } from "@/lib/api";

export default function ObsidianPage() {
  const [diretorio, setDiretorio] = useState("obsidian_vault");
  const [resultado, setResultado] = useState<ExportarObsidianResultado | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function handleExportar() {
    setCarregando(true);
    setErro(null);
    setResultado(null);
    try {
      const resposta = await exportarObsidian(diretorio);
      setResultado(resposta);
    } catch (e) {
      setErro(String(e));
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div>
      <h1>Export Obsidian</h1>
      <p>
        Gera arquivos Markdown (frontmatter YAML + wiki-links) para toda a Matriz de Referencia e o corpus de itens,
        navegaveis no Graph View do Obsidian.
      </p>

      <div className="card">
        <label>
          Diretorio (no servidor do backend):{" "}
          <input value={diretorio} onChange={(e) => setDiretorio(e.target.value)} style={{ width: 260 }} />
        </label>
        <div style={{ marginTop: 12 }}>
          <button onClick={handleExportar} disabled={carregando}>
            {carregando ? "Exportando..." : "Exportar tudo"}
          </button>
        </div>
      </div>

      {erro && (
        <div className="card" style={{ borderColor: "#f87171", background: "#fef2f2" }}>
          Erro: {erro} <br />
          <small>Requer autenticacao de superusuario e o grafo carregado.</small>
        </div>
      )}

      {resultado && (
        <div className="card">
          <h2>Exportacao concluida</h2>
          <ul>
            <li>Diretorio: {resultado.diretorio}</li>
            <li>Habilidades exportadas: {resultado.habilidades_exportadas}</li>
            <li>Questoes exportadas: {resultado.questoes_exportadas}</li>
          </ul>
          <p style={{ fontSize: 12, color: "#666" }}>
            Abra o diretorio como um vault no Obsidian e use o Graph View para navegar pelas conexoes
            Area → Competencia → Habilidade → Objeto de Conhecimento / Questao.
          </p>
        </div>
      )}
    </div>
  );
}
