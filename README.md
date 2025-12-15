# Dynamic Entity Builder - Backend

This directory contains the backend services for the Dynamic Entity Builder, built with **FastAPI** and **Neo4j**.

> [!NOTE]
> This is a **development setup** configuration.

**Note**: Frontend will be added later.

## Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- Python 3.9+

## Setup & Installation

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development

### 1. Start Database (Neo4j)

Use Docker Compose to spin up the Neo4j database.

```bash
docker-compose up -d
```
*Accessible at http://localhost:7474 (Username: `neo4j`, Password: `password`)*

### 2. Run Backend Server

Start the FastAPI development server.

```bash
uvicorn app.main:app --reload
```

*API Config*:
- **Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## Troubleshooting

- If Neo4j fails to start, ensure ports `7474` and `7687` are free.
- Check database logs: `docker-compose logs -f neo4j`
