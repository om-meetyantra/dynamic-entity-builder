from typing import List
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from app.database import get_driver
from app.schemas import EntityCreate, EntityResponse, FacetCreate, FacetResponse, RelationCreate, RelationResponse, GraphResponse
from app.core.builder import SystemBuilder

router = APIRouter()

@router.post("/entities", response_model=EntityResponse)
def create_entity(entity: EntityCreate, driver: Driver = Depends(get_driver)):
    return SystemBuilder.create_entity(driver, entity)

@router.get("/entities", response_model=List[EntityResponse])
def get_entities(driver: Driver = Depends(get_driver)):
    return SystemBuilder.get_all_entities(driver)

@router.get("/entities/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: str, driver: Driver = Depends(get_driver)):
    db_entity = SystemBuilder.get_entity(driver, entity_id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db_entity

@router.post("/entities/{entity_id}/facets", response_model=FacetResponse)
def add_entity_facet(entity_id: str, facet: FacetCreate, driver: Driver = Depends(get_driver)):
    return SystemBuilder.add_facet(driver, entity_id, facet, target_type="Entity")

@router.post("/relations/{relation_id}/facets", response_model=FacetResponse)
def add_relation_facet(relation_id: str, facet: FacetCreate, driver: Driver = Depends(get_driver)):
    return SystemBuilder.add_facet(driver, relation_id, facet, target_type="RelationDefinition")

@router.post("/entities/{entity_id}/relations", response_model=RelationResponse)
def create_relation(entity_id: str, relation: RelationCreate, driver: Driver = Depends(get_driver)):
    return SystemBuilder.create_relation(driver, entity_id, relation)

@router.get("/graph", response_model=GraphResponse)
def get_graph(driver: Driver = Depends(get_driver)):
    return SystemBuilder.get_graph(driver)
