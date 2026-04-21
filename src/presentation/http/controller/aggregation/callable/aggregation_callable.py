from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)
from src.presentation.http.controller.aggregation.container import container


def get_city_aggregations_use_case() -> GetCityAggregations:
    return container.get_city_aggregations_use_case()


def get_neighborhood_aggregations_use_case() -> GetNeighborhoodAggregations:
    return container.get_neighborhood_aggregations_use_case()
