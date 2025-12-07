from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables"""

    # Application Settings
    APP_NAME: str = "Antibody API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str  # REQUIRED - JWT secret key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL Configuration
    POSTGRES_USER: str  # REQUIRED
    POSTGRES_PASSWORD: str  # REQUIRED
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "antibody"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Neo4j Configuration
    NEO4J_URI: str  # REQUIRED - e.g., "bolt://localhost:7687"
    NEO4J_USER: str  # REQUIRED
    NEO4J_PASSWORD: str  # REQUIRED
    NEO4J_DATABASE: str = "neo4j"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Qdrant Configuration
    QDRANT_HOST: str = "localhost"  # REQUIRED
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "claims"

    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def CELERY_BROKER(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def CELERY_BACKEND(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # Grok API Configuration (xAI)
    GROK_API_KEY: str  # REQUIRED
    GROK_API_BASE: str = "https://api.x.ai/v1"
    GROK_MODEL: str = "grok-beta"

    # X (Twitter) API Configuration
    X_API_KEY: str  # REQUIRED
    X_API_SECRET: str  # REQUIRED
    X_ACCESS_TOKEN: str  # REQUIRED
    X_ACCESS_TOKEN_SECRET: str  # REQUIRED
    X_BEARER_TOKEN: str  # REQUIRED

    # Cohere API Configuration
    COHERE_API_KEY: str  # REQUIRED
    COHERE_MODEL: str = "embed-multilingual-v3.0"

    # Rate Limiting
    RATE_LIMIT_AUTHENTICATED: int = 100  # requests per minute
    RATE_LIMIT_ANONYMOUS: int = 20  # requests per minute

    # Cache Settings
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # CORS Settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
