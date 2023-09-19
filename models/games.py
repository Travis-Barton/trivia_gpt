from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from question import Question
from category import Category
from dataclasses import dataclass


@dataclass
class Games(ABC):
    game_id: str
    user_id: str
    questions: Dict[str, List[Question]]
    categories: List[Category]


@dataclass
class GameState(ABC):
    game_id: str
    user_id: str
    current_page: int
    valid_questions: List[Question]
    invalid_questions: List[Question]
    current_question: Question
    current_category: Category
    current_score: int
    