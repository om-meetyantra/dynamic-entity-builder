from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class FacetCreate(BaseModel):
    type: str # 'property', 'lifecycle'
    configuration: Dict[str, Any]

class FacetResponse(FacetCreate):
    id: str
    entity_id: str

class RelationCreate(BaseModel):
    target_entity_id: str
    name: str
    description: Optional[str] = None

class RelationResponse(RelationCreate):
    id: str
    source_entity_id: str

class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None

class EntityResponse(EntityCreate):
    id: str
    facets: List[FacetResponse] = []
    outgoing_relations: List[RelationResponse] = []
    incoming_relations: List[RelationResponse] = []

class GraphNode(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    facets: List[FacetResponse]

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_name: str
    relation_id: str

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
