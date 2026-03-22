from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


class LaTeXGeneratorAgent(BaseAgent):
    """Generate resume and cover-letter LaTeX split by delimiter."""

    prompt_name = "latex_generator"

    def run(self, state: ResumeState) -> ResumeState:
        """Populate latex_resume and latex_cover_letter fields.

        Example:
            state = LaTeXGeneratorAgent().run(state)
        """
        user_message = (
            f"Optimized resume content:\n{state.optimized_experience or state.resume_text}\n\n"
            f"Cover letter content:\n{state.cover_letter or ''}\n\n"
            "Return two LaTeX documents separated by ---COVERLETTER---"
        )
        response = call_llm(self.system_prompt, user_message, max_tokens=2000)
        parts = response.split("---COVERLETTER---", maxsplit=1)
        if len(parts) != 2:
            raise ValueError("LaTeXGeneratorAgent output missing ---COVERLETTER--- delimiter")

        state.latex_resume = parts[0].strip()
        state.latex_cover_letter = parts[1].strip()
        return state
