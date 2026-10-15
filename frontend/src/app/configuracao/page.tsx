"use client";

import { useEffect, useState } from "react";
import { ConfigExperimento, atualizarConfig, getConfig } from "@/lib/api";

export default function ConfiguracaoPage() {
  const [config, setConfig] = useState<ConfigExperimento | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    getConfig()
      .then(setConfig)
      .catch((e) => setErro(String(e)));
  }, []);

  function atualizarCampo<K extends keyof ConfigExperimento>(campo: K, valor: ConfigExperimento[K]) {
    setConfig((atual) => (atual ? { ...atual, [campo]: valor } : atual));
  }

  async function handleSalvar() {
    if (!config) return;
    setSalvando(true);
    setErro(null);
    setMensagem(null);
    try {
      const atualizado = await atualizarConfig(config);
      setConfig(atualizado);
      setMensagem("Configuracao salva.");
    } catch (e) {
      setErro(String(e));
    } finally {
      setSalvando(false);
    }
  }

  if (erro && !config) {
    return (
      <div className="card" style={{ borderColor: "#f87171", background: "#fef2f2" }}>
        Erro ao carregar configuracao: {erro}
      </div>
    );
  }

  if (!config) return <p>Carregando...</p>;

  return (
    <div>
      <h1>Configuracao</h1>
      <p>Parametros de geracao/validacao editaveis em runtime, persistidos no no :Config.</p>

      <div className="card">
        <h2>GLM (Zhipu AI)</h2>
        <label>
          Modelo de geracao:{" "}
          <input value={config.glm_generation_model} onChange={(e) => atualizarCampo("glm_generation_model", e.target.value)} />
        </label>
        <br />
        <br />
        <label>
          Modelo de julgamento:{" "}
          <input value={config.glm_judge_model} onChange={(e) => atualizarCampo("glm_judge_model", e.target.value)} />
        </label>
        <br />
        <br />
        <label>
          Temperatura:{" "}
          <input
            type="number"
            step="0.1"
            value={config.glm_temperature}
            onChange={(e) => atualizarCampo("glm_temperature", Number(e.target.value))}
          />
        </label>
        <br />
        <br />
        <label>
          Max tokens:{" "}
          <input
            type="number"
            value={config.glm_max_tokens}
            onChange={(e) => atualizarCampo("glm_max_tokens", Number(e.target.value))}
          />
        </label>
      </div>

      <div className="card">
        <h2>Geracao</h2>
        <label>
          Itens por condicao:{" "}
          <input
            type="number"
            value={config.geracao_itens_por_condicao}
            onChange={(e) => atualizarCampo("geracao_itens_por_condicao", Number(e.target.value))}
          />
        </label>
        <br />
        <br />
        <label>
          Few-shots por habilidade:{" "}
          <input
            type="number"
            value={config.geracao_fewshots_por_habilidade}
            onChange={(e) => atualizarCampo("geracao_fewshots_por_habilidade", Number(e.target.value))}
          />
        </label>
      </div>

      <div className="card">
        <h2>Validacao</h2>
        <label>
          Enunciado - minimo de caracteres:{" "}
          <input
            type="number"
            value={config.validacao_enunciado_min_chars}
            onChange={(e) => atualizarCampo("validacao_enunciado_min_chars", Number(e.target.value))}
          />
        </label>
        <br />
        <br />
        <label>
          Justificativa - minimo de caracteres:{" "}
          <input
            type="number"
            value={config.validacao_justificativa_min_chars}
            onChange={(e) => atualizarCampo("validacao_justificativa_min_chars", Number(e.target.value))}
          />
        </label>
      </div>

      <div className="card">
        <h2>Analise estatistica</h2>
        <label>
          Alpha:{" "}
          <input
            type="number"
            step="0.01"
            value={config.estatistica_alpha}
            onChange={(e) => atualizarCampo("estatistica_alpha", Number(e.target.value))}
          />
        </label>
        <br />
        <br />
        <label>
          Alpha (Bonferroni):{" "}
          <input
            type="number"
            step="0.001"
            value={config.estatistica_alpha_bonferroni}
            onChange={(e) => atualizarCampo("estatistica_alpha_bonferroni", Number(e.target.value))}
          />
        </label>
      </div>

      <button onClick={handleSalvar} disabled={salvando}>
        {salvando ? "Salvando..." : "Salvar configuracao"}
      </button>

      {mensagem && <p style={{ color: "#166534" }}>{mensagem}</p>}
      {erro && <p style={{ color: "#991b1b" }}>Erro: {erro}</p>}
    </div>
  );
}
