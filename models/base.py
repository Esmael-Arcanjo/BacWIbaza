from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

class BaseDocument(BaseModel):
    """Base model with audit fields"""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
