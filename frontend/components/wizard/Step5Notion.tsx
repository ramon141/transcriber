"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { BookOpen, Send } from "lucide-react";
import { Stepper } from "./Stepper";
import { WizardNav } from "./WizardNav";
import { useWizard } from "@/lib/store";
import { criarAssunto, enviarNotion, extrairAtividades, listarAssuntos, notionStatus, resumirTranscricao } from "@/lib/api";
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
  const [resumirAtivo, setResumirAtivo] = useState(false);
  const [ativarAtividades, setAtivarAtividades] = useState(false);
  const [statusEnvio, setStatusEnvio] = useState<"idle" | "resumindo" | "extraindo" | "enviando">("idle");
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const enviando = statusEnvio !== "idle";


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
    setErro(null);

    let resumo: string | undefined;
    let atividades: Record<string, string[]> | undefined;

    if (resumirAtivo) {
      setStatusEnvio("resumindo");
      try {
        resumo = await resumirTranscricao(results.transcricao_completa);
      } catch {
        setErro("Erro ao gerar resumo com IA. Verifique o Claude CLI.");
        setStatusEnvio("idle");
        return;
      }
    }

    if (ativarAtividades) {
      setStatusEnvio("extraindo");
      try {
        atividades = await extrairAtividades(results.transcricao_completa);
      } catch {
        setErro("Erro ao extrair atividades com IA. Verifique o Claude CLI.");
        setStatusEnvio("idle");
        return;
      }
    }

    setStatusEnvio("enviando");
    try {
      const tituloFinal = `Reunião ${titulo.trim()}`;
      const url = await enviarNotion({
        assunto_id: assuntoSel.value,
        titulo: tituloFinal,
        transcricao_completa: results.transcricao_completa,
        segmentos_com_falantes: results.segmentos_com_falantes,
        resumo_falantes: results.resumo_falantes,
        diarizar: results.diarizacao_ativada,
        resumo,
        atividades,
      });
      setSucesso(url);
    } catch {
      setErro("Erro ao enviar para o Notion. Verifique as configurações.");
    } finally {
      setStatusEnvio("idle");
    }
  }, [results, assuntoSel, titulo, resumirAtivo, ativarAtividades]);

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
          resumirAtivo={resumirAtivo}
          ativarAtividades={ativarAtividades}
          statusEnvio={statusEnvio}
          onAssuntoChange={handleCriarOuSelecionar}
          onTituloChange={setTitulo}
          onResumirChange={setResumirAtivo}
          onAtividadesChange={setAtivarAtividades}
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
  opcoes, assuntoSel, titulo, resumirAtivo, ativarAtividades, statusEnvio,
  onAssuntoChange, onTituloChange, onResumirChange, onAtividadesChange, onEnviar,
}: {
  opcoes: SelectOption[];
  assuntoSel: SelectOption | null;
  titulo: string;
  resumirAtivo: boolean;
  ativarAtividades: boolean;
  statusEnvio: "idle" | "resumindo" | "extraindo" | "enviando";
  onAssuntoChange: (v: SelectOption | null) => void;
  onTituloChange: (v: string) => void;
  onResumirChange: (v: boolean) => void;
  onAtividadesChange: (v: boolean) => void;
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

      <div className="card space-y-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Opções de IA</p>
        <ToggleOpcao
          ativo={resumirAtivo}
          onChange={onResumirChange}
          titulo="Resumir transcrição com IA"
          descricao={<>Gera resumo com pontos, decisões e pendências usando <code>claude-opus-4-8</code></>}
        />
        <ToggleOpcao
          ativo={ativarAtividades}
          onChange={onAtividadesChange}
          titulo="Criar aba de Atividades"
          descricao="Extrai tarefas por participante e cria checklist no Notion"
        />
      </div>

      <button
        onClick={onEnviar}
        disabled={statusEnvio !== "idle" || !assuntoSel || !titulo.trim()}
        className="btn-primary w-full justify-center"
      >
        {statusEnvio === "resumindo" && <>🤖 Gerando resumo com IA...</>}
        {statusEnvio === "extraindo" && <>📋 Extraindo atividades com IA...</>}
        {statusEnvio === "enviando" && <>⏳ Publicando no Notion...</>}
        {statusEnvio === "idle" && <><Send size={14} /> Publicar no Notion</>}
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

function ToggleOpcao({ ativo, onChange, titulo, descricao }: {
  ativo: boolean;
  onChange: (v: boolean) => void;
  titulo: string;
  descricao: React.ReactNode;
}) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <button
        type="button"
        onClick={() => onChange(!ativo)}
        className={`w-11 h-6 rounded-full transition-all relative shrink-0 ${ativo ? "bg-gradient-primary" : "bg-gray-200"}`}
      >
        <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all ${ativo ? "left-5" : "left-0.5"}`} />
      </button>
      <div>
        <p className="text-sm font-semibold text-gray-700">{titulo}</p>
        <p className="text-xs text-gray-400">{descricao}</p>
      </div>
    </label>
  );
}

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
