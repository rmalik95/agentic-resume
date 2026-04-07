interface Props {
  before: number;
  after: number;
  atsVerdict: string;
  missingAfter: string[];
  keywordsAdded: string[];
}

export default function ScoreCard({
  before,
  after,
  atsVerdict,
  missingAfter,
  keywordsAdded,
}: Props) {
  const delta = after - before;

  return (
    <div className="rounded-[10px] border border-border bg-surface p-6 mb-6">
      {/* Main score row */}
      <div className="flex items-center justify-center gap-6 mb-4">
        <div className="text-center">
          <p className="font-heading text-5xl font-bold text-text-muted leading-none">
            {before}
          </p>
          <p className="text-xs text-text-muted mt-1">Before</p>
        </div>
        <span className="text-3xl text-text-muted">→</span>
        <div className="text-center">
          <p className="font-heading text-5xl font-bold text-accent leading-none">
            {after}
          </p>
          <p className="text-xs text-text-muted mt-1">After</p>
        </div>
        <span
          className={`font-heading text-2xl font-bold px-4 py-2 rounded-lg ${
            delta > 0
              ? 'text-success bg-success/10'
              : delta < 0
                ? 'text-error bg-error/10'
                : 'text-text-muted bg-surface-raised'
          }`}
        >
          {delta > 0 ? '+' : ''}
          {delta} pts
        </span>
      </div>

      {/* ATS verdict */}
      <div className="flex items-center gap-4 text-sm border-t border-border pt-4">
        <span className="text-text-muted">ATS verdict:</span>
        <span className="text-text-primary font-medium">{atsVerdict}</span>
      </div>

      {/* Keywords */}
      {keywordsAdded.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-text-muted mb-1">Keywords added:</p>
          <div className="flex flex-wrap gap-1">
            {keywordsAdded.map((k, i) => (
              <span
                key={i}
                className="text-xs bg-success/10 text-success px-2 py-0.5 rounded"
              >
                {k}
              </span>
            ))}
          </div>
        </div>
      )}
      {missingAfter.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-text-muted mb-1">Keywords still missing:</p>
          <div className="flex flex-wrap gap-1">
            {missingAfter.map((k, i) => (
              <span
                key={i}
                className="text-xs bg-surface-raised text-text-muted px-2 py-0.5 rounded"
              >
                {k}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
