import { AGENT_LIST, AGENT_MAP } from '../lib/agentMeta';
import type { PipelineState } from '../hooks/usePipelineStream';
import ScoreCard from '../components/ScoreCard';
import ReviewFlagsPanel from '../components/ReviewFlagsPanel';
import DownloadSection from '../components/DownloadSection';
import TokenMicro from '../components/TokenMicro';
import ReasoningPanel from '../components/ReasoningPanel';
import { useState } from 'react';

interface Props {
  state: PipelineState;
  onReset: () => void;
}

export default function ResultsStage({ state, onReset }: Props) {
  const fp = state.finalPayload ?? {};
  const [openAccordion, setOpenAccordion] = useState<string | null>(null);

  const scoreBefore = (fp.match_score_before as number) ?? 0;
  const scoreAfter = (fp.match_score_after as number) ?? 0;
  const atsVerdict = (fp.ats_verdict as string) ?? 'Unknown';
  const reviewFlags = (fp.review_flags as string[]) ?? [];
  const missingAfter = (fp.missing_keywords_after as string[]) ?? [];
  const keywordsAdded = (fp.keywords_added as string[]) ?? [];
  const pdfResumePath = fp.pdf_resume_path as string | undefined;
  const pdfCoverPath = fp.pdf_cover_letter_path as string | undefined;
  const markdownPath = fp.output_markdown_path as string | undefined;
  const renderError = fp.render_error as string | undefined;
  const terminatedEarly = (fp.terminated_early as boolean) ?? false;
  const terminationReason = (fp.termination_reason as string) ?? '';
  const metrics = (fp.metrics as Record<string, number>) ?? {};

  return (
    <div className="stage-enter mx-auto w-full max-w-[800px] px-6 py-12">
      {/* Header */}
      <h1 className="font-heading text-[28px] font-semibold mb-8">
        Run complete
      </h1>

      {terminatedEarly && (
        <div className="mb-8 rounded-[10px] border border-border bg-surface p-4 text-sm text-text-primary">
          {terminationReason || 'Run stopped before optimisation based on your choice.'}
        </div>
      )}

      {/* Score Summary */}
      <ScoreCard
        before={scoreBefore}
        after={scoreAfter}
        atsVerdict={atsVerdict}
        missingAfter={missingAfter}
        keywordsAdded={keywordsAdded}
      />

      {/* Review Flags */}
      {reviewFlags.length > 0 && (
        <ReviewFlagsPanel flags={reviewFlags} />
      )}

      {/* Downloads */}
      <DownloadSection
        runId={state.runId!}
        pdfResumePath={pdfResumePath}
        pdfCoverPath={pdfCoverPath}
        markdownPath={markdownPath}
        renderError={renderError}
      />

      {/* Agent Output Review Accordion */}
      <div className="mt-10">
        <h2 className="font-heading text-lg font-semibold mb-4">
          Agent output review
        </h2>
        <div className="space-y-2">
          {AGENT_LIST.map((agentMeta) => {
            const as_ = state.agents[agentMeta.key];
            if (!as_ || as_.status === 'pending') return null;
            const isOpen = openAccordion === agentMeta.key;
            return (
              <div
                key={agentMeta.key}
                className="rounded-[10px] border border-border bg-surface overflow-hidden"
              >
                <button
                  onClick={() => setOpenAccordion(isOpen ? null : agentMeta.key)}
                  className="w-full px-5 py-3 flex items-center justify-between text-left hover:bg-surface-raised transition-colors"
                >
                  <span className="text-sm font-heading font-medium">
                    {agentMeta.icon} {agentMeta.displayName}
                  </span>
                  <span className="text-xs text-text-muted">
                    {isOpen ? '▾' : '▸'}
                  </span>
                </button>
                {isOpen && (
                  <div className="px-5 pb-4">
                    <ReasoningPanel meta={AGENT_MAP[agentMeta.key]} agentState={as_} compact />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* LLM Usage Summary */}
      <div className="mt-10">
        <h2 className="font-heading text-lg font-semibold mb-3">
          LLM usage summary
        </h2>
        <TokenMicro metrics={metrics} />
      </div>

      {/* Start New Run */}
      <div className="mt-12 text-center">
        <button
          onClick={onReset}
          className="px-8 py-3 rounded-[10px] border border-border bg-surface font-heading font-semibold text-sm text-text-primary hover:bg-surface-raised transition-colors"
        >
          Optimise another CV
        </button>
      </div>
    </div>
  );
}
