"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { getConfigStatus } from "@/lib/api";
import { OnboardingWizard } from "@/components/config/OnboardingWizard";
import { Sidebar } from "./Sidebar";

type Modo = "loading" | "onboarding" | "app";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [modo, setModo] = useState<Modo>("loading");

  useEffect(() => {
    getConfigStatus()
      .then((s) => setModo(s.conexao_ok ? "app" : "onboarding"))
      .catch(() => setModo("onboarding"));
  }, []);

  if (modo === "loading") {
    return (
      <div className="flex-1 grid place-items-center text-gray-400">
        <Loader2 size={28} className="animate-spin" />
      </div>
    );
  }

  if (modo === "onboarding") {
    return <OnboardingWizard onConcluir={() => setModo("app")} />;
  }

  return (
    <>
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-8 py-8">{children}</div>
      </main>
    </>
  );
}
