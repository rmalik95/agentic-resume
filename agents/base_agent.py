from abc import ABC, abstractmethod

from state import ResumeState
from utils.prompt_loader import load_prompt


class BaseAgent(ABC):
    """Base class that loads a system prompt for each concrete agent."""

    prompt_name: str = ""

    def __init__(self) -> None:
        """Initialize prompt text from prompts directory when configured."""
        self.system_prompt = load_prompt(self.prompt_name) if self.prompt_name else ""

    @abstractmethod
    def run(self, state: ResumeState) -> ResumeState:
        raise NotImplementedError
