"use client";

import { useState } from "react";
import Image from "next/image";
import { ArrowRight, Check } from "lucide-react";
import { ConexaoForm } from "./ConexaoForm";
import { IntegracoesForm } from "./IntegracoesForm";
import { AjudaConexao, AjudaIntegracoes } from "./Ajuda";

interface Props {
  onConcluir: () => void;
}

const PASSOS = ["Conexão", "Integrações"] as const;

export function OnboardingWizard({ onConcluir }: Props) {
  const [passo, setPasso] = useState(1);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-2xl px-8 py-10">
        <Cabecalho />
        <Stepper passo={passo} />

        {passo === 1 ? (
          <div className="mt-6">
            <AjudaConexao />
            <ConexaoForm onSalvo={() => setPasso(2)} />
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-4">
            <AjudaIntegracoes />
            <IntegracoesForm habilitado onSalvo={() => undefined} />
            <div className="flex justify-between">
              <button onClick={onConcluir} className="btn-secondary">
                Pular por enquanto
              </button>
              <button onClick={onConcluir} className="btn-primary">
                <Check size={14} />
                Concluir e entrar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Cabecalho() {
  return (
    <div className="flex items-center gap-3 mb-6">
      <Image
        src="/apple-touch-icon.png"
        alt="Transcriber"
        width={44}
        height={44}
        className="rounded-xl shadow-lg shadow-primary/40"
        priority
      />
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Bem-vindo ao Transcriber</h1>
        <p className="text-sm text-gray-500">Configuração inicial em 2 etapas.</p>
      </div>
    </div>
  );
}

function Stepper({ passo }: { passo: number }) {
  return (
    <div className="flex items-center justify-center gap-3">
      {PASSOS.map((rotulo, i) => {
        const numero = i + 1;
        const ativo = numero === passo;
        const concluido = numero < passo;
        return (
          <div key={rotulo} className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                  ativo
                    ? "bg-gradient-primary text-white"
                    : concluido
                      ? "bg-green-500 text-white"
                      : "bg-gray-200 text-gray-500"
                }`}
              >
                {concluido ? <Check size={14} /> : numero}
              </span>
              <span
                className={`text-sm font-medium ${
                  ativo ? "text-gray-800" : "text-gray-400"
                }`}
              >
                {rotulo}
              </span>
            </div>
            {i < PASSOS.length - 1 && <ArrowRight size={16} className="text-gray-300" />}
          </div>
        );
      })}
    </div>
  );
}
