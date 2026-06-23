import type {
  AssuntoNotion,
  ResultadoTranscricao,
  TranscricaoRecord,
  FileInfo,
} from "./types";

const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

const BASE = isTauri ? "http://localhost:8001/api" : "/api";

async function _get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

async function _post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function uploadArquivo(file: File): Promise<FileInfo> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/transcricoes/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<FileInfo>;
}

export function urlProcessar(params: {
  file_id: string;
  modelo_nome: string;
  duracao_segmentos: number;
  diarizar: boolean;
  tempo_inicio: number;
  tempo_fim: number | null;
  hash_arquivo: string;
  nome_arquivo: string;
}): string {
  const q = new URLSearchParams({
    file_id: params.file_id,
    modelo_nome: params.modelo_nome,
    duracao_segmentos: String(params.duracao_segmentos),
    diarizar: String(params.diarizar),
    tempo_inicio: String(params.tempo_inicio),
    hash_arquivo: params.hash_arquivo,
    nome_arquivo: params.nome_arquivo,
  });
  if (params.tempo_fim !== null) {
    q.set("tempo_fim", String(params.tempo_fim));
  }
  return `${BASE}/transcricoes/processar?${q.toString()}`;
}

export async function salvarTranscricao(payload: {
  hash_arquivo: string;
  nome_arquivo: string;
  transcricao_completa: string;
  segmentos_com_falantes: unknown[];
  resumo_falantes: Record<string, unknown>;
  diarizacao_ativada: boolean;
  modelo_whisper: string;
  duracao_total: number;
}): Promise<void> {
  await _post("/transcricoes/salvar", payload);
}

export async function buscarCache(
  hash: string
): Promise<TranscricaoRecord | null> {
  try {
    return await _get<TranscricaoRecord>(`/transcricoes/hash/${hash}`);
  } catch {
    return null;
  }
}

export async function listarTranscricoes(
  limite = 100
): Promise<TranscricaoRecord[]> {
  return _get<TranscricaoRecord[]>(`/transcricoes/?limite=${limite}`);
}

export async function buscarTranscricoes(params: {
  termo?: string;
  modelo?: string;
  data_inicio?: string;
  data_fim?: string;
}): Promise<TranscricaoRecord[]> {
  const q = new URLSearchParams();
  if (params.termo) q.set("termo", params.termo);
  if (params.modelo) q.set("modelo", params.modelo);
  if (params.data_inicio) q.set("data_inicio", params.data_inicio);
  if (params.data_fim) q.set("data_fim", params.data_fim);
  return _get<TranscricaoRecord[]>(`/transcricoes/buscar?${q}`);
}

export async function notionStatus(): Promise<boolean> {
  const r = await _get<{ configurado: boolean }>("/notion/status");
  return r.configurado;
}

export async function listarAssuntos(): Promise<AssuntoNotion[]> {
  return _get<AssuntoNotion[]>("/notion/assuntos");
}

export async function criarAssunto(nome: string): Promise<AssuntoNotion> {
  return _post<AssuntoNotion>("/notion/assuntos", { nome });
}

export async function extrairAtividades(transcricao: string): Promise<Record<string, string[]>> {
  const r = await _post<{ atividades: Record<string, string[]> }>("/transcricoes/atividades", { transcricao });
  return r.atividades;
}

export async function resumirTranscricao(transcricao: string): Promise<string> {
  const r = await _post<{ resumo: string }>("/transcricoes/resumir", { transcricao });
  return r.resumo;
}

export async function enviarNotion(payload: {
  assunto_id: string;
  titulo: string;
  transcricao_completa: string;
  segmentos_com_falantes: unknown[];
  resumo_falantes: Record<string, unknown>;
  diarizar: boolean;
  resumo?: string;
  atividades?: Record<string, string[]>;
}): Promise<string> {
  const r = await _post<{ url: string }>("/notion/enviar", payload);
  return r.url;
}

export function recordToResultado(r: TranscricaoRecord): ResultadoTranscricao {
  return {
    sucesso: true,
    transcricao_completa: r.transcricao_completa,
    segmentos: [],
    segmentos_com_falantes: r.segmentos_com_falantes,
    resumo_falantes: r.resumo_falantes,
    diarizacao_ativada: r.diarizacao_ativada,
    duracao_total: r.duracao_total,
    arquivo_completo: "",
    arquivo_detalhado: "",
    pasta_saida: "",
    from_cache: true,
  };
}
