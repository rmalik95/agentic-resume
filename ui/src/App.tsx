import { useCallback } from 'react';
import InputStage from './stages/InputStage';
import PipelineStage from './stages/PipelineStage';
import ResultsStage from './stages/ResultsStage';
import { usePipelineStream } from './hooks/usePipelineStream';
import { startRun, answerCoverLetter, answerLowScore } from './lib/api';

export default function App() {
  const {
    state,
    startStream,
    answerCoverLetter: markAnswered,
    answerLowScore: markLowScoreAnswered,
    reset,
  } = usePipelineStream();

  const handleStart = useCallback(
    async (form: FormData) => {
      try {
        const runId = await startRun(form);
        startStream(runId);
      } catch (err) {
        console.error('Failed to start run:', err);
      }
    },
    [startStream],
  );

  const handleCoverLetterAnswer = useCallback(
    async (generate: boolean, context: string) => {
      if (!state.runId) return;
      try {
        await answerCoverLetter(state.runId, generate, context);
        markAnswered();
      } catch (err) {
        console.error('Failed to submit cover letter decision:', err);
      }
    },
    [state.runId, markAnswered],
  );

  const handleLowScoreAnswer = useCallback(
    async (proceed: boolean) => {
      if (!state.runId) return;
      try {
        await answerLowScore(state.runId, proceed);
        if (proceed) {
          markLowScoreAnswered();
        }
      } catch (err) {
        console.error('Failed to submit low score decision:', err);
      }
    },
    [state.runId, markLowScoreAnswered],
  );

  return (
    <div className="min-h-screen">
      {state.stage === 'idle' && <InputStage onStart={handleStart} />}
      {(state.stage === 'running' || state.stage === 'cover_letter_gate' || state.stage === 'low_score_gate') && (
        <PipelineStage
          state={state}
          onCoverLetterAnswer={handleCoverLetterAnswer}
          onLowScoreAnswer={handleLowScoreAnswer}
        />
      )}
      {state.stage === 'complete' && (
        <ResultsStage state={state} onReset={reset} />
      )}
    </div>
  );
}
