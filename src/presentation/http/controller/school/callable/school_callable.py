from ..container import container
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from src.application.school.get_school_by_id.get_school_by_id import (
    GetSchoolById,
)

def get_list_all_schools_use_case() -> ListAllSchools:
    """Resolve and return an instance of the Use Case."""
    return container.list_all_schools_use_case()

def get_school_by_id_use_case() -> GetSchoolById:
    """Resolve and return an instance of the Use Case."""
    return container.get_school_by_id_use_case()