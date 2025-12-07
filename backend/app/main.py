from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import auth, ingest, graph, retrieve, triage
from app.services.neo4j_client import neo4j_client
from app.services.qdrant_client import qdrant_service
from app.services.embedding_service import embedding_service
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""

    # Startup
    print("Starting Antibody API...")

    # Initialize database connections
    try:
        await neo4j_client.connect()
        await neo4j_client.create_indexes()
        print("✓ Connected to Neo4j")
    except Exception as e:
        print(f"✗ Failed to connect to Neo4j: {e}")

    try:
        await qdrant_service.connect()
        # Create collection if it doesn't exist
        if not await qdrant_service.collection_exists():
            await qdrant_service.create_collection()
        print("✓ Connected to Qdrant")
    except Exception as e:
        print(f"✗ Failed to connect to Qdrant: {e}")

    print(f"✓ Antibody API started on {settings.HOST}:{settings.PORT}")

    yield

    # Shutdown
    print("Shutting down Antibody API...")

    await neo4j_client.close()
    await qdrant_service.close()
    await embedding_service.close()

    print("✓ Antibody API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Proactive knowledge integrity platform for GrokiPedia",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (optional, uncomment if needed)
# from app.utils.rate_limiter import limiter
# from slowapi import _rate_limit_exceeded_handler
# from slowapi.errors import RateLimitExceeded
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(graph.router)
app.include_router(retrieve.router)
app.include_router(triage.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""

    health_status = {
        "status": "healthy",
        "services": {}
    }

    # Check Neo4j
    try:
        await neo4j_client.driver.verify_connectivity()
        health_status["services"]["neo4j"] = "connected"
    except Exception as e:
        health_status["services"]["neo4j"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Qdrant
    try:
        await qdrant_service.collection_exists()
        health_status["services"]["qdrant"] = "connected"
    except Exception as e:
        health_status["services"]["qdrant"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
