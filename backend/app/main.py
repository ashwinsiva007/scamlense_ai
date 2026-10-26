from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config import settings

app = FastAPI(
    title="ScamLens API",
    version="0.1.0",
    description="Explainable, privacy-first scam analysis and multilingual Family Alert generator.",
    license_info={
        "name": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
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
