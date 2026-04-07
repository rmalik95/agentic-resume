/** Thin wrappers around fetch for the ResumAI API. */

const BASE = '/api';

export async function startRun(form: FormData): Promise<string> {
  const res = await fetch(`${BASE}/run`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || 'Failed to start run');
  }
  const data = await res.json();
  return data.run_id as string;
}

export function streamUrl(runId: string): string {
  return `${BASE}/run/${runId}/stream`;
}

export function outputUrl(runId: string, filename: string): string {
  return `${BASE}/run/${runId}/output/${encodeURIComponent(filename)}`;
}

export async function answerCoverLetter(
  runId: string,
  generate: boolean,
  companyContext: string = '',
): Promise<void> {
  const res = await fetch(`${BASE}/run/${runId}/cover-letter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ generate, company_context: companyContext }),
  });
  if (!res.ok) throw new Error('Failed to submit cover letter decision');
}

export async function answerLowScore(runId: string, proceed: boolean): Promise<void> {
  const res = await fetch(`${BASE}/run/${runId}/low-score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proceed }),
  });
  if (!res.ok) throw new Error('Failed to submit low score decision');
}
