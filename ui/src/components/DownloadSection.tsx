import { outputUrl } from '../lib/api';

interface Props {
  runId: string;
  pdfResumePath?: string;
  pdfCoverPath?: string;
  markdownPath?: string;
  renderError?: string;
}

function basename(path: string): string {
  return path.split('/').pop() ?? path;
}

export default function DownloadSection({
  runId,
  pdfResumePath,
  pdfCoverPath,
  markdownPath,
  renderError,
}: Props) {
  const buttons: { label: string; href: string; available: boolean }[] = [];

  if (pdfResumePath && !renderError) {
    buttons.push({
      label: 'Download CV (PDF)',
      href: outputUrl(runId, basename(pdfResumePath)),
      available: true,
    });
  } else if (renderError) {
    // Offer fallback tex download
    buttons.push({
      label: 'Download raw LaTeX (.tex)',
      href: outputUrl(runId, 'resume_fallback.tex'),
      available: true,
    });
  }

  if (markdownPath) {
    buttons.push({
      label: 'Download CV (Markdown)',
      href: outputUrl(runId, basename(markdownPath)),
      available: true,
    });
  }

  if (pdfCoverPath) {
    buttons.push({
      label: 'Download Cover Letter (PDF)',
      href: outputUrl(runId, basename(pdfCoverPath)),
      available: true,
    });
  }

  return (
    <div className="mb-6">
      <h2 className="font-heading text-lg font-semibold mb-3">Downloads</h2>

      {renderError && (
        <p className="text-sm text-warning mb-3">
          PDF rendering failed — download the raw LaTeX and upload it to{' '}
          <a
            href="https://www.overleaf.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline text-accent"
          >
            Overleaf
          </a>{' '}
          to compile it.
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        {buttons.map((btn, i) => (
          <a
            key={i}
            href={btn.href}
            download
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[10px] bg-accent text-white text-sm font-medium hover:brightness-110 transition-all"
          >
            ↓ {btn.label}
          </a>
        ))}
      </div>
    </div>
  );
}
