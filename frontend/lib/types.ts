export interface FileInfo {
  file_id: string;
  nome: string;
  hash_arquivo: string;
  duracao: number | null;
  tipo: string;
}

export interface SegmentoTranscricao {
  numero: number;
  texto: string;
  duracao: number;
}

export interface SegmentoFalante {
  falante: string;
  texto: string;
}

export interface EstatFalante {
  num_falas: number;
  tempo_total: number;
  textos: string[];
}

export interface ResultadoTranscricao {
  sucesso: boolean;
  transcricao_completa: string;
  segmentos: SegmentoTranscricao[];
  segmentos_com_falantes: SegmentoFalante[];
  resumo_falantes: Record<string, EstatFalante>;
  diarizacao_ativada: boolean;
  duracao_total: number;
  arquivo_completo: string;
  arquivo_detalhado: string;
  pasta_saida: string;
  erro?: string;
  from_cache?: boolean;
}

export interface TranscricaoRecord {
  id: string;
  hash_arquivo: string;
  nome_arquivo: string;
  transcricao_completa: string;
  segmentos_com_falantes: SegmentoFalante[];
  resumo_falantes: Record<string, EstatFalante>;
  diarizacao_ativada: boolean;
  modelo_whisper: string;
  duracao_total: number;
  created_at: string;
}

export interface AssuntoNotion {
  id: string;
  nome: string;
}

export interface ConfigStatus {
  conexao_ok: boolean;
  hf_ok: boolean;
  notion_ok: boolean;
}

export interface ConexaoAtual {
  supabase_url: string;
  supabase_key: string;
  database_url: string;
}

export interface ConexaoPayload {
  supabase_url: string;
  supabase_key: string;
  database_url: string;
}

export interface IntegracoesAtual {
  hf_token: string;
  notion_token: string;
  notion_parent_id: string;
}

export interface IntegracoesPayload {
  hf_token?: string;
  notion_token?: string;
  notion_parent_id?: string;
}

export type SSEEvent =
  | { type: "progress"; value: number }
  | { type: "status"; message: string }
  | { type: "preview"; text: string }
  | { type: "heartbeat" }
  | { type: "complete"; data: ResultadoTranscricao }
  | { type: "error"; message: string; traceback: string };

export type ModeloNome =
  | "tiny" | "base" | "small" | "medium"
  | "large" | "large-v1" | "large-v2" | "large-v3";

export const MODELOS: ModeloNome[] = [
  "tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3",
];

export interface ModeloInfo {
  qualidade: string;
  velocidade: string;
  tempo_estimado: string;
  descricao: string;
}

export const MODELOS_INFO: Record<ModeloNome, ModeloInfo> = {
  tiny:      { qualidade: "Básica",    velocidade: "Muito rápida", tempo_estimado: "~1 min",  descricao: "Rápido, menor precisão. Ideal para testes." },
  base:      { qualidade: "Boa",       velocidade: "Rápida",       tempo_estimado: "~2 min",  descricao: "Equilíbrio entre velocidade e qualidade." },
  small:     { qualidade: "Boa+",      velocidade: "Média",        tempo_estimado: "~4 min",  descricao: "Boa qualidade para a maioria dos casos." },
  medium:    { qualidade: "Ótima",     velocidade: "Lenta",        tempo_estimado: "~8 min",  descricao: "Alta qualidade. Recomendado para reuniões." },
  large:     { qualidade: "Excelente", velocidade: "Muito lenta",  tempo_estimado: "~15 min", descricao: "Máxima qualidade. Requer GPU." },
  "large-v1":{ qualidade: "Excelente", velocidade: "Muito lenta",  tempo_estimado: "~15 min", descricao: "large v1." },
  "large-v2":{ qualidade: "Excelente", velocidade: "Muito lenta",  tempo_estimado: "~15 min", descricao: "large v2, melhor que v1." },
  "large-v3":{ qualidade: "Máxima",    velocidade: "Muito lenta",  tempo_estimado: "~20 min", descricao: "Melhor modelo disponível. Requer GPU potente." },
};
