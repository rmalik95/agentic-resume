from abc import ABC, abstractmethod

from state import ResumeState
from utils.prompt_loader import load_global_instructions, load_prompt


class BaseAgent(ABC):
    """Base class that loads a system prompt for each concrete agent."""

    prompt_name: str = ""
    use_global_instructions: bool = False

    def __init__(self) -> None:
        """Initialize prompt text from prompts directory when configured."""
        self.system_prompt = load_prompt(self.prompt_name) if self.prompt_name else ""
        if self.use_global_instructions:
            global_text = load_global_instructions()
            if global_text:
                self.system_prompt = f"{global_text}\n\n{self.system_prompt}"

    @abstractmethod
    def run(self, state: ResumeState) -> ResumeState:
        raise NotImplementedError
