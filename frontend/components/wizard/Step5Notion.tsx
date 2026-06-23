"use client";

import { useCallback, useEffect, useState } from "react";
import { BookOpen, Plus, Send } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";
import {
  criarAssunto,
  enviarNotion,
  listarAssuntos,
  notionStatus,
} from "@/lib/api";
import type { AssuntoNotion } from "@/lib/types";

export function Step5Notion() {
  const { results, fileInfo, prevStep } = useWizard();
  const [configurado, setConfigurado] = useState<boolean | null>(null);
  const [assuntos, setAssuntos] = useState<AssuntoNotion[]>([]);
  const [assuntoId, setAssuntoId] = useState("");
  const [novoAssunto, setNovoAssunto] = useState("");
  const [titulo, setTitulo] = useState(fileInfo?.nome ?? "");
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    notionStatus()
      .then((ok) => {
        setConfigurado(ok);
        if (ok) carregarAssuntos();
      })
      .catch(() => setConfigurado(false));
  }, []);

  const carregarAssuntos = useCallback(async () => {
    try {
      const lista = await listarAssuntos();
      setAssuntos(lista);
      if (lista.length > 0) setAssuntoId(lista[0].id);
    } catch {
      setErro("Erro ao carregar assuntos do Notion.");
    }
  }, []);

  const handleCriarAssunto = useCallback(async () => {
    if (!novoAssunto.trim()) return;
    try {
      const criado = await criarAssunto(novoAssunto.trim());
      setAssuntos((prev) => [...prev, criado]);
      setAssuntoId(criado.id);
      setNovoAssunto("");
    } catch {
      setErro("Erro ao criar assunto.");
    }
  }, [novoAssunto]);

  const handleEnviar = useCallback(async () => {
    if (!results || !assuntoId || !titulo.trim()) return;
    setEnviando(true);
    setErro(null);
    try {
      const url = await enviarNotion({
        assunto_id: assuntoId,
        titulo: titulo.trim(),
        transcricao_completa: results.transcricao_completa,
        segmentos_com_falantes: results.segmentos_com_falantes,
        resumo_falantes: results.resumo_falantes,
        diarizar: results.diarizacao_ativada,
      });
      setSucesso(url);
    } catch {
      setErro("Erro ao enviar para o Notion. Verifique as configurações.");
    } finally {
      setEnviando(false);
    }
  }, [results, assuntoId, titulo]);

  return (
    <div>
      <Stepper passo={5} />
      <div className="flex items-center gap-2 mb-1">
        <BookOpen size={20} className="text-primary" />
        <h1 className="text-2xl font-bold text-gray-800">Enviar ao Notion</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Publique a transcrição em uma página do Notion.
      </p>

      {configurado === false && <NotionNaoConfigurado />}

      {configurado === true && !sucesso && (
        <FormularioEnvio
          assuntos={assuntos}
          assuntoId={assuntoId}
          novoAssunto={novoAssunto}
          titulo={titulo}
          enviando={enviando}
          setAssuntoId={setAssuntoId}
          setNovoAssunto={setNovoAssunto}
          setTitulo={setTitulo}
          onCriarAssunto={handleCriarAssunto}
          onEnviar={handleEnviar}
        />
      )}

      {erro && (
        <div className="card mb-4 bg-red-50 border-red-200 text-red-700 text-sm">
          {erro}
        </div>
      )}

      {sucesso && <Sucesso url={sucesso} />}

      {!sucesso && (
        <WizardNav onBack={prevStep} />
      )}
    </div>
  );
}

function NotionNaoConfigurado() {
  return (
    <div className="card mb-6 bg-amber-50 border-amber-200">
      <p className="text-sm font-semibold text-amber-800 mb-2">
        ⚠️ Notion não configurado
      </p>
      <p className="text-xs text-amber-700 mb-3">
        Adicione as variáveis abaixo ao arquivo <code>.env</code> na raiz do projeto:
      </p>
      <pre className="text-xs bg-amber-100 rounded-lg px-4 py-3 text-amber-900 font-mono">
        {`NOTION_TOKEN=secret_xxxxxxxxxxxxxxxx\nNOTION_PARENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`}
      </pre>
      <p className="text-xs text-amber-600 mt-3">
        Reinicie o servidor backend após configurar.
      </p>
    </div>
  );
}

function FormularioEnvio({
  assuntos, assuntoId, novoAssunto, titulo, enviando,
  setAssuntoId, setNovoAssunto, setTitulo, onCriarAssunto, onEnviar,
}: {
  assuntos: AssuntoNotion[];
  assuntoId: string;
  novoAssunto: string;
  titulo: string;
  enviando: boolean;
  setAssuntoId: (v: string) => void;
  setNovoAssunto: (v: string) => void;
  setTitulo: (v: string) => void;
  onCriarAssunto: () => void;
  onEnviar: () => void;
}) {
  return (
    <div className="space-y-4 mb-6">
      <div className="card">
        <label className="label">Assunto (sub-página)</label>
        <select
          value={assuntoId}
          onChange={(e) => setAssuntoId(e.target.value)}
          className="input mt-1"
        >
          {assuntos.map((a) => (
            <option key={a.id} value={a.id}>
              {a.nome}
            </option>
          ))}
        </select>

        <p className="text-xs text-gray-400 mt-3 mb-2">Ou crie um novo:</p>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Nome do novo assunto"
            value={novoAssunto}
            onChange={(e) => setNovoAssunto(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onCriarAssunto()}
            className="input flex-1"
          />
          <button onClick={onCriarAssunto} className="btn-secondary px-3">
            <Plus size={14} />
          </button>
        </div>
      </div>

      <div className="card">
        <label className="label">Título da página</label>
        <input
          type="text"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          className="input mt-1"
          placeholder="Título da transcrição no Notion"
        />
      </div>

      <button
        onClick={onEnviar}
        disabled={enviando || !assuntoId || !titulo.trim()}
        className="btn-primary w-full justify-center"
      >
        {enviando ? (
          <>⏳ Enviando...</>
        ) : (
          <>
            <Send size={14} /> Publicar no Notion
          </>
        )}
      </button>
    </div>
  );
}

function Sucesso({ url }: { url: string }) {
  return (
    <div className="card mb-6 bg-green-50 border-green-200">
      <p className="text-sm font-semibold text-green-800 mb-2">
        ✅ Publicado com sucesso!
      </p>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-green-700 underline break-all"
      >
        {url}
      </a>
      <p className="text-xs text-green-600 mt-2">Abra o link acima para ver no Notion.</p>
    </div>
  );
}
