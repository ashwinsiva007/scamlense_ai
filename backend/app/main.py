import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config import settings

logger = logging.getLogger("scamlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Masked startup log for Gemini key (never logs the value)
    key_len = len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0
    env_source = getattr(settings, "ENV_FILE_LOADED", "none") or "none"
    if key_len > 0:
        msg = f"Gemini key: present (length {key_len}) from {env_source}"
        logger.info(msg)
        print(msg)
    else:
        msg = "Gemini key: MISSING"
        logger.warning(msg)
        print(msg)
    yield


app = FastAPI(
    title="ScamLens API",
    version="0.1.0",
    description="Explainable, privacy-first scam analysis and multilingual Family Alert generator.",
    license_info={
        "name": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    lifespan=lifespan,
)

# Configure CORS from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Applies security response headers to all outgoing responses.
    Strict privacy: does not log request bodies, uploaded media, or message text.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# Register API endpoints
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "ScamLens API",
        "version": "0.1.0",
        "status": "operational",
        "docs_url": "/docs",
    }
