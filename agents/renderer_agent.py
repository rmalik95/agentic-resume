import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

from state import ResumeState


logger = logging.getLogger(__name__)
OUTPUTS_DIR = Path("outputs")


class RendererAgent:
    """Render LaTeX into PDFs using API-first fallback chain."""

    def run(self, state: ResumeState) -> ResumeState:
        """Compile resume and cover letter LaTeX and set output paths.

        Example:
            state = RendererAgent().run(state)
        """
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        resume_pdf = OUTPUTS_DIR / "resume_optimised.pdf"
        cover_pdf = OUTPUTS_DIR / "cover_letter.pdf"

        if not state.latex_resume or not state.latex_cover_letter:
            raise ValueError("RendererAgent requires latex_resume and latex_cover_letter")

        resume_ok = self._render_single(state.latex_resume, resume_pdf, "resume")
        cover_ok = self._render_single(state.latex_cover_letter, cover_pdf, "cover_letter")

        if resume_ok:
            state.pdf_resume_path = str(resume_pdf)
            print(f"PDF saved to: {state.pdf_resume_path}")
        if cover_ok:
            state.pdf_cover_letter_path = str(cover_pdf)
            print(f"PDF saved to: {state.pdf_cover_letter_path}")

        if not resume_ok or not cover_ok:
            state.render_error = "One or more PDF renders failed. Raw .tex fallback saved to outputs/."

        return state

    def _render_single(self, latex_code: str, output_path: Path, stem: str) -> bool:
        if self._render_with_latexonline(latex_code, output_path):
            return True
        if self._render_with_pdflatex(latex_code, output_path):
            return True

        fallback_tex = OUTPUTS_DIR / f"{stem}_fallback.tex"
        fallback_tex.write_text(latex_code, encoding="utf-8")
        logger.error("Rendering failed for %s; fallback tex saved at %s", stem, fallback_tex)
        return False

    def _render_with_latexonline(self, latex_code: str, output_path: Path) -> bool:
        try:
            response = requests.post(
                "https://latexonline.cc/compile",
                data={"text": latex_code},
                timeout=30,
            )
            content_type = response.headers.get("content-type", "")
            if response.status_code == 200 and "application/pdf" in content_type.lower():
                output_path.write_bytes(response.content)
                return True
            logger.warning(
                "LaTeX.Online render failed status=%s content_type=%s",
                response.status_code,
                content_type,
            )
        except Exception as exc:
            logger.warning("LaTeX.Online request failed: %s", exc)
        return False

    def _render_with_pdflatex(self, latex_code: str, output_path: Path) -> bool:
        pdflatex_path = shutil.which("pdflatex")
        if not pdflatex_path:
            logger.info("pdflatex not found on PATH")
            return False

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                tex_file = tmp_path / "document.tex"
                tex_file.write_text(latex_code, encoding="utf-8")

                command = [pdflatex_path, "-interaction=nonstopmode", "document.tex"]
                first = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)
                second = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)

                pdf_file = tmp_path / "document.pdf"
                if first.returncode == 0 and second.returncode == 0 and pdf_file.exists():
                    output_path.write_bytes(pdf_file.read_bytes())
                    return True

                logger.warning(
                    "pdflatex failed with return codes %s/%s",
                    first.returncode,
                    second.returncode,
                )
        except Exception as exc:
            logger.warning("pdflatex fallback failed: %s", exc)
        return False
