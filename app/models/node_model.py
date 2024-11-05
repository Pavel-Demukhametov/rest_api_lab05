from pydantic import BaseModel
from typing import Optional, Dict, List

class Relationship(BaseModel):
    to_id: int
    type: str 

class NodeCreate(BaseModel):
    id: int
    label: str
    attributes: Optional[Dict[str, str]] = None
    relationships: Optional[List[Relationship]] = None