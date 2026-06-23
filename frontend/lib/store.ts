"use client";

import { create } from "zustand";
import type { FileInfo, ModeloNome, ResultadoTranscricao } from "./types";

interface WizardState {
  step: number;
  fileInfo: FileInfo | null;
  rawFile: File | null;
  cfgModeloNome: ModeloNome;
  cfgDuracaoSegmentos: number;
  cfgDiarizar: boolean;
  corteInicio: number;
  corteFim: number | null;
  processing: boolean;
  results: ResultadoTranscricao | null;

  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setFileInfo: (info: FileInfo, raw: File) => void;
  setCfg: (cfg: Partial<Pick<WizardState, "cfgModeloNome" | "cfgDuracaoSegmentos" | "cfgDiarizar">>) => void;
  setCorte: (inicio: number, fim: number) => void;
  setProcessing: (v: boolean) => void;
  setResults: (r: ResultadoTranscricao) => void;
  clearResults: () => void;
  reset: () => void;
}

export const useWizard = create<WizardState>((set) => ({
  step: 1,
  fileInfo: null,
  rawFile: null,
  cfgModeloNome: "base",
  cfgDuracaoSegmentos: 4,
  cfgDiarizar: true,
  corteInicio: 0,
  corteFim: null,
  processing: false,
  results: null,

  setStep: (step) => set({ step }),
  nextStep: () => set((s) => ({ step: s.step + 1 })),
  prevStep: () => set((s) => ({ step: Math.max(1, s.step - 1) })),
  setFileInfo: (info, raw) =>
    set({
      fileInfo: info,
      rawFile: raw,
      corteInicio: 0,
      corteFim: info.duracao ?? null,
    }),
  setCfg: (cfg) => set(cfg),
  setCorte: (inicio, fim) => set({ corteInicio: inicio, corteFim: fim }),
  setProcessing: (v) => set({ processing: v }),
  setResults: (r) => set({ results: r }),
  clearResults: () => set({ results: null }),
  reset: () =>
    set({
      step: 1,
      fileInfo: null,
      rawFile: null,
      corteInicio: 0,
      corteFim: null,
      processing: false,
      results: null,
    }),
}));
