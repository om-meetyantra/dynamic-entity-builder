from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def cleanup_neo4j():
    # Clean up DB
    from app.database import get_driver
    driver = get_driver()
    driver.execute_query("MATCH (n) DETACH DELETE n", database_="neo4j")
    print("--- Neo4j Database Cleared ---")

def print_step(msg):
    print(f"\n--- {msg} ---")

def verify():
    # 1. Create Entity "User"
    print_step("Creating Entity 'User'")
    resp = client.post("/entities", json={"name": "User", "description": "System User"})
    assert resp.status_code == 200
    user_id = resp.json()["id"]
    print(f"Created User with ID: {user_id}")

    # 2. Add Property Facet to User
    # 2. Add Property Facets to User (Granular)
    print_step("Adding Property Facets to 'User'")
    # Property 1: Username
    resp = client.post(f"/entities/{user_id}/facets", json={
        "type": "property", 
        "configuration": {
            "name": "username", 
            "dataType": "string",
            "description": "Unique identifier for the user"
        }
    })
    assert resp.status_code == 200
    
    # Property 2: Email
    resp = client.post(f"/entities/{user_id}/facets", json={
        "type": "property", 
        "configuration": {
            "name": "email", 
            "dataType": "string",
            "description": "Contact email"
        }
    })
    assert resp.status_code == 200
    print("Added Property Facets (Granular)")

    # 3. Create Entity "Ticket"
    print_step("Creating Entity 'Ticket'")
    resp = client.post("/entities", json={"name": "Ticket", "description": "Support Ticket"})
    assert resp.status_code == 200
    ticket_id = resp.json()["id"]
    print(f"Created Ticket with ID: {ticket_id}")

    # 4. Add Lifecycle Facet to Ticket
    print_step("Adding Lifecycle Facet to 'Ticket'")
    lifecycle_config = {
        "states": ["Open", "InProgress", "Closed"],
        "transitions": [
            {"from": "Open", "to": "InProgress"},
            {"from": "InProgress", "to": "Closed"}
        ]
    }
    resp = client.post(f"/entities/{ticket_id}/facets", json={"type": "lifecycle", "configuration": lifecycle_config})
    assert resp.status_code == 200
    print("Added Lifecycle Facet")

    # 5. Create Relation Ticket -> User (assigned_to)
    print_step("Linking Ticket -> User (assigned_to)")
    resp = client.post(f"/entities/{ticket_id}/relations", json={
        "target_entity_id": user_id,
        "name": "assigned_to",
        "description": "Who is working on this ticket"
    })
    assert resp.status_code == 200
    print("Relation Created")

    # 5.1 Add Facet to Relation
    print_step("Adding Facet to Relation")
    # Fetch relations to get ID
    resp = client.get(f"/entities/{ticket_id}")
    ticket_data = resp.json()
    rel_id = ticket_data["outgoing_relations"][0]["id"]
    
    # Add Criteria Facet to Relation
    criteria_config = {
        "name": "Must be assigned to active user",
        "rule": "user.status == 'active'"
    }
    resp = client.post(f"/relations/{rel_id}/facets", json={"type": "criteria", "configuration": criteria_config})
    assert resp.status_code == 200
    print("Added Criteria Facet to Relation")

    # 5.2 Add Entity Facet to Ticket (Reference)
    print_step("Adding Entity Facet to 'Ticket'")
    entity_facet_config = {
        "target_entity_id": user_id
    }
    resp = client.post(f"/entities/{ticket_id}/facets", json={"type": "entity", "configuration": entity_facet_config})
    assert resp.status_code == 200
    print("Added Entity Reference Facet")

    # 6. Verify Graph Structure
    print_step("Verifying Entities and Relations")
    resp = client.get(f"/entities/{ticket_id}")
    data = resp.json()
    print("Ticket Data:", json.dumps(data, indent=2))
    assert len(data["outgoing_relations"]) == 1
    assert data["outgoing_relations"][0]["name"] == "assigned_to"
    # Check Relation Facets
    rel = data["outgoing_relations"][0]
    assert "facets" in rel
    assert len(rel["facets"]) >= 1
    assert rel["facets"][0]["type"] == "criteria"

    # 7. Attempt Cycle (User -> Ticket) - Should Fail?
    # User said "acyclic directed graph".
    # User -> Ticket would create User -> Ticket -> User depending on how we traverse or if we add User -> Ticket.
    # We have Ticket -> User.
    # Adding User -> Ticket makes a cycle: Ticket -> User -> Ticket.
    print_step("Attempting to create Cycle (User -> Ticket)")
    resp = client.post(f"/entities/{user_id}/relations", json={
        "target_entity_id": ticket_id,
        "name": "creates_ticket"
    })
    if resp.status_code == 400:
        print("Cycle Correctly Detected and Blocked!")
        print(resp.json())
    else:
        print(f"FAILED to detect cycle! Status: {resp.status_code}")
        exit(1)

    # 8. Verify /graph Endpoint
    print_step("Verifying /graph Endpoint")
    resp = client.get("/graph")
    assert resp.status_code == 200
    graph_data = resp.json()
    print("Graph Data:", json.dumps(graph_data, indent=2))
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["edges"]) >= 1

if __name__ == "__main__":
    cleanup_neo4j()
    verify()
