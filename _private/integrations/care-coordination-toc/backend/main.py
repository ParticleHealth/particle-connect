"""FastAPI application for the Transitions of Care workflow."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import Database


db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    db.initialize()
    app.state.db = db
    yield
    db.close()


app = FastAPI(
    title="Transitions of Care Workflow",
    description="Multi-agent workflow for post-discharge care coordination",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount routers after app is created to avoid circular imports
from routers import workflows, gates, patients, webhooks, signal  # noqa: E402

app.include_router(workflows.router)
app.include_router(gates.router)
app.include_router(patients.router)
app.include_router(webhooks.router)
app.include_router(signal.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "db_connected": db.conn is not None}


if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
