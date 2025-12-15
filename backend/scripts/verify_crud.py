import requests
import sys

BASE_URL = "http://localhost:8000"

def log(msg):
    print(f"[TEST] {msg}")

def check(condition, msg):
    if not condition:
        print(f"[FAIL] {msg}")
        sys.exit(1)
    print(f"[PASS] {msg}")

def test_crud():
    log("Starting CRUD Verification...")

    # 1. Create Entity A
    log("Creating Entity A...")
    resp = requests.post(f"{BASE_URL}/entities", json={"name": "Entity A", "description": "Description A"})
    check(resp.status_code == 200, "Create Entity A")
    entity_a = resp.json()
    log(f"Entity A ID: {entity_a['id']}")

    # 2. Update Entity A
    log("Updating Entity A...")
    resp = requests.put(f"{BASE_URL}/entities/{entity_a['id']}", json={"description": "Updated Description A"})
    check(resp.status_code == 200, "Update Entity A")
    entity_a = resp.json()
    check(entity_a["description"] == "Updated Description A", "Verify Update")

    # 3. Create Entity B
    log("Creating Entity B...")
    resp = requests.post(f"{BASE_URL}/entities", json={"name": "Entity B", "description": "Description B"})
    check(resp.status_code == 200, "Create Entity B")
    entity_b = resp.json()

    # 4. Create Relation A -> B
    log("Creating Relation A -> B...")
    resp = requests.post(f"{BASE_URL}/entities/{entity_a['id']}/relations", json={
        "target_entity_id": entity_b['id'],
        "name": "RELATES_TO",
        "description": "A relates to B"
    })
    check(resp.status_code == 200, "Create Relation")
    relation = resp.json()
    
    # 5. Add Facet to Entity A
    log("Adding Facet to Entity A...")
    resp = requests.post(f"{BASE_URL}/entities/{entity_a['id']}/facets", json={
        "type": "property",
        "configuration": {"name": "prop1", "datatype": "string"}
    })
    check(resp.status_code == 200, "Add Entity Facet")
    facet_e = resp.json()

    # 6. Add Facet to Relation
    log("Adding Facet to Relation...")
    resp = requests.post(f"{BASE_URL}/relations/{relation['id']}/facets", json={
        "type": "criteria",
        "configuration": {"rule": "x > 0"}
    })
    check(resp.status_code == 200, "Add Relation Facet")
    facet_r = resp.json()
    
    # 7. Get Graph
    log("Fetching Graph...")
    resp = requests.get(f"{BASE_URL}/graph")
    check(resp.status_code == 200, "Get Graph")
    graph = resp.json()
    # Basic check if nodes and edges exist
    found_node = any(n['id'] == entity_a['id'] for n in graph['nodes'])
    check(found_node, "Graph contains Entity A")
    
    # 8. Update Facet
    log("Updating Facet...")
    resp = requests.put(f"{BASE_URL}/facets/{facet_e['id']}", json={
        "configuration": {"name": "prop1_updated", "datatype": "string"}
    })
    check(resp.status_code == 200, "Update Facet")
    check(resp.json()["configuration"]["name"] == "prop1_updated", "Verify Facet Update")

    # 9. Delete Facet
    log("Deleting Facet...")
    resp = requests.delete(f"{BASE_URL}/facets/{facet_e['id']}")
    check(resp.status_code == 200, "Delete Facet")

    # 10. Delete Relation
    log("Deleting Relation...")
    resp = requests.delete(f"{BASE_URL}/relations/{relation['id']}")
    check(resp.status_code == 200, "Delete Relation")

    # 11. Delete Entities
    log("Deleting Entities...")
    resp = requests.delete(f"{BASE_URL}/entities/{entity_a['id']}")
    check(resp.status_code == 200, "Delete Entity A")
    resp = requests.delete(f"{BASE_URL}/entities/{entity_b['id']}")
    check(resp.status_code == 200, "Delete Entity B")

    log("ALL TESTS PASSED")

if __name__ == "__main__":
    test_crud()
