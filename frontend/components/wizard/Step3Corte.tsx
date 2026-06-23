"use client";

import { useState } from "react";
import { Scissors } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";

function fmtMmss(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function Step3Corte() {
  const { fileInfo, corteInicio, corteFim, cfgDuracaoSegmentos, setCorte, nextStep, prevStep } = useWizard();
  const duracao = fileInfo?.duracao ?? null;

  const [inicio, setInicio] = useState(corteInicio);
  const [fim, setFim] = useState(corteFim ?? duracao ?? 0);

  const avancar = () => {
    setCorte(inicio, fim);
    nextStep();
  };

  if (!duracao || duracao <= 0) return <SemDuracao onBack={prevStep} onNext={() => { setCorte(0, 0); nextStep(); }} />;

  const duracaoSel = fim - inicio;
  const nSegs = Math.ceil(duracaoSel / (cfgDuracaoSegmentos * 60));
  const invalido = duracaoSel <= 0;

  return (
    <div>
      <Stepper passo={3} />
      <h1 className="text-2xl font-bold text-gray-800 mb-1">✂️ Recorte do áudio</h1>
      <p className="text-sm text-gray-500 mb-6">Defina o trecho que será transcrito.</p>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <MetricCard label="Duração total" value={fmtMmss(duracao)} />
        <MetricCard label="Segmentos (completo)" value={String(Math.ceil(duracao / (cfgDuracaoSegmentos * 60)))} />
      </div>

      <div className="card mb-4">
        <p className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Scissors size={14} /> Intervalo de transcrição
        </p>
        <RangeSlider min={0} max={duracao} inicio={inicio} fim={fim} setInicio={setInicio} setFim={setFim} />

        <div className="grid grid-cols-3 gap-3 mt-4">
          <MetricCard label="Início" value={fmtMmss(inicio)} />
          <MetricCard label="Fim" value={fmtMmss(fim)} />
          <MetricCard label="Selecionado" value={fmtMmss(duracaoSel)} />
        </div>

        {!invalido && (
          <div className="mt-4 bg-primary/5 border border-primary/20 rounded-xl px-4 py-3 text-sm text-primary font-medium">
            📦 {nSegs} segmento(s) de {cfgDuracaoSegmentos} min serão criados.
          </div>
        )}
        {invalido && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
            O fim deve ser maior que o início.
          </div>
        )}
      </div>

      <WizardNav onBack={prevStep} onNext={avancar} nextDisabled={invalido} />
    </div>
  );
}

function RangeSlider({ min, max, inicio, fim, setInicio, setFim }: {
  min: number; max: number; inicio: number; fim: number;
  setInicio: (v: number) => void; setFim: (v: number) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="label text-xs">Início</label>
        <input type="range" min={min} max={max} value={inicio}
          onChange={(e) => setInicio(Math.min(Number(e.target.value), fim - 1))}
          className="w-full accent-primary" />
      </div>
      <div>
        <label className="label text-xs">Fim</label>
        <input type="range" min={min} max={max} value={fim}
          onChange={(e) => setFim(Math.max(Number(e.target.value), inicio + 1))}
          className="w-full accent-primary" />
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-base font-bold text-gray-800 mt-0.5 font-mono">{value}</p>
    </div>
  );
}

function SemDuracao({ onBack, onNext }: { onBack: () => void; onNext: () => void }) {
  return (
    <div>
      <Stepper passo={3} />
      <h1 className="text-2xl font-bold text-gray-800 mb-6">✂️ Recorte</h1>
      <div className="card mb-6">
        <p className="text-sm text-gray-500">Duração não detectada. O arquivo completo será transcrito.</p>
      </div>
      <WizardNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
