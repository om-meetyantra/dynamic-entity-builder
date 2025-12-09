from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

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
    print_step("Adding Property Facet to 'User'")
    prop_config = {
        "properties": [
            {"name": "username", "type": "string"},
            {"name": "email", "type": "string"}
        ]
    }
    resp = client.post(f"/entities/{user_id}/facets", json={"type": "property", "configuration": prop_config})
    assert resp.status_code == 200
    print("Added Property Facet")

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

    # 6. Verify Graph Structure
    print_step("Verifying Entities and Relations")
    resp = client.get(f"/entities/{ticket_id}")
    data = resp.json()
    print("Ticket Data:", json.dumps(data, indent=2))
    assert len(data["outgoing_relations"]) == 1
    assert data["outgoing_relations"][0]["name"] == "assigned_to"

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

if __name__ == "__main__":
    verify()
