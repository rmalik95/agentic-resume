from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


class ExperienceOptimizerAgent(BaseAgent):
    """Rewrite experience bullets using JD tone and required keywords."""

    prompt_name = "experience_optimizer"

    def run(self, state: ResumeState) -> ResumeState:
        """Generate optimized experience text and collect [REVIEW] lines.

        Example:
            state = ExperienceOptimizerAgent().run(state)
        """
        keywords_text = ", ".join(state.missing_keywords) if state.missing_keywords else "None"
        user_message = (
            f"Original resume:\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}\n\n"
            f"Missing keywords to incorporate:\n{keywords_text}\n\n"
            "Rewrite only the experience content."
        )
        optimized = call_llm(self.system_prompt, user_message, max_tokens=2000)
        state.optimized_experience = optimized.strip()
        state.review_flags = [line.strip() for line in state.optimized_experience.splitlines() if "[REVIEW]" in line]
        return state
