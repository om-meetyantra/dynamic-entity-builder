from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def cleanup_neo4j():
    from app.database import get_driver
    driver = get_driver()
    driver.execute_query("MATCH (n) DETACH DELETE n", database_="neo4j")
    print("--- Neo4j Database Cleared ---")

def print_step(msg):
    print(f"\n--- {msg} ---")

def create_entity(name, desc):
    resp = client.post("/entities", json={"name": name, "description": desc})
    assert resp.status_code == 200
    return resp.json()["id"]

def add_prop(entity_id, name, dtype, desc):
    resp = client.post(f"/entities/{entity_id}/facets", json={
        "type": "property",
        "configuration": {
            "name": name,
            "dataType": dtype,
            "description": desc
        }
    })
    assert resp.status_code == 200

def create_relation_def(s_id, t_id, name, desc):
    resp = client.post(f"/entities/{s_id}/relations", json={
        "target_entity_id": t_id,
        "name": name,
        "description": desc
    })
    assert resp.status_code == 200
    return resp.json()["id"]

def add_criteria(rel_id, name, rule):
    resp = client.post(f"/relations/{rel_id}/facets", json={
        "type": "criteria",
        "configuration": {
            "name": name,
            "rule": rule
        }
    })
    assert resp.status_code == 200

def run_taxi_demo():
    print_step("Setting up Taxi Leasing System Model")
    
    # 1. Define Entities
    driver_id = create_entity("Driver", "A taxi driver")
    license_id = create_entity("License", "Driver's license")
    medallion_id = create_entity("TaxiMedallion", "Taxi Medallion permit")
    lease_id = create_entity("Lease", "Lease agreement")
    
    print(f"Entities Created: Driver({driver_id}), License({license_id}), Medallion({medallion_id}), Lease({lease_id})")

    # 2. Add Properties (Granular)
    # Driver
    add_prop(driver_id, "Name", "string", "Full Name")
    add_prop(driver_id, "Address", "string", "Residential Address")
    add_prop(driver_id, "Phone", "string", "Contact Number")
    
    # License
    add_prop(license_id, "LicenseNumber", "string", "Unique License No")
    add_prop(license_id, "IssueDate", "date", "Date Issued")
    add_prop(license_id, "ExpirationDate", "date", "Date Expires")
    
    # Medallion
    add_prop(medallion_id, "MedallionNumber", "string", "Unique Medallion No")
    add_prop(medallion_id, "Status", "enum", "Active, Suspended, Retired")
    
    # Lease
    add_prop(lease_id, "StartDate", "date", "Lease Start")
    add_prop(lease_id, "EndDate", "date", "Lease End")
    add_prop(lease_id, "LeaseRate", "decimal", "Daily Rate")

    print("Properties Added to Entities")

    # 3. Define Relations & Criteria
    
    # Driver -[has_license]-> License
    d_l_rel = create_relation_def(driver_id, license_id, "has_license", "Driver possesses a license")
    add_criteria(d_l_rel, "One License Per Driver", "count(license) <= 1")
    
    # License -[belongs_to]-> Driver
    # NOTE: Bi-directional relation causes cycle (Driver -> License -> Driver). 
    # System enforces Acyclic Graph. So we only define Driver -> License.
    # l_d_rel = create_relation_def(license_id, driver_id, "belongs_to", "License belongs to driver")
    
    # Lease -[issued_to]-> Driver
    l_dr_rel = create_relation_def(lease_id, driver_id, "issued_to", "Lease issued to driver")
    
    # Lease -[for_medallion]-> Medallion
    l_m_rel = create_relation_def(lease_id, medallion_id, "for_medallion", "Lease for specific medallion")
    
    # Validation Rule: EndDate > StartDate (Attached to Lease entity via Criteria Facet? Or Relation?)
    # Rules are usually on relations or the entity itself. Let's add criteria to the Lease Entity itself.
    resp = client.post(f"/entities/{lease_id}/facets", json={
        "type": "criteria",
        "configuration": {
            "name": "Date Validation",
            "rule": "EndDate > StartDate"
        }
    })
    
    print("Relations and Constraints Defined")

    # 4. Verify Graph
    print_step("Verifying Taxi System Graph")
    resp = client.get("/graph")
    graph = resp.json()
    
    # Assert counts
    assert len(graph["nodes"]) == 4
    # Relations: has_license, issued_to, for_medallion = 3 (removed belongs_to to avoid cycle)
    assert len(graph["edges"]) == 3
    
    print(f"Graph Verified: {len(graph['nodes'])} Nodes, {len(graph['edges'])} Edges")
    # print(json.dumps(graph, indent=2))

if __name__ == "__main__":
    cleanup_neo4j()
    run_taxi_demo()
