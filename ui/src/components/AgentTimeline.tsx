import type { AgentMeta } from '../lib/agentMeta';
import type { AgentState, AgentStatus } from '../hooks/usePipelineStream';

interface Props {
  agents: AgentMeta[];
  agentStates: Record<string, AgentState>;
  activeAgent: string | null;
}

function StatusIcon({ status }: { status: AgentStatus }) {
  switch (status) {
    case 'active':
      return (
        <span className="inline-block w-4 h-4 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      );
    case 'complete':
      return <span className="text-success text-sm">✓</span>;
    case 'error':
      return <span className="text-error text-sm">✕</span>;
    case 'skipped':
      return <span className="text-text-muted text-sm">—</span>;
    default:
      return <span className="inline-block w-3 h-3 rounded-full bg-border" />;
  }
}

export default function AgentTimeline({ agents, agentStates, activeAgent }: Props) {
  return (
    <div role="status" aria-label="Pipeline progress">
      <p className="font-mono text-xs text-text-muted mb-4 uppercase tracking-wider">
        Pipeline
      </p>
      <ul className="space-y-0.5">
        {agents.map((agent) => {
          const state = agentStates[agent.key];
          const status: AgentStatus = state?.status ?? 'pending';
          const isActive = agent.key === activeAgent;
          const elapsed = state?.elapsedMs;

          return (
            <li
              key={agent.key}
              className={`flex items-center gap-3 h-12 px-3 rounded-lg transition-all duration-150 ${
                isActive
                  ? 'bg-surface-raised border-l-2 border-accent'
                  : 'border-l-2 border-transparent'
              } ${status === 'pending' ? 'opacity-40' : ''}`}
            >
              <span className="w-5 flex-shrink-0 flex items-center justify-center">
                <StatusIcon status={status} />
              </span>
              <span
                className={`font-heading text-[13px] font-medium flex-1 truncate ${
                  isActive ? 'text-text-primary' : 'text-text-muted'
                }`}
              >
                {agent.displayName}
              </span>
              {elapsed !== undefined && status !== 'pending' && (
                <span className="font-mono text-[11px] text-text-muted whitespace-nowrap">
                  {(elapsed / 1000).toFixed(1)}s
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
