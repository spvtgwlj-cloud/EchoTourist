"""
清理测试过程数据脚本（数据库 + Elasticsearch 索引）。

使用方式：PYTHONPATH=$PWD .venv/bin/python scripts/cleanup_test_data.py

清理内容：
1. tours 中以 "test" 开头的 slug 记录（含关联的 reviews, orders, translations 等）
2. destinations 中以 "test"/"detail"/"dup"/"upd"/"del" 开头的 slug 记录
3. Elasticsearch 索引中 slug 以 "test-" 开头的文档
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings


async def cleanup():
    engine = create_async_engine(settings.database_url, echo=False, pool_size=2)
    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        # ── Phase 1: 清理 test tours ──────────────────────────────
        print("=== 清理 Tours 测试数据 ===")
        # 找到所有以 "test" 开头的 tour slug
        result = await session.execute(
            text("SELECT id, slug FROM tours WHERE slug ILIKE 'test-%'")
        )
        test_tours = result.all()
        print(f"  找到 {len(test_tours)} 个 test tour:")
        for t in test_tours:
            print(f"    - {t.slug} ({t.id})")

        if test_tours:
            tour_ids = [t.id for t in test_tours]

            # 按外键依赖顺序删除

            # 1) attraction_wishlists (无 tour FK, 跳过)
            # 2) reviews
            r1 = await session.execute(
                text("DELETE FROM reviews WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r1.rowcount} 条 reviews")

            # 3) wishlists
            r2 = await session.execute(
                text("DELETE FROM wishlists WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r2.rowcount} 条 wishlists")

            # 4) order_passengers (先删子表)
            r3 = await session.execute(
                text("""
                    DELETE FROM order_passengers
                    WHERE order_id IN (
                        SELECT id FROM orders WHERE tour_id = ANY(:ids)
                    )
                """),
                {"ids": tour_ids},
            )
            print(f"  删除 {r3.rowcount} 条 order_passengers")

            # 5) orders
            r4 = await session.execute(
                text("DELETE FROM orders WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r4.rowcount} 条 orders")

            # 6) tour_dates
            r5 = await session.execute(
                text("DELETE FROM tour_dates WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r5.rowcount} 条 tour_dates")

            # 7) tour_images
            r6 = await session.execute(
                text("DELETE FROM tour_images WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r6.rowcount} 条 tour_images")

            # 8) tour_translations
            r7 = await session.execute(
                text("DELETE FROM tour_translations WHERE tour_id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r7.rowcount} 条 tour_translations")

            # 9) tours
            r8 = await session.execute(
                text("DELETE FROM tours WHERE id = ANY(:ids)"),
                {"ids": tour_ids},
            )
            print(f"  删除 {r8.rowcount} 条 tours (本体)")

        # ── Phase 2: 清理 test/detail destinations ────────────────
        print("\n=== 清理 Destinations 测试数据 ===")

        # 先查找匹配的 destinations
        result = await session.execute(
            text("""
                SELECT d.id, d.slug
                FROM destinations d
                WHERE d.slug ILIKE 'test-%' OR d.slug ILIKE 'detail-%'
                   OR d.slug ILIKE 'dup-%' OR d.slug ILIKE 'upd-%'
                   OR d.slug ILIKE 'del-%'
                   OR d.slug ILIKE '%-test' OR d.slug ILIKE '%-detail'
            """)
        )
        test_dests = result.all()
        print(f"  找到 {len(test_dests)} 个 test/detail destination:")
        for d in test_dests:
            print(f"    - {d.slug} ({d.id})")

        if test_dests:
            dest_ids = [d.id for d in test_dests]

            # 1) 处理 custom_tour 系列的引用 (先删子表)
            #    custom_tour_segment_tours → segments
            #    custom_tour_attractions → segments
            #    custom_tour_segments → destinations + requests
            #    custom_tour_services → requests
            #    custom_tour_requests → destinations

            # 找到所有引用了 test destinations 的 segments
            seg_result = await session.execute(
                text("SELECT id FROM custom_tour_segments WHERE destination_id = ANY(:ids)"),
                {"ids": dest_ids},
            )
            seg_ids = [r.id for r in seg_result.all()]

            if seg_ids:
                r = await session.execute(
                    text("DELETE FROM custom_tour_segment_tours WHERE segment_id = ANY(:sids)"),
                    {"sids": seg_ids},
                )
                print(f"  删除 {r.rowcount} 条 custom_tour_segment_tours")

                r = await session.execute(
                    text("DELETE FROM custom_tour_attractions WHERE segment_id = ANY(:sids)"),
                    {"sids": seg_ids},
                )
                print(f"  删除 {r.rowcount} 条 custom_tour_attractions")

                r = await session.execute(
                    text("DELETE FROM custom_tour_segments WHERE id = ANY(:sids)"),
                    {"sids": seg_ids},
                )
                print(f"  删除 {r.rowcount} 条 custom_tour_segments")

            # 找到所有引用了 test destinations 的 requests
            req_result = await session.execute(
                text("SELECT id FROM custom_tour_requests WHERE destination_id = ANY(:ids)"),
                {"ids": dest_ids},
            )
            req_ids = [r.id for r in req_result.all()]

            if req_ids:
                r = await session.execute(
                    text("DELETE FROM custom_tour_services WHERE request_id = ANY(:rids)"),
                    {"rids": req_ids},
                )
                print(f"  删除 {r.rowcount} 条 custom_tour_services")

                r = await session.execute(
                    text("DELETE FROM custom_tour_requests WHERE id = ANY(:rids)"),
                    {"rids": req_ids},
                )
                print(f"  删除 {r.rowcount} 条 custom_tour_requests")

            # 2) 解除 tours 对 destination_ids 的引用
            r = await session.execute(
                text("SELECT id, destination_ids FROM tours WHERE destination_ids && :ids"),
                {"ids": dest_ids},
            )
            ref_tours = r.all()
            for tour_row in ref_tours:
                new_ids = [did for did in tour_row.destination_ids if did not in dest_ids]
                await session.execute(
                    text("UPDATE tours SET destination_ids = :new_ids WHERE id = :tid"),
                    {"new_ids": new_ids, "tid": tour_row.id},
                )
            print(f"  更新 {len(ref_tours)} 条 tours (移除引用)")

            # 3) destination_translations
            r = await session.execute(
                text("DELETE FROM destination_translations WHERE destination_id = ANY(:ids)"),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 destination_translations")

            # 4) 删除关联的 attraction_wishlists
            r = await session.execute(
                text("""
                    DELETE FROM attraction_wishlists
                    WHERE attraction_id IN (
                        SELECT id FROM attractions WHERE destination_id = ANY(:ids)
                    )
                """),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 attraction_wishlists")

            # 5) 删除关联的 attraction_media
            r = await session.execute(
                text("""
                    DELETE FROM attraction_media
                    WHERE attraction_id IN (
                        SELECT id FROM attractions WHERE destination_id = ANY(:ids)
                    )
                """),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 attraction_media")

            # 6) 删除关联的 attraction_tickets
            r = await session.execute(
                text("""
                    DELETE FROM attraction_tickets
                    WHERE attraction_id IN (
                        SELECT id FROM attractions WHERE destination_id = ANY(:ids)
                    )
                """),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 attraction_tickets")

            # 7) 删除关联的 attraction_translations
            r = await session.execute(
                text("""
                    DELETE FROM attraction_translations
                    WHERE attraction_id IN (
                        SELECT id FROM attractions WHERE destination_id = ANY(:ids)
                    )
                """),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 attraction_translations")

            # 8) 删除关联的 attractions
            r = await session.execute(
                text("DELETE FROM attractions WHERE destination_id = ANY(:ids)"),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 attractions")

            # 9) 删除 destinations
            r = await session.execute(
                text("DELETE FROM destinations WHERE id = ANY(:ids)"),
                {"ids": dest_ids},
            )
            print(f"  删除 {r.rowcount} 条 destinations (本体)")

        await session.commit()
        print("\n✅ 清理完成!")

    await engine.dispose()


def cleanup_es():
    """清理 Elasticsearch 索引中的测试数据"""
    ES_URL = settings.elasticsearch_url.rstrip("/")

    # 查找 ES 索引（搜索可能的索引名）
    r = requests.get(f"{ES_URL}/_cat/indices/tours*?format=json", timeout=5)
    indices = r.json()
    if not indices:
        print("⚠️  未找到 ES 索引，跳过 ES 清理")
        return

    index_name = indices[0]["index"]
    print(f"\n=== 清理 ES 索引 [{index_name}] 中的测试数据 ===")

    # 1. 搜索 test- 前缀的文档
    query = {
        "query": {
            "bool": {
                "filter": [
                    {"prefix": {"slug": "test-"}}
                ]
            }
        },
        "_source": ["slug"],
        "size": 200,
    }
    r = requests.post(f"{ES_URL}/{index_name}/_search", json=query, timeout=10)
    data = r.json()
    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        print("  🔍 未找到 test- 前缀文档，ES 已干净")
        return

    doc_ids = [h["_id"] for h in hits]
    slugs = [h["_source"]["slug"] for h in hits]
    print(f"  找到 {len(doc_ids)} 个 test 文档:")
    for slug in sorted(set(slugs)):
        count = slugs.count(slug)
        print(f"    - {slug} ({count} 语言)")

    # 2. 逐个删除
    for doc_id in doc_ids:
        r = requests.delete(f"{ES_URL}/{index_name}/_doc/{doc_id}", timeout=5)
        if r.status_code not in (200, 404):
            print(f"  ⚠️  删除 {doc_id} 失败: {r.status_code} {r.text[:100]}")

    # 3. 刷新索引
    requests.post(f"{ES_URL}/{index_name}/_refresh", timeout=5)
    print(f"  ✅ 已删除 {len(doc_ids)} 个文档，索引已刷新")


if __name__ == "__main__":
    cleanup_es()
    print()
    asyncio.run(cleanup())
