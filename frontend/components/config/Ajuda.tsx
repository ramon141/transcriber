"use client";

import { ExternalLink, HelpCircle } from "lucide-react";

interface Link {
  label: string;
  href: string;
}

interface Passo {
  titulo: string;
  itens: string[];
  links?: Link[];
}

function Bloco({ passos }: { passos: Passo[] }) {
  return (
    <details className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 mb-4">
      <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-gray-700 select-none">
        <HelpCircle size={15} className="text-primary" />
        Onde encontrar essas informações?
      </summary>
      <div className="mt-3 flex flex-col gap-3">
        {passos.map((p) => (
          <div key={p.titulo}>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
              {p.titulo}
            </p>
            <ul className="mt-1 list-disc pl-5 text-sm text-gray-600 space-y-0.5">
              {p.itens.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            {p.links && (
              <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 pl-5">
                {p.links.map((l) => (
                  <a
                    key={l.href}
                    href={l.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    <ExternalLink size={13} />
                    {l.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </details>
  );
}

export function AjudaConexao() {
  return (
    <Bloco
      passos={[
        {
          titulo: "SUPABASE_URL e SUPABASE_KEY",
          itens: [
            "Supabase Dashboard → Project Settings → API.",
            "URL = Project URL. KEY = chave publishable (anon).",
          ],
          links: [{ label: "Abrir Supabase Dashboard", href: "https://supabase.com/dashboard" }],
        },
        {
          titulo: "DATABASE_URL",
          itens: [
            "Dashboard → Settings → Database → Connection string → Transaction pooler (URI).",
            "Formato: postgresql://postgres.[ref]:[senha]@aws-0-[região].pooler.supabase.com:6543/postgres",
          ],
          links: [
            { label: "Configurações do banco", href: "https://supabase.com/dashboard/project/_/settings/database" },
          ],
        },
        {
          titulo: "Validação",
          itens: [
            "Ao salvar, a conexão é testada e as tabelas são criadas automaticamente.",
            "Se as credenciais estiverem incorretas, o sistema avisa e pede novamente.",
          ],
        },
      ]}
    />
  );
}

export function AjudaIntegracoes() {
  return (
    <Bloco
      passos={[
        {
          titulo: "HF_TOKEN (diarização)",
          itens: [
            "huggingface.co → Settings → Access Tokens → gerar token.",
            "Aceitar os termos do modelo pyannote/speaker-diarization-3.1.",
          ],
          links: [
            { label: "Access Tokens", href: "https://huggingface.co/settings/tokens" },
            { label: "Aceitar termos do modelo", href: "https://huggingface.co/pyannote/speaker-diarization-3.1" },
          ],
        },
        {
          titulo: "NOTION_TOKEN",
          itens: [
            "New integration → copiar o Internal Integration Token.",
          ],
          links: [{ label: "Notion · My integrations", href: "https://www.notion.so/my-integrations" }],
        },
        {
          titulo: "NOTION_PARENT_ID",
          itens: [
            "Cole o link completo da página do Notion — o ID é extraído automaticamente.",
            "Compartilhe essa página com a integração criada acima.",
          ],
        },
      ]}
    />
  );
}
