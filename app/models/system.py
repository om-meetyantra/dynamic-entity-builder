from sqlalchemy import Column, Integer, String, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    facets = relationship("Facet", back_populates="entity", cascade="all, delete-orphan")
    
    # Relationships where this entity is the source
    outgoing_relations = relationship(
        "Relation",
        foreign_keys="[Relation.source_entity_id]",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    
    # Relationships where this entity is the target
    incoming_relations = relationship(
        "Relation",
        foreign_keys="[Relation.target_entity_id]",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )

class Facet(Base):
    __tablename__ = "facets"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    type = Column(String, nullable=False)  # e.g., 'property', 'lifecycle'
    configuration = Column(JSON, nullable=False) # Stores the schema/config

    entity = relationship("Entity", back_populates="facets")
    
    __table_args__ = (
        UniqueConstraint('entity_id', 'type', name='uq_entity_facet_type'),
    )

class Relation(Base):
    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    target_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="outgoing_relations")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="incoming_relations")

    __table_args__ = (
        UniqueConstraint('source_entity_id', 'target_entity_id', 'name', name='uq_relation_source_target_name'),
    )
