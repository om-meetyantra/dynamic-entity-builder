from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

# Facet Types: 'property', 'lifecycle', 'criteria', 'entity'

class FacetCreate(BaseModel):
    type: str 
    # configuration can be flexible. 
    # For property: { "name": "p1", "datatype": "string" }
    # For criteria: { "name": "c1", "rule": "x > 10" }
    # For entity: { "target_entity_id": "uuid" }
    configuration: Dict[str, Any]

class FacetUpdate(BaseModel):
    # Only allow updating configuration for now, maybe type?
    # Usually type shouldn't change, but configuration might.
    configuration: Optional[Dict[str, Any]] = None

class FacetResponse(FacetCreate):
    id: str
    entity_id: Optional[str] = None # Can belong to Entity OR Relation
    relation_id: Optional[str] = None

class RelationCreate(BaseModel):
    target_entity_id: str
    name: str
    description: Optional[str] = None

class RelationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RelationResponse(RelationCreate):
    id: str
    source_entity_id: str
    facets: List[FacetResponse] = [] # Relations can now have facets

class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None

class EntityUpdate(BaseModel):
    name: Optional[str] = None
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
    # facets: List[FacetResponse] # Optional in graph view maybe? simplified 
    facets: List[Dict[str, Any]]

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_name: str
    relation_id: str
    # facets: List[FacetResponse]
    facets: List[Dict[str, Any]]

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
