"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, RefreshCw } from "lucide-react";
import { listarTranscricoes, recordToResultado } from "@/lib/api";
import { useWizard } from "@/lib/store";
import type { TranscricaoRecord } from "@/lib/types";
import { useRouter } from "next/navigation";

function fmtData(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function fmtMin(duracao: number): string {
  return `${duracao.toFixed(1)} min`;
}

export function ListagemPage() {
  const [registros, setRegistros] = useState<TranscricaoRecord[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const lista = await listarTranscricoes(100);
      setRegistros(lista);
    } catch {
      setErro("Erro ao carregar transcrições. Verifique se o backend está rodando.");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => { carregar(); }, [carregar]);

  return (
    <div>
      <Header onRefresh={carregar} />

      {carregando && <Skeleton />}

      {!carregando && erro && (
        <div className="card bg-red-50 border-red-200 text-red-700 text-sm">{erro}</div>
      )}

      {!carregando && !erro && registros.length === 0 && <Vazia />}

      {!carregando && !erro && registros.length > 0 && (
        <div className="space-y-3">
          {registros.map((r) => (
            <CartaoTranscricao key={r.id} registro={r} />
          ))}
        </div>
      )}
    </div>
  );
}

function Header({ onRefresh }: { onRefresh: () => void }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Transcrições</h1>
        <p className="text-sm text-gray-500 mt-0.5">Histórico de arquivos transcritos</p>
      </div>
      <button onClick={onRefresh} className="btn-secondary">
        <RefreshCw size={14} /> Atualizar
      </button>
    </div>
  );
}

function CartaoTranscricao({ registro }: { registro: TranscricaoRecord }) {
  const [expandido, setExpandido] = useState(false);
  const { setResults, setStep } = useWizard();
  const router = useRouter();

  const carregarNaWizard = () => {
    setResults(recordToResultado(registro));
    setStep(4);
    router.push("/transcricao");
  };

  const numFalantes = Object.keys(registro.resumo_falantes ?? {}).length;

  return (
    <div className="card hover:border-primary/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <FileText size={16} className="text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-800 text-sm truncate">{registro.nome_arquivo}</p>
            <p className="text-xs text-gray-400 mt-0.5">{fmtData(registro.created_at)}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badges registro={registro} numFalantes={numFalantes} />
          <button onClick={carregarNaWizard} className="btn-primary text-xs py-1.5 px-3">
            Carregar
          </button>
          <button
            onClick={() => setExpandido(!expandido)}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            {expandido ? "Recolher" : "Prévia"}
          </button>
        </div>
      </div>

      {expandido && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 leading-relaxed line-clamp-6">
            {registro.transcricao_completa}
          </p>
        </div>
      )}
    </div>
  );
}

function Badges({ registro, numFalantes }: { registro: TranscricaoRecord; numFalantes: number }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <span className="badge">{registro.modelo_whisper}</span>
      <span className="badge">{fmtMin(registro.duracao_total)}</span>
      {registro.diarizacao_ativada && (
        <span className="badge bg-purple-100 text-purple-700">
          👥 {numFalantes} falantes
        </span>
      )}
    </div>
  );
}

function Vazia() {
  return (
    <div className="card flex flex-col items-center justify-center py-12 text-center">
      <FileText size={32} className="text-gray-200 mb-3" />
      <p className="text-sm font-semibold text-gray-500">Nenhuma transcrição encontrada</p>
      <p className="text-xs text-gray-400 mt-1">Faça sua primeira transcrição na aba "Fazer Transcrição"</p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card animate-pulse">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gray-100" />
            <div className="flex-1 space-y-2">
              <div className="h-3 bg-gray-100 rounded w-48" />
              <div className="h-2 bg-gray-100 rounded w-32" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
