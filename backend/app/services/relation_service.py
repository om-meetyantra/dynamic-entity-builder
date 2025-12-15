from neo4j import Driver
from app.schemas import RelationCreate, RelationUpdate, RelationResponse
from fastapi import HTTPException
import uuid
import json

class RelationService:
    @staticmethod
    def create_relation(driver: Driver, source_id: str, relation: RelationCreate):
        if source_id == relation.target_entity_id:
            raise HTTPException(status_code=400, detail="Self-loops not allowed")

        # Cycle Check (Path existence)
        cycle_query = """
        MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid})
        MATCH p = (t)-[:HAS_OUTGOING|TARGETS*]->(s)
        RETURN p LIMIT 1
        """
        records, _, _ = driver.execute_query(cycle_query, sid=source_id, tid=relation.target_entity_id, database_="neo4j")
        if records:
             raise HTTPException(status_code=400, detail="Creating this relation would cause a cycle")

        # Create Reified Relation Node
        query = """
        MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid})
        CREATE (s)-[:HAS_OUTGOING]->(r:RelationDefinition {
            id: $rid, 
            name: $name, 
            description: $desc
        })-[:TARGETS]->(t)
        RETURN r
        """
        rid = str(uuid.uuid4())
        desc = relation.description if relation.description else ""
        
        records, _, _ = driver.execute_query(
            query,
            sid=source_id,
            tid=relation.target_entity_id,
            rid=rid,
            name=relation.name,
            desc=desc,
            database_="neo4j"
        )
        
        if not records:
             raise HTTPException(status_code=404, detail="Source or Target Entity not found")
             
        r = records[0]["r"]
        return {
            "id": r["id"],
            "source_entity_id": source_id,
            "target_entity_id": relation.target_entity_id,
            "name": r["name"],
            "description": r.get("description"),
            "facets": []
        }

    @staticmethod
    def get_relation(driver: Driver, relation_id: str):
        query = """
        MATCH (s:Entity)-[:HAS_OUTGOING]->(r:RelationDefinition {id: $id})-[:TARGETS]->(t:Entity)
        RETURN r, s.id as sid, t.id as tid, [(r)-[:HAS_FACET]->(f:Facet) | f] as facets
        """
        records, _, _ = driver.execute_query(query, id=relation_id, database_="neo4j")
        
        if not records:
            return None
            
        r = records[0]["r"]
        sid = records[0]["sid"]
        tid = records[0]["tid"]
        
        facets = []
        for f in records[0]["facets"]:
            try: conf = json.loads(f["configuration"])
            except: conf = {}
            facets.append({
                "id": f["id"],
                "type": f["type"],
                "configuration": conf
            })
            
        return {
            "id": r["id"],
            "source_entity_id": sid,
            "target_entity_id": tid,
            "name": r["name"],
            "description": r.get("description"),
            "facets": facets
        }

    @staticmethod
    def update_relation(driver: Driver, relation_id: str, updates: RelationUpdate):
        set_clauses = []
        params = {"id": relation_id}
        
        if updates.name is not None:
            set_clauses.append("r.name = $name")
            params["name"] = updates.name
        
        if updates.description is not None:
            set_clauses.append("r.description = $description")
            params["description"] = updates.description
            
        if not set_clauses:
            return RelationService.get_relation(driver, relation_id)

        query = f"""
        MATCH (r:RelationDefinition {{id: $id}})
        SET {", ".join(set_clauses)}
        RETURN r
        """
        
        records, _, _ = driver.execute_query(query, parameters_=params, database_="neo4j")
        
        if not records:
             return None
             
        return RelationService.get_relation(driver, relation_id)

    @staticmethod
    def delete_relation(driver: Driver, relation_id: str):
        query = """
        MATCH (r:RelationDefinition {id: $id})
        OPTIONAL MATCH (r)-[:HAS_FACET]->(f:Facet)
        DETACH DELETE f, r
        """
        driver.execute_query(query, id=relation_id, database_="neo4j")
        return {"message": "Relation deleted successfully"}
