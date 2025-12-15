from neo4j import Driver
from app.schemas import EntityCreate, EntityUpdate
from fastapi import HTTPException
import uuid
import json

class EntityService:
    @staticmethod
    def create_entity(driver: Driver, entity: EntityCreate):
        query = """
        CREATE (n:Entity {
            id: $id,
            name: $name,
            description: $description
        })
        RETURN n.id as id, n.name as name, n.description as description
        """
        try:
            eid = str(uuid.uuid4())
            records, summary, keys = driver.execute_query(
                query, 
                id=eid,
                name=entity.name,
                description=entity.description,
                database_="neo4j"
            )
            record = records[0]
            return {
                "id": record["id"],
                "name": record["name"],
                "description": record["description"],
                "facets": [],
                "outgoing_relations": [],
                "incoming_relations": []
            }
        except Exception as e:
            print(f"Error creating entity: {e}")
            raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")

    @staticmethod
    def get_entity(driver: Driver, entity_id: str):
        # Fetch Entity, its Facets, and its Relations (Nodes)
        query = """
        MATCH (n:Entity {id: $id})
        RETURN n, 
               [(n)-[:HAS_FACET]->(f:Facet) | f] as facets,
               [(n)-[:HAS_OUTGOING]->(r:RelationDefinition)-[:TARGETS]->(t:Entity) | {rel: r, target: t, facets: [(r)-[:HAS_FACET]->(rf:Facet) | rf]}] as outgoing,
               [(inc_s:Entity)-[:HAS_OUTGOING]->(inc_r:RelationDefinition)-[:TARGETS]->(n) | {rel: inc_r, source: inc_s, facets: [(inc_r)-[:HAS_FACET]->(inc_rf:Facet) | inc_rf]}] as incoming
        """
        records, _, _ = driver.execute_query(query, id=entity_id, database_="neo4j")
        
        if not records:
            return None
        
        record = records[0]
        node = record["n"]
        if not node:
            return None

        # Helper to parse facet node
        def parse_facet(f):
            if not f: return None
            try:
                conf = json.loads(f["configuration"])
            except:
                conf = {}
            return {
                "id": f["id"],
                "type": f["type"],
                "configuration": conf
            }

        # Parse facets
        facets = [parse_facet(f) for f in record["facets"] if f]

        # Parse outgoing
        outgoing = []
        for item in record["outgoing"]:
            if item["rel"]:
                r_node = item["rel"]
                r_facets = [parse_facet(rf) for rf in item["facets"] if rf]
                outgoing.append({
                    "id": r_node["id"],
                    "source_entity_id": entity_id,
                    "target_entity_id": item["target"]["id"],
                    "name": r_node["name"],
                    "description": r_node.get("description"),
                    "facets": r_facets
                })
        
        # Parse incoming
        incoming = []
        for item in record["incoming"]:
            if item["rel"]:
                r_node = item["rel"]
                r_facets = [parse_facet(rf) for rf in item["facets"] if rf]
                incoming.append({
                    "id": r_node["id"],
                    "source_entity_id": item["source"]["id"],
                    "target_entity_id": entity_id,
                    "name": r_node["name"],
                    "description": r_node.get("description"),
                    "facets": r_facets
                })

        return {
            "id": node["id"],
            "name": node["name"],
            "description": node.get("description"),
            "facets": facets,
            "outgoing_relations": outgoing,
            "incoming_relations": incoming
        }

    @staticmethod
    def get_all_entities(driver: Driver):
        query = """
        MATCH (n:Entity)
        RETURN n
        """
        records, _, _ = driver.execute_query(query, database_="neo4j")
        entities = []
        for r in records:
            entities.append({
                "id": r["n"]["id"],
                "name": r["n"]["name"],
                "description": r["n"].get("description"),
                "facets": [], "outgoing_relations": [], "incoming_relations": [] 
            })
        return entities

    @staticmethod
    def update_entity(driver: Driver, entity_id: str, updates: EntityUpdate):
        # Only update fields that are provided
        set_clauses = []
        params = {"id": entity_id}
        
        if updates.name is not None:
            set_clauses.append("n.name = $name")
            params["name"] = updates.name
        
        if updates.description is not None:
            set_clauses.append("n.description = $description")
            params["description"] = updates.description
            
        if not set_clauses:
            return EntityService.get_entity(driver, entity_id)

        query = f"""
        MATCH (n:Entity {{id: $id}})
        SET {", ".join(set_clauses)}
        RETURN n
        """
        
        records, _, _ = driver.execute_query(query, parameters_=params, database_="neo4j")
        
        if not records:
             return None
             
        return EntityService.get_entity(driver, entity_id)

    @staticmethod
    def delete_entity(driver: Driver, entity_id: str):
        # Detach delete to remove relationships
        # Also need to cleanup facets attached to the entity
        # And potentially RelationDefinitions that are connected?
        # If we delete an Entity, any RelationDefinition connecting FROM it or TO it is invalid?
        # Yes, standard graph: delete node deletes incident edges.
        # But here edges are nodes (RelationDefinition).
        # We need to delete those RelationDefinition nodes too.
        
        # 1. Delete outgoing RelationDefinitions and their facets
        # 2. Delete incoming RelationDefinitions (where this entity is target) - Wait, if S->R->T, and we delete T, R becomes dangling.
        # Yes, we should delete R as well.
        # 3. Delete Facets attached to this entity
        # 4. Delete the Entity itself
        
        query = """
        MATCH (n:Entity {id: $id})
        
        // Collect everything to delete
        OPTIONAL MATCH (n)-[:HAS_OUTGOING]->(r_out:RelationDefinition)
        OPTIONAL MATCH (r_out)-[:HAS_FACET]->(rf_out:Facet)
        
        OPTIONAL MATCH (inc:RelationDefinition)-[:TARGETS]->(n)
        OPTIONAL MATCH (inc)-[:HAS_FACET]->(rf_inc:Facet)
        
        OPTIONAL MATCH (n)-[:HAS_FACET]->(f:Facet)
        
        DETACH DELETE n, r_out, rf_out, inc, rf_inc, f
        """
        
        driver.execute_query(query, id=entity_id, database_="neo4j")
        return {"message": "Entity deleted successfully"}
