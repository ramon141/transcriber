"use client";

import { useCallback, useState } from "react";
import { Upload, FileAudio, AlertCircle } from "lucide-react";
import { clsx } from "clsx";
import { Stepper } from "./Stepper";
import { useWizard } from "@/lib/store";
import { uploadArquivo } from "@/lib/api";

const TIPOS = ".mp3,.wav,.m4a,.aac,.flac,.ogg,.wma,.mp4,.avi,.mov,.mkv,.flv,.wmv,.webm,.m4v,.mpg,.mpeg";
const MAX_MB = 500;

export function Step1Upload() {
  const { setFileInfo, nextStep } = useWizard();
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const processar = useCallback(
    async (file: File) => {
      setErro(null);
      const mb = file.size / 1024 / 1024;
      if (mb > MAX_MB) {
        setErro(`Arquivo muito grande (${mb.toFixed(1)} MB). Limite: ${MAX_MB} MB.`);
        return;
      }
      setLoading(true);
      try {
        const info = await uploadArquivo(file);
        setFileInfo(info);
        nextStep();
      } catch (e) {
        setErro(e instanceof Error ? e.message : "Erro no upload");
      } finally {
        setLoading(false);
      }
    },
    [setFileInfo, nextStep]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) processar(file);
    },
    [processar]
  );

  const onInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processar(file);
    },
    [processar]
  );

  return (
    <div>
      <Stepper passo={1} />
      <PageTitle title="📁 Selecione seu arquivo" sub="Formatos suportados: MP3, WAV, M4A, AAC, FLAC, OGG · MP4, AVI, MOV, MKV e mais." />

      <label
        className={clsx(
          "card flex flex-col items-center justify-center gap-4 cursor-pointer min-h-[220px]",
          "border-2 border-dashed transition-all duration-200",
          dragging ? "border-primary bg-primary/5" : "border-gray-200 hover:border-primary/50",
          loading && "opacity-60 pointer-events-none"
        )}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input type="file" accept={TIPOS} className="sr-only" onChange={onInput} />
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
          {loading ? (
            <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          ) : (
            <Upload size={28} className="text-primary" />
          )}
        </div>
        <div className="text-center">
          <p className="font-semibold text-gray-700">
            {loading ? "Enviando arquivo..." : "Arraste aqui ou clique para selecionar"}
          </p>
          <p className="text-sm text-gray-400 mt-1">Tamanho máximo: {MAX_MB} MB</p>
        </div>
      </label>

      {erro && (
        <div className="mt-4 flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      <FormatsInfo />
    </div>
  );
}

function FormatsInfo() {
  return (
    <div className="mt-4 card">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Formatos suportados</p>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-sm font-medium text-gray-600 flex items-center gap-1.5">
            <FileAudio size={14} /> Áudio
          </p>
          <p className="text-xs text-gray-400 mt-1">MP3 · WAV · M4A · AAC · FLAC · OGG · WMA</p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-600">🎬 Vídeo</p>
          <p className="text-xs text-gray-400 mt-1">MP4 · AVI · MOV · MKV · FLV · WMV · WEBM · M4V</p>
        </div>
      </div>
    </div>
  );
}

function PageTitle({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
      <p className="text-sm text-gray-500 mt-1">{sub}</p>
    </div>
  );
}
