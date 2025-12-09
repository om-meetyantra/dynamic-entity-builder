from fastapi import FastAPI
from app.database import engine, Base
from app.api import routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dynamic Entity System Model Builder")

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Dynamic Entity Builder"}
