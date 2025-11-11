from dependency_injector import containers, providers
from src.infrastructure.database.repository import mongo_school_repository
from src.infrastructure.database.config.connect_db import mongodb
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)


class Container(containers.DeclarativeContainer):
    school_repository = providers.Factory(
        mongo_school_repository.MongoSchoolRepository,
        collection=providers.Callable(mongodb.get_collection, "enrich_schools")
    )

    list_all_schools_use_case = providers.Singleton(
        ListAllSchools,
        school_repository=school_repository
    )


container = Container()
