interface Props {
  flags: string[];
}

export default function ReviewFlagsPanel({ flags }: Props) {
  return (
    <div className="rounded-[10px] border-l-4 border-warning bg-warning/5 border border-warning/20 p-5 mb-6">
      <p className="text-sm font-semibold text-warning mb-2">
        {flags.length} item{flags.length !== 1 ? 's' : ''} need your review
      </p>
      <p className="text-sm text-text-muted mb-3">
        These placeholders were inserted where your original CV lacked specific metrics or dates.
        Open the Markdown file to fill them in before sending your CV.
      </p>
      <ul className="space-y-1">
        {flags.map((flag, i) => (
          <li key={i} className="text-sm font-mono text-text-primary">
            • {flag}
          </li>
        ))}
      </ul>
    </div>
  );
}
