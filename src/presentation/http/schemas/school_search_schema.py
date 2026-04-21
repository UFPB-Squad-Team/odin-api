from dataclasses import asdict
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.value_objects.query import QueryOptions

SCHOOL_ALLOWED_FILTER_FIELDS = {
    "id",
    "escola_id_inep",
    "escola_nome",
    "municipio_nome",
    "estado_sigla",
    "dependencia_adm",
    "tipo_localizacao",
    "municipio_id_ibge",
    "bairro",
}

SCHOOL_ALLOWED_SORT_FIELDS = SCHOOL_ALLOWED_FILTER_FIELDS
SCHOOL_ALLOWED_FIELDS = SCHOOL_ALLOWED_FILTER_FIELDS
SCHOOL_ALLOWED_OPERATORS = {
    "eq",
    "ne",
    "in",
    "nin",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "startswith",
    "endswith",
}


class SchoolSearchFilterSchema(BaseModel):
    field: str
    operator: str = Field(default="eq")
    value: object

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        if value not in SCHOOL_ALLOWED_FILTER_FIELDS:
            raise ValueError(f"Filter field '{value}' is not allowed")
        return value

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        if value not in SCHOOL_ALLOWED_OPERATORS:
            raise ValueError(f"Filter operator '{value}' is not allowed")
        return value


class SchoolSearchSchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1)
    cursor: Optional[str] = None
    sort: Optional[str] = None
    fields: Optional[List[str]] = None
    filters: List[SchoolSearchFilterSchema] = Field(default_factory=list)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        invalid = [field for field in value if field not in SCHOOL_ALLOWED_FIELDS]
        if invalid:
            raise ValueError(f"Projection field(s) not allowed: {', '.join(invalid)}")
        return value

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        field = value[1:] if value.startswith("-") else value
        if field not in SCHOOL_ALLOWED_SORT_FIELDS:
            raise ValueError(f"Sort field '{field}' is not allowed")
        return value

    @model_validator(mode="after")
    def validate_filters(self):
        for item in self.filters:
            if item.field not in SCHOOL_ALLOWED_FILTER_FIELDS:
                raise ValueError(f"Filter field '{item.field}' is not allowed")
        return self

    @classmethod
    def from_query_options(cls, query_options: QueryOptions) -> "SchoolSearchSchema":
        return cls.model_validate(
            {
                "page": query_options.page,
                "page_size": query_options.page_size,
                "cursor": query_options.cursor,
                "sort": (
                    f"-{query_options.sort.field}"
                    if query_options.sort and query_options.sort.direction < 0
                    else query_options.sort.field if query_options.sort else None
                ),
                "fields": query_options.fields,
                "filters": [
                    {
                        "field": item.field,
                        "operator": item.operator,
                        "value": item.value,
                    }
                    for item in query_options.filters
                ],
            }
        )

    def to_query_options(self) -> QueryOptions:
        from src.domain.value_objects.query import QueryFilter, QuerySort

        sort = None
        if self.sort:
            sort = QuerySort(
                field=self.sort[1:] if self.sort.startswith("-") else self.sort,
                direction=-1 if self.sort.startswith("-") else 1,
            )

        return QueryOptions(
            page=self.page,
            page_size=self.page_size,
            cursor=self.cursor,
            sort=sort,
            fields=self.fields,
            filters=[
                QueryFilter(field=item.field, operator=item.operator, value=item.value)
                for item in self.filters
            ],
        )
