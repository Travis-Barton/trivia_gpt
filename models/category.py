from abc import ABC
from typing import List, Optional, Dict


class Category:
    category_id: str
    name: str
    game_ids: List[str]
