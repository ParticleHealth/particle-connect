import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, credentials, notifications, projects, service_accounts
from app.services.particle_client import particle_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting management-ui backend")
    logger.info(
        "Config: env=%s base_url=%s timeout=%d cors_origins=%s",
        settings.particle_env,
        settings.particle_base_url,
        settings.particle_timeout,
        settings.cors_origins,
    )

    # Auto-connect using .env credentials on startup
    if settings.particle_client_id and settings.particle_client_secret:
        try:
            await particle_client.connect()
            logger.info("Auto-connected to Particle (%s)", settings.particle_env)
        except Exception:
            logger.warning("Auto-connect failed — credentials may be invalid")
    else:
        logger.info("No credentials in .env — skipping auto-connect")

    yield
    logger.info("Shutting down management-ui backend")
    await particle_client.close()


app = FastAPI(
    title="Particle Management API Proxy",
    description="Backend proxy for Particle Health Management API admin UI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(service_accounts.router, prefix="/api")
app.include_router(credentials.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "authenticated": particle_client.is_authenticated,
        "environment": particle_client.environment,
    }
