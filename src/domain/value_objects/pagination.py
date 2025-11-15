from dataclasses import dataclass
from typing import Generic, TypeVar, List
from math import ceil

# This TypeVar ("T") allows our class to be generic.
# It can be a "page of Schools", "page of Students", etc.
T = TypeVar("T")


@dataclass
class PaginatedResponse(Generic[T]):
    """
    A generic container for paginated query results.
    This DTO (Data Transfer Object) is used to return data from
    repositories or services to the API layer.
    """

    # --- Input parameters that generated this page ---
    page: int
    page_size: int

    # --- Data for the current page ---
    total_items: int
    items: List[T]

    @property
    def total_pages(self) -> int:
        """Calculates the total number of pages."""
        if self.page_size == 0:
            return 0
        return ceil(self.total_items / self.page_size)

    @property
    def has_next(self) -> bool:
        """Checks if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Checks if there is a previous page."""
        return self.page > 1
