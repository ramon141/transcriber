"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, EyeOff, Loader2, Plug } from "lucide-react";
import {
  getIntegracoes,
  IntegracoesInvalidas,
  salvarIntegracoes,
} from "@/lib/api";
import type { CamposErroIntegracoes } from "@/lib/types";

interface Props {
  habilitado: boolean;
  onSalvo: () => void;
}

const SEM_ERROS: CamposErroIntegracoes = {};

export function IntegracoesForm({ habilitado, onSalvo }: Props) {
  const [hfToken, setHfToken] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionParent, setNotionParent] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [erroCampo, setErroCampo] = useState<CamposErroIntegracoes>(SEM_ERROS);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    if (!habilitado) return;
    getIntegracoes()
      .then((c) => {
        setHfToken(c.hf_token);
        setNotionToken(c.notion_token);
        setNotionParent(c.notion_parent_id);
      })
      .catch(() => {
        /* ignora */
      });
  }, [habilitado]);

  const salvar = useCallback(async () => {
    setSalvando(true);
    setErro(null);
    setErroCampo(SEM_ERROS);
    setOk(false);
    try {
      await salvarIntegracoes({
        hf_token: hfToken.trim() || undefined,
        notion_token: notionToken.trim() || undefined,
        notion_parent_id: notionParent.trim() || undefined,
      });
      setOk(true);
      onSalvo();
    } catch (e) {
      if (e instanceof IntegracoesInvalidas) {
        setErroCampo(e.campos);
      } else {
        setErro(e instanceof Error ? e.message : "Falha ao salvar integrações.");
      }
    } finally {
      setSalvando(false);
    }
  }, [hfToken, notionToken, notionParent, onSalvo]);

  return (
    <div className={`card ${habilitado ? "" : "opacity-50 pointer-events-none"}`}>
      <div className="flex items-center gap-2 mb-1">
        <Plug size={18} className="text-primary" />
        <h2 className="text-lg font-bold text-gray-800">Integrações</h2>
      </div>
      <p className="text-sm text-gray-500 mb-5">
        Opcional. Hugging Face (diarização) e Notion (envio de transcrições).
        {!habilitado && " Configure a conexão primeiro."}
      </p>

      <Campo
        label="HF_TOKEN"
        value={hfToken}
        onChange={setHfToken}
        placeholder="hf_..."
        secret
        erro={erroCampo.HF_TOKEN}
      />
      <Campo
        label="NOTION_TOKEN"
        value={notionToken}
        onChange={setNotionToken}
        placeholder="ntn_..."
        secret
        erro={erroCampo.NOTION_TOKEN}
      />
      <Campo
        label="NOTION_PARENT_ID"
        value={notionParent}
        onChange={setNotionParent}
        placeholder="Cole o link da página do Notion ou o ID"
        erro={erroCampo.NOTION_PARENT_ID}
      />

      {erro && (
        <div className="mt-3 rounded-xl bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
          {erro}
        </div>
      )}
      {ok && !erro && (
        <div className="mt-3 rounded-xl bg-green-50 border border-green-200 px-4 py-2.5 text-sm text-green-700">
          Integrações salvas.
        </div>
      )}

      <div className="flex justify-end mt-5">
        <button onClick={salvar} disabled={!habilitado || salvando} className="btn-primary">
          {salvando ? <Loader2 size={14} className="animate-spin" /> : <Plug size={14} />}
          {salvando ? "Salvando..." : "Salvar integrações"}
        </button>
      </div>
    </div>
  );
}

interface CampoProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  secret?: boolean;
  erro?: string;
}

function Campo({ label, value, onChange, placeholder, secret, erro }: CampoProps) {
  const [revelar, setRevelar] = useState(false);

  return (
    <div className="mb-4">
      <label className="label">{label}</label>
      <div className="relative">
        <input
          type={secret && !revelar ? "password" : "text"}
          className={`input pr-12 ${erro ? "border-red-300 focus:border-red-400" : ""}`}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        {secret && (
          <button
            type="button"
            onClick={() => setRevelar((v) => !v)}
            aria-label={revelar ? "Ocultar" : "Mostrar"}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {revelar ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {erro && <p className="mt-1 text-xs text-red-600">{erro}</p>}
    </div>
  );
}
