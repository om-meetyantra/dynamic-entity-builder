from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EntityCreate, EntityResponse, FacetCreate, FacetResponse, RelationCreate, RelationResponse
from app.core.builder import SystemBuilder

router = APIRouter()

@router.post("/entities", response_model=EntityResponse)
def create_entity(entity: EntityCreate, db: Session = Depends(get_db)):
    return SystemBuilder.create_entity(db, entity)

@router.get("/entities", response_model=List[EntityResponse])
def get_entities(db: Session = Depends(get_db)):
    return SystemBuilder.get_all_entities(db)

@router.get("/entities/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    db_entity = SystemBuilder.get_entity(db, entity_id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db_entity

@router.post("/entities/{entity_id}/facets", response_model=FacetResponse)
def add_facet(entity_id: int, facet: FacetCreate, db: Session = Depends(get_db)):
    return SystemBuilder.add_facet(db, entity_id, facet)

@router.post("/entities/{entity_id}/relations", response_model=RelationResponse)
def create_relation(entity_id: int, relation: RelationCreate, db: Session = Depends(get_db)):
    return SystemBuilder.create_relation(db, entity_id, relation)
