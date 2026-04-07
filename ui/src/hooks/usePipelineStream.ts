import { useCallback, useReducer, useRef } from 'react';
import { streamUrl } from '../lib/api';

export type AgentStatus = 'pending' | 'active' | 'complete' | 'error' | 'skipped';

export interface AgentState {
  status: AgentStatus;
  data: Record<string, unknown>;
  elapsedMs?: number;
  error?: string;
}

export interface PipelineState {
  stage: 'idle' | 'running' | 'cover_letter_gate' | 'low_score_gate' | 'complete' | 'error';
  agents: Record<string, AgentState>;
  activeAgent: string | null;
  finalPayload: Record<string, unknown> | null;
  runId: string | null;
  lowScoreGateData: Record<string, unknown> | null;
}

type Action =
  | { type: 'START_RUN'; runId: string }
  | { type: 'AGENT_START'; agent: string; data: Record<string, unknown> }
  | { type: 'AGENT_COMPLETE'; agent: string; data: Record<string, unknown> }
  | { type: 'AGENT_ERROR'; agent: string; data: Record<string, unknown> }
  | { type: 'LOW_SCORE_GATE'; data: Record<string, unknown> }
  | { type: 'LOW_SCORE_ANSWERED' }
  | { type: 'COVER_LETTER_GATE' }
  | { type: 'COVER_LETTER_ANSWERED' }
  | { type: 'PIPELINE_COMPLETE'; data: Record<string, unknown> }
  | { type: 'RESET' };

const initialState: PipelineState = {
  stage: 'idle',
  agents: {},
  activeAgent: null,
  finalPayload: null,
  runId: null,
  lowScoreGateData: null,
};

function reducer(state: PipelineState, action: Action): PipelineState {
  switch (action.type) {
    case 'START_RUN':
      return { ...initialState, stage: 'running', runId: action.runId };
    case 'AGENT_START':
      return {
        ...state,
        activeAgent: action.agent,
        agents: {
          ...state.agents,
          [action.agent]: { status: 'active', data: action.data },
        },
      };
    case 'AGENT_COMPLETE':
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.agent]: {
            status: action.data.skipped ? 'skipped' : 'complete',
            data: action.data,
            elapsedMs: action.data.elapsed_ms as number | undefined,
          },
        },
      };
    case 'AGENT_ERROR':
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.agent]: {
            status: 'error',
            data: action.data,
            error: action.data.error as string,
            elapsedMs: action.data.elapsed_ms as number | undefined,
          },
        },
      };
    case 'LOW_SCORE_GATE':
      return { ...state, stage: 'low_score_gate', lowScoreGateData: action.data };
    case 'LOW_SCORE_ANSWERED':
      return { ...state, stage: 'running' };
    case 'COVER_LETTER_GATE':
      return { ...state, stage: 'cover_letter_gate' };
    case 'COVER_LETTER_ANSWERED':
      return { ...state, stage: 'running' };
    case 'PIPELINE_COMPLETE':
      return { ...state, stage: 'complete', activeAgent: null, finalPayload: action.data };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export function usePipelineStream() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const esRef = useRef<EventSource | null>(null);

  const startStream = useCallback((runId: string) => {
    dispatch({ type: 'START_RUN', runId });

    const es = new EventSource(streamUrl(runId));
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const { event, agent, data } = payload;

        switch (event) {
          case 'agent_start':
            dispatch({ type: 'AGENT_START', agent, data });
            break;
          case 'agent_complete':
            dispatch({ type: 'AGENT_COMPLETE', agent, data });
            break;
          case 'agent_error':
            dispatch({ type: 'AGENT_ERROR', agent, data });
            break;
          case 'low_score_gate':
            dispatch({ type: 'LOW_SCORE_GATE', data });
            break;
          case 'cover_letter_gate':
            dispatch({ type: 'COVER_LETTER_GATE' });
            break;
          case 'pipeline_complete':
            dispatch({ type: 'PIPELINE_COMPLETE', data });
            es.close();
            break;
        }
      } catch {
        // ignore malformed events
      }
    };

    es.addEventListener('done', () => {
      es.close();
    });

    es.onerror = () => {
      es.close();
    };
  }, []);

  const answerCoverLetter = useCallback(() => {
    dispatch({ type: 'COVER_LETTER_ANSWERED' });
  }, []);

  const answerLowScore = useCallback(() => {
    dispatch({ type: 'LOW_SCORE_ANSWERED' });
  }, []);

  const reset = useCallback(() => {
    esRef.current?.close();
    dispatch({ type: 'RESET' });
  }, []);

  return { state, startStream, answerCoverLetter, answerLowScore, reset };
}
