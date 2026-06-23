"use client";

import { useCallback, useState } from "react";
import { Play, RefreshCw } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { Step4Resultados } from "./Step4Resultados";
import { useWizard } from "@/lib/store";
import { useSSE } from "@/hooks/useSSE";
import { buscarCache, salvarTranscricao, urlProcessar } from "@/lib/api";
import type { ResultadoTranscricao } from "@/lib/types";

export function Step4Processar() {
  const store = useWizard();
  const { fileInfo, cfgModeloNome, cfgDuracaoSegmentos, cfgDiarizar,
          corteInicio, corteFim, results, setResults, clearResults, prevStep, setStep } = store;

  const [cacheInfo, setCacheInfo] = useState<string | null>(null);
  const [cacheData, setCacheData] = useState<ResultadoTranscricao | null>(null);

  const onComplete = useCallback(
    (data: ResultadoTranscricao) => {
      setResults(data);
      if (fileInfo && data.sucesso) {
        salvarTranscricao({
          hash_arquivo: fileInfo.hash_arquivo,
          nome_arquivo: fileInfo.nome,
          transcricao_completa: data.transcricao_completa,
          segmentos_com_falantes: data.segmentos_com_falantes,
          resumo_falantes: data.resumo_falantes as Record<string, unknown>,
          diarizacao_ativada: data.diarizacao_ativada,
          modelo_whisper: cfgModeloNome,
          duracao_total: data.duracao_total,
        }).catch(() => {});
      }
    },
    [fileInfo, cfgModeloNome, setResults]
  );

  const sse = useSSE(onComplete);

  const iniciar = useCallback(async () => {
    if (!fileInfo) return;
    const url = urlProcessar({
      file_id: fileInfo.file_id,
      modelo_nome: cfgModeloNome,
      duracao_segmentos: cfgDuracaoSegmentos,
      diarizar: cfgDiarizar,
      tempo_inicio: corteInicio,
      tempo_fim: corteFim,
      hash_arquivo: fileInfo.hash_arquivo,
      nome_arquivo: fileInfo.nome,
    });
    sse.start(url);
  }, [fileInfo, cfgModeloNome, cfgDuracaoSegmentos, cfgDiarizar, corteInicio, corteFim, sse]);

  const verificarCache = useCallback(async () => {
    if (!fileInfo) return;
    const cached = await buscarCache(fileInfo.hash_arquivo);
    if (cached) {
      const resultado: ResultadoTranscricao = {
        sucesso: true,
        transcricao_completa: cached.transcricao_completa,
        segmentos: [],
        segmentos_com_falantes: cached.segmentos_com_falantes,
        resumo_falantes: cached.resumo_falantes,
        diarizacao_ativada: cached.diarizacao_ativada,
        duracao_total: cached.duracao_total,
        arquivo_completo: "", arquivo_detalhado: "", pasta_saida: "",
        from_cache: true,
      };
      setCacheInfo(`Cache: ${cached.nome_arquivo} · ${cached.modelo_whisper}`);
      setCacheData(resultado);
    }
  }, [fileInfo]);

  if (results?.sucesso) {
    return (
      <div>
        <Stepper passo={4} />
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-800">✅ Transcrição concluída</h1>
          <button onClick={clearResults} className="btn-secondary text-xs py-1.5 px-3">
            <RefreshCw size={12} /> Novo
          </button>
        </div>
        <Step4Resultados resultado={results} />
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <button onClick={prevStep} className="btn-secondary"><span>← Voltar</span></button>
          <button onClick={() => setStep(5)} className="btn-primary">📝 Enviar ao Notion →</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Stepper passo={4} />
      <h1 className="text-2xl font-bold text-gray-800 mb-1">▶️ Processamento</h1>
      <p className="text-sm text-gray-500 mb-6">Inicie a transcrição quando estiver pronto.</p>

      <ConfigResumo />

      {!sse.running && !cacheInfo && (
        <CacheCheck onVerificar={verificarCache} />
      )}

      {cacheInfo && cacheData && (
        <CacheCard info={cacheInfo} onUsar={() => setResults(cacheData)} />
      )}

      {sse.running && <ProgressCard sse={sse} />}

      {sse.error && (
        <div className="card mb-4 bg-red-50 border-red-200 text-red-700 text-sm">{sse.error}</div>
      )}

      {!sse.running && (
        <WizardNav
          onBack={prevStep}
          onNext={iniciar}
          nextLabel="🚀 Iniciar Transcrição"
        />
      )}
    </div>
  );
}

function ConfigResumo() {
  const { fileInfo, cfgModeloNome, cfgDuracaoSegmentos, cfgDiarizar } = useWizard();
  return (
    <div className="grid grid-cols-4 gap-3 mb-6">
      {[
        { label: "Arquivo", value: fileInfo?.nome ?? "—" },
        { label: "Modelo", value: cfgModeloNome },
        { label: "Segmentos", value: `${cfgDuracaoSegmentos} min` },
        { label: "Falantes", value: cfgDiarizar ? "Sim" : "Não" },
      ].map((m) => (
        <div key={m.label} className="metric-card">
          <p className="metric-label">{m.label}</p>
          <p className="metric-value text-sm truncate">{m.value}</p>
        </div>
      ))}
    </div>
  );
}

function CacheCheck({ onVerificar }: { onVerificar: () => void }) {
  return (
    <div className="card mb-4 flex items-center justify-between">
      <p className="text-sm text-gray-600">Verificar se este arquivo já foi transcrito antes?</p>
      <button onClick={onVerificar} className="btn-secondary text-xs py-1.5 px-3">🗄️ Verificar cache</button>
    </div>
  );
}

function CacheCard({ info, onUsar }: { info: string; onUsar: () => void }) {
  return (
    <div className="card mb-4 bg-blue-50 border-blue-100">
      <div className="flex items-center justify-between">
        <p className="text-sm text-blue-700 font-medium">🗄️ {info}</p>
        <button onClick={onUsar} className="btn-primary text-xs py-1.5 px-3">✅ Usar cache</button>
      </div>
    </div>
  );
}

function ProgressCard({ sse }: { sse: ReturnType<typeof useSSE> }) {
  return (
    <div className="card mb-4">
      <div className="flex items-center gap-2 mb-3">
        <Play size={14} className="text-primary animate-pulse" />
        <p className="text-sm font-semibold text-gray-700">Processando...</p>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-primary rounded-full transition-all duration-300"
          style={{ width: `${Math.round(sse.progress * 100)}%` }}
        />
      </div>
      {sse.status && <p className="text-xs text-gray-500">{sse.status}</p>}
      {sse.preview && <p className="text-xs text-gray-400 mt-1 italic truncate">{sse.preview}</p>}
    </div>
  );
}
