from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponseSchema(BaseModel, Generic[T]):
    """
    Pydantic schema for HTTP responses with pagination metadata.
    Used in FastAPI response_model for type checking and OpenAPI documentation.
    """
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total_items: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None

