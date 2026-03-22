from abc import ABC, abstractmethod

from state import ResumeState
from utils.prompt_loader import load_prompt


class BaseAgent(ABC):
    prompt_name: str

    def __init__(self) -> None:
        if not getattr(self, "prompt_name", None):
            raise ValueError("Agent must define prompt_name")
        self.system_prompt = load_prompt(self.prompt_name)

    @abstractmethod
    def run(self, state: ResumeState) -> ResumeState:
        raise NotImplementedError
