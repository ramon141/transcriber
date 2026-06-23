"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { BookOpen, Send } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";
import { criarAssunto, enviarNotion, listarAssuntos, notionStatus } from "@/lib/api";
import type { AssuntoNotion } from "@/lib/types";

const CreatableSelect = dynamic(
  () => import("react-select/creatable").then((m) => m.default),
  { ssr: false }
);

interface SelectOption {
  value: string;
  label: string;
  __isNew__?: boolean;
}

export function Step5Notion() {
  const { results, fileInfo, prevStep } = useWizard();
  const [configurado, setConfigurado] = useState<boolean | null>(null);
  const [assuntos, setAssuntos] = useState<AssuntoNotion[]>([]);
  const [assuntoSel, setAssuntoSel] = useState<SelectOption | null>(null);
  const [titulo, setTitulo] = useState(
    () => new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })
  );
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const carregarAssuntos = useCallback(async () => {
    try {
      const lista = await listarAssuntos();
      setAssuntos(lista);
    } catch {
      setErro("Erro ao carregar assuntos do Notion.");
    }
  }, []);

  useEffect(() => {
    notionStatus()
      .then((ok) => {
        setConfigurado(ok);
        if (ok) carregarAssuntos();
      })
      .catch(() => setConfigurado(false));
  }, [carregarAssuntos]);

  const opcoesSelect: SelectOption[] = assuntos.map((a) => ({
    value: a.id,
    label: a.nome,
  }));

  const handleCriarOuSelecionar = useCallback(
    async (opcao: SelectOption | null) => {
      if (!opcao) { setAssuntoSel(null); return; }
      if (opcao.__isNew__) {
        try {
          const criado = await criarAssunto(opcao.label);
          const nova: SelectOption = { value: criado.id, label: criado.nome };
          setAssuntos((prev) => [...prev, criado]);
          setAssuntoSel(nova);
        } catch {
          setErro("Erro ao criar assunto.");
        }
      } else {
        setAssuntoSel(opcao);
      }
    },
    []
  );

  const handleEnviar = useCallback(async () => {
    if (!results || !assuntoSel || !titulo.trim()) return;
    setEnviando(true);
    setErro(null);
    try {
      const tituloFinal = `Reunião ${titulo.trim()}`;
      const url = await enviarNotion({
        assunto_id: assuntoSel.value,
        titulo: tituloFinal,
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
  }, [results, assuntoSel, titulo]);

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
          opcoes={opcoesSelect}
          assuntoSel={assuntoSel}
          titulo={titulo}
          enviando={enviando}
          onAssuntoChange={handleCriarOuSelecionar}
          onTituloChange={setTitulo}
          onEnviar={handleEnviar}
        />
      )}

      {erro && (
        <div className="card mb-4 bg-red-50 border-red-200 text-red-700 text-sm">{erro}</div>
      )}

      {sucesso && <Sucesso url={sucesso} />}

      {!sucesso && <WizardNav onBack={prevStep} />}
    </div>
  );
}

function FormularioEnvio({
  opcoes, assuntoSel, titulo, enviando,
  onAssuntoChange, onTituloChange, onEnviar,
}: {
  opcoes: SelectOption[];
  assuntoSel: SelectOption | null;
  titulo: string;
  enviando: boolean;
  onAssuntoChange: (v: SelectOption | null) => void;
  onTituloChange: (v: string) => void;
  onEnviar: () => void;
}) {
  return (
    <div className="space-y-4 mb-6">
      <div className="card">
        <label className="label">Pasta (assunto)</label>
        <p className="text-xs text-gray-400 mb-2">
          Selecione uma existente ou digite para criar uma nova.
        </p>
        <CreatableSelect
          options={opcoes}
          value={assuntoSel}
          onChange={(v) => onAssuntoChange(v as SelectOption | null)}
          placeholder="Selecione ou crie uma pasta..."
          formatCreateLabel={(input) => `✚ Criar "${input}"`}
          isClearable
          styles={selectStyles}
        />
      </div>

      <div className="card">
        <label className="label">Título da reunião</label>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm text-gray-500 shrink-0">Reunião</span>
          <input
            type="text"
            value={titulo}
            onChange={(e) => onTituloChange(e.target.value)}
            className="input"
            placeholder="22/06/2026 às 22:00"
          />
        </div>
        <p className="text-xs text-gray-400 mt-1.5">
          Será criado como: <span className="font-mono">Reunião {titulo}</span>
        </p>
      </div>

      <button
        onClick={onEnviar}
        disabled={enviando || !assuntoSel || !titulo.trim()}
        className="btn-primary w-full justify-center"
      >
        {enviando ? <>⏳ Enviando...</> : <><Send size={14} /> Publicar no Notion</>}
      </button>
    </div>
  );
}

const selectStyles = {
  control: (base: object) => ({
    ...base,
    borderRadius: "0.75rem",
    borderColor: "#e5e7eb",
    padding: "2px 4px",
    boxShadow: "none",
    "&:hover": { borderColor: "#6C63FF" },
  }),
  option: (base: object, state: { isFocused: boolean }) => ({
    ...base,
    backgroundColor: state.isFocused ? "#f3f4f6" : "white",
    color: "#374151",
    fontSize: "0.875rem",
  }),
  menu: (base: object) => ({
    ...base,
    borderRadius: "0.75rem",
    overflow: "hidden",
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  }),
};

function NotionNaoConfigurado() {
  return (
    <div className="card mb-6 bg-amber-50 border-amber-200">
      <p className="text-sm font-semibold text-amber-800 mb-2">⚠️ Notion não configurado</p>
      <p className="text-xs text-amber-700 mb-3">
        Adicione as variáveis abaixo ao arquivo <code>.env</code> na raiz do projeto:
      </p>
      <pre className="text-xs bg-amber-100 rounded-lg px-4 py-3 text-amber-900 font-mono">
        {`NOTION_TOKEN=secret_xxxxxxxxxxxxxxxx\nNOTION_PARENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`}
      </pre>
      <p className="text-xs text-amber-600 mt-3">Reinicie o servidor backend após configurar.</p>
    </div>
  );
}

function Sucesso({ url }: { url: string }) {
  return (
    <div className="card mb-6 bg-green-50 border-green-200">
      <p className="text-sm font-semibold text-green-800 mb-2">✅ Publicado com sucesso!</p>
      <a href={url} target="_blank" rel="noopener noreferrer"
        className="text-xs text-green-700 underline break-all">
        {url}
      </a>
      <p className="text-xs text-green-600 mt-2">Abra o link acima para ver no Notion.</p>
    </div>
  );
}
