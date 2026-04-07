interface Props {
  score: number;
  threshold: number;
  onAnswer: (proceed: boolean) => void;
}

export default function LowScoreModal({ score, threshold, onAnswer }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        className="bg-surface border border-border rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-label="Low match score confirmation"
      >
        <h3 className="font-heading text-xl font-semibold mb-3">
          Low role-match warning
        </h3>
        <p className="text-sm text-text-muted mb-3">
          Baseline match score is <span className="text-text-primary font-semibold">{score}/100</span>, which is below the recommended threshold of <span className="text-text-primary font-semibold">{threshold}</span>.
        </p>
        <p className="text-sm text-text-muted mb-6">
          This usually means the job is not a strong fit for your current experience. Do you still want to continue optimisation?
        </p>

        <div className="flex gap-3">
          <button
            onClick={() => onAnswer(true)}
            className="flex-1 px-4 py-2.5 rounded-lg bg-accent text-white text-sm font-medium hover:brightness-110 transition-all"
            autoFocus
          >
            Continue anyway
          </button>
          <button
            onClick={() => onAnswer(false)}
            className="flex-1 px-4 py-2.5 rounded-lg border border-border bg-surface text-text-primary text-sm font-medium hover:bg-surface-raised transition-colors"
          >
            Stop run
          </button>
        </div>
      </div>
    </div>
  );
}
