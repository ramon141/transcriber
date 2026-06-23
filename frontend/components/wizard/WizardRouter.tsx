"use client";

import { useWizard } from "@/lib/store";
import { Step1Upload } from "./Step1Upload";
import { Step2Config } from "./Step2Config";
import { Step3Corte } from "./Step3Corte";
import { Step4Processar } from "./Step4Processar";
import { Step5Notion } from "./Step5Notion";

export function WizardRouter() {
  const step = useWizard((s) => s.step);

  switch (step) {
    case 1: return <Step1Upload />;
    case 2: return <Step2Config />;
    case 3: return <Step3Corte />;
    case 4: return <Step4Processar />;
    case 5: return <Step5Notion />;
    default: return <Step1Upload />;
  }
}
