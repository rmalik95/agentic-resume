/** Static metadata for each pipeline agent — display names and reasoning copy. */

export interface AgentMeta {
  key: string;
  displayName: string;
  reasoning: string;
  icon: string; // emoji shorthand
}

const agents: AgentMeta[] = [
  {
    key: 'pdf_parse',
    displayName: 'Reading your CV',
    reasoning:
      'Your CV is being converted from PDF to structured text. Font sizes, bold text, and bullet characters are used to reconstruct headings, sections, and list items. No content is added or removed at this step.',
    icon: '📄',
  },
  {
    key: 'match_score_before',
    displayName: 'Scoring your CV (before)',
    reasoning:
      'Your CV is being scored against the job description before any changes are made. This baseline score will be compared against your final score so you can see exactly how much the optimisation improved your match.',
    icon: '🔍',
  },
  {
    key: 'positioning_strategy',
    displayName: 'Positioning strategy',
    reasoning:
      'Before any writing begins, this step decides how to frame you as a candidate. It reads your CV and the job description and produces a positioning brief — your target headline, what to emphasise, what to reduce, and how to set your seniority level relative to the role.',
    icon: '🎯',
  },
  {
    key: 'jd_intelligence',
    displayName: 'Job description analysis',
    reasoning:
      'This step reads the job description the way a senior recruiter would. It extracts the top keywords, identifies the hidden expectations behind the formal language, and maps the tools, seniority signals, and culture markers that most candidates miss.',
    icon: '📋',
  },
  {
    key: 'gap_analysis',
    displayName: 'Gap analysis',
    reasoning:
      'This step compares your CV directly against the job description, the positioning strategy, and the JD analysis produced in the previous steps. It produces a frank assessment of what is missing, what is undersold, and what should be removed — before any rewriting begins.',
    icon: '⚖️',
  },
  {
    key: 'cv_rewrite',
    displayName: 'Rewriting your CV',
    reasoning:
      'This is the longest and most important step. Your CV is being fully rewritten using all of the intelligence gathered so far. The agent will not invent experience, qualifications, or metrics — any numbers or dates that need your input will be marked with [brackets] for you to review.',
    icon: '✏️',
  },
  {
    key: 'ats_qa_scan',
    displayName: 'ATS & recruiter check',
    reasoning:
      'The rewritten CV is now being read by a simulated ATS parser and a simulated recruiter doing a 10-second screen. This step checks for formatting risks, keyword coverage, seniority alignment, and anything that could trigger an automatic rejection.',
    icon: '🤖',
  },
  {
    key: 'cover_letter',
    displayName: 'Cover letter',
    reasoning:
      'A targeted cover letter is being written using the optimised CV and any company context provided. It will not repeat the CV verbatim — it will address why you are applying, what you bring to this specific role, and why this company.',
    icon: '💌',
  },
  {
    key: 'match_score_after',
    displayName: 'Scoring your CV (after)',
    reasoning:
      'Your optimised CV is being scored against the same job description using the same rubric as the baseline score. The delta shows how much the optimisation improved your match.',
    icon: '📊',
  },
  {
    key: 'latex_generator',
    displayName: 'Generating LaTeX',
    reasoning:
      'The optimised CV is being formatted into a professional LaTeX document using the moderncv template. Your name, email, and phone number are extracted directly from your original CV — not from the rewritten text.',
    icon: '📐',
  },
  {
    key: 'renderer',
    displayName: 'Compiling PDF',
    reasoning:
      'The LaTeX document is being compiled into a PDF. If the primary renderer is unavailable, a local fallback is used automatically. If both fail, a raw .tex file is saved so you can compile it manually in Overleaf.',
    icon: '🖨️',
  },
];

export const AGENT_LIST = agents;
export const AGENT_MAP = Object.fromEntries(agents.map((a) => [a.key, a]));
