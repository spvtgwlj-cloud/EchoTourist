"""Elasticsearch 搜索查询构建器。"""

import logging
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.schemas.search import SearchResponse, SearchTourItem
from app.search.index import INDEX_NAME

logger = logging.getLogger(__name__)


async def search_tours(
    es: AsyncElasticsearch,
    *,
    query: Optional[str] = None,
    locale: str = "en",
    difficulty: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    sort_by: str = "rating",
    page: int = 1,
    page_size: int = 12,
) -> SearchResponse:
    """在 ES 中搜索旅游产品。"""
    page = max(1, page)
    page_size = min(50, max(1, page_size))
    from_ = (page - 1) * page_size

    must_clauses = [
        {"term": {"status": "published"}},
        {"term": {"locale": locale}},
    ]

    if query and query.strip():
        must_clauses.append({
            "multi_match": {
                "query": query.strip(),
                "fields": ["name^3", "description^1.5", "subtitle^2", "highlights^1"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        })

    filter_clauses = []

    if difficulty:
        filter_clauses.append({"term": {"difficulty": difficulty}})

    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        filter_clauses.append({"range": {"start_price": price_range}})

    if min_duration is not None or max_duration is not None:
        duration_range = {}
        if min_duration is not None:
            duration_range["gte"] = min_duration
        if max_duration is not None:
            duration_range["lte"] = max_duration
        filter_clauses.append({"range": {"duration_days": duration_range}})

    # 排序
    sort_field_map = {
        "rating": {"avg_rating": {"order": "desc"}},
        "price_asc": {"start_price": {"order": "asc"}},
        "price_desc": {"start_price": {"order": "desc"}},
        "duration": {"duration_days": {"order": "asc"}},
        "newest": {"published_at": {"order": "desc", "missing": "_last"}},
    }
    sort = sort_field_map.get(sort_by, sort_field_map["rating"])
    # 如果无搜索词，纯按评分排序；有搜索词时，ES 的 _score 优先
    if query and query.strip():
        sort = [{"_score": {"order": "desc"}}, sort]

    body: dict = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses if filter_clauses else None,
            }
        },
        "sort": sort,
        "from": from_,
        "size": page_size,
        "aggs": {
            "difficulties": {
                "terms": {"field": "difficulty", "size": 10}
            },
            "price_ranges": {
                "range": {
                    "field": "start_price",
                    "ranges": [
                        {"key": "0-100", "to": 100},
                        {"key": "100-500", "from": 100, "to": 500},
                        {"key": "500-1000", "from": 500, "to": 1000},
                        {"key": "1000-2000", "from": 1000, "to": 2000},
                        {"key": "2000+", "from": 2000},
                    ],
                }
            },
        },
    }

    # 清理 null filter
    if not filter_clauses:
        del body["query"]["bool"]["filter"]

    logger.info(f"ES search body: {body}")

    try:
        response = await es.search(index=INDEX_NAME, body=body)
    except Exception as e:
        logger.error(f"ES search failed: {e}")
        return SearchResponse(tours=[], total=0, page=page, page_size=page_size)

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    tours = []
    for hit in hits:
        src = hit["_source"]
        tours.append(
            SearchTourItem(
                id=src["id"],
                slug=src["slug"],
                name=src["name"],
                subtitle=src.get("subtitle"),
                duration_days=src["duration_days"],
                start_price=src["start_price"],
                currency=src.get("currency", "USD"),
                avg_rating=src.get("avg_rating", 0),
                review_count=src.get("review_count", 0),
                difficulty=src.get("difficulty", "easy"),
                highlights=src.get("highlights", ""),
                images=src.get("images", []),
            )
        )

    # 提取聚合
    aggregations = response.get("aggregations", {})
    facets = {}
    for name, agg in aggregations.items():
        if "buckets" in agg:
            facets[name] = [
                {"key": b["key"], "count": b["doc_count"]}
                for b in agg["buckets"]
            ]

    return SearchResponse(
        tours=tours,
        total=total,
        page=page,
        page_size=page_size,
        facets=facets if facets else None,
    )
