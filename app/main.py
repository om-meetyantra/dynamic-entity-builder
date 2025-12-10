from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="Dynamic Entity System Model Builder (Neo4j)")

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Dynamic Entity Builder (GraphDB)"}
