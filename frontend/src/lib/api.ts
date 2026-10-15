import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1",
  withCredentials: true,
});

// --- Matriz de Referencia (Objetivo A) ---

export interface Area {
  codigo: string;
  nome: string;
}

export interface HabilidadeSummary {
  codigo: string;
  descricao: string;
}

export interface ObjetoConhecimento {
  codigo: string;
  titulo: string;
  descricao: string;
}

export interface HabilidadeContexto {
  habilidade_codigo: string;
  habilidade_descricao: string;
  competencia_numero: number;
  competencia_descricao: string;
  area_codigo: string;
  area_nome: string;
  objetos_conhecimento: ObjetoConhecimento[];
}

export interface IntegridadeRelatorio {
  total_areas: number;
  total_competencias: number;
  total_habilidades: number;
  total_objetos_conhecimento: number;
  habilidades_sem_objeto_conhecimento: number;
  habilidades_sem_competencia: number;
  competencias_sem_area: number;
  integro: boolean;
}

export async function getAreas(): Promise<Area[]> {
  const { data } = await api.get<Area[]>("/matriz/areas");
  return data;
}

export async function getHabilidadesPorArea(areaCodigo: string): Promise<HabilidadeSummary[]> {
  const { data } = await api.get<HabilidadeSummary[]>(`/matriz/areas/${areaCodigo}/habilidades`);
  return data;
}

export async function getHabilidade(codigo: string): Promise<HabilidadeContexto> {
  const { data } = await api.get<HabilidadeContexto>(`/matriz/habilidades/${codigo}`);
  return data;
}

export async function getIntegridade(): Promise<IntegridadeRelatorio> {
  const { data } = await api.get<IntegridadeRelatorio>("/matriz/integridade");
  return data;
}

// --- Geracao (Objetivo B/C) ---

export type CondicaoExperimental = "com_grafo" | "com_fewshot_sem_grafo" | "sem_grafo";

export interface FewShot {
  enunciado: string;
  alternativas: Record<string, string>;
  gabarito: string;
}

export interface ItemGerado {
  enunciado: string;
  alternativas: Record<string, string>;
  gabarito: string;
  justificativa: string;
}

export interface ValidacaoResultado {
  validacao_estrutural_ok: boolean;
  criterios_reprovados: string[];
}

export interface GeracaoResponse {
  item: ItemGerado;
  validacao: ValidacaoResultado;
}

export async function gerarItem(
  habilidadeCodigo: string,
  condicao: CondicaoExperimental,
  fewShots: FewShot[] = []
): Promise<GeracaoResponse> {
  const { data } = await api.post<GeracaoResponse>("/geracao/item", {
    habilidade_codigo: habilidadeCodigo,
    condicao,
    few_shots: fewShots,
  });
  return data;
}

// --- Questoes (corpus, Objetivo D/E) ---

export type OrigemQuestao = "ENEM" | CondicaoExperimental;

export interface QuestaoMetricas {
  cobertura_lexical: number | null;
  especificidade_curricular: number | null;
  similaridade_semantica: number | null;
  ttr: number | null;
  fkgl: number | null;
}

export interface QuestaoJulgamento {
  d1_alinhamento_habilidade: number | null;
  d2_adequacao_objetos_conhecimento: number | null;
  d3_plausibilidade_distratores: number | null;
  d4_nivel_escolaridade: number | null;
  d5_aderencia_formato_enem: number | null;
  justificativa: string | null;
}

export interface Questao {
  id: string;
  habilidade_codigo: string;
  enunciado: string;
  alternativas: Record<string, string>;
  gabarito: string;
  justificativa: string | null;
  origem: OrigemQuestao;
  ano_origem: number | null;
  validacao_estrutural_ok: boolean;
  metricas: QuestaoMetricas;
  julgamento: QuestaoJulgamento;
}

export async function getQuestoesPorOrigem(origem: OrigemQuestao): Promise<Questao[]> {
  const { data } = await api.get<Questao[]>("/questoes/", { params: { origem } });
  return data;
}

export async function getContagemPorOrigem(): Promise<Record<OrigemQuestao, number>> {
  const { data } = await api.get<Record<OrigemQuestao, number>>("/questoes/contagem");
  return data;
}

// --- Configuracao (Secao 3.5.3) ---

export interface ConfigExperimento {
  glm_generation_model: string;
  glm_judge_model: string;
  glm_temperature: number;
  glm_max_tokens: number;
  geracao_itens_por_condicao: number;
  geracao_fewshots_por_habilidade: number;
  validacao_enunciado_min_chars: number;
  validacao_justificativa_min_chars: number;
  estatistica_alpha: number;
  estatistica_alpha_bonferroni: number;
}

export async function getConfig(): Promise<ConfigExperimento> {
  const { data } = await api.get<ConfigExperimento>("/config/");
  return data;
}

export async function atualizarConfig(patch: Partial<ConfigExperimento>): Promise<ConfigExperimento> {
  const { data } = await api.put<ConfigExperimento>("/config/", patch);
  return data;
}

// --- Obsidian export (Secao 3.5.4) ---

export interface ExportarObsidianResultado {
  diretorio: string;
  habilidades_exportadas: number;
  questoes_exportadas: number;
}

export async function exportarObsidian(diretorio = "obsidian_vault"): Promise<ExportarObsidianResultado> {
  const { data } = await api.post<ExportarObsidianResultado>("/obsidian/exportar", { diretorio });
  return data;
}

// --- Validacao (Objetivo C, standalone check) ---

export async function verificarItem(item: ItemGerado): Promise<ValidacaoResultado> {
  const { data } = await api.post<ValidacaoResultado>("/validacao/verificar", item);
  return data;
}
