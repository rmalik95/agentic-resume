import type { AgentMeta } from '../lib/agentMeta';
import type { AgentState } from '../hooks/usePipelineStream';
import MarkdownPreview from './MarkdownPreview';
import { useState } from 'react';

interface Props {
  meta: AgentMeta;
  agentState: AgentState;
  compact?: boolean;
}

/** Split agent output text into sections by markdown headings. */
function parseSections(content: string): { title: string; body: string }[] {
  const lines = content.split('\n');
  const sections: { title: string; body: string }[] = [];
  let current: { title: string; lines: string[] } | null = null;

  for (const line of lines) {
    const m = line.match(/^#{1,3}\s+(.+)/);
    if (m) {
      if (current) sections.push({ title: current.title, body: current.lines.join('\n').trim() });
      current = { title: m[1], lines: [] };
    } else if (current) {
      current.lines.push(line);
    } else {
      // Content before any heading
      if (line.trim()) {
        if (!current) current = { title: '', lines: [line] };
      }
    }
  }
  if (current) sections.push({ title: current.title, body: current.lines.join('\n').trim() });
  return sections;
}

function AccordionSections({
  content,
  defaultOpen = 2,
}: {
  content: string;
  defaultOpen?: number;
}) {
  const sections = parseSections(content);
  const [openSet, setOpenSet] = useState<Set<number>>(
    new Set(sections.slice(0, defaultOpen).map((_, i) => i)),
  );

  if (sections.length <= 1) {
    return <MarkdownPreview content={content} />;
  }

  const toggle = (idx: number) => {
    setOpenSet((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="space-y-1">
      {sections.map((s, i) => (
        <div key={i} className="rounded-lg border border-border overflow-hidden">
          <button
            onClick={() => toggle(i)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-left bg-surface-raised hover:brightness-105 transition-colors"
          >
            <span className="text-sm font-medium text-text-primary">
              {s.title || `Section ${i + 1}`}
            </span>
            <span className="text-xs text-text-muted">{openSet.has(i) ? '▾' : '▸'}</span>
          </button>
          {openSet.has(i) && (
            <div className="px-4 py-3 text-sm">
              <MarkdownPreview content={s.body} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function ReasoningPanel({ meta, agentState, compact }: Props) {
  const isActive = agentState.status === 'active';
  const isError = agentState.status === 'error';
  const data = agentState.data;
  const content = (data.content as string) ?? '';
  const tokensIn = data.tokens_in as number | undefined;
  const tokensOut = data.tokens_out as number | undefined;
  const hasStructuredContent =
    meta.key === 'positioning_strategy' ||
    meta.key === 'jd_intelligence' ||
    meta.key === 'gap_analysis' ||
    meta.key === 'ats_qa_scan';
  const isCoverLetter = meta.key === 'cover_letter';
  const wasSkipped = Boolean(data.skipped);

  return (
    <div className={`${compact ? '' : 'min-h-[400px]'}`}>
      {/* Header */}
      {!compact && (
        <div className="flex items-center gap-3 mb-4">
          <span className="text-2xl">{meta.icon}</span>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-semibold">{meta.displayName}</h2>
          </div>
          <span
            className={`text-xs font-mono px-2 py-1 rounded ${
              isActive
                ? 'text-accent bg-accent/10'
                : isError
                  ? 'text-error bg-error/10'
                  : 'text-success bg-success/10'
            }`}
          >
            {isActive ? 'Running…' : isError ? 'Failed' : 'Done'}
            {!isActive && agentState.elapsedMs !== undefined && (
              <> · {(agentState.elapsedMs / 1000).toFixed(1)}s</>
            )}
          </span>
        </div>
      )}

      {/* Reasoning description */}
      {!compact && (
        <div className="rounded-[10px] bg-surface border border-border p-4 mb-4">
          <p className="text-xs uppercase tracking-wider text-text-muted mb-1.5">
            What this step is doing
          </p>
          <p className="text-[15px] text-text-primary leading-relaxed">
            {meta.reasoning}
          </p>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="rounded-[10px] bg-error/10 border border-error/30 p-4 mb-4">
          <p className="text-sm text-error font-medium">Error</p>
          <p className="text-sm text-text-primary mt-1">{agentState.error}</p>
        </div>
      )}

      {/* Active state — streaming cursor */}
      {isActive && !content && (
        <div className="rounded-[10px] bg-surface border border-border p-4">
          <p className="text-sm text-text-muted streaming-cursor">Processing</p>
        </div>
      )}

      {/* Agent-specific output */}
      {!isActive && content ? (
        <AgentOutput meta={meta} data={data} content={content} isCoverLetter={isCoverLetter} wasSkipped={wasSkipped} hasStructuredContent={hasStructuredContent} />
      ) : null}

      {/* Token usage micro-stat */}
      {tokensIn !== undefined && tokensOut !== undefined && !isActive ? (
        <p className="text-right mt-2 font-mono text-[11px] text-text-muted">
          ↑ {tokensIn.toLocaleString()} tokens in &nbsp; ↓ {tokensOut.toLocaleString()} tokens out
        </p>
      ) : null}
    </div>
  );
}

/** Extracted component for agent output to avoid unknown-type JSX issues. */
function AgentOutput({
  meta,
  data,
  content,
  isCoverLetter,
  wasSkipped,
  hasStructuredContent,
}: {
  meta: AgentMeta;
  data: Record<string, unknown>;
  content: string;
  isCoverLetter: boolean;
  wasSkipped: boolean;
  hasStructuredContent: boolean;
}) {
  const reviewFlags = (data.review_flags as string[]) ?? [];
  const headings = (data.headings as string[]) ?? [];
  const wordCount = (data.word_count as number) ?? 0;
  const renderError = (data.render_error as string) ?? '';
  const isScore = meta.key === 'match_score_before' || meta.key === 'match_score_after';

  return (
    <div className="rounded-[10px] bg-surface border border-border p-4" aria-live="polite">
      <p className="text-xs uppercase tracking-wider text-text-muted mb-2">
        {meta.key === 'cv_rewrite' ? 'What it produced' : 'What it found'}
      </p>

      {isScore ? <ScoreMini data={data} agentKey={meta.key} /> : null}

      {meta.key === 'cv_rewrite' ? (
        <div>
          <div className="max-h-[500px] overflow-y-auto">
            <MarkdownPreview content={content} />
          </div>
          {reviewFlags.length > 0 ? (
            <div className="mt-4 rounded-lg border-l-4 border-warning bg-warning/10 p-3">
              <p className="text-sm font-medium text-warning mb-1">
                {reviewFlags.length} items need your review
              </p>
              <ul className="text-xs text-text-primary space-y-0.5">
                {reviewFlags.map((f, i) => (
                  <li key={i} className="font-mono">{f}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {hasStructuredContent ? <AccordionSections content={content} /> : null}

      {isCoverLetter ? (
        wasSkipped ? (
          <p className="text-sm text-text-muted italic">Skipped by user.</p>
        ) : (
          <MarkdownPreview content={content} />
        )
      ) : null}

      {meta.key === 'pdf_parse' ? (
        <div className="space-y-2">
          <p className="text-sm">
            <span className="text-text-muted">Words:</span>{' '}
            <span className="font-mono">{wordCount}</span>
          </p>
          {headings.length > 0 ? (
            <div>
              <p className="text-xs text-text-muted mb-1">Sections found:</p>
              <div className="flex flex-wrap gap-1">
                {headings.map((h, i) => (
                  <span key={i} className="text-xs bg-surface-raised px-2 py-0.5 rounded">{h}</span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {meta.key === 'latex_generator' || meta.key === 'renderer' ? (
        <p className="text-sm text-text-primary">{content}</p>
      ) : null}
      {meta.key === 'renderer' && renderError ? (
        <p className="text-sm text-warning mt-2">{renderError}</p>
      ) : null}
    </div>
  );
}

/** Small inline score display for match score agents. */
function ScoreMini({ data, agentKey }: { data: Record<string, unknown>; agentKey: string }) {
  const score = data.match_score as number | undefined;
  const analysis = data.score_analysis as string | undefined;
  const missing = (data.missing_keywords as string[]) ?? [];

  if (agentKey === 'match_score_after') {
    const scoreBefore = data.match_score_before as number | undefined;
    const delta = (score ?? 0) - (scoreBefore ?? 0);
    const missingAfter = (data.missing_keywords_after as string[]) ?? [];
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <p className="font-heading text-4xl font-bold text-text-muted">{scoreBefore ?? '?'}</p>
            <p className="text-xs text-text-muted">Before</p>
          </div>
          <span className="text-2xl text-text-muted">→</span>
          <div className="text-center">
            <p className="font-heading text-4xl font-bold text-accent">{score ?? '?'}</p>
            <p className="text-xs text-text-muted">After</p>
          </div>
          <span
            className={`font-heading text-xl font-bold px-3 py-1 rounded ${
              delta > 0 ? 'text-success bg-success/10' : 'text-error bg-error/10'
            }`}
          >
            {delta > 0 ? '+' : ''}{delta}
          </span>
        </div>
        {missingAfter.length > 0 && (
          <div>
            <p className="text-xs text-text-muted mb-1">Keywords still missing:</p>
            <div className="flex flex-wrap gap-1">
              {missingAfter.map((k, i) => (
                <span key={i} className="text-xs bg-surface-raised text-text-muted px-2 py-0.5 rounded">
                  {k}
                </span>
              ))}
            </div>
          </div>
        )}
        {analysis && <p className="text-sm text-text-primary">{analysis}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="font-heading text-5xl font-bold text-accent leading-none">
        {score ?? '?'}
        <span className="text-lg text-text-muted font-normal"> / 100</span>
      </p>
      {missing.length > 0 && (
        <div>
          <p className="text-xs text-text-muted mb-1">Missing keywords:</p>
          <div className="flex flex-wrap gap-1">
            {missing.map((k, i) => (
              <span key={i} className="text-xs bg-surface-raised text-text-muted px-2 py-0.5 rounded">
                {k}
              </span>
            ))}
          </div>
        </div>
      )}
      {analysis && <p className="text-sm text-text-primary mt-2">{analysis}</p>}
    </div>
  );
}
