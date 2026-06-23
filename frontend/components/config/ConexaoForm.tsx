"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Database, Eye, EyeOff, Loader2 } from "lucide-react";
import { getConexao, salvarConexao } from "@/lib/api";

interface Props {
  onSalvo: () => void;
}

export function ConexaoForm({ onSalvo }: Props) {
  const [supabaseUrl, setSupabaseUrl] = useState("");
  const [supabaseKey, setSupabaseKey] = useState("");
  const [databaseUrl, setDatabaseUrl] = useState("");
  const [jaConfigurado, setJaConfigurado] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    getConexao()
      .then((c) => {
        setSupabaseUrl(c.supabase_url);
        setSupabaseKey(c.supabase_key);
        setDatabaseUrl(c.database_url);
        setJaConfigurado(Boolean(c.supabase_key || c.database_url));
      })
      .catch(() => {
        /* sem conexão ainda */
      });
  }, []);

  const salvar = useCallback(async () => {
    setSalvando(true);
    setErro(null);
    setOk(false);
    try {
      await salvarConexao({
        supabase_url: supabaseUrl.trim(),
        supabase_key: supabaseKey.trim(),
        database_url: databaseUrl.trim(),
      });
      setOk(true);
      setJaConfigurado(true);
      onSalvo();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao validar credenciais.");
    } finally {
      setSalvando(false);
    }
  }, [supabaseUrl, supabaseKey, databaseUrl, onSalvo]);

  const podeSalvar =
    Boolean(supabaseUrl.trim() && supabaseKey.trim() && databaseUrl.trim()) &&
    !salvando;

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-1">
        <Database size={18} className="text-primary" />
        <h2 className="text-lg font-bold text-gray-800">Conexão com o banco</h2>
        {jaConfigurado && (
          <span className="ml-1 inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
            <Check size={12} />
            Configurado
          </span>
        )}
      </div>
      <p className="text-sm text-gray-500 mb-5">
        As credenciais são testadas antes de salvar.
      </p>

      <Campo
        label="SUPABASE_URL"
        value={supabaseUrl}
        onChange={setSupabaseUrl}
        placeholder="https://xxxx.supabase.co"
      />
      <Campo
        label="SUPABASE_KEY"
        value={supabaseKey}
        onChange={setSupabaseKey}
        placeholder="sb_publishable_..."
        secret
      />
      <Campo
        label="DATABASE_URL"
        value={databaseUrl}
        onChange={setDatabaseUrl}
        placeholder="postgresql://postgres...pooler.supabase.com:6543/postgres"
        secret
      />

      {erro && (
        <div className="mt-3 rounded-xl bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
          {erro}
        </div>
      )}
      {ok && !erro && (
        <div className="mt-3 rounded-xl bg-green-50 border border-green-200 px-4 py-2.5 text-sm text-green-700">
          Conexão validada e salva com sucesso.
        </div>
      )}

      <div className="flex justify-end mt-5">
        <button onClick={salvar} disabled={!podeSalvar} className="btn-primary">
          {salvando ? <Loader2 size={14} className="animate-spin" /> : <Database size={14} />}
          {salvando ? "Testando conexão..." : "Testar e salvar"}
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
}

function Campo({ label, value, onChange, placeholder, secret }: CampoProps) {
  const [revelar, setRevelar] = useState(false);

  return (
    <div className="mb-4">
      <label className="label">{label}</label>
      <div className="relative">
        <input
          type={secret && !revelar ? "password" : "text"}
          className="input pr-12"
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
    </div>
  );
}
