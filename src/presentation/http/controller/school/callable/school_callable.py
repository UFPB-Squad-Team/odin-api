from ..container import container
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from src.application.school.get_school_by_id.get_school_by_id import (
    GetSchoolById,
)
from src.application.school.fuzzy_search.fuzzy_search import FuzzySearch

def get_list_all_schools_use_case() -> ListAllSchools:
    """Resolve and return an instance of the Use Case."""
    return container.list_all_schools_use_case()

def get_school_by_id_use_case() -> GetSchoolById:
    """Resolve and return an instance of the Use Case."""
    return container.get_school_by_id_use_case()

def get_fuzzy_search_use_case() -> FuzzySearch:
    """Resolve and return an instance of the Use Case."""
    return container.fuzzy_search_use_case()