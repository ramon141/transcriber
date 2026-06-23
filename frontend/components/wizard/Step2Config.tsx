"use client";

import { useEffect, useState } from "react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";
import { getConfigStatus } from "@/lib/api";
import { MODELOS, MODELOS_INFO, type ModeloNome } from "@/lib/types";

export function Step2Config() {
  const { cfgModeloNome, cfgDuracaoSegmentos, cfgDiarizar, setCfg, nextStep, prevStep } = useWizard();

  const [modelo, setModelo] = useState<ModeloNome>(cfgModeloNome);
  const [duracao, setDuracao] = useState(cfgDuracaoSegmentos);
  const [diarizar, setDiarizar] = useState(cfgDiarizar);
  const [hfOk, setHfOk] = useState(false);

  useEffect(() => {
    getConfigStatus()
      .then((s) => {
        setHfOk(s.hf_ok);
        if (!s.hf_ok) setDiarizar(false);
      })
      .catch(() => setHfOk(false));
  }, []);

  const info = MODELOS_INFO[modelo];

  const avancar = () => {
    setCfg({ cfgModeloNome: modelo, cfgDuracaoSegmentos: duracao, cfgDiarizar: diarizar });
    nextStep();
  };

  return (
    <div>
      <Stepper passo={2} />
      <h1 className="text-2xl font-bold text-gray-800 mb-1">⚙️ Configurações</h1>
      <p className="text-sm text-gray-500 mb-6">Escolha o modelo, duração dos segmentos e identificação de falantes.</p>

      <ModelSelector modelo={modelo} setModelo={setModelo} info={info} />
      <SegmentosInput duracao={duracao} setDuracao={setDuracao} />
      <DiarizacaoToggle diarizar={diarizar} setDiarizar={setDiarizar} hfOk={hfOk} />

      <WizardNav onBack={prevStep} onNext={avancar} nextLabel="Avançar →" />
    </div>
  );
}

function ModelSelector({ modelo, setModelo, info }: {
  modelo: ModeloNome;
  setModelo: (m: ModeloNome) => void;
  info: (typeof MODELOS_INFO)[ModeloNome];
}) {
  return (
    <div className="card mb-4">
      <p className="text-sm font-semibold text-gray-700 mb-3">Modelo Whisper</p>
      <div className="flex gap-1 flex-wrap mb-4">
        {MODELOS.map((m) => (
          <button
            key={m}
            onClick={() => setModelo(m)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              m === modelo
                ? "bg-gradient-primary text-white shadow-sm"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {m}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Metric label="Qualidade" value={info.qualidade} />
        <Metric label="Velocidade" value={info.velocidade} />
        <Metric label="Tempo est." value={info.tempo_estimado} />
      </div>
      <p className="text-xs text-gray-400 mt-3 italic">{info.descricao}</p>
    </div>
  );
}

function SegmentosInput({ duracao, setDuracao }: { duracao: number; setDuracao: (n: number) => void }) {
  return (
    <div className="card mb-4">
      <p className="text-sm font-semibold text-gray-700 mb-3">Duração dos segmentos</p>
      <div className="flex items-center gap-3">
        <input
          type="number"
          min={1}
          max={10}
          value={duracao}
          onChange={(e) => setDuracao(Math.max(1, Math.min(10, Number(e.target.value))))}
          className="input w-24"
        />
        <span className="text-sm text-gray-500">minutos por segmento</span>
      </div>
      <p className="text-xs text-gray-400 mt-2">Segmentos menores usam menos memória.</p>
    </div>
  );
}

function DiarizacaoToggle({
  diarizar,
  setDiarizar,
  hfOk,
}: {
  diarizar: boolean;
  setDiarizar: (v: boolean) => void;
  hfOk: boolean;
}) {
  return (
    <div className="card mb-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-700">Identificação de falantes</p>
          {hfOk ? (
            <p className="text-xs text-gray-400 mt-0.5">Separa a transcrição por falante.</p>
          ) : (
            <p className="text-xs text-amber-600 mt-0.5">
              HF_TOKEN não configurado.{" "}
              <a href="/configuracoes" className="underline hover:text-amber-800">
                Configurar em Integrações
              </a>
            </p>
          )}
        </div>
        <button
          onClick={() => hfOk && setDiarizar(!diarizar)}
          disabled={!hfOk}
          aria-disabled={!hfOk}
          className={`w-11 h-6 rounded-full transition-all relative ${
            !hfOk
              ? "bg-gray-100 cursor-not-allowed"
              : diarizar
              ? "bg-gradient-primary"
              : "bg-gray-200"
          }`}
        >
          <span
            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all ${
              diarizar && hfOk ? "left-5" : "left-0.5"
            }`}
          />
        </button>
      </div>
      {diarizar && hfOk && (
        <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 mt-3">
          ⚠️ Diarização é mais lenta. GPU recomendada.
        </p>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-sm font-bold text-gray-700 mt-0.5">{value}</p>
    </div>
  );
}
