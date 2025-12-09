from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class FacetCreate(BaseModel):
    type: str # 'property', 'lifecycle'
    configuration: Dict[str, Any]

class FacetResponse(FacetCreate):
    id: int
    entity_id: int

    class Config:
        from_attributes = True

class RelationCreate(BaseModel):
    target_entity_id: int
    name: str
    description: Optional[str] = None

class RelationResponse(RelationCreate):
    id: int
    source_entity_id: int

    class Config:
        from_attributes = True

class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None

class EntityResponse(EntityCreate):
    id: int
    facets: List[FacetResponse] = []
    outgoing_relations: List[RelationResponse] = []
    incoming_relations: List[RelationResponse] = []

    class Config:
        from_attributes = True
