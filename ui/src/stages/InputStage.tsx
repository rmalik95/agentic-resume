import { useCallback, useRef, useState } from 'react';

interface Props {
  onStart: (form: FormData) => void;
}

export default function InputStage({ onStart }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState('');
  const [showOptions, setShowOptions] = useState(false);
  const [companyUrl, setCompanyUrl] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [coverLetterChoice, setCoverLetterChoice] = useState('ask');
  const [dragOver, setDragOver] = useState(false);
  const [fileError, setFileError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const canStart = file !== null && jd.trim().length > 0;

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setFileError('Only .pdf files are accepted');
      return;
    }
    setFileError('');
    setFile(f);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    },
    [handleFile],
  );

  const handleSubmit = () => {
    if (!canStart || !file) return;
    const form = new FormData();
    form.append('resume_file', file);
    form.append('job_description', jd);
    form.append('company_url', companyUrl);
    form.append('job_title', jobTitle || 'Unknown Role');
    form.append('company_name', companyName || 'Unknown Company');
    form.append('cover_letter_choice', coverLetterChoice);
    onStart(form);
  };

  return (
    <div className="stage-enter mx-auto w-full max-w-[680px] px-6 py-16">
      {/* Wordmark */}
      <p className="font-mono text-sm font-medium text-text-muted mb-12 tracking-wider">
        ResumAI
      </p>

      {/* CV Upload Zone */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-text-primary mb-2">
          Your CV
        </label>
        {file ? (
          <div className="flex items-center gap-3 rounded-[10px] border border-border bg-surface p-4">
            <span className="text-success text-lg">✓</span>
            <span className="text-sm text-text-primary flex-1 truncate">
              {file.name}{' '}
              <span className="text-text-muted">
                ({(file.size / 1024).toFixed(0)} KB)
              </span>
            </span>
            <button
              onClick={() => setFile(null)}
              className="text-xs text-text-muted hover:text-error transition-colors"
            >
              Remove
            </button>
          </div>
        ) : (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
            className={`flex flex-col items-center justify-center rounded-[10px] border-2 border-dashed p-10 cursor-pointer transition-colors ${
              dragOver
                ? 'border-accent bg-accent/5'
                : 'border-border hover:border-text-muted'
            }`}
          >
            <p className="text-sm text-text-muted">
              Drop your CV here or click to browse
            </p>
            <p className="text-xs text-text-muted mt-1">.pdf only</p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) handleFile(e.target.files[0]);
              }}
            />
          </div>
        )}
        {fileError && (
          <p className="text-xs text-error mt-2">{fileError}</p>
        )}
      </div>

      {/* Job Description */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-text-primary mb-2">
          Paste the job description
        </label>
        <div className="relative">
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the full job description here — including requirements, responsibilities, and any detail about the role."
            className="w-full min-h-[200px] max-h-[500px] rounded-[10px] border border-border bg-surface p-4 text-[15px] text-text-primary placeholder:text-text-muted resize-y focus:outline-none focus:border-accent transition-colors"
          />
          <span className="absolute bottom-3 right-3 text-xs text-text-muted font-mono">
            {jd.length}
          </span>
        </div>
      </div>

      {/* Optional Settings */}
      <div className="mb-10">
        <button
          onClick={() => setShowOptions(!showOptions)}
          className="text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          {showOptions ? '▾' : '▸'} More options
        </button>
        {showOptions && (
          <div className="mt-4 space-y-4 rounded-[10px] border border-border bg-surface p-5">
            <div>
              <label className="block text-xs text-text-muted mb-1">
                Company URL
              </label>
              <input
                type="url"
                value={companyUrl}
                onChange={(e) => setCompanyUrl(e.target.value)}
                placeholder="https://company.com/about"
                className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-text-muted mb-1">
                  Job title
                </label>
                <input
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">
                  Company name
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-2">
                Cover letter
              </label>
              <div className="flex gap-4 text-sm">
                {(['ask', 'always', 'skip'] as const).map((val) => (
                  <label key={val} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="cover_letter"
                      value={val}
                      checked={coverLetterChoice === val}
                      onChange={() => setCoverLetterChoice(val)}
                      className="accent-accent"
                    />
                    <span className="text-text-primary">
                      {val === 'ask' ? 'Ask me after' : val === 'always' ? 'Always generate' : 'Skip'}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Start Button */}
      <button
        onClick={handleSubmit}
        disabled={!canStart}
        className={`w-full sm:w-auto sm:mx-auto sm:block px-8 py-3 rounded-[10px] font-heading font-semibold text-[15px] transition-all ${
          canStart
            ? 'bg-accent text-white hover:brightness-110 cursor-pointer'
            : 'bg-surface-raised text-text-muted cursor-not-allowed'
        }`}
      >
        Optimise my CV
      </button>
    </div>
  );
}
