from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from app.database import get_driver
from app.schemas import FacetResponse, FacetUpdate
from app.services.facet_service import FacetService

router = APIRouter()

@router.get("/{facet_id}", response_model=FacetResponse)
def get_facet(facet_id: str, driver: Driver = Depends(get_driver)):
    db_facet = FacetService.get_facet(driver, facet_id)
    if not db_facet:
        raise HTTPException(status_code=404, detail="Facet not found")
    return db_facet

@router.put("/{facet_id}", response_model=FacetResponse)
def update_facet(facet_id: str, updates: FacetUpdate, driver: Driver = Depends(get_driver)):
    db_facet = FacetService.update_facet(driver, facet_id, updates)
    if not db_facet:
        raise HTTPException(status_code=404, detail="Facet not found")
    return db_facet

@router.delete("/{facet_id}")
def delete_facet(facet_id: str, driver: Driver = Depends(get_driver)):
    return FacetService.delete_facet(driver, facet_id)
