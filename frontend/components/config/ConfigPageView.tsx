"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { getConfigStatus } from "@/lib/api";
import type { ConfigStatus } from "@/lib/types";
import { ConfigPanel } from "./ConfigPanel";

export function ConfigPageView() {
  const [status, setStatus] = useState<ConfigStatus | null>(null);

  useEffect(() => {
    getConfigStatus()
      .then(setStatus)
      .catch(() => setStatus({ conexao_ok: false, hf_ok: false, notion_ok: false }));
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Configurações</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Credenciais de conexão e integrações do sistema.
        </p>
      </div>

      {status === null ? (
        <div className="grid place-items-center py-16 text-gray-400">
          <Loader2 size={24} className="animate-spin" />
        </div>
      ) : (
        <ConfigPanel conexaoOk={status.conexao_ok} onStatusChange={setStatus} />
      )}
    </div>
  );
}
