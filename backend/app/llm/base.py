from abc import ABC, abstractmethod

from ..schemas import RequirementsAnalysis
from ..schemas_pm import ProjectPlan


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

    @abstractmethod
    def generate_project_plan(
        self,
        project_name: str,
        project_description: str,
        requirements: dict,
        project_info: dict,
        feedback: list[str] | None = None,
    ) -> ProjectPlan:
        """Create a project plan from validated Requirements Analyst output.

        ``feedback`` lists validation problems from a previous attempt so the
        model can repair its plan.
        """
        raise NotImplementedError
