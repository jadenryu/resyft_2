from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class ClaimBase(BaseModel):
    """Base model for claim data"""
    text: str = Field(..., description="The claim text")
    source_url: str = Field(..., description="Source URL of the claim")
    article_id: str = Field(..., description="ID of the parent article")
    language: str = Field(default="en", description="ISO language code")


class ClaimCreate(ClaimBase):
    """Model for creating a new claim"""
    is_immutable: bool = Field(default=False, description="Whether the claim is immutable")
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)


class ClaimNode(ClaimBase):
    """Model representing a claim node in Neo4j"""
    id: UUID = Field(default_factory=uuid4)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    decay_score: float = Field(default=0.0, ge=0.0, le=1.0)
    half_life_days: int = Field(default=365)
    is_immutable: bool = Field(default=False)
    contradiction_count: int = Field(default=0)
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True


class ClaimWithDependencies(ClaimNode):
    """Model for claim with its dependency relationships"""
    supports: List['ClaimNode'] = Field(default_factory=list)
    supported_by: List['ClaimNode'] = Field(default_factory=list)


class ClaimImpact(BaseModel):
    """Model for claim impact analysis"""
    claim_id: UUID
    downstream_impact_score: float = Field(..., ge=0.0, le=1.0)
    affected_claims: List[UUID] = Field(default_factory=list)
    affected_claims_count: int = 0


class VulnerableClaim(ClaimNode):
    """Model for vulnerable claim in triage queue"""
    dependency_weight: float = Field(..., ge=0.0)
    vulnerability_score: float = Field(..., ge=0.0, le=1.0)
    contradicting_sources: List['ContradictingSource'] = Field(default_factory=list)


class ContradictingSource(BaseModel):
    """Model for a source that contradicts a claim"""
    url: str
    text: str
    language: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class Article(BaseModel):
    """Model for encyclopedia article"""
    article_id: str
    title: str
    content: str
    source_urls: List[str] = Field(default_factory=list)
    language: str = Field(default="en")


class ArticleIngestRequest(BaseModel):
    """Request model for article ingestion"""
    article_id: str
    title: str
    content: str
    source_urls: List[str] = Field(default_factory=list)


class ArticleIngestResponse(BaseModel):
    """Response model for article ingestion"""
    job_id: str
    status: str = "queued"
    message: str = "Article queued for processing"


class JobStatus(BaseModel):
    """Model for job status tracking"""
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: Optional[int] = None  # percentage 0-100
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
