"""Elasticsearch 索引定义和批量索引操作。"""

import logging

from elasticsearch import AsyncElasticsearch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tour import Tour, TourTranslation

logger = logging.getLogger(__name__)

INDEX_NAME = "tours"

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "tours_combined": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "slug": {"type": "keyword"},
            "status": {"type": "keyword"},
            "type": {"type": "keyword"},
            "duration_days": {"type": "short"},
            "start_price": {"type": "float"},
            "currency": {"type": "keyword"},
            "avg_rating": {"type": "float"},
            "review_count": {"type": "integer"},
            "difficulty": {"type": "keyword"},
            "max_pax": {"type": "short"},
            "destination_ids": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "tours_combined",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "standard"},
            "subtitle": {"type": "text", "analyzer": "standard"},
            "highlights": {"type": "text", "analyzer": "standard"},
            "locale": {"type": "keyword"},
            "published_at": {"type": "date"},
            "created_at": {"type": "date"},
        }
    },
}


async def create_index(es: AsyncElasticsearch) -> bool:
    """创建索引（如果不存在）。"""
    exists = await es.indices.exists(index=INDEX_NAME)
    if not exists:
        await es.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        logger.info(f"Created ES index: {INDEX_NAME}")
        return True
    return False


async def delete_index(es: AsyncElasticsearch):
    """删除索引（用于重建）。"""
    exists = await es.indices.exists(index=INDEX_NAME)
    if exists:
        await es.indices.delete(index=INDEX_NAME)
        logger.info(f"Deleted ES index: {INDEX_NAME}")


async def index_tour(es: AsyncElasticsearch, tour: Tour, translation: TourTranslation):
    """索引单个 Tour（以某 locale 的翻译为内容）。"""
    doc = {
        "id": str(tour.id),
        "slug": tour.slug,
        "status": tour.status,
        "type": tour.type,
        "duration_days": tour.duration_days,
        "start_price": tour.start_price or 0,
        "currency": tour.currency or "USD",
        "avg_rating": tour.avg_rating or 0,
        "review_count": tour.review_count or 0,
        "difficulty": tour.difficulty or "easy",
        "max_pax": tour.max_pax,
        "destination_ids": [str(d) for d in (tour.destination_ids or [])],
        "name": translation.name,
        "description": translation.description or "",
        "subtitle": translation.subtitle or "",
        "highlights": " ".join(tour.highlights or []),
        "locale": translation.locale,
        "published_at": tour.published_at.isoformat() if tour.published_at else None,
        "created_at": tour.created_at.isoformat() if tour.created_at else None,
    }
    # 用 tour_id + locale 作为文档 ID，每个 locale 一条记录
    doc_id = f"{tour.id}-{translation.locale}"
    await es.index(index=INDEX_NAME, id=doc_id, document=doc)


async def bulk_index_tours(db: AsyncSession, es: AsyncElasticsearch) -> int:
    """将 DB 中所有已发布的 Tour 批量索引到 ES。返回索引条数。"""
    result = await db.execute(
        select(Tour)
        .options(selectinload(Tour.tour_translations))
        .where(Tour.status == "published", Tour.deleted_at.is_(None))
    )
    tours = result.scalars().all()

    indexed = 0
    for tour in tours:
        for translation in tour.tour_translations or []:
            try:
                await index_tour(es, tour, translation)
                indexed += 1
            except Exception as e:
                logger.error(f"Failed to index tour {tour.id}/{translation.locale}: {e}")

    logger.info(f"Indexed {indexed} tour documents into ES")
    return indexed
