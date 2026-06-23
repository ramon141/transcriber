"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Scissors, Play, Pause, BookmarkCheck } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";
import { DualRangeSlider } from "@/components/ui/DualRangeSlider";

function fmtMmss(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function Step3Corte() {
  const { fileInfo, rawFile, corteInicio, corteFim, cfgDuracaoSegmentos, setCorte, nextStep, prevStep } = useWizard();
  const duracao = fileInfo?.duracao ?? null;

  const [inicio, setInicio] = useState(corteInicio);
  const [fim, setFim] = useState(corteFim ?? duracao ?? 0);

  const avancar = () => {
    setCorte(inicio, fim);
    nextStep();
  };

  if (!duracao || duracao <= 0) {
    return <SemDuracao onBack={prevStep} onNext={() => { setCorte(0, 0); nextStep(); }} />;
  }

  const duracaoSel = fim - inicio;
  const nSegs = Math.ceil(duracaoSel / (cfgDuracaoSegmentos * 60));
  const invalido = duracaoSel <= 0;

  return (
    <div>
      <Stepper passo={3} />
      <h1 className="text-2xl font-bold text-gray-800 mb-1">✂️ Recorte do áudio</h1>
      <p className="text-sm text-gray-500 mb-6">
        Use o player para navegar e marque o trecho que será transcrito.
      </p>

      {rawFile && (
        <MediaPlayer
          file={rawFile}
          tipo={fileInfo?.tipo ?? "audio"}
          duracao={duracao}
          inicio={inicio}
          fim={fim}
          setInicio={setInicio}
          setFim={setFim}
        />
      )}

      <div className="card mb-4">
        <p className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Scissors size={14} /> Ajuste fino do intervalo
        </p>
        <RangeSlider min={0} max={duracao} inicio={inicio} fim={fim} setInicio={setInicio} setFim={setFim} />

        <div className="grid grid-cols-4 gap-3 mt-4">
          <MetricCard label="Início" value={fmtMmss(inicio)} />
          <MetricCard label="Fim" value={fmtMmss(fim)} />
          <MetricCard label="Duração selecionada" value={fmtMmss(duracaoSel)} />
          <MetricCard label="Segmentos" value={invalido ? "—" : String(nSegs)} />
        </div>

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

function MediaPlayer({ file, tipo, duracao, inicio, fim, setInicio, setFim }: {
  file: File;
  tipo: string;
  duracao: number;
  inicio: number;
  fim: number;
  setInicio: (v: number) => void;
  setFim: (v: number) => void;
}) {
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [src, setSrc] = useState<string>("");
  const isVideo = tipo.startsWith("video");

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const onTimeUpdate = useCallback(() => {
    if (mediaRef.current) setCurrentTime(mediaRef.current.currentTime);
  }, []);

  const onPlayPause = () => {
    const el = mediaRef.current;
    if (!el) return;
    if (el.paused) { el.play(); setPlaying(true); }
    else { el.pause(); setPlaying(false); }
  };

  const seekTo = (t: number) => {
    if (mediaRef.current) mediaRef.current.currentTime = t;
    setCurrentTime(t);
  };

  const marcarInicio = () => setInicio(Math.min(Math.floor(currentTime), fim - 1));
  const marcarFim = () => setFim(Math.max(Math.ceil(currentTime), inicio + 1));

  if (!src) return null;

  return (
    <div className="card mb-4">
      <p className="text-sm font-semibold text-gray-700 mb-3">🎵 Player</p>

      {isVideo ? (
        <video
          ref={mediaRef as React.RefObject<HTMLVideoElement>}
          src={src}
          className="w-full rounded-xl bg-black mb-3 max-h-52"
          onTimeUpdate={onTimeUpdate}
          onEnded={() => setPlaying(false)}
        />
      ) : (
        <audio
          ref={mediaRef as React.RefObject<HTMLAudioElement>}
          src={src}
          className="hidden"
          onTimeUpdate={onTimeUpdate}
          onEnded={() => setPlaying(false)}
        />
      )}

      <ProgressBar
        duracao={duracao}
        currentTime={currentTime}
        inicio={inicio}
        fim={fim}
        onSeek={seekTo}
      />

      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-2">
          <button onClick={onPlayPause} className="btn-primary py-2 px-4">
            {playing ? <Pause size={14} /> : <Play size={14} />}
            {playing ? "Pausar" : "Play"}
          </button>
          <span className="text-xs font-mono text-gray-500">
            {fmtMmss(currentTime)} / {fmtMmss(duracao)}
          </span>
        </div>

        <div className="flex gap-2">
          <button onClick={marcarInicio} className="btn-secondary text-xs py-1.5 px-3 gap-1.5">
            <BookmarkCheck size={12} className="text-green-500" />
            Marcar início ({fmtMmss(currentTime)})
          </button>
          <button onClick={marcarFim} className="btn-secondary text-xs py-1.5 px-3 gap-1.5">
            <BookmarkCheck size={12} className="text-red-500" />
            Marcar fim ({fmtMmss(currentTime)})
          </button>
        </div>
      </div>

      <SelectionInfo inicio={inicio} fim={fim} duracao={duracao} onSeekInicio={() => seekTo(inicio)} onSeekFim={() => seekTo(fim)} />
    </div>
  );
}

function ProgressBar({ duracao, currentTime, inicio, fim, onSeek }: {
  duracao: number;
  currentTime: number;
  inicio: number;
  fim: number;
  onSeek: (t: number) => void;
}) {
  const barRef = useRef<HTMLDivElement>(null);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!barRef.current) return;
    const rect = barRef.current.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    onSeek(Math.max(0, Math.min(duracao, ratio * duracao)));
  };

  const pct = (v: number) => `${(v / duracao) * 100}%`;

  return (
    <div
      ref={barRef}
      onClick={handleClick}
      className="relative h-6 bg-gray-100 rounded-full cursor-pointer group"
    >
      <div
        className="absolute top-0 h-full bg-primary/20 rounded-full"
        style={{ left: pct(inicio), width: pct(fim - inicio) }}
      />
      <div
        className="absolute top-0 h-full bg-gradient-primary rounded-full opacity-80"
        style={{ width: pct(currentTime) }}
      />
      <div
        className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-primary rounded-full shadow-md transition-all"
        style={{ left: `calc(${pct(currentTime)} - 6px)` }}
      />
      <span
        className="absolute -top-5 text-[10px] font-mono text-green-600 -translate-x-1/2"
        style={{ left: pct(inicio) }}
      >
        {fmtMmss(inicio)}
      </span>
      <span
        className="absolute -top-5 text-[10px] font-mono text-red-500 -translate-x-1/2"
        style={{ left: pct(fim) }}
      >
        {fmtMmss(fim)}
      </span>
    </div>
  );
}

function SelectionInfo({ inicio, fim, duracao, onSeekInicio, onSeekFim }: {
  inicio: number; fim: number; duracao: number;
  onSeekInicio: () => void; onSeekFim: () => void;
}) {
  return (
    <div className="flex items-center gap-3 mt-4 text-xs text-gray-500">
      <button onClick={onSeekInicio} className="flex items-center gap-1 hover:text-green-600 transition-colors">
        <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
        Início: {fmtMmss(inicio)}
      </button>
      <span>→</span>
      <button onClick={onSeekFim} className="flex items-center gap-1 hover:text-red-500 transition-colors">
        <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
        Fim: {fmtMmss(fim)}
      </button>
      <span className="ml-auto">
        {((fim - inicio) / duracao * 100).toFixed(0)}% do arquivo
      </span>
    </div>
  );
}

function RangeSlider({ min, max, inicio, fim, setInicio, setFim }: {
  min: number; max: number; inicio: number; fim: number;
  setInicio: (v: number) => void; setFim: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between mb-1 px-2.5">
        <span className="text-xs font-mono text-green-600 font-semibold">▶ {fmtMmss(inicio)}</span>
        <span className="text-xs font-mono text-red-500 font-semibold">{fmtMmss(fim)} ◀</span>
      </div>
      <DualRangeSlider
        min={min}
        max={max}
        inicio={inicio}
        fim={fim}
        setInicio={setInicio}
        setFim={setFim}
        step={1}
      />
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
