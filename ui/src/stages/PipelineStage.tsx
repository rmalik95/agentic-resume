import { AGENT_LIST, AGENT_MAP } from '../lib/agentMeta';
import type { PipelineState } from '../hooks/usePipelineStream';
import AgentTimeline from '../components/AgentTimeline';
import ReasoningPanel from '../components/ReasoningPanel';
import CoverLetterModal from '../components/CoverLetterModal';
import LowScoreModal from '../components/LowScoreModal';

interface Props {
  state: PipelineState;
  onCoverLetterAnswer: (generate: boolean, context: string) => void;
  onLowScoreAnswer: (proceed: boolean) => void;
}

export default function PipelineStage({ state, onCoverLetterAnswer, onLowScoreAnswer }: Props) {
  const activeKey = state.activeAgent;
  // Show the most recent agent that has data (active or last completed)
  const displayKey =
    activeKey ??
    [...AGENT_LIST]
      .reverse()
      .find((a) => state.agents[a.key]?.status === 'complete' || state.agents[a.key]?.status === 'error')
      ?.key ??
    null;

  const meta = displayKey ? AGENT_MAP[displayKey] : null;
  const agentState = displayKey ? state.agents[displayKey] : null;

  return (
    <div className="stage-enter flex flex-col lg:flex-row gap-8 px-6 md:px-12 lg:px-16 py-10 min-h-screen">
      {/* Left — Agent Timeline */}
      <div className="w-full lg:w-[220px] shrink-0">
        <AgentTimeline agents={AGENT_LIST} agentStates={state.agents} activeAgent={activeKey} />
      </div>

      {/* Right — Reasoning Panel */}
      <div className="flex-1 min-w-0">
        {meta && agentState ? (
          <ReasoningPanel meta={meta} agentState={agentState} />
        ) : (
          <div className="flex items-center justify-center h-[400px] text-text-muted text-sm">
            Waiting for pipeline to start…
          </div>
        )}
      </div>

      {/* Cover Letter Gate Modal */}
      {state.stage === 'cover_letter_gate' && (
        <CoverLetterModal onAnswer={onCoverLetterAnswer} />
      )}

      {/* Low Match Score Gate Modal */}
      {state.stage === 'low_score_gate' && (
        <LowScoreModal
          score={(state.lowScoreGateData?.match_score as number | undefined) ?? 0}
          threshold={(state.lowScoreGateData?.threshold as number | undefined) ?? 50}
          onAnswer={onLowScoreAnswer}
        />
      )}
    </div>
  );
}
