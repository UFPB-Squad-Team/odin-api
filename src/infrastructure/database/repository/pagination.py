from typing import Any, Dict, Optional, Tuple


async def fetch_paginated_documents(
    collection: Any,
    *,
    page: int,
    page_size: int,
    sort_field: str,
    query: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, int]] = None,
    use_estimated_total_for_unfiltered: bool = False,
) -> Tuple[list[Dict[str, Any]], int]:
    filters = query or {}

    cursor = collection.find(filters, projection).sort(sort_field, 1)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)
    documents = await cursor.to_list(length=page_size)
    if use_estimated_total_for_unfiltered and not filters:
        total_items = await collection.estimated_document_count()
    else:
        total_items = await collection.count_documents(filters)

    return documents, total_items