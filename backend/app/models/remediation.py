from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RemediationAction(str, Enum):
    """Remediation action types"""
    VERIFIED = "verified"
    UPDATED = "updated"
    FLAGGED = "flagged"
    DISMISSED = "dismissed"


class RemediationBase(BaseModel):
    """Base remediation model"""
    claim_id: UUID
    action: RemediationAction
    previous_text: Optional[str] = None
    new_text: Optional[str] = None


class RemediationCreate(RemediationBase):
    """Model for creating a remediation record"""
    pass


class Remediation(RemediationBase):
    """Full remediation model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AuditLog(BaseModel):
    """Audit log entry"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    action: str
    target_type: str  # claim, article, user, etc.
    target_id: str
    metadata: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
