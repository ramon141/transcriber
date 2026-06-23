import { clsx } from "clsx";
import { Check } from "lucide-react";

const ETAPAS = ["Arquivo", "Configurações", "Corte", "Processar", "Notion"];

export function Stepper({ passo }: { passo: number }) {
  return (
    <div className="card flex items-center justify-center gap-0 mb-6">
      {ETAPAS.map((nome, i) => {
        const num = i + 1;
        const done = num < passo;
        const active = num === passo;
        return (
          <div key={num} className="flex items-center">
            <StepItem num={num} nome={nome} done={done} active={active} />
            {num < ETAPAS.length && <StepLine done={done} />}
          </div>
        );
      })}
    </div>
  );
}

function StepItem({
  num, nome, done, active,
}: {
  num: number; nome: string; done: boolean; active: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5 min-w-[72px]">
      <div
        className={clsx(
          "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all",
          done && "bg-primary text-white",
          active && "bg-gradient-primary text-white shadow-lg shadow-primary/40 scale-110",
          !done && !active && "bg-gray-100 text-gray-400"
        )}
      >
        {done ? <Check size={16} /> : num}
      </div>
      <span
        className={clsx(
          "text-[11px] font-medium text-center",
          active && "text-primary font-semibold",
          done && "text-gray-500",
          !done && !active && "text-gray-400"
        )}
      >
        {nome}
      </span>
    </div>
  );
}

function StepLine({ done }: { done: boolean }) {
  return (
    <div
      className={clsx(
        "h-0.5 w-12 mx-1 mb-5 transition-all",
        done ? "bg-gradient-primary" : "bg-gray-200"
      )}
    />
  );
}
