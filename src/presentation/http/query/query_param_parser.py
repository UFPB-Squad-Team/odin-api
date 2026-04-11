import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException
from starlette.datastructures import QueryParams

from src.domain.value_objects.query import QueryFilter, QueryOptions, QuerySort


@dataclass(frozen=True)
class AllowedFilter:
    caster: Callable[[str], Any]
    operators: List[str]


def to_int(value: str) -> int:
    return int(value)


def to_str(value: str) -> str:
    return value


class QueryParamParser:
    FILTER_PATTERN = re.compile(r"^filter\[(?P<field>[a-zA-Z0-9_]+)(?:__(?P<op>[a-z_]+))?\]$")

    @classmethod
    def parse(
        cls,
        *,
        query_params: QueryParams,
        allowed_filters: Dict[str, AllowedFilter],
        allowed_fields: List[str],
        default_sort_field: str,
        default_page_size: int,
        max_page_size: int,
    ) -> QueryOptions:
        try:
            page = int(query_params.get("page", 1))
            page_size = int(query_params.get("page_size", default_page_size))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid page or page_size") from exc

        if page < 1:
            raise HTTPException(status_code=422, detail="page must be >= 1")

        if page_size < 1 or page_size > max_page_size:
            raise HTTPException(
                status_code=422,
                detail=f"page_size must be between 1 and {max_page_size}",
            )

        cursor = query_params.get("cursor")
        sort = cls._parse_sort(query_params.get("sort"), default_sort_field, allowed_fields)
        fields = cls._parse_fields(query_params.get("fields"), allowed_fields)
        filters = cls._parse_filters(query_params, allowed_filters)

        return QueryOptions(
            page=page,
            page_size=page_size,
            cursor=cursor,
            filters=filters,
            sort=sort,
            fields=fields,
        )

    @classmethod
    def _parse_sort(
        cls,
        raw_sort: Optional[str],
        default_sort_field: str,
        allowed_fields: List[str],
    ) -> QuerySort:
        if not raw_sort:
            return QuerySort(field=default_sort_field, direction=1)

        direction = -1 if raw_sort.startswith("-") else 1
        field = raw_sort[1:] if raw_sort.startswith("-") else raw_sort

        if field not in allowed_fields:
            raise HTTPException(status_code=422, detail=f"Sort field '{field}' is not allowed")

        return QuerySort(field=field, direction=direction)

    @classmethod
    def _parse_fields(
        cls,
        raw_fields: Optional[str],
        allowed_fields: List[str],
    ) -> Optional[List[str]]:
        if not raw_fields:
            return None

        parsed = [field.strip() for field in raw_fields.split(",") if field.strip()]
        if not parsed:
            return None

        invalid = [field for field in parsed if field not in allowed_fields]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Projection field(s) not allowed: {', '.join(invalid)}",
            )

        return parsed

    @classmethod
    def _parse_filters(
        cls,
        query_params: QueryParams,
        allowed_filters: Dict[str, AllowedFilter],
    ) -> List[QueryFilter]:
        filters: List[QueryFilter] = []

        for key, value in query_params.multi_items():
            match = cls.FILTER_PATTERN.match(key)
            if not match:
                continue

            field = match.group("field")
            operator = match.group("op") or "eq"

            if field not in allowed_filters:
                raise HTTPException(status_code=422, detail=f"Filter field '{field}' is not allowed")

            filter_config = allowed_filters[field]
            if operator not in filter_config.operators:
                raise HTTPException(
                    status_code=422,
                    detail=f"Operator '{operator}' is not allowed for filter '{field}'",
                )

            parsed_value = cls._cast_filter_value(value, operator, filter_config.caster)
            filters.append(QueryFilter(field=field, operator=operator, value=parsed_value))

        return filters

    @staticmethod
    def _cast_filter_value(raw_value: str, operator: str, caster: Callable[[str], Any]) -> Any:
        try:
            if operator in {"in", "nin"}:
                return [caster(item.strip()) for item in raw_value.split(",") if item.strip()]
            return caster(raw_value)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid filter value") from exc
