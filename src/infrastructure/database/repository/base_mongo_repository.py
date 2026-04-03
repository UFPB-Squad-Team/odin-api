import base64
import json
import re
from abc import ABC
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from bson import ObjectId
from bson.errors import InvalidId

from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryFilter, QueryOptions

T = TypeVar("T")


class BaseMongoRepository(ABC, Generic[T]):
    def __init__(
        self,
        collection: Any,
        *,
        mapper_to_domain: Callable[[Dict[str, Any]], T],
        field_map: Dict[str, str],
        required_projection_fields: Optional[List[str]] = None,
        default_sort_field: str,
    ):
        self.collection = collection
        self.mapper_to_domain = mapper_to_domain
        self.field_map = field_map
        self.required_projection_fields = required_projection_fields or []
        self.default_sort_field = default_sort_field

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        document = None

        try:
            document = await self.collection.find_one({"_id": ObjectId(entity_id)})
        except InvalidId:
            document = None

        if document is None:
            document = await self.collection.find_one({"_id": entity_id})

        if document is None:
            return None

        return self.mapper_to_domain(document)

    async def exists(self, entity_id: str) -> bool:
        return (await self.get_by_id(entity_id)) is not None

    async def find_paginated(self, query: QueryOptions) -> PaginatedResponse[T]:
        filters_query = self._build_filters(query.filters)
        sort_field, sort_direction = self._resolve_sort(query)
        projection = self._build_projection(query.fields)

        mongo_query = filters_query
        if query.cursor:
            cursor_clause = self._build_cursor_clause(
                cursor=query.cursor,
                sort_field=sort_field,
                sort_direction=sort_direction,
            )
            mongo_query = self._merge_queries(filters_query, cursor_clause)

        cursor = self.collection.find(mongo_query, projection)
        cursor = cursor.sort([(sort_field, sort_direction), ("_id", sort_direction)])

        page = max(query.page, 1)
        limit = max(query.page_size, 1)

        if query.cursor:
            cursor = cursor.limit(limit + 1)
            documents = await cursor.to_list(length=limit + 1)
            has_more = len(documents) > limit
            page_docs = documents[:limit]
            next_cursor = (
                self._encode_cursor(page_docs[-1], sort_field) if has_more and page_docs else None
            )
        else:
            cursor = cursor.skip((page - 1) * limit).limit(limit)
            page_docs = await cursor.to_list(length=limit)
            next_cursor = None

        total_items = await self.collection.count_documents(filters_query)
        items = [self.mapper_to_domain(doc) for doc in page_docs]

        return PaginatedResponse[T](
            items=items,
            total_items=total_items,
            page=page,
            page_size=limit,
            next_cursor=next_cursor,
        )

    def _build_filters(self, filters: List[QueryFilter]) -> Dict[str, Any]:
        if not filters:
            return {}

        clauses: List[Dict[str, Any]] = []
        for item in filters:
            mongo_field = self.field_map.get(item.field)
            if not mongo_field:
                raise ValueError(f"Filter field '{item.field}' is not allowed")

            op = item.operator
            value = item.value

            if op == "eq":
                clauses.append({mongo_field: value})
            elif op == "ne":
                clauses.append({mongo_field: {"$ne": value}})
            elif op == "in":
                clauses.append({mongo_field: {"$in": value}})
            elif op == "nin":
                clauses.append({mongo_field: {"$nin": value}})
            elif op == "gt":
                clauses.append({mongo_field: {"$gt": value}})
            elif op == "gte":
                clauses.append({mongo_field: {"$gte": value}})
            elif op == "lt":
                clauses.append({mongo_field: {"$lt": value}})
            elif op == "lte":
                clauses.append({mongo_field: {"$lte": value}})
            elif op == "contains":
                pattern = re.escape(str(value))
                clauses.append({mongo_field: {"$regex": pattern, "$options": "i"}})
            elif op == "startswith":
                pattern = f"^{re.escape(str(value))}"
                clauses.append({mongo_field: {"$regex": pattern, "$options": "i"}})
            elif op == "endswith":
                pattern = f"{re.escape(str(value))}$"
                clauses.append({mongo_field: {"$regex": pattern, "$options": "i"}})
            else:
                raise ValueError(f"Filter operator '{op}' is not allowed")

        if len(clauses) == 1:
            return clauses[0]

        return {"$and": clauses}

    def _resolve_sort(self, query: QueryOptions) -> tuple[str, int]:
        if not query.sort:
            return self.default_sort_field, 1

        mongo_field = self.field_map.get(query.sort.field)
        if not mongo_field:
            raise ValueError(f"Sort field '{query.sort.field}' is not allowed")

        direction = -1 if query.sort.direction < 0 else 1
        return mongo_field, direction

    def _build_projection(self, requested_fields: Optional[List[str]]) -> Optional[Dict[str, int]]:
        if not requested_fields:
            return None

        projection: Dict[str, int] = {"_id": 1}
        all_fields = set(requested_fields + self.required_projection_fields)

        for field in all_fields:
            mongo_field = self.field_map.get(field)
            if not mongo_field:
                raise ValueError(f"Projection field '{field}' is not allowed")
            projection[mongo_field] = 1

        return projection

    def _encode_cursor(self, document: Dict[str, Any], sort_field: str) -> str:
        payload = {
            "sort_value": document.get(sort_field),
            "id": str(document.get("_id")),
        }
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
        return encoded.decode("utf-8")

    def _build_cursor_clause(
        self,
        *,
        cursor: str,
        sort_field: str,
        sort_direction: int,
    ) -> Dict[str, Any]:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            payload = json.loads(decoded)
        except Exception as exc:
            raise ValueError("Invalid cursor format") from exc

        sort_value = payload.get("sort_value")
        cursor_id_raw = payload.get("id")
        if cursor_id_raw is None:
            raise ValueError("Invalid cursor payload")

        cursor_id = self._parse_mongo_id(cursor_id_raw)

        cmp_operator = "$gt" if sort_direction > 0 else "$lt"

        return {
            "$or": [
                {sort_field: {cmp_operator: sort_value}},
                {sort_field: sort_value, "_id": {cmp_operator: cursor_id}},
            ]
        }

    def _merge_queries(self, left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
        if not left:
            return right
        if not right:
            return left
        return {"$and": [left, right]}

    @staticmethod
    def _parse_mongo_id(value: str) -> Any:
        try:
            return ObjectId(value)
        except InvalidId:
            return value
