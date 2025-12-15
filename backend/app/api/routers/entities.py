from typing import List
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from app.database import get_driver
from app.schemas import EntityCreate, EntityUpdate, EntityResponse, FacetCreate, FacetResponse, RelationResponse, RelationCreate
from app.services.entity_service import EntityService
from app.services.relation_service import RelationService
from app.services.facet_service import FacetService

router = APIRouter()

@router.post("", response_model=EntityResponse)
def create_entity(entity: EntityCreate, driver: Driver = Depends(get_driver)):
    return EntityService.create_entity(driver, entity)

@router.get("", response_model=List[EntityResponse])
def get_entities(driver: Driver = Depends(get_driver)):
    return EntityService.get_all_entities(driver)

@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: str, driver: Driver = Depends(get_driver)):
    db_entity = EntityService.get_entity(driver, entity_id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db_entity

@router.put("/{entity_id}", response_model=EntityResponse)
def update_entity(entity_id: str, updates: EntityUpdate, driver: Driver = Depends(get_driver)):
    db_entity = EntityService.update_entity(driver, entity_id, updates)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db_entity

@router.delete("/{entity_id}")
def delete_entity(entity_id: str, driver: Driver = Depends(get_driver)):
    return EntityService.delete_entity(driver, entity_id)

@router.post("/{entity_id}/facets", response_model=FacetResponse)
def add_entity_facet(entity_id: str, facet: FacetCreate, driver: Driver = Depends(get_driver)):
    return FacetService.add_facet(driver, entity_id, facet, target_type="Entity")

@router.post("/{entity_id}/relations", response_model=RelationResponse)
def create_relation(entity_id: str, relation: RelationCreate, driver: Driver = Depends(get_driver)):
    return RelationService.create_relation(driver, entity_id, relation)
