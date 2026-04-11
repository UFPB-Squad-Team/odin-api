from ..container import container
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from src.application.school.get_school_by_id.get_school_by_id import (
    GetSchoolById,
)
from src.application.school.geojson.get_paraiba_geojson import GetParaibaGeoJson
from src.application.school.geojson.get_bairros_geojson import GetBairrosGeoJson
from src.application.school.geojson.get_bairro_by_school_id import GetBairroBySchoolId

def get_list_all_schools_use_case() -> ListAllSchools:
    """Resolve and return an instance of the Use Case."""
    return container.list_all_schools_use_case()

def get_school_by_id_use_case() -> GetSchoolById:
    """Resolve and return an instance of the Use Case."""
    return container.get_school_by_id_use_case()


def get_paraiba_geojson_use_case() -> GetParaibaGeoJson:
    return container.get_paraiba_geojson_use_case()


def get_bairros_geojson_use_case() -> GetBairrosGeoJson:
    return container.get_bairros_geojson_use_case()


def get_bairro_by_school_id_use_case() -> GetBairroBySchoolId:
    return container.get_bairro_by_school_id_use_case()
