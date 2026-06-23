"use client";

import { useCallback, useState } from "react";
import { getConfigStatus } from "@/lib/api";
import type { ConfigStatus } from "@/lib/types";
import { ConexaoForm } from "./ConexaoForm";
import { IntegracoesForm } from "./IntegracoesForm";
import { AjudaConexao, AjudaIntegracoes } from "./Ajuda";

interface Props {
  conexaoOk: boolean;
  onStatusChange: (status: ConfigStatus) => void;
}

export function ConfigPanel({ conexaoOk, onStatusChange }: Props) {
  const [atualizando, setAtualizando] = useState(false);

  const recarregarStatus = useCallback(async () => {
    setAtualizando(true);
    try {
      const status = await getConfigStatus();
      onStatusChange(status);
    } finally {
      setAtualizando(false);
    }
  }, [onStatusChange]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <AjudaConexao />
        <ConexaoForm onSalvo={recarregarStatus} />
      </div>
      <div>
        <AjudaIntegracoes />
        <IntegracoesForm habilitado={conexaoOk} onSalvo={recarregarStatus} />
      </div>
      {atualizando && (
        <p className="text-xs text-gray-400 text-center">Atualizando status...</p>
      )}
    </div>
  );
}
