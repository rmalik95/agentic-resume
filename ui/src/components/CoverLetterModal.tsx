import { useState } from 'react';

interface Props {
  onAnswer: (generate: boolean, companyContext: string) => void;
}

export default function CoverLetterModal({ onAnswer }: Props) {
  const [context, setContext] = useState('');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        className="bg-surface border border-border rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-label="Cover letter decision"
      >
        <h3 className="font-heading text-xl font-semibold mb-3">
          Generate a cover letter?
        </h3>
        <p className="text-sm text-text-muted mb-5">
          Your CV has been optimised. Would you like a tailored cover letter as well?
        </p>

        <div className="mb-5">
          <label className="block text-xs text-text-muted mb-1">
            Optional: paste a short description of the company for a more targeted letter
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="What the company does, team info, etc."
            className="w-full min-h-[80px] rounded-lg border border-border bg-bg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-y focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => onAnswer(true, context)}
            className="flex-1 px-4 py-2.5 rounded-lg bg-accent text-white text-sm font-medium hover:brightness-110 transition-all"
            autoFocus
          >
            Generate cover letter
          </button>
          <button
            onClick={() => onAnswer(false, '')}
            className="flex-1 px-4 py-2.5 rounded-lg border border-border bg-surface text-text-primary text-sm font-medium hover:bg-surface-raised transition-colors"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}
