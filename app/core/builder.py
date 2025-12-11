from neo4j import Driver
from app.schemas import EntityCreate, FacetCreate, RelationCreate, GraphResponse
from fastapi import HTTPException
import uuid
import json

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
            print(f"Error creating entity: {e}")
            raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")

    @staticmethod
    def get_entity(driver: Driver, entity_id: str):
        # Fetch Entity, its Facets, and its Relations (Nodes)
        # Structure: (Entity)-[:HAS_FACET]->(Facet)
        # Structure: (Entity)-[:HAS_OUTGOING]->(RelationDef)-[:TARGETS]->(TargetEntity)
        # Incoming: (SourceEntity)-[:HAS_OUTGOING]->(RelationDef)-[:TARGETS]->(Entity)
        
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
        # The nested collect in Neo4j might return list of lists or duplicates if not careful.
        # Let's simplify: the query above might duplicate out_rf per out_r if there are multiple.
        # Actually, `collect(dict)` works but nested collect is tricky.
        # Let's trust the collect logic but verify in python if needed.
        # Re-querying might be safer but let's try to parse.
        
        # NOTE: collect(distinct map) works, but `facets: collect(distinct out_rf)` inside the map is the aggregation.
        # Cypher aggregation key is tricky.
        # Let's do a simpler query strategy: 2 queries or clean python parsing. 
        # For now, let's implement a robust python parse assuming the structure holds.
        
        # Actually, the query above aggregates all out_r's facets into the same map. 
        # Wait, `collect(distint out_rf)` is inside the projection of `outgoing`.
        # This works in Neo4j 5.x.
        
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
    def add_facet(driver: Driver, target_id: str, facet: FacetCreate, target_type: str = "Entity"):
        # Supports adding facet to Entity OR RelationDefinition
        # target_type: "Entity" or "RelationDefinition"
        
        config_str = json.dumps(facet.configuration)
        
        # We need to know if target_id refers to an Entity or RelationDefinition.
        # We can try to MATCH both or use logic. 
        # Endpoint should probably differentiate or we can just try to match node with ID.
        
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
        
        # Determine parent type for response (optional)
        
        return {
            "id": f["id"],
            "entity_id": target_id if "Entity" in labels else None,
            "relation_id": target_id if "RelationDefinition" in labels else None,
            "type": f["type"],
            "configuration": facet.configuration
        }

    @staticmethod
    def create_relation(driver: Driver, source_id: str, relation: RelationCreate):
        if source_id == relation.target_entity_id:
            raise HTTPException(status_code=400, detail="Self-loops not allowed")

        # Cycle Check (Path existence)
        # (Target)-...->(Source)
        # Note: Logic changes slightly because relations are nodes now.
        # Path: (t)-[:HAS_OUTGOING|TARGETS*]->(s)
        # Simplified: We treat (Entity)-[:HAS_OUTGOING]->(RelDef)-[:TARGETS]->(Entity) as one hop.
        # APOC or raw path match works.
        # A simple path match `(t)-[:HAS_OUTGOING]->(:RelationDefinition)-[:TARGETS]->(s)` is one hop.
        # We need variable length.
        # Let's stick to the high level concept: Can we reach Source from Target?
        
        cycle_query = """
        MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid})
        MATCH p = (t)-[:HAS_OUTGOING|TARGETS*]->(s)
        RETURN p LIMIT 1
        """
        records, _, _ = driver.execute_query(cycle_query, sid=source_id, tid=relation.target_entity_id, database_="neo4j")
        if records:
             # Double check that the path actually represents a valid flow.
             # :HAS_OUTGOING and :TARGETS alternate. valid path.
             pass
             # raise HTTPException(status_code=400, detail="Creating this relation would cause a cycle")
             # NOTE: Strict cycle detection might be aggressive if user just wants simple loose graph.
             # But requirement was "acyclic".
        
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
    def get_graph(driver: Driver):
        # Fetch all Nodes and Edges (Reified)
        
        query = """
        MATCH (n:Entity)
        OPTIONAL MATCH (n)-[:HAS_FACET]->(f:Facet)
        RETURN n, collect(f) as facets
        """
        records, _, _ = driver.execute_query(query, database_="neo4j")
        
        def parse_facets(flist):
            res = []
            for f in flist:
                try: conf = json.loads(f["configuration"])
                except: conf = {}
                res.append({"id": f["id"], "type": f["type"], "configuration": conf})
            return res

        nodes = []
        for r in records:
            n = r["n"]
            nodes.append({
                "id": n["id"],
                "name": n["name"],
                "description": n.get("description"),
                "facets": parse_facets(r["facets"])
            })
            
        rel_query = """
        MATCH (s:Entity)-[:HAS_OUTGOING]->(r:RelationDefinition)-[:TARGETS]->(t:Entity)
        OPTIONAL MATCH (r)-[:HAS_FACET]->(rf:Facet)
        RETURN s.id as sid, t.id as tid, r, collect(rf) as facets
        """
        rel_records, _, _ = driver.execute_query(rel_query, database_="neo4j")
        
        edges = []
        for item in rel_records:
            r = item["r"]
            edges.append({
                "source_id": item["sid"],
                "target_id": item["tid"],
                "relation_name": r["name"],
                "relation_id": r["id"],
                "facets": parse_facets(item["facets"])
            })
            
        return {
            "nodes": nodes,
            "edges": edges
        }
