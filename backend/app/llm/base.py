from abc import ABC, abstractmethod

from ..schemas import RequirementsAnalysis


class LLMProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def generate_analysis(self, project_name: str, project_description: str, contexts: list[dict]) -> RequirementsAnalysis:
        raise NotImplementedError

    @abstractmethod
    def answer_question(self, question: str, contexts: list[dict]) -> str:
        raise NotImplementedError