from typing import List
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from app.database import get_driver
from app.schemas import RelationResponse, RelationUpdate, FacetCreate, FacetResponse
from app.services.relation_service import RelationService
from app.services.facet_service import FacetService

router = APIRouter()

@router.get("/{relation_id}", response_model=RelationResponse)
def get_relation(relation_id: str, driver: Driver = Depends(get_driver)):
    db_relation = RelationService.get_relation(driver, relation_id)
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    return db_relation

@router.put("/{relation_id}", response_model=RelationResponse)
def update_relation(relation_id: str, updates: RelationUpdate, driver: Driver = Depends(get_driver)):
    db_relation = RelationService.update_relation(driver, relation_id, updates)
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    return db_relation

@router.delete("/{relation_id}")
def delete_relation(relation_id: str, driver: Driver = Depends(get_driver)):
    return RelationService.delete_relation(driver, relation_id)

@router.post("/{relation_id}/facets", response_model=FacetResponse)
def add_relation_facet(relation_id: str, facet: FacetCreate, driver: Driver = Depends(get_driver)):
    return FacetService.add_facet(driver, relation_id, facet, target_type="RelationDefinition")
