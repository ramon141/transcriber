"use client";

import { useCallback, useState } from "react";
import { FileText, Search } from "lucide-react";
import { buscarTranscricoes, recordToResultado } from "@/lib/api";
import { useWizard } from "@/lib/store";
import { MODELOS } from "@/lib/types";
import type { TranscricaoRecord } from "@/lib/types";
import { useRouter } from "next/navigation";

function fmtData(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function BuscaPage() {
  const [termo, setTermo] = useState("");
  const [modelo, setModelo] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [resultados, setResultados] = useState<TranscricaoRecord[] | null>(null);
  const [buscando, setBuscando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const buscar = useCallback(async () => {
    setBuscando(true);
    setErro(null);
    try {
      const lista = await buscarTranscricoes({
        termo: termo || undefined,
        modelo: modelo || undefined,
        data_inicio: dataInicio || undefined,
        data_fim: dataFim || undefined,
      });
      setResultados(lista);
    } catch {
      setErro("Erro ao buscar. Verifique se o backend está rodando.");
    } finally {
      setBuscando(false);
    }
  }, [termo, modelo, dataInicio, dataFim]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") buscar();
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Busca Avançada</h1>
        <p className="text-sm text-gray-500 mt-0.5">Encontre transcrições por conteúdo, modelo ou data</p>
      </div>

      <div className="card mb-6">
        <FiltroTexto
          value={termo}
          onChange={setTermo}
          onKeyDown={handleKeyDown}
        />

        <div className="grid grid-cols-3 gap-4 mt-4">
          <FiltroModelo value={modelo} onChange={setModelo} />
          <FiltroData label="Data início" value={dataInicio} onChange={setDataInicio} />
          <FiltroData label="Data fim" value={dataFim} onChange={setDataFim} />
        </div>

        <div className="flex justify-end mt-4">
          <button onClick={buscar} disabled={buscando} className="btn-primary">
            <Search size={14} />
            {buscando ? "Buscando..." : "Buscar"}
          </button>
        </div>
      </div>

      {erro && (
        <div className="card mb-4 bg-red-50 border-red-200 text-red-700 text-sm">{erro}</div>
      )}

      {resultados !== null && (
        <ResultadosBusca resultados={resultados} />
      )}
    </div>
  );
}

function FiltroTexto({ value, onChange, onKeyDown }: {
  value: string;
  onChange: (v: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}) {
  return (
    <div>
      <label className="label">Pesquisar no conteúdo</label>
      <div className="relative mt-1">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Palavra-chave na transcrição..."
          className="input pl-9"
        />
      </div>
    </div>
  );
}

function FiltroModelo({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="label">Modelo Whisper</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input mt-1">
        <option value="">Todos</option>
        {MODELOS.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  );
}

function FiltroData({ label, value, onChange }: {
  label: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input mt-1"
      />
    </div>
  );
}

function ResultadosBusca({ resultados }: { resultados: TranscricaoRecord[] }) {
  if (resultados.length === 0) {
    return (
      <div className="card flex flex-col items-center py-12 text-center">
        <Search size={28} className="text-gray-200 mb-3" />
        <p className="text-sm font-semibold text-gray-500">Nenhum resultado encontrado</p>
        <p className="text-xs text-gray-400 mt-1">Tente outros termos ou remova filtros</p>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-gray-400 mb-3">{resultados.length} resultado(s)</p>
      <div className="space-y-3">
        {resultados.map((r) => (
          <CartaoResultado key={r.id} registro={r} />
        ))}
      </div>
    </div>
  );
}

function CartaoResultado({ registro }: { registro: TranscricaoRecord }) {
  const [expandido, setExpandido] = useState(false);
  const { setResults, setStep } = useWizard();
  const router = useRouter();

  const carregarNaWizard = () => {
    setResults(recordToResultado(registro));
    setStep(4);
    router.push("/transcricao");
  };

  return (
    <div className="card hover:border-primary/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <FileText size={16} className="text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-800 text-sm truncate">{registro.nome_arquivo}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {fmtData(registro.created_at)} · {registro.modelo_whisper} · {registro.duracao_total.toFixed(1)} min
            </p>
          </div>
        </div>

        <div className="flex gap-2 shrink-0">
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
