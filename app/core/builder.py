from neo4j import Driver
from app.schemas import EntityCreate, FacetCreate, RelationCreate, GraphResponse
from fastapi import HTTPException
import uuid

class SystemBuilder:
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
            # Check for unique constraint violation if we set it up (we haven't yet, but good practice to handle errors)
            # For now, just raise generic or assume name conflict if we enforce it
            # To enforce uniqueness we should create a constraint, but let's just handle basic creation
            print(f"Error creating entity: {e}")
            raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")

    @staticmethod
    def get_entity(driver: Driver, entity_id: str):
        query = """
        MATCH (n:Entity {id: $id})
        OPTIONAL MATCH (n)-[:HAS_FACET]->(f:Facet)
        OPTIONAL MATCH (n)-[r:RELATED]->(t:Entity)
        OPTIONAL MATCH (inc_s:Entity)-[inc_r:RELATED]->(n)
        RETURN n, collect(f) as facets, collect({rel: r, target: t}) as outgoing, collect({rel: inc_r, source: inc_s}) as incoming
        """
        records, _, _ = driver.execute_query(query, id=entity_id, database_="neo4j")
        
        if not records:
            return None
        
        record = records[0]
        node = record["n"]
        if not node:
            return None

        # Parse facets
        facets = []
        for f in record["facets"]:
            facets.append({
                "id": f["id"],
                "entity_id": entity_id,
                "type": f["type"],
                "configuration":  dict(f.items())["configuration"] # f is a Node, access props
            })
            # Note: configuration is stored as string property or we can try to store as map if neo4j supports it nicely
            # Neo4j properties can't be complex JSON objects natively unless using APOC or separate nodes.
            # Workaround: We will store configuration as a JSON string and parse it, OR rely on basic type support.
            # Implementation detail: Use separate properties or JSON string. 
            # Let's assume we store it as a JSON string for simplicity in the 'configuration' property.
            import json
            if isinstance(facets[-1]["configuration"], str):
                 facets[-1]["configuration"] = json.loads(facets[-1]["configuration"])

        # Parse outgoing
        outgoing = []
        for item in record["outgoing"]:
            if item["rel"]:
                outgoing.append({
                    "id": item["rel"]["id"],
                    "source_entity_id": entity_id,
                    "target_entity_id": item["target"]["id"],
                    "name": item["rel"]["name"],
                    "description": item["rel"].get("description")
                })
        
        # Parse incoming
        incoming = []
        for item in record["incoming"]:
            if item["rel"]:
                incoming.append({
                    "id": item["rel"]["id"],
                    "source_entity_id": item["source"]["id"],
                    "target_entity_id": entity_id,
                    "name": item["rel"]["name"],
                    "description": item["rel"].get("description")
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
            # Minimal mapping for list
            entities.append({
                "id": r["n"]["id"],
                "name": r["n"]["name"],
                "description": r["n"].get("description"),
                "facets": [], "outgoing_relations": [], "incoming_relations": [] # optimization: don't load everything
            })
        return entities

    @staticmethod
    def add_facet(driver: Driver, entity_id: str, facet: FacetCreate):
        # We store configuration as JSON string if it's complex, or just properties.
        # Let's standardize on JSON string for 'configuration' property to keep it flexible.
        import json
        config_str = json.dumps(facet.configuration)
        
        query = """
        MATCH (n:Entity {id: $eid})
        CREATE (n)-[:HAS_FACET]->(f:Facet {
            id: $fid,
            type: $type,
            configuration: $config
        })
        RETURN f
        """
        fid = str(uuid.uuid4())
        records, _, _ = driver.execute_query(
            query, 
            eid=entity_id, 
            fid=fid, 
            type=facet.type, 
            config=config_str,
            database_="neo4j"
        )
        
        if not records:
             raise HTTPException(status_code=404, detail="Entity not found")

        f = records[0]["f"]
        return {
            "id": f["id"],
            "entity_id": entity_id,
            "type": f["type"],
            "configuration": facet.configuration
        }

    @staticmethod
    def create_relation(driver: Driver, source_id: str, relation: RelationCreate):
        if source_id == relation.target_entity_id:
            raise HTTPException(status_code=400, detail="Self-loops not allowed")

        # Cycle Check (Path existence)
        # Check if path exists from Target -> Source
        cycle_query = """
        MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid})
        MATCH p = (t)-[:RELATED*]->(s)
        RETURN p LIMIT 1
        """
        records, _, _ = driver.execute_query(cycle_query, sid=source_id, tid=relation.target_entity_id, database_="neo4j")
        if records:
            raise HTTPException(status_code=400, detail="Creating this relation would cause a cycle")

        query = """
        MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid})
        CREATE (s)-[r:RELATED {id: $rid, name: $name, description: $desc}]->(t)
        RETURN r
        """
        rid = str(uuid.uuid4())
        # description can be None
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
            "description": r.get("description")
        }

    @staticmethod
    def get_graph(driver: Driver):
        # Fetch all Nodes and Edges
        # Nodes: Entities
        # Edges: Relations
        # Note: Facets are separate nodes in our graph model (Entity)-[:HAS_FACET]->(Facet)
        # In GraphResponse, Facets are embedded in GraphNode.
        
        query = """
        MATCH (n:Entity)
        OPTIONAL MATCH (n)-[:HAS_FACET]->(f:Facet)
        RETURN n, collect(f) as facets
        """
        records, _, _ = driver.execute_query(query, database_="neo4j")
        
        nodes = []
        for r in records:
            n = r["n"]
            facets_list = []
            for f in r["facets"]:
                import json
                try:
                    conf = json.loads(f["configuration"])
                except:
                    conf = {}
                facets_list.append({
                    "id": f["id"],
                    "entity_id": n["id"],
                    "type": f["type"],
                    "configuration": conf
                })
            
            nodes.append({
                "id": n["id"],
                "name": n["name"],
                "description": n.get("description"),
                "facets": facets_list
            })
            
        rel_query = """
        MATCH (s:Entity)-[r:RELATED]->(t:Entity)
        RETURN s.id as sid, t.id as tid, r
        """
        rel_records, _, _ = driver.execute_query(rel_query, database_="neo4j")
        
        edges = []
        for item in rel_records:
            r = item["r"]
            edges.append({
                "source_id": item["sid"],
                "target_id": item["tid"],
                "relation_name": r["name"],
                "relation_id": r["id"]
            })
            
        return {
            "nodes": nodes,
            "edges": edges
        }
