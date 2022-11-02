from pydantic import BaseModel
from typing import List, Optional


class HWork(BaseModel):
    """Подкласс структуры домашней работы."""

    homework_name: Optional[str]
    status: Optional[str]


class ResponseModel(BaseModel):
    """Класс структуры результата запроса."""

    current_date: int
    homeworks: List[HWork]
