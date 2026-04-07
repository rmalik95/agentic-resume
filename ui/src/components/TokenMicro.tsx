interface Props {
  metrics: Record<string, number>;
}

export default function TokenMicro({ metrics }: Props) {
  const rows: [string, string][] = [
    ['Anthropic API requests', String(metrics.anthropic_requests ?? 0)],
    ['Input tokens', (metrics.input_tokens ?? 0).toLocaleString()],
    ['Output tokens', (metrics.output_tokens ?? 0).toLocaleString()],
    [
      'Cache write tokens',
      (metrics.cache_creation_input_tokens ?? 0).toLocaleString(),
    ],
    [
      'Cache read tokens (saved)',
      (metrics.cache_read_input_tokens ?? 0).toLocaleString(),
    ],
    ['Estimated cost', `~$${(metrics.estimated_cost ?? 0).toFixed(4)}`],
  ];

  return (
    <table className="w-full text-sm">
      <tbody>
        {rows.map(([label, value]) => (
          <tr key={label} className="border-b border-border/50">
            <td className="py-1.5 text-text-muted">{label}</td>
            <td className="py-1.5 text-right font-mono text-text-primary">
              {value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
