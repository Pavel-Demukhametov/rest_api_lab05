from pydantic import BaseModel
from typing import Optional, Dict, List

class Relationship(BaseModel):
    to_id: int
    type: str  # Например, "Follow" или "Subscribe"

class NodeCreate(BaseModel):
    id: int
    label: str  # Тип узла, например "User" или "Group"
    attributes: Optional[Dict[str, str]] = None  # Дополнительные атрибуты узла
    relationships: Optional[List[Relationship]] = None  # Например, {"to_id": 123, "type": "Follow"}