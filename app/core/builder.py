from sqlalchemy.orm import Session
from app.models.system import Entity, Facet, Relation
from app.schemas import EntityCreate, FacetCreate, RelationCreate
from fastapi import HTTPException, status

class SystemBuilder:
    @staticmethod
    def create_entity(db: Session, entity: EntityCreate):
        db_entity = Entity(name=entity.name, description=entity.description)
        try:
            db.add(db_entity)
            db.commit()
            db.refresh(db_entity)
            return db_entity
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="Entity with this name might already exist")

    @staticmethod
    def get_entity(db: Session, entity_id: int):
        return db.query(Entity).filter(Entity.id == entity_id).first()

    @staticmethod
    def get_all_entities(db: Session):
        return db.query(Entity).all()

    @staticmethod
    def add_facet(db: Session, entity_id: int, facet: FacetCreate):
        # Validate Entity exists
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Check if facet type already exists (UniqueConstraint)
        existing = db.query(Facet).filter(Facet.entity_id == entity_id, Facet.type == facet.type).first()
        if existing:
            # Update existing
            existing.configuration = facet.configuration
            db.commit()
            db.refresh(existing)
            return existing
        else:
            db_facet = Facet(entity_id=entity_id, type=facet.type, configuration=facet.configuration)
            db.add(db_facet)
            db.commit()
            db.refresh(db_facet)
            return db_facet

    @staticmethod
    def create_relation(db: Session, source_id: int, relation: RelationCreate):
        target_id = relation.target_entity_id
        
        if source_id == target_id:
             raise HTTPException(status_code=400, detail="Self-loops not allowed or cycle detected")

        source = db.query(Entity).filter(Entity.id == source_id).first()
        target = db.query(Entity).filter(Entity.id == target_id).first()

        if not source or not target:
            raise HTTPException(status_code=404, detail="Source or Target Entity not found")

        # Cycle Detection
        if SystemBuilder._detect_cycle(db, source_id, target_id):
            raise HTTPException(status_code=400, detail="Creating this relation would cause a cycle")

        db_relation = Relation(
            source_entity_id=source_id,
            target_entity_id=target_id,
            name=relation.name,
            description=relation.description
        )
        try:
            db.add(db_relation)
            db.commit()
            db.refresh(db_relation)
            return db_relation
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="Relation might already exist")

    @staticmethod
    def _detect_cycle(db: Session, source_id: int, target_id: int) -> bool:
        """
        Check if adding an edge source -> target creates a cycle.
        This means checking if there is already a path from target -> source.
        """
        visited = set()
        stack = [target_id]

        while stack:
            current = stack.pop()
            if current == source_id:
                return True # Path found from target to source
            
            if current in visited:
                continue
            visited.add(current)
            
            # Find all outgoing neighbors of current
            # We need to query relations where source_entity_id == current
            outgoing = db.query(Relation).filter(Relation.source_entity_id == current).all()
            for rel in outgoing:
                stack.append(rel.target_entity_id)
        
        return False
