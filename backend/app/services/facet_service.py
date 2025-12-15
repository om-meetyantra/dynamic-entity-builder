from neo4j import Driver
from app.schemas import FacetCreate, FacetUpdate
from fastapi import HTTPException
import uuid
import json

class FacetService:
    @staticmethod
    def add_facet(driver: Driver, target_id: str, facet: FacetCreate, target_type: str = "Entity"):
        # Supports adding facet to Entity OR RelationDefinition
        
        config_str = json.dumps(facet.configuration)
        
        query = f"""
        MATCH (n) WHERE n.id = $eid AND (n:Entity OR n:RelationDefinition)
        CREATE (n)-[:HAS_FACET]->(f:Facet {{
            id: $fid,
            type: $type,
            configuration: $config
        }})
        RETURN f, labels(n) as labels
        """
        fid = str(uuid.uuid4())
        records, _, _ = driver.execute_query(
            query, 
            eid=target_id, 
            fid=fid, 
            type=facet.type, 
            config=config_str,
            database_="neo4j"
        )
        
        if not records:
             raise HTTPException(status_code=404, detail="Target (Entity or Relation) not found")

        f = records[0]["f"]
        labels = records[0]["labels"]
        
        return {
            "id": f["id"],
            "entity_id": target_id if "Entity" in labels else None,
            "relation_id": target_id if "RelationDefinition" in labels else None,
            "type": f["type"],
            "configuration": facet.configuration
        }

    @staticmethod
    def get_facet(driver: Driver, facet_id: str):
        query = """
        MATCH (n)-[:HAS_FACET]->(f:Facet {id: $id})
        RETURN f, n.id as nid, labels(n) as labels
        """
        records, _, _ = driver.execute_query(query, id=facet_id, database_="neo4j")
        
        if not records:
            return None
            
        f = records[0]["f"]
        nid = records[0]["nid"]
        labels = records[0]["labels"]
        
        try: conf = json.loads(f["configuration"])
        except: conf = {}
        
        return {
            "id": f["id"],
            "entity_id": nid if "Entity" in labels else None,
            "relation_id": nid if "RelationDefinition" in labels else None,
            "type": f["type"],
            "configuration": conf
        }

    @staticmethod
    def update_facet(driver: Driver, facet_id: str, updates: FacetUpdate):
        if updates.configuration is None:
            return FacetService.get_facet(driver, facet_id)
            
        config_str = json.dumps(updates.configuration)
        
        query = """
        MATCH (f:Facet {id: $id})
        SET f.configuration = $config
        RETURN f
        """
        
        records, _, _ = driver.execute_query(query, id=facet_id, config=config_str, database_="neo4j")
        
        if not records:
             return None
             
        return FacetService.get_facet(driver, facet_id)

    @staticmethod
    def delete_facet(driver: Driver, facet_id: str):
        query = """
        MATCH (f:Facet {id: $id})
        DETACH DELETE f
        """
        driver.execute_query(query, id=facet_id, database_="neo4j")
        return {"message": "Facet deleted successfully"}
