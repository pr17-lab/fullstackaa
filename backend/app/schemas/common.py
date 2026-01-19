from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    items: List[T] = Field(..., description="List of items")

class HealthStatus(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status")
    database: str = Field(..., description="Database connection status")
    version: str = Field(default="1.0.0", description="API version")

class DetailedHealthStatus(BaseModel):
    """Detailed health check response model."""
    status: str = Field(..., description="Overall health status")
    database: dict = Field(..., description="Database metrics")
    memory: dict = Field(..., description="Memory usage metrics")
