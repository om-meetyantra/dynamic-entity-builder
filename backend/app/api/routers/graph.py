from fastapi import APIRouter, Depends
from neo4j import Driver
from app.database import get_driver
from app.schemas import GraphResponse
from app.services.entity_service import EntityService
import json

router = APIRouter()

@router.get("", response_model=GraphResponse)
def get_graph(driver: Driver = Depends(get_driver)):
    # Re-implementing graph logic here or could make a service for it.
    # Logic is nearly same as before, let's keep it here or create GraphService if complex.
    # It was in SystemBuilder.get_graph.
    # Let's put logic in EntityService for now or a new GraphService?
    # Actually, logic is best placed in a service. Let's create a Helper in EntityService or standalone.
    # For simplicity, I will implement logic here or create a small helper in EntityService if reusable.
    
    # Let's use GraphService pattern if we want to be strict, but keeping it simple:
    
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
