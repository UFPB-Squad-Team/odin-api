from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from ..container import container


def get_list_all_schools_use_case() -> ListAllSchools:
    """Resolve and return an instance of the Use Case."""
    return container.list_all_schools_use_case()
