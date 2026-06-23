"use client";

import { useState } from "react";
import type { ResultadoTranscricao } from "@/lib/types";

const CORES_FALANTE: Record<string, string> = {
  "FALANTE 1": "#1f77b4", "FALANTE 2": "#ff7f0e", "FALANTE 3": "#2ca02c",
  "FALANTE 4": "#d62728", "FALANTE 5": "#9467bd", "FALANTE 6": "#8c564b",
  "DESCONHECIDO": "#bcbd22",
};

function corFalante(f: string): string {
  return CORES_FALANTE[f] ?? "#17becf";
}

export function Step4Resultados({ resultado }: { resultado: ResultadoTranscricao }) {
  const [tab, setTab] = useState<"completa" | "falantes" | "segmentos">("completa");
  const { diarizacao_ativada, resumo_falantes, segmentos_com_falantes,
          transcricao_completa, segmentos, from_cache } = resultado;

  return (
    <div>
      {from_cache && (
        <div className="mb-4 px-4 py-2.5 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-600 font-medium">
          🗄️ Resultado carregado do cache do Supabase
        </div>
      )}

      <div className="grid grid-cols-4 gap-3 mb-4">
        <Metric label="Segmentos" value={String(segmentos.length || segmentos_com_falantes.length)} />
        <Metric label="Duração" value={`${resultado.duracao_total.toFixed(1)} min`} />
        <Metric label="Falantes" value={diarizacao_ativada ? String(Object.keys(resumo_falantes).length) : "—"} />
        <Metric label="Tipo" value={diarizacao_ativada ? "Diarizado" : "Simples"} />
      </div>

      <TabBar tab={tab} setTab={setTab} diarizacao={diarizacao_ativada} />

      <div className="card mt-2">
        {tab === "completa" && (
          <TabCompleta transcricao={transcricao_completa} segs={segmentos_com_falantes} diarizacao={diarizacao_ativada} />
        )}
        {tab === "falantes" && diarizacao_ativada && (
          <TabFalantes resumo={resumo_falantes} />
        )}
        {tab === "segmentos" && (
          <TabSegmentos segmentos={segmentos} />
        )}
      </div>
    </div>
  );
}

function TabBar({ tab, setTab, diarizacao }: {
  tab: string; setTab: (t: "completa" | "falantes" | "segmentos") => void; diarizacao: boolean;
}) {
  const tabs: { key: "completa" | "falantes" | "segmentos"; label: string }[] = [
    { key: "completa", label: "📄 Completa" },
    ...(diarizacao ? [{ key: "falantes" as const, label: "👥 Por Falante" }] : []),
    { key: "segmentos", label: "📁 Segmentos" },
  ];
  return (
    <div className="tab-list">
      {tabs.map((t) => (
        <button key={t.key} onClick={() => setTab(t.key)}
          className={`tab ${tab === t.key ? "tab-active" : ""}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

function TabCompleta({ transcricao, segs, diarizacao }: {
  transcricao: string; segs: ResultadoTranscricao["segmentos_com_falantes"]; diarizacao: boolean;
}) {
  if (diarizacao && segs.length > 0) {
    return (
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {segs.map((s, i) => {
          const cor = corFalante(s.falante);
          return (
            <div key={i} className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-sm">
              <span style={{ color: cor }} className="font-bold mr-2">[{s.falante}]</span>
              {s.texto}
            </div>
          );
        })}
      </div>
    );
  }
  return (
    <textarea
      readOnly value={transcricao}
      className="w-full h-80 text-sm text-gray-700 resize-none border-0 outline-none bg-transparent"
    />
  );
}

function TabFalantes({ resumo }: { resumo: ResultadoTranscricao["resumo_falantes"] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="space-y-2">
      {Object.entries(resumo).map(([falante, stats]) => {
        const cor = corFalante(falante);
        const isOpen = open === falante;
        return (
          <div key={falante} className="border border-gray-100 rounded-xl overflow-hidden">
            <button onClick={() => setOpen(isOpen ? null : falante)}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-left">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cor }} />
              <span className="font-medium text-sm text-gray-700">{falante}</span>
              <span className="text-xs text-gray-400 ml-auto">
                {stats.num_falas} falas · {(stats.tempo_total / 60).toFixed(1)} min
              </span>
            </button>
            {isOpen && (
              <div className="px-4 pb-3 space-y-1 border-l-4" style={{ borderColor: cor }}>
                {stats.textos.map((t, i) => (
                  <p key={i} className="text-xs text-gray-600">• {t}</p>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function TabSegmentos({ segmentos }: { segmentos: ResultadoTranscricao["segmentos"] }) {
  const [open, setOpen] = useState<number | null>(null);
  if (segmentos.length === 0) {
    return <p className="text-sm text-gray-400 text-center py-4">Segmentos não disponíveis (resultado do cache).</p>;
  }
  return (
    <div className="space-y-1.5 max-h-80 overflow-y-auto">
      {segmentos.map((s) => (
        <div key={s.numero} className="border border-gray-100 rounded-xl overflow-hidden">
          <button onClick={() => setOpen(open === s.numero ? null : s.numero)}
            className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 text-left">
            <span className="text-xs font-mono text-gray-400">#{String(s.numero).padStart(2, "0")}</span>
            <span className="text-xs text-gray-500">{s.duracao.toFixed(1)}s</span>
            <span className="text-sm text-gray-700 truncate">{s.texto.slice(0, 60)}...</span>
          </button>
          {open === s.numero && (
            <div className="px-4 pb-3 text-sm text-gray-600">{s.texto}</div>
          )}
        </div>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
    </div>
  );
}
