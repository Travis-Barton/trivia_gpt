from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from category import Category


class Question(ABC):
    question_id: str
    answer: str
    category: List[Category]
    fact_checks_score: float
    fact_checks_count: int
    feedback_score: float
    games_used: List[str]



    @abstractmethod
    def get_question(self) -> str:
        pass

    @abstractmethod
    def get_answer(self) -> str:
        pass

    @abstractmethod
    def get_options(self) -> List[str]:
        pass

    @abstractmethod
    def get_explanation(self) -> Optional[str]:
        pass