import { ArrowLeft, ArrowRight } from "lucide-react";

interface Props {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
}

export function WizardNav({ onBack, onNext, nextLabel = "Avançar →", nextDisabled }: Props) {
  return (
    <div className="flex items-center justify-between pt-4 border-t border-gray-100">
      {onBack ? (
        <button onClick={onBack} className="btn-secondary">
          <ArrowLeft size={14} /> Voltar
        </button>
      ) : (
        <div />
      )}
      {onNext && (
        <button onClick={onNext} className="btn-primary" disabled={nextDisabled}>
          {nextLabel} <ArrowRight size={14} />
        </button>
      )}
    </div>
  );
}
