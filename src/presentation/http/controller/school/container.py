from dependency_injector import containers, providers
from src.infrastructure.database.repository import mongo_school_repository
from src.infrastructure.database.config.connect_db import mongodb
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from src.application.school.get_school_by_id.get_school_by_id import (
    GetSchoolById,
)
from src.application.school.geojson.get_paraiba_geojson import GetParaibaGeoJson
from src.application.school.geojson.get_bairros_geojson import GetBairrosGeoJson
from src.application.school.geojson.get_bairro_by_school_id import GetBairroBySchoolId

class Container(containers.DeclarativeContainer):
    school_repository = providers.Factory(
        mongo_school_repository.MongoSchoolRepository,
        collection=providers.Callable(mongodb.get_collection, "escolas")
    )

    list_all_schools_use_case = providers.Singleton(
        ListAllSchools,
        school_repository=school_repository
    )

    get_school_by_id_use_case = providers.Singleton(
        GetSchoolById,
        school_repository=school_repository
    )

    get_paraiba_geojson_use_case = providers.Singleton(
        GetParaibaGeoJson,
        school_repository=school_repository,
    )

    get_bairros_geojson_use_case = providers.Singleton(
        GetBairrosGeoJson,
        school_repository=school_repository,
    )

    get_bairro_by_school_id_use_case = providers.Singleton(
        GetBairroBySchoolId,
        school_repository=school_repository,
    )

container = Container()
