#!/usr/bin/env python3
"""
Echo Tours 种子数据脚本。

为开发和演示环境创建示例数据：
- 目的地：北京（主，含全部主要5A景区信息）、南京、西安
- 旅游产品：涵盖北京主要5A景区的深度游览线路
- 价格日历：近3个月可选日期及价格
- 多语言翻译：中文（主）/ 英文
- 用户：管理员 + 普通用户
- 评论示例（含审核通过状态）

用法：
    # 在 Docker 容器中运行（推荐）
    cd /Users/wulianjun/.claude/Echo-Website
    docker compose exec backend python /app/scripts/seed_data.py

    # 或在本地直接运行（需安装后端依赖及运行中的 PostgreSQL）
    cd scripts && python seed_data.py
"""

import asyncio
import logging
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import os  # noqa: E402

# ── 路径处理：确保能导入 backend 模块 ──────────────────────────────────────
# 兼容 Docker 容器内（/app）和项目根目录运行两种场景
_script_dir = Path(__file__).resolve().parent
_candidates = [
    _script_dir.parent.parent / "src" / "backend",  # 项目根/src/backend
    _script_dir.parent,                               # 项目根目录 or /app
]
for _p in _candidates:
    _app_dir = _p / "app"
    if _app_dir.is_dir() and (_app_dir / "__init__.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/echo_tours")
os.environ["DEBUG"] = "False"  # 抑制 SQLAlchemy 引擎的 SQL 语句打印

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")

# ── 数据库 ────────────────────────────────────────────────────────────────
from sqlalchemy import text, select  # noqa: E402
from app.database import async_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    Tour, TourTranslation, TourDate, TourImage,
    User, Review,
    Destination, DestinationTranslation,
    Attraction, AttractionTranslation, AttractionTicket, AttractionMedia,
    BaseService,
)

# ═══════════════════════════════════════════════════════════════════════════
# 数据定义
# ═══════════════════════════════════════════════════════════════════════════

# ── 目的地 ────────────────────────────────────────────────────────────────

DESTINATIONS = {
    "beijing": {
        "slug": "beijing",
        "area_code": "010",
        "image_url": "/images/destinations/beijing.svg",
        "translations": {
            "zh": {"name": "北京", "description": "中国首都，拥有三千多年历史的古都，汇聚了众多世界文化遗产和5A级旅游景区。", "meta_title": "北京旅游攻略 | Echo Tours", "meta_description": "探索北京故宫、长城、颐和园等世界级景点，体验千年古都的魅力与现代活力。"},
            "en": {"name": "Beijing", "description": "China's capital, an ancient capital with over 3,000 years of history, home to numerous UNESCO World Heritage sites and premier attractions.", "meta_title": "Beijing Travel Guide | Echo Tours", "meta_description": "Explore Beijing's Forbidden City, Great Wall, Summer Palace and more world-class attractions."},
        },
    },
    "nanjing": {
        "slug": "nanjing",
        "area_code": "025",
        "image_url": "/images/destinations/nanjing.svg",
        "translations": {
            "zh": {"name": "南京", "description": "六朝古都，中国东部重要历史文化名城，拥有夫子庙、中山陵等著名景点。", "meta_title": "南京旅游攻略 | Echo Tours", "meta_description": "游六朝古都南京，访中山陵、夫子庙，感受金陵千年文化底蕴。"},
            "en": {"name": "Nanjing", "description": "Ancient capital of six dynasties, a historically and culturally significant city in eastern China.", "meta_title": "Nanjing Travel Guide | Echo Tours", "meta_description": "Visit Nanjing's Sun Yat-sen Mausoleum, Confucius Temple and experience millennia of culture."},
        },
    },
    "xian": {
        "slug": "xian",
        "area_code": "029",
        "image_url": "/images/destinations/xian.svg",
        "translations": {
            "zh": {"name": "西安", "description": "十三朝古都，世界四大古都之一，以兵马俑和盛唐文化闻名于世。", "meta_title": "西安旅游攻略 | Echo Tours", "meta_description": "参观世界第八大奇迹兵马俑，漫步古城墙，品味盛唐风华。"},
            "en": {"name": "Xi'an", "description": "Ancient capital of 13 dynasties, one of the four great ancient capitals of the world, famous for the Terracotta Warriors.", "meta_title": "Xi'an Travel Guide | Echo Tours", "meta_description": "Visit the Eighth Wonder of the World — Terracotta Warriors, walk the ancient city wall."},
        },
    },
}

# ── 旅游产品 ──────────────────────────────────────────────────────────────

TOURS = [
    # ═══════════════ 北京-故宫相关 ═══════════════
    {
        "slug": "forbidden-city-royal-walk",
        "serial_number": "0001",
        "type": "group_tour",
        "status": "published",
        "duration_days": 1,
        "duration_nights": 0,
        "max_pax": 30,
        "min_pax": 2,
        "start_price": 99.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["故宫博物院深度讲解", "三大殿+后三宫+珍宝馆", "专享快速通道免排队", "专业中文/英文导游陪同", "含故宫文创纪念品"],
        "includes": ["故宫门票+珍宝馆门票", "专业导游讲解服务", "无线耳麦接收器", "故宫文创小礼品", "旅游意外险"],
        "excludes": ["个人消费", "餐饮费用", "酒店接送（可加购）"],
        "translations": {
            "zh": {
                "name": "故宫深度文化游",
                "subtitle": "漫步紫禁城，探寻六百年皇家秘密",
                "description": "故宫，又称紫禁城，是明清两代的皇家宫殿，位于北京中轴线的中心，是世界上现存规模最大、保存最完整的木质结构古建筑群。本行程由资深导游带领，深入探索三大殿、后三宫、珍宝馆等核心区域，为您讲述六百年皇家历史的兴衰更替。",
                "itinerary": [
                    {"day": 1, "title": "故宫深度游", "description": "上午：午门集合 → 太和殿 → 中和殿 → 保和殿\n中午：故宫内休息\n下午：乾清宫 → 交泰殿 → 坤宁宫 → 御花园 → 珍宝馆 → 神武门结束"},
                ],
                "meta_title": "故宫深度文化游 | Echo Tours",
                "meta_description": "专业导游带您深度游览故宫博物院，探索三大殿、后三宫、珍宝馆，感受六百年紫禁城的辉煌。",
            },
            "en": {
                "name": "Forbidden City Deep Cultural Tour",
                "subtitle": "Roam the Purple Forbidden City, uncover 600 years of imperial secrets",
                "description": "The Forbidden City, a UNESCO World Heritage site, served as the imperial palace for 24 emperors during the Ming and Qing dynasties. This tour offers an expert-guided exploration of the Hall of Supreme Harmony, the Imperial Garden, and the Treasure Gallery.",
                "itinerary": [
                    {"day": 1, "title": "Forbidden City Tour", "description": "Morning: Meet at Meridian Gate → Hall of Supreme Harmony → Hall of Central Harmony → Hall of Preserving Harmony\nAfternoon: Palace of Heavenly Purity → Hall of Union → Palace of Earthly Tranquility → Imperial Garden → Treasure Gallery → Exit from Gate of Divine Might"},
                ],
                "highlights": [
                    "Expert-guided Forbidden City tour",
                    "Hall of Supreme Harmony & Imperial Garden",
                    "Treasure Gallery admission included",
                    "Fast-track entry — skip the lines",
                    "Professional bilingual guide",
                    "Commemorative souvenir gift",
                ],
                "includes": [
                    "Forbidden City + Treasure Gallery tickets",
                    "Professional guide service",
                    "Wireless headset receiver",
                    "Souvenir gift",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal expenses",
                    "Meals and drinks",
                    "Hotel pickup (available as add-on)",
                ],
                "meta_title": "Forbidden City Deep Tour | Echo Tours",
                "meta_description": "Expert-guided in-depth tour of the Forbidden City, exploring the Hall of Supreme Harmony, Imperial Garden and Treasure Gallery.",
            },
        },
        "images": [
            {"url": "/images/tours/forbidden-city-1.svg", "alt_text": "故宫太和殿全景", "sort_order": 1},
            {"url": "/images/tours/forbidden-city-2.svg", "alt_text": "故宫金水桥与太和门", "sort_order": 2},
            {"url": "/images/tours/forbidden-city-3.svg", "alt_text": "故宫御花园", "sort_order": 3},
        ],
        "dates": [
            {"start_date_offset": 7, "price": 99.0, "availability": 20},
            {"start_date_offset": 14, "price": 99.0, "availability": 15},
            {"start_date_offset": 21, "price": 109.0, "availability": 25},
            {"start_date_offset": 30, "price": 109.0, "availability": 18},
            {"start_date_offset": 45, "price": 99.0, "availability": 22},
            {"start_date_offset": 60, "price": 99.0, "availability": 30},
        ],
    },
    # ═══════════════ 北京-长城 ═══════════════
    {
        "slug": "great-wall-badaling-hike",
        "serial_number": "0002",
        "type": "group_tour",
        "status": "published",
        "duration_days": 1,
        "duration_nights": 0,
        "max_pax": 35,
        "min_pax": 2,
        "start_price": 129.0,
        "currency": "USD",
        "difficulty": "moderate",
        "destination_slugs": ["beijing"],
        "highlights": ["八达岭长城徒步", "居庸关外景拍照", "长城好汉证书", "含往返缆车/滑车", "北京特色午餐"],
        "includes": ["八达岭长城门票", "往返缆车/滑车票", "专业导游服务", "北京特色午餐", "长城好汉证书", "旅游意外险"],
        "excludes": ["个人购物", "酒店接送（可加购）", "额外饮品"],
        "translations": {
            "zh": {
                "name": "八达岭长城徒步之旅",
                "subtitle": "登长城做好汉，俯瞰万里江山",
                "description": "八达岭长城是明长城最具代表性的一段，位于北京市延庆区，海拔约1000米。作为中国开放最早、保护最完好的长城段落，八达岭长城以其宏伟的景观和完善的设施闻名于世。行程包含往返缆车，轻松登顶。",
                "itinerary": [
                    {"day": 1, "title": "长城一日游", "description": "上午：市区集合出发 → 抵达八达岭长城 → 乘缆车上山\n中午：长城脚下北京特色午餐\n下午：北段长城徒步 → 好汉坡 → 自由拍照 → 滑车下山 → 返回市区"},
                ],
                "meta_title": "八达岭长城徒步之旅 | Echo Tours",
                "meta_description": "登临八达岭长城，体验\"不到长城非好汉\"的豪情，含往返缆车和北京特色午餐。",
            },
            "en": {
                "name": "Badaling Great Wall Hiking Tour",
                "subtitle": "Climb the Great Wall and behold the magnificent landscapes",
                "description": "Badaling is the most representative and best-preserved section of the Ming Great Wall. Located in Yanqing District at an elevation of 1,000 meters, it offers breathtaking views and well-maintained facilities. Round-trip cable car included.",
                "itinerary": [
                    {"day": 1, "title": "Great Wall Day Trip", "description": "Morning: Depart from downtown Beijing → Arrive at Badaling → Cable car up\nAfternoon: North section hike → Hero Slope → Free time for photos → Toboggan down → Return to Beijing"},
                ],
                "highlights": [
                    "Badaling Great Wall hiking experience",
                    "Juyongguan Pass photo opportunity",
                    "Great Wall hero certificate",
                    "Round-trip cable car / toboggan ride",
                    "Beijing-style lunch included",
                ],
                "includes": [
                    "Badaling Great Wall entrance ticket",
                    "Round-trip cable car / toboggan ticket",
                    "Professional guide service",
                    "Beijing-style lunch",
                    "Great Wall hero certificate",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal shopping",
                    "Hotel pickup (available as add-on)",
                    "Additional drinks",
                ],
                "meta_title": "Badaling Great Wall Hiking | Echo Tours",
                "meta_description": "Hike the iconic Badaling Great Wall with round-trip cable car and Beijing-style lunch included.",
            },
        },
        "images": [
            {"url": "/images/tours/great-wall-1.svg", "alt_text": "八达岭长城全景", "sort_order": 1},
            {"url": "/images/tours/great-wall-2.svg", "alt_text": "长城上的游客", "sort_order": 2},
        ],
        "dates": [
            {"start_date_offset": 5, "price": 129.0, "availability": 25},
            {"start_date_offset": 12, "price": 129.0, "availability": 20},
            {"start_date_offset": 19, "price": 139.0, "availability": 30},
            {"start_date_offset": 28, "price": 139.0, "availability": 22},
            {"start_date_offset": 50, "price": 129.0, "availability": 28},
        ],
    },
    # ═══════════════ 北京-慕田峪长城 ═══════════════
    {
        "slug": "mutianyu-great-wall-premium",
        "serial_number": "0003",
        "type": "private_tour",
        "status": "published",
        "duration_days": 1,
        "duration_nights": 0,
        "max_pax": 10,
        "min_pax": 1,
        "start_price": 249.0,
        "currency": "USD",
        "difficulty": "moderate",
        "destination_slugs": ["beijing"],
        "highlights": ["慕田峪长城（人少景美）", "含往返缆车+下山滑道", "私家团小团出行", "可定制行程", "赠送长城纪念册"],
        "includes": ["慕田峪长城门票", "往返缆车+下山滑道", "资深导游专属服务", "北京特色午餐", "长城纪念相册", "旅游意外险"],
        "excludes": ["个人购物", "酒店接送（可加购）"],
        "translations": {
            "zh": {
                "name": "慕田峪长城精品私家游",
                "subtitle": "避开人潮，独享长城壮美",
                "description": "慕田峪长城位于北京市怀柔区，是明长城的精华段落之一。相比八达岭，慕田峪游客较少、风光更为秀丽。本行程采用精品小团模式（最多10人），包含刺激的下山滑道体验，让您以最舒适的方式领略长城之美。",
                "itinerary": [
                    {"day": 1, "title": "慕田峪长城精品游", "description": "上午：市区酒店接送 → 抵达慕田峪 → 缆车上山\n中午：长城脚下农家午餐\n下午：慕田峪精华段徒步 → 敌楼探访 → 滑道下山 → 返回市区"},
                ],
                "meta_title": "慕田峪长城精品游 | Echo Tours",
                "meta_description": "避开人潮的小团体验，含缆车和下山滑道，品味慕田峪长城的宁静壮美。",
            },
            "en": {
                "name": "Mutianyu Great Wall Premium Tour",
                "subtitle": "Avoid the crowds, enjoy the Great Wall in style",
                "description": "Mutianyu Great Wall is one of the best-preserved sections with fewer tourists than Badaling. This premium small-group tour (max 10 pax) includes a thrilling toboggan ride down and a farmhouse lunch.",
                "itinerary": [
                    {"day": 1, "title": "Mutianyu Premium Tour", "description": "Morning: Hotel pickup → Arrive at Mutianyu → Cable car up\nAfternoon: Hike the essence section → Explore watchtowers → Toboggan down → Return to Beijing"},
                ],
                "highlights": [
                    "Mutianyu Great Wall — fewer crowds, stunning scenery",
                    "Round-trip cable car + downhill toboggan ride",
                    "Premium small group tour (max 10 pax)",
                    "Customizable itinerary options",
                    "Free souvenir photo album",
                ],
                "includes": [
                    "Mutianyu Great Wall ticket",
                    "Round-trip cable car + toboggan ride",
                    "Senior guide exclusive service",
                    "Farmhouse lunch",
                    "Great Wall souvenir photo album",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal shopping",
                    "Hotel pickup (available as add-on)",
                ],
                "meta_title": "Mutianyu Great Wall Premium Tour | Echo Tours",
                "meta_description": "Premium small-group tour of Mutianyu Great Wall with cable car, toboggan ride and farm lunch.",
            },
        },
        "images": [
            {"url": "/images/tours/mutianyu-1.svg", "alt_text": "慕田峪长城敌楼", "sort_order": 1},
            {"url": "/images/tours/mutianyu-2.svg", "alt_text": "慕田峪长城秋色", "sort_order": 2},
        ],
        "dates": [
            {"start_date_offset": 8, "price": 249.0, "availability": 8},
            {"start_date_offset": 15, "price": 249.0, "availability": 6},
            {"start_date_offset": 22, "price": 274.0, "availability": 10},
            {"start_date_offset": 35, "price": 249.0, "availability": 8},
            {"start_date_offset": 55, "price": 274.0, "availability": 7},
        ],
    },
    # ═══════════════ 北京-天坛 ═══════════════
    {
        "slug": "temple-of-heaven-cultural",
        "serial_number": "0004",
        "type": "group_tour",
        "status": "published",
        "duration_days": 0.5,
        "duration_nights": 0,
        "max_pax": 25,
        "min_pax": 2,
        "start_price": 69.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["天坛祈年殿/圜丘坛", "皇家祭祀文化讲解", "天坛公园古柏群", "可观看晨练太极", "赠送天坛祈福丝带"],
        "includes": ["天坛公园联票（含祈年殿+回音壁+圜丘坛）", "专业导游讲解", "无线耳麦", "祈福丝带", "旅游意外险"],
        "excludes": ["餐饮费用", "个人消费", "酒店接送"],
        "translations": {
            "zh": {
                "name": "天坛皇家祭祀文化半日游",
                "subtitle": "走进皇帝与天对话的地方",
                "description": "天坛是明清两代皇帝祭天祈谷的神圣场所，是中国现存规模最大、保存最完整的祭天建筑群。行程涵盖祈年殿、回音壁、圜丘坛等核心建筑，深入了解中国古代天人合一的哲学思想和皇家祭祀礼仪。",
                "itinerary": [
                    {"day": 1, "title": "天坛半日游", "description": "上午：天坛南门集合 → 圜丘坛 → 回音壁 → 皇穹宇\n中午：祈年殿 → 丹陛桥 → 皇乾殿 → 天坛公园自由活动"},
                ],
                "meta_title": "天坛皇家祭祀文化游 | Echo Tours",
                "meta_description": "深度游览天坛祈年殿、圜丘坛、回音壁，了解明清皇帝祭天礼仪和中国古代天人合一哲学。",
            },
            "en": {
                "name": "Temple of Heaven Half-Day Tour",
                "subtitle": "Where emperors communed with heaven",
                "description": "The Temple of Heaven is the largest and best-preserved sacrificial building complex in China. This tour covers the Hall of Prayer for Good Harvests, the Echo Wall, and the Circular Mound Altar, offering insights into ancient Chinese philosophy and imperial rituals.",
                "itinerary": [
                    {"day": 1, "title": "Temple of Heaven Tour", "description": "Morning: Meet at South Gate → Circular Mound Altar → Echo Wall → Imperial Vault of Heaven\nAfternoon: Hall of Prayer for Good Harvests → Danbi Bridge → Free exploration"},
                ],
                "highlights": [
                    "Hall of Prayer & Circular Mound Altar",
                    "Imperial ceremonial culture explained",
                    "Ancient cypress groves in the park",
                    "Watch locals practicing tai chi",
                    "Temple blessing ribbon included",
                ],
                "includes": [
                    "Temple of Heaven combo ticket (Hall of Prayer + Echo Wall + Circular Mound)",
                    "Professional guide service",
                    "Wireless headset",
                    "Blessing ribbon",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Meals and drinks",
                    "Personal expenses",
                    "Hotel pickup",
                ],
                "meta_title": "Temple of Heaven Cultural Tour | Echo Tours",
                "meta_description": "Explore the Temple of Heaven's Hall of Prayer, Echo Wall and Circular Mound with expert guide.",
            },
        },
        "images": [
            {"url": "/images/tours/temple-of-heaven-1.svg", "alt_text": "天坛祈年殿", "sort_order": 1},
        ],
        "dates": [
            {"start_date_offset": 3, "price": 69.0, "availability": 20},
            {"start_date_offset": 10, "price": 69.0, "availability": 25},
            {"start_date_offset": 17, "price": 79.0, "availability": 22},
            {"start_date_offset": 24, "price": 79.0, "availability": 18},
            {"start_date_offset": 40, "price": 69.0, "availability": 30},
        ],
    },
    # ═══════════════ 北京-颐和园 ═══════════════
    {
        "slug": "summer-palace-royal-garden",
        "serial_number": "0005",
        "type": "group_tour",
        "status": "published",
        "duration_days": 1,
        "duration_nights": 0,
        "max_pax": 25,
        "min_pax": 2,
        "start_price": 89.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["颐和园全景游览", "昆明湖游船体验", "长廊彩绘赏析", "佛香阁登高望远", "十七孔桥打卡"],
        "includes": ["颐和园大门票+佛香阁门票", "昆明湖游船票", "专业导游讲解", "无线耳麦", "旅游意外险"],
        "excludes": ["餐饮费用", "个人购物", "酒店接送"],
        "translations": {
            "zh": {
                "name": "颐和园皇家园林一日游",
                "subtitle": "漫步中国最后的皇家园林",
                "description": "颐和园是中国现存规模最大、保存最完整的皇家园林，被誉为\"皇家园林博物馆\"。这里曾是慈禧太后的夏宫，融合了江南园林的精致与北方建筑的恢宏。行程包含昆明湖游船、登佛香阁俯瞰全景、漫步世界最长的画廊——长廊。",
                "itinerary": [
                    {"day": 1, "title": "颐和园一日游", "description": "上午：东宫门集合 → 仁寿殿 → 德和园 → 乐寿堂\n中午：长廊漫步 → 排云殿 → 佛香阁登高\n下午：石舫 → 昆明湖游船 → 南湖岛 → 十七孔桥 → 新建宫门结束"},
                ],
                "meta_title": "颐和园皇家园林游 | Echo Tours",
                "meta_description": "游览中国最美的皇家园林——颐和园，含昆明湖游船、佛香阁登高和长廊漫步。",
            },
            "en": {
                "name": "Summer Palace Royal Garden Tour",
                "subtitle": "Stroll through China's last imperial garden",
                "description": "The Summer Palace is the best-preserved imperial garden in China, known as the 'Museum of Royal Gardens.' This tour includes a Kunming Lake boat ride, climbing the Tower of Buddhist Incense, and walking the world's longest painted corridor.",
                "itinerary": [
                    {"day": 1, "title": "Summer Palace Tour", "description": "Morning: East Palace Gate → Hall of Benevolence → Hall of Joyful Longevity\nAfternoon: Long Corridor → Cloud-Dispelling Hall → Tower of Buddhist Incense → Marble Boat → Kunming Lake cruise → Seventeen-Arch Bridge"},
                ],
                "highlights": [
                    "Full Summer Palace exploration",
                    "Kunming Lake boat cruise",
                    "Long Corridor painted gallery",
                    "Tower of Buddhist Incense climb",
                    "Seventeen-Arch Bridge photo spot",
                ],
                "includes": [
                    "Summer Palace + Tower of Buddhist Incense tickets",
                    "Kunming Lake cruise ticket",
                    "Professional guide service",
                    "Wireless headset",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Meals and drinks",
                    "Personal shopping",
                    "Hotel pickup",
                ],
                "meta_title": "Summer Palace Tour | Echo Tours",
                "meta_description": "Explore the magnificent Summer Palace with Kunming Lake cruise and Tower of Buddhist Incense climb.",
            },
        },
        "images": [
            {"url": "/images/tours/summer-palace-1.svg", "alt_text": "颐和园佛香阁", "sort_order": 1},
            {"url": "/images/tours/summer-palace-2.svg", "alt_text": "颐和园长廊", "sort_order": 2},
            {"url": "/images/tours/summer-palace-3.svg", "alt_text": "十七孔桥与南湖岛", "sort_order": 3},
        ],
        "dates": [
            {"start_date_offset": 4, "price": 89.0, "availability": 20},
            {"start_date_offset": 11, "price": 89.0, "availability": 25},
            {"start_date_offset": 18, "price": 99.0, "availability": 22},
            {"start_date_offset": 32, "price": 99.0, "availability": 18},
            {"start_date_offset": 48, "price": 89.0, "availability": 30},
        ],
    },
    # ═══════════════ 北京-恭王府 ═══════════════
    {
        "slug": "prince-gong-mansion-hutong",
        "serial_number": "0006",
        "type": "group_tour",
        "status": "published",
        "duration_days": 0.5,
        "duration_nights": 0,
        "max_pax": 20,
        "min_pax": 2,
        "start_price": 79.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["恭王府深度游览", "和珅府邸传奇故事", "什刹海胡同文化区", "三轮车胡同游", "老北京小吃品尝"],
        "includes": ["恭王府门票", "专业中文导游", "三轮车胡同游（约30分钟）", "老北京小吃品尝", "旅游意外险"],
        "excludes": ["个人购物", "正餐费用", "酒店接送"],
        "translations": {
            "zh": {
                "name": "恭王府+什刹海胡同文化游",
                "subtitle": "一座恭王府，半部清朝史",
                "description": "恭王府是清代规模最大、保存最完整的一座王府，曾为和珅、恭亲王奕訢的府邸，素有\"一座恭王府，半部清朝史\"之说。行程不仅探访恭王府的奢华建筑与福字文化，还将乘坐三轮车穿梭于什刹海周边胡同，体验地道的老北京生活。",
                "itinerary": [
                    {"day": 1, "title": "恭王府+胡同游", "description": "上午：恭王府集合 → 银安殿 → 后花园 → 邀月台 → 福字碑\n中午：什刹海周边漫步\n下午：三轮车胡同游（参观四合院）→ 烟袋斜街 → 钟鼓楼广场结束"},
                ],
                "meta_title": "恭王府+什刹海胡同游 | Echo Tours",
                "meta_description": "探访清代最大王府恭王府，乘坐三轮车游什刹海胡同，体验地道老北京文化。",
            },
            "en": {
                "name": "Prince Gong's Mansion & Hutong Tour",
                "subtitle": "One mansion, half of Qing dynasty history",
                "description": "Prince Gong's Mansion is the largest and best-preserved princely residence from the Qing dynasty. This tour combines a deep exploration of the mansion with a rickshaw ride through Shichahai's historic hutongs.",
                "itinerary": [
                    {"day": 1, "title": "Mansion & Hutong Tour", "description": "Morning: Meet at Prince Gong's Mansion → Silver Peace Hall → Back Garden → Fuzi Stele\nAfternoon: Rickshaw hutong tour → Yandai Xiejie → Bell & Drum Towers"},
                ],
                "highlights": [
                    "Prince Gong's Mansion in-depth tour",
                    "Fascinating story of Heshen's former residence",
                    "Shichahai hutong cultural district",
                    "Rickshaw ride through historic lanes",
                    "Old Beijing snack tasting",
                ],
                "includes": [
                    "Prince Gong's Mansion ticket",
                    "Professional Chinese guide",
                    "Rickshaw hutong tour (~30 min)",
                    "Old Beijing snack tasting",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal shopping",
                    "Full meal costs",
                    "Hotel pickup",
                ],
                "meta_title": "Prince Gong's Mansion & Hutong Tour | Echo Tours",
                "meta_description": "Explore the magnificent Prince Gong's Mansion and ride rickshaws through Beijing's historic hutongs.",
            },
        },
        "images": [
            {"url": "/images/tours/gong-mansion-1.svg", "alt_text": "恭王府后花园", "sort_order": 1},
        ],
        "dates": [
            {"start_date_offset": 6, "price": 79.0, "availability": 18},
            {"start_date_offset": 13, "price": 79.0, "availability": 20},
            {"start_date_offset": 20, "price": 89.0, "availability": 22},
            {"start_date_offset": 35, "price": 79.0, "availability": 16},
        ],
    },
    # ═══════════════ 北京-奥林匹克公园 ═══════════════
    {
        "slug": "olympic-park-modern-beijing",
        "serial_number": "0007",
        "type": "group_tour",
        "status": "published",
        "duration_days": 0.5,
        "duration_nights": 0,
        "max_pax": 30,
        "min_pax": 2,
        "start_price": 49.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["鸟巢（国家体育场）", "水立方/冰立方", "奥林匹克观光塔", "2022冬奥会场地", "现代建筑摄影胜地"],
        "includes": ["鸟巢参观门票", "水立方参观门票", "专业导游讲解", "旅游意外险"],
        "excludes": ["餐饮费用", "奥林匹克塔门票", "个人消费"],
        "translations": {
            "zh": {
                "name": "奥林匹克公园现代北京半日游",
                "subtitle": "从2008到2022，双奥之城的骄傲",
                "description": "北京奥林匹克公园是2008年夏季奥运会和2022年冬季奥运会的核心举办地，见证了北京成为全球首个\"双奥之城\"的历史时刻。行程将参观鸟巢国家体育场、水立方国家游泳中心，感受奥运精神与现代建筑之美。",
                "itinerary": [
                    {"day": 1, "title": "奥体公园半日游", "description": "上午：奥林匹克公园集合 → 鸟巢（入内参观）→ 水立方（入内参观）\n中午：奥林匹克公园自由活动 → 拍照留念 → 结束"},
                ],
                "meta_title": "北京奥林匹克公园游 | Echo Tours",
                "meta_description": "参观鸟巢和水立方，感受双奥之城的魅力与现代北京的地标建筑。",
            },
            "en": {
                "name": "Olympic Park Modern Beijing Tour",
                "subtitle": "From 2008 to 2022, the pride of the dual-Olympic city",
                "description": "Beijing Olympic Park hosted both the 2008 Summer and 2022 Winter Olympics, making Beijing the world's first 'Dual Olympic City.' Visit the iconic Bird's Nest and Water Cube.",
                "itinerary": [
                    {"day": 1, "title": "Olympic Park Tour", "description": "Morning: Meet at Olympic Park → Bird's Nest (interior visit) → Water Cube (interior visit)\nAfternoon: Free time for photos"},
                ],
                "highlights": [
                    "Bird's Nest (National Stadium)",
                    "Water Cube / Ice Cube",
                    "Olympic sightseeing tower",
                    "2022 Winter Olympics venue",
                    "Modern architecture photography",
                ],
                "includes": [
                    "Bird's Nest visit ticket",
                    "Water Cube visit ticket",
                    "Professional guide service",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Meals and drinks",
                    "Olympic Tower ticket",
                    "Personal expenses",
                ],
                "meta_title": "Beijing Olympic Park Tour | Echo Tours",
                "meta_description": "Visit the Bird's Nest and Water Cube at Beijing's iconic Olympic Park.",
            },
        },
        "images": [
            {"url": "/images/tours/olympic-1.svg", "alt_text": "鸟巢体育场夜景", "sort_order": 1},
            {"url": "/images/tours/olympic-2.svg", "alt_text": "水立方与鸟巢", "sort_order": 2},
        ],
        "dates": [
            {"start_date_offset": 2, "price": 49.0, "availability": 25},
            {"start_date_offset": 9, "price": 49.0, "availability": 30},
            {"start_date_offset": 16, "price": 59.0, "availability": 28},
            {"start_date_offset": 25, "price": 59.0, "availability": 25},
            {"start_date_offset": 42, "price": 49.0, "availability": 35},
        ],
    },
    # ═══════════════ 北京-圆明园 ═══════════════
    {
        "slug": "old-summer-palace-history",
        "serial_number": "0008",
        "type": "group_tour",
        "status": "published",
        "duration_days": 0.5,
        "duration_nights": 0,
        "max_pax": 25,
        "min_pax": 2,
        "start_price": 49.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["圆明园西洋楼遗址", "大水法标志景观", "爱国主义教育基地", "正觉寺参观", "圆明园盛时全景沙盘"],
        "includes": ["圆明园遗址公园门票", "西洋楼遗址区门票", "专业导游讲解", "旅游意外险"],
        "excludes": ["餐饮费用", "游船票", "个人消费"],
        "translations": {
            "zh": {
                "name": "圆明园历史探索半日游",
                "subtitle": "追寻万园之园的昔日辉煌",
                "description": "圆明园是清代大型皇家园林，被誉为\"万园之园\"，曾是人类文化的宝库。1860年遭英法联军劫掠焚毁，如今成为重要的爱国主义教育基地。行程将参观西洋楼遗址、大水法、海晏堂等标志性遗迹，并通过全景沙盘还原圆明园盛时风貌。",
                "itinerary": [
                    {"day": 1, "title": "圆明园半日游", "description": "上午：圆明园南门集合 → 正觉寺 → 绮春园 → 长春园\n中午：西洋楼遗址区（大水法、海晏堂、谐奇趣）→ 全景沙盘展 → 结束"},
                ],
                "meta_title": "圆明园历史探索游 | Echo Tours",
                "meta_description": "参观圆明园西洋楼遗址与大水法，了解万园之园的辉煌历史与沧桑变迁。",
            },
            "en": {
                "name": "Old Summer Palace Historical Tour",
                "subtitle": "Trace the glory of the Garden of Gardens",
                "description": "The Old Summer Palace was once known as the 'Garden of Gardens,' a magnificent imperial garden complex before its destruction in 1860. Visit the Western-style ruins, the iconic Great Waterworks, and the panoramic model of the original garden.",
                "itinerary": [
                    {"day": 1, "title": "Old Summer Palace Tour", "description": "Morning: South Gate → Zhengjue Temple → Qichun Garden → Changchun Garden\nAfternoon: Western-style ruins (Great Waterworks, Haiyantang, Xiejiqu) → Panoramic model exhibition"},
                ],
                "highlights": [
                    "Western-style ruins of Yuanmingyuan",
                    "Iconic Great Waterworks site",
                    "Historical education experience",
                    "Zhengjue Temple visit",
                    "Panoramic model of the original garden",
                ],
                "includes": [
                    "Old Summer Palace park ticket",
                    "Western ruins area ticket",
                    "Professional guide service",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Meals and drinks",
                    "Boat ride ticket",
                    "Personal expenses",
                ],
                "meta_title": "Old Summer Palace Tour | Echo Tours",
                "meta_description": "Explore the historic ruins of the Old Summer Palace, including the Western-style buildings and iconic Great Waterworks.",
            },
        },
        "images": [
            {"url": "/images/tours/yuanmingyuan-1.svg", "alt_text": "圆明园大水法遗址", "sort_order": 1},
        ],
        "dates": [
            {"start_date_offset": 5, "price": 49.0, "availability": 20},
            {"start_date_offset": 12, "price": 49.0, "availability": 25},
            {"start_date_offset": 26, "price": 59.0, "availability": 22},
            {"start_date_offset": 40, "price": 49.0, "availability": 28},
        ],
    },
    # ═══════════════ 北京-明十三陵 ═══════════════
    {
        "slug": "ming-tombs-royal-cemetery",
        "serial_number": "0009",
        "type": "group_tour",
        "status": "published",
        "duration_days": 0.5,
        "duration_nights": 0,
        "max_pax": 20,
        "min_pax": 2,
        "start_price": 79.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["长陵（明成祖朱棣陵墓）", "定陵（唯一开放地宫的陵墓）", "神道石像生群", "万历皇帝金丝翼善冠复制品", "明文化讲解"],
        "includes": ["长陵+定陵门票", "定陵地宫参观", "专业导游讲解", "旅游意外险"],
        "excludes": ["餐饮费用", "神道门票", "个人消费"],
        "translations": {
            "zh": {
                "name": "明十三陵皇家陵寝文化游",
                "subtitle": "探访大明王朝的地下宫殿",
                "description": "明十三陵是明朝十三位皇帝的陵寝群，位于北京昌平区天寿山麓，是中国乃至世界现存规模最大、保存最完整的帝王陵墓群。行程将参观长陵（明成祖朱棣陵墓）和定陵（唯一发掘地宫开放的陵墓），领略明代皇家陵寝的恢宏气势。",
                "itinerary": [
                    {"day": 1, "title": "明十三陵半日游", "description": "上午：神道（石像生群）→ 长陵（祾恩殿、明楼）\n中午：定陵（深入地下宫殿参观地宫）→ 明文化展览 → 结束"},
                ],
                "meta_title": "明十三陵皇家陵寝游 | Echo Tours",
                "meta_description": "参观明十三陵长陵与定陵地宫，探索大明王朝的地下宫殿与皇家陵寝文化。",
            },
            "en": {
                "name": "Ming Tombs Royal Cemetery Tour",
                "subtitle": "Explore the underground palaces of the Ming dynasty",
                "description": "The Ming Tombs house the burial sites of 13 Ming emperors. Visit Changling (Emperor Yongle's tomb) and Dingling (the only excavated tomb with an open underground palace), and walk the Sacred Way lined with stone statues.",
                "itinerary": [
                    {"day": 1, "title": "Ming Tombs Tour", "description": "Morning: Sacred Way (stone statues) → Changling (Ling'en Hall, Ming Tower)\nAfternoon: Dingling (underground palace tour) → Ming culture exhibition"},
                ],
                "highlights": [
                    "Changling — Emperor Yongle's tomb",
                    "Dingling — only open underground palace",
                    "Sacred Way stone statue avenue",
                    "Wanli Emperor's golden crown replica",
                    "Ming dynasty history & culture",
                ],
                "includes": [
                    "Changling + Dingling entrance tickets",
                    "Dingling underground palace visit",
                    "Professional guide service",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Meals and drinks",
                    "Sacred Way ticket",
                    "Personal expenses",
                ],
                "meta_title": "Ming Tombs Tour | Echo Tours",
                "meta_description": "Visit the Ming Tombs' Changling and Dingling underground palace, explore Ming dynasty royal burial culture.",
            },
        },
        "images": [
            {"url": "/images/tours/ming-tombs-1.svg", "alt_text": "明十三陵神道石像", "sort_order": 1},
        ],
        "dates": [
            {"start_date_offset": 9, "price": 79.0, "availability": 15},
            {"start_date_offset": 16, "price": 79.0, "availability": 18},
            {"start_date_offset": 30, "price": 89.0, "availability": 20},
            {"start_date_offset": 48, "price": 79.0, "availability": 16},
        ],
    },
    # ═══════════════ 北京-多日深度游 ═══════════════
    {
        "slug": "beijing-essence-3-day",
        "serial_number": "0010",
        "type": "group_tour",
        "status": "published",
        "duration_days": 3,
        "duration_nights": 2,
        "max_pax": 20,
        "min_pax": 4,
        "start_price": 699.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["beijing"],
        "highlights": ["故宫+长城+颐和园+天坛全覆盖", "全程豪华旅游大巴", "四星级酒店住宿含早餐", "地道北京风味餐（烤鸭/涮肉）", "资深导游全程陪同"],
        "includes": ["两晚四星级酒店（含早）", "行程所列景点首道门票", "全程专业导游服务", "空调旅游大巴", "行程中所列正餐（第1天午餐晚餐/第2天午餐晚餐/第3天午餐）", "旅游意外险"],
        "excludes": ["个人消费", "单房差价", "酒店接送", "行程外自费项目"],
        "translations": {
            "zh": {
                "name": "北京全景精华三日游",
                "subtitle": "三天玩遍北京核心景点",
                "description": "这是一条精心设计的北京经典线路，三天时间涵盖北京最核心的六大景点：故宫、天坛、颐和园、八达岭长城、恭王府、奥林匹克公园。全程入住四星级酒店，品尝正宗北京烤鸭和铜锅涮肉，让您在最短时间内领略北京千年古都的魅力。",
                "itinerary": [
                    {"day": 1, "title": "皇城中轴线", "description": "上午：天坛（祈年殿/回音壁/圜丘坛）\n中午：前门大街（品尝北京炸酱面）\n下午：故宫博物院（三大殿/后三宫/御花园）→ 景山公园俯瞰故宫全景\n晚上：王府井夜市自由活动"},
                    {"day": 2, "title": "皇家园林+长城", "description": "上午：八达岭长城（含缆车往返）\n中午：长城脚下农家菜\n下午：颐和园（昆明湖游船/长廊/佛香阁）\n晚上：全聚德正宗北京烤鸭"},
                    {"day": 3, "title": "王府+奥运", "description": "上午：恭王府（和珅府邸/福字碑）→ 什刹海胡同游\n中午：东来顺铜锅涮肉\n下午：奥林匹克公园（鸟巢/水立方外观）→ 结束行程"},
                ],
                "meta_title": "北京全景精华三日游 | Echo Tours",
                "meta_description": "三天玩遍北京故宫、长城、颐和园、天坛等核心景点，含四星级酒店和正宗北京美食。",
            },
            "en": {
                "name": "Beijing Essence 3-Day Tour",
                "subtitle": "Experience Beijing's best in just 3 days",
                "description": "A carefully curated tour covering Beijing's top 6 attractions: Forbidden City, Temple of Heaven, Summer Palace, Badaling Great Wall, Prince Gong's Mansion and Olympic Park. Includes 4-star hotel accommodation and authentic Peking Duck dinner.",
                "itinerary": [
                    {"day": 1, "title": "Imperial Central Axis", "description": "Morning: Temple of Heaven\nAfternoon: Forbidden City → Jingshan Park panoramic view\nEvening: Wangfujing Night Market"},
                    {"day": 2, "title": "Royal Gardens & Great Wall", "description": "Morning: Badaling Great Wall (cable car)\nAfternoon: Summer Palace (Kunming Lake cruise)\nEvening: Authentic Peking Duck dinner"},
                    {"day": 3, "title": "Mansion & Olympics", "description": "Morning: Prince Gong's Mansion → Shichahai Hutong tour\nAfternoon: Olympic Park (Bird's Nest & Water Cube) → Tour ends"},
                ],
                "highlights": [
                    "Forbidden City + Great Wall + Summer Palace + Temple of Heaven",
                    "Luxury air-conditioned tour bus",
                    "4-star hotel with breakfast included",
                    "Authentic Peking duck & hotpot dinner",
                    "Senior guide throughout the journey",
                ],
                "includes": [
                    "Two nights 4-star hotel (with breakfast)",
                    "All listed attraction entrance tickets",
                    "Full-time professional guide service",
                    "Air-conditioned tour bus",
                    "Meals as listed (Day 1 L/D, Day 2 L/D, Day 3 L)",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal expenses",
                    "Single room supplement",
                    "Hotel pickup/drop-off",
                    "Optional activities not listed",
                ],
                "meta_title": "Beijing 3-Day Essence Tour | Echo Tours",
                "meta_description": "A 3-day tour covering Beijing's top attractions including Forbidden City, Great Wall and Summer Palace with 4-star hotel.",
            },
        },
        "images": [
            {"url": "/images/tours/beijing-3day-1.svg", "alt_text": "北京天安门广场", "sort_order": 1},
            {"url": "/images/tours/beijing-3day-2.svg", "alt_text": "北京烤鸭", "sort_order": 2},
            {"url": "/images/tours/beijing-3day-3.svg", "alt_text": "胡同文化体验", "sort_order": 3},
        ],
        "dates": [
            {"start_date_offset": 10, "price": 699.0, "availability": 15},
            {"start_date_offset": 24, "price": 799.0, "availability": 18},
            {"start_date_offset": 38, "price": 699.0, "availability": 12},
            {"start_date_offset": 52, "price": 899.0, "availability": 20},
            {"start_date_offset": 66, "price": 799.0, "availability": 16},
        ],
    },
    # ═══════════════ 南京 ═══════════════
    {
        "slug": "nanjing-historical-essence",
        "serial_number": "0001",
        "type": "group_tour",
        "status": "published",
        "duration_days": 2,
        "duration_nights": 1,
        "max_pax": 20,
        "min_pax": 2,
        "start_price": 449.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["nanjing"],
        "highlights": ["中山陵（孙中山陵寝）", "夫子庙秦淮河风光", "明孝陵世界遗产", "南京博物院", "品尝南京盐水鸭"],
        "includes": ["景点首道门票", "1晚三星级酒店", "专业导游服务", "行程所列正餐", "旅游意外险"],
        "excludes": ["个人消费", "单房差", "往返大交通"],
        "translations": {
            "zh": {
                "name": "南京历史精华两日游",
                "subtitle": "六朝古都深度探访",
                "description": "南京是中国四大古都之一，拥有6000多年文明史。本行程涵盖中山陵、明孝陵、夫子庙秦淮河风光带和南京博物院等核心景点，感受六朝古都的厚重历史与人文魅力。",
                "itinerary": [
                    {"day": 1, "title": "钟山风景区+夫子庙", "description": "上午：中山陵（博爱坊/墓道/祭堂）\n中午：南京盐水鸭特色午餐\n下午：明孝陵（神道/方城明楼）→ 美龄宫\n晚上：夫子庙秦淮河夜景（乘船夜游）"},
                    {"day": 2, "title": "博物院+玄武湖", "description": "上午：南京博物院（历史馆/特展馆）\n中午：老门东美食街\n下午：玄武湖公园 → 结束行程"},
                ],
                "meta_title": "南京精华两日游 | Echo Tours",
                "meta_description": "两日游遍南京中山陵、明孝陵、夫子庙、南京博物院，感受六朝古都的深厚底蕴。",
            },
            "en": {
                "name": "Nanjing Historical Essence 2-Day Tour",
                "subtitle": "Deep dive into the ancient capital of six dynasties",
                "description": "Nanjing, one of China's four great ancient capitals, boasts over 6,000 years of civilization. This tour covers Dr. Sun Yat-sen's Mausoleum, Ming Xiaoling Mausoleum, Confucius Temple and the Qinhuai River.",
                "itinerary": [
                    {"day": 1, "title": "Zhongshan Scenic Area", "description": "Morning: Sun Yat-sen Mausoleum\nAfternoon: Ming Xiaoling Mausoleum\nEvening: Qinhuai River night cruise"},
                    {"day": 2, "title": "Museum & Xuanwu Lake", "description": "Morning: Nanjing Museum\nAfternoon: Xuanwu Lake Park → Tour ends"},
                ],
                "highlights": [
                    "Dr. Sun Yat-sen's Mausoleum",
                    "Confucius Temple & Qinhuai River scenery",
                    "Ming Xiaoling UNESCO World Heritage site",
                    "Nanjing Museum",
                    "Nanjing salted duck tasting",
                ],
                "includes": [
                    "All listed attraction entrance tickets",
                    "1 night 3-star hotel accommodation",
                    "Professional guide service",
                    "Meals as listed",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal expenses",
                    "Single room supplement",
                    "Round-trip transportation",
                ],
                "meta_title": "Nanjing 2-Day Historical Tour | Echo Tours",
                "meta_description": "A 2-day tour of Nanjing's historical highlights including Sun Yat-sen Mausoleum, Ming Tombs and Confucius Temple.",
            },
        },
        "images": [
            {"url": "/images/tours/nanjing-1.svg", "alt_text": "南京中山陵", "sort_order": 1},
        ],
        "dates": [
            {"start_date_offset": 12, "price": 449.0, "availability": 15},
            {"start_date_offset": 26, "price": 489.0, "availability": 18},
            {"start_date_offset": 45, "price": 449.0, "availability": 20},
        ],
    },
    # ═══════════════ 西安 ═══════════════
    {
        "slug": "xian-terracotta-warriors-2day",
        "serial_number": "0001",
        "type": "group_tour",
        "status": "published",
        "duration_days": 2,
        "duration_nights": 1,
        "max_pax": 20,
        "min_pax": 2,
        "start_price": 549.0,
        "currency": "USD",
        "difficulty": "easy",
        "destination_slugs": ["xian"],
        "highlights": ["兵马俑博物馆（世界第八大奇迹）", "华清宫（唐玄宗与杨贵妃爱情故事）", "西安古城墙骑行", "回民街美食", "大雁塔广场音乐喷泉"],
        "includes": ["兵马俑+华清宫门票", "1晚三星级酒店含早", "专业导游服务", "城墙自行车租赁", "旅游意外险"],
        "excludes": ["个人消费", "单房差", "往返大交通"],
        "translations": {
            "zh": {
                "name": "西安兵马俑古都文化两日游",
                "subtitle": "穿越周秦汉唐，感受十三朝古都的震撼",
                "description": "西安是世界四大古都之一，曾作为十三朝古都。本行程将带您参观世界第八大奇迹——秦始皇兵马俑博物馆，感受大唐盛世的华清宫，骑行中国最完整的古城墙，品尝回民街特色美食。",
                "itinerary": [
                    {"day": 1, "title": "兵马俑+华清宫", "description": "上午：兵马俑博物馆（一号坑/二号坑/三号坑/铜车马展）\n中午：临潼特色午餐\n下午：华清宫（唐御汤遗址/五间厅）→ 骊山\n晚上：大雁塔广场（音乐喷泉+大唐不夜城）"},
                    {"day": 2, "title": "古城墙+回民街", "description": "上午：西安古城墙（骑行/漫步）\n中午：回民街美食探索（肉夹馍/羊肉泡馍/biangbiang面）\n下午：钟鼓楼广场 → 结束行程"},
                ],
                "meta_title": "西安兵马俑两日游 | Echo Tours",
                "meta_description": "参观世界第八大奇迹兵马俑，游华清宫，骑行古城墙，品味西安千年古都文化。",
            },
            "en": {
                "name": "Xi'an Terracotta Warriors 2-Day Tour",
                "subtitle": "Travel through Zhou, Qin, Han and Tang dynasties",
                "description": "Xi'an, one of the world's four great ancient capitals, was home to 13 dynasties. Visit the Eighth Wonder of the World — the Terracotta Warriors, the Huaqing Palace, cycle the ancient city wall, and explore the Muslim Quarter.",
                "itinerary": [
                    {"day": 1, "title": "Terracotta Warriors", "description": "Morning: Terracotta Warriors Museum (Pits 1-3, Bronze Chariots)\nAfternoon: Huaqing Palace → Lishan Mountain\nEvening: Giant Wild Goose Pagoda Square"},
                    {"day": 2, "title": "City Wall & Muslim Quarter", "description": "Morning: Xi'an Ancient City Wall (cycling)\nAfternoon: Muslim Quarter food tour → Bell & Drum Towers → Tour ends"},
                ],
                "highlights": [
                    "Terracotta Warriors Museum (Eighth Wonder of the World)",
                    "Huaqing Palace — Tang emperor's love story",
                    "Xi'an Ancient City Wall cycling",
                    "Muslim Quarter food tour",
                    "Giant Wild Goose Pagoda & musical fountain",
                ],
                "includes": [
                    "Terracotta Warriors + Huaqing Palace tickets",
                    "1 night 3-star hotel with breakfast",
                    "Professional guide service",
                    "City wall bicycle rental",
                    "Travel accident insurance",
                ],
                "excludes": [
                    "Personal expenses",
                    "Single room supplement",
                    "Round-trip transportation",
                ],
                "meta_title": "Xi'an 2-Day Terracotta Warriors Tour | Echo Tours",
                "meta_description": "A 2-day Xi'an tour covering the Terracotta Warriors, Ancient City Wall and Muslim Quarter food tour.",
            },
        },
        "images": [
            {"url": "/images/tours/xian-1.svg", "alt_text": "兵马俑一号坑", "sort_order": 1},
            {"url": "/images/tours/xian-2.svg", "alt_text": "西安古城墙", "sort_order": 2},
        ],
        "dates": [
            {"start_date_offset": 14, "price": 549.0, "availability": 18},
            {"start_date_offset": 28, "price": 589.0, "availability": 20},
            {"start_date_offset": 42, "price": 549.0, "availability": 15},
            {"start_date_offset": 56, "price": 629.0, "availability": 22},
        ],
    },
]

# ── 景点 ──────────────────────────────────────────────────────────────────

# Unsplash 图片 URL 模板（可用于生产环境替换，开发环境使用本地 SVG 占位图）
_UNSPLASH = "https://images.unsplash.com/photo-{id}?w=800&h=600&fit=crop"
# 本地 SVG 占位图路径（支持在管理后台替换为真实图片）
_PLACEHOLDER = "/images/attractions/{slug}.svg"

ATTRACTIONS = {
    "beijing": [
        {
            "slug": "forbidden-city",
            "sort_order": 1,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="forbidden-city"),
            "translations": {
                "zh": {"name": "故宫博物院", "description": "明清两代的皇家宫殿，旧称紫禁城，世界最大保存最完整的木结构古建筑群，1987年被列为世界文化遗产。"},
                "en": {"name": "Forbidden City", "description": "The imperial palace of Ming and Qing dynasties, the world's largest and best-preserved wooden structure complex, a UNESCO World Heritage site since 1987."},
            },
        },
        {
            "slug": "badaling-great-wall",
            "sort_order": 2,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="badaling-great-wall"),
            "translations": {
                "zh": {"name": "八达岭长城", "description": "明长城最具代表性的一段，海拔约1000米，是开放最早、保护最完好的长城段落。"},
                "en": {"name": "Badaling Great Wall", "description": "The most representative section of the Ming Great Wall at 1,000m elevation, the earliest opened and best-preserved section."},
            },
        },
        {
            "slug": "temple-of-heaven",
            "sort_order": 3,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="temple-of-heaven"),
            "translations": {
                "zh": {"name": "天坛公园", "description": "明清两代皇帝祭天祈谷的场所，中国现存规模最大的祭天建筑群，世界文化遗产。"},
                "en": {"name": "Temple of Heaven", "description": "The largest and best-preserved sacrificial building complex in China, where Ming and Qing emperors prayed for good harvests, a UNESCO World Heritage site."},
            },
        },
        {
            "slug": "summer-palace",
            "sort_order": 4,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="summer-palace"),
            "translations": {
                "zh": {"name": "颐和园", "description": "中国现存规模最大、保存最完整的皇家园林，被誉为皇家园林博物馆，世界文化遗产。"},
                "en": {"name": "Summer Palace", "description": "The largest and best-preserved imperial garden in China, known as the 'Museum of Royal Gardens', a UNESCO World Heritage site."},
            },
        },
        {
            "slug": "ming-tombs",
            "sort_order": 5,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="ming-tombs"),
            "translations": {
                "zh": {"name": "明十三陵", "description": "明朝十三位皇帝的陵墓群，世界现存规模最大、保存最完整的帝王陵墓群之一，世界文化遗产。"},
                "en": {"name": "Ming Tombs", "description": "The burial site of 13 Ming emperors, one of the largest and best-preserved imperial tomb complexes in the world, a UNESCO World Heritage site."},
            },
        },
        {
            "slug": "prince-gong-mansion",
            "sort_order": 6,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="prince-gong-mansion"),
            "translations": {
                "zh": {"name": "恭王府", "description": "清代规模最大、保存最完整的一座王府，曾为和珅和恭亲王奕訢的府邸，素有'一座恭王府，半部清朝史'之说。"},
                "en": {"name": "Prince Gong's Mansion", "description": "The largest and best-preserved princely residence from the Qing dynasty, once home to the notorious official Heshen and Prince Gong."},
            },
        },
        {
            "slug": "olympic-park",
            "sort_order": 7,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="olympic-park"),
            "translations": {
                "zh": {"name": "北京奥林匹克公园", "description": "2008年夏季奥运会和2022年冬季奥运会的核心举办地，拥有鸟巢、水立方等标志性建筑。"},
                "en": {"name": "Olympic Park", "description": "The main venue for the 2008 Summer and 2022 Winter Olympics, featuring iconic structures like the Bird's Nest and Water Cube."},
            },
        },
        {
            "slug": "old-summer-palace",
            "sort_order": 8,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="old-summer-palace"),
            "translations": {
                "zh": {"name": "圆明园", "description": "清代大型皇家园林，被誉为万园之园，1860年遭英法联军焚毁，现为爱国主义教育基地和遗址公园。"},
                "en": {"name": "Old Summer Palace", "description": "A magnificent imperial garden complex known as the 'Garden of Gardens', destroyed in 1860 by Anglo-French forces, now a historic site and museum."},
            },
        },
        {
            "slug": "mutianyu-great-wall",
            "sort_order": 9,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="mutianyu-great-wall"),
            "translations": {
                "zh": {"name": "慕田峪长城", "description": "明长城的精华段落之一，游客较少、风光秀丽，以敌楼密集和壮美景色著称。"},
                "en": {"name": "Mutianyu Great Wall", "description": "One of the finest sections of the Ming Great Wall, known for its dense watchtowers, fewer crowds, and stunning scenery."},
            },
        },
        {
            "slug": "beihai-park",
            "sort_order": 10,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="beihai-park"),
            "translations": {
                "zh": {"name": "北海公园", "description": "中国现存最古老、保存最完整的皇家园林之一，以白塔和琼岛春阴著称，距今已有千年历史。"},
                "en": {"name": "Beihai Park", "description": "One of the oldest and best-preserved imperial gardens in China, famous for the White Pagoda and ancient Qiong Island."},
            },
        },
        {
            "slug": "lama-temple",
            "sort_order": 11,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="lama-temple"),
            "translations": {
                "zh": {"name": "雍和宫", "description": "北京规模最大、保存最完整的藏传佛教寺庙，原为雍正皇帝府邸，现为著名佛教文化景点。"},
                "en": {"name": "Lama Temple", "description": "The largest and best-preserved Tibetan Buddhist temple in Beijing, originally the residence of Emperor Yongzheng."},
            },
        },
        {
            "slug": "national-museum",
            "sort_order": 12,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="national-museum"),
            "translations": {
                "zh": {"name": "中国国家博物馆", "description": "世界最大的博物馆之一，位于天安门广场东侧，藏品涵盖中华五千年文明史。"},
                "en": {"name": "National Museum of China", "description": "One of the world's largest museums, located on the east side of Tiananmen Square, covering 5,000 years of Chinese civilization."},
            },
        },
        {
            "slug": "jingshan-park",
            "sort_order": 13,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="jingshan-park"),
            "translations": {
                "zh": {"name": "景山公园", "description": "位于北京中轴线上，万春亭可俯瞰故宫全景，是拍摄故宫全景的最佳地点。"},
                "en": {"name": "Jingshan Park", "description": "Located on Beijing's central axis, the Wanchun Pavilion offers a panoramic view of the entire Forbidden City."},
            },
        },
        {
            "slug": "shichahai",
            "sort_order": 14,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="shichahai"),
            "translations": {
                "zh": {"name": "什刹海", "description": "北京历史文化保护区，由前海、后海、西海组成，周边遍布胡同、四合院和酒吧，体验老北京生活的最佳去处。"},
                "en": {"name": "Shichahai", "description": "A historic area comprising three lakes, surrounded by hutongs, courtyard residences and bars — the best place to experience old Beijing."},
            },
        },
        {
            "slug": "fragrant-hills",
            "sort_order": 15,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="fragrant-hills"),
            "translations": {
                "zh": {"name": "香山公园", "description": "北京西郊著名的皇家园林和山林公园，以秋日红叶闻名，每年吸引大量游客赏枫。"},
                "en": {"name": "Fragrant Hills Park", "description": "A famous imperial garden and mountain park in western Beijing, renowned for its autumn red leaves that attract visitors from around the world."},
            },
        },
    ],
    "nanjing": [
        {
            "slug": "sun-yat-sen-mausoleum",
            "sort_order": 1,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="sun-yat-sen-mausoleum"),
            "translations": {
                "zh": {"name": "中山陵", "description": "孙中山先生的陵寝，位于紫金山南麓，依山而建气势恢宏，是中国近代建筑史上的重要里程碑。"},
                "en": {"name": "Sun Yat-sen Mausoleum", "description": "The resting place of Dr. Sun Yat-sen, located at the southern foot of Purple Mountain, a masterpiece of modern Chinese architecture."},
            },
        },
        {
            "slug": "confucius-temple-nanjing",
            "sort_order": 2,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="confucius-temple-nanjing"),
            "translations": {
                "zh": {"name": "夫子庙秦淮河风光带", "description": "南京最著名的历史文化街区，集庙宇、科举文化、秦淮河夜景和美食于一体。"},
                "en": {"name": "Confucius Temple & Qinhuai River", "description": "Nanjing's most famous historical and cultural area, combining temples, imperial exam culture, Qinhuai River night scenery and cuisine."},
            },
        },
        {
            "slug": "ming-xiaoling",
            "sort_order": 3,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="ming-xiaoling"),
            "translations": {
                "zh": {"name": "明孝陵", "description": "明朝开国皇帝朱元璋的陵墓，世界文化遗产，神道石像生群是中国古代石刻艺术的瑰宝。"},
                "en": {"name": "Ming Xiaoling Mausoleum", "description": "The tomb of Zhu Yuanzhang, founder of the Ming dynasty. The Sacred Way stone statues are a treasure of ancient Chinese stone carving art."},
            },
        },
        {
            "slug": "nanjing-museum",
            "sort_order": 4,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="nanjing-museum"),
            "translations": {
                "zh": {"name": "南京博物院", "description": "中国三大博物馆之一，藏品逾43万件，涵盖从远古到近现代的完整历史脉络。"},
                "en": {"name": "Nanjing Museum", "description": "One of China's three major museums, housing over 430,000 artifacts spanning from ancient to modern times."},
            },
        },
        {
            "slug": "xuanwu-lake",
            "sort_order": 5,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="xuanwu-lake"),
            "translations": {
                "zh": {"name": "玄武湖公园", "description": "中国最大的皇家园林湖泊，位于南京城中，三面环山一面靠城，风景秀丽历史悠久。"},
                "en": {"name": "Xuanwu Lake Park", "description": "China's largest imperial garden lake, located in the heart of Nanjing, surrounded by mountains and the ancient city wall."},
            },
        },
        {
            "slug": "presidential-palace",
            "sort_order": 6,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="presidential-palace"),
            "translations": {
                "zh": {"name": "总统府", "description": "中国近代史的重要见证，曾为太平天国天王府和中华民国总统府，现为中国近代史博物馆。"},
                "en": {"name": "Presidential Palace", "description": "A key witness to modern Chinese history, served as the palace of the Taiping Heavenly Kingdom and the Presidential Palace of the Republic of China."},
            },
        },
        {
            "slug": "qinhuai-river",
            "sort_order": 7,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="qinhuai-river"),
            "translations": {
                "zh": {"name": "秦淮河", "description": "南京的母亲河，素有六朝金粉之称，乘船夜游秦淮是体验金陵风情的经典方式。"},
                "en": {"name": "Qinhuai River", "description": "The mother river of Nanjing, known as the 'Golden Powder of Six Dynasties'. A night cruise is the classic way to experience Jinling charm."},
            },
        },
        {
            "slug": "jiming-temple",
            "sort_order": 8,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="jiming-temple"),
            "translations": {
                "zh": {"name": "鸡鸣寺", "description": "南京最古老的佛教寺庙之一，始建于西晋，位于玄武湖畔，春天樱花盛开时格外美丽。"},
                "en": {"name": "Jiming Temple", "description": "One of Nanjing's oldest Buddhist temples, built in the Western Jin dynasty, located by Xuanwu Lake with stunning spring cherry blossoms."},
            },
        },
        {
            "slug": "purple-mountain",
            "sort_order": 9,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="purple-mountain"),
            "translations": {
                "zh": {"name": "紫金山", "description": "南京的绿色明珠，汇集中山陵、明孝陵、灵谷寺等众多名胜，是城市中央的国家森林公园。"},
                "en": {"name": "Purple Mountain", "description": "The green pearl of Nanjing, home to Sun Yat-sen Mausoleum, Ming Xiaoling, and Linggu Temple — a national forest park in the city center."},
            },
        },
        {
            "slug": "yangtze-river-bridge",
            "sort_order": 10,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="yangtze-river-bridge"),
            "translations": {
                "zh": {"name": "南京长江大桥", "description": "长江上第一座由中国自行设计和建造的双层铁路公路两用桥，是新中国技术成就的象征。"},
                "en": {"name": "Nanjing Yangtze River Bridge", "description": "The first dual-purpose rail-road bridge across the Yangtze River designed and built by China, a symbol of China's technological achievement."},
            },
        },
        {
            "slug": "memorial-hall-nanjing",
            "sort_order": 11,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="memorial-hall-nanjing"),
            "translations": {
                "zh": {"name": "侵华日军南京大屠杀遇难同胞纪念馆", "description": "为纪念南京大屠杀遇难同胞而建，是重要的爱国主义教育基地和世界和平的警示。"},
                "en": {"name": "Memorial Hall of the Victims in Nanjing Massacre", "description": "Built in memory of the victims of the Nanjing Massacre, an important education base for patriotism and a warning for world peace."},
            },
        },
        {
            "slug": "zhan-yuan-garden",
            "sort_order": 12,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="zhan-yuan-garden"),
            "translations": {
                "zh": {"name": "瞻园", "description": "南京现存历史最久的明代古典园林，太平天国时期为东王杨秀清的府邸花园，江南四大名园之一。"},
                "en": {"name": "Zhan Yuan Garden", "description": "The oldest existing Ming dynasty classical garden in Nanjing, once the residence of the Taiping Eastern King, one of the four famous gardens in Jiangnan."},
            },
        },
        {
            "slug": "zhonghua-gate",
            "sort_order": 13,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="zhonghua-gate"),
            "translations": {
                "zh": {"name": "中华门", "description": "中国现存规模最大的城门，世界上保存最完好、结构最复杂的古代瓮城，有'天下第一瓮城'之称。"},
                "en": {"name": "Zhonghua Gate", "description": "China's largest existing city gate, the world's best-preserved and most complex ancient barbican, known as the 'Number One Barbican Under Heaven'."},
            },
        },
        {
            "slug": "linggu-temple",
            "sort_order": 14,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="linggu-temple"),
            "translations": {
                "zh": {"name": "灵谷寺", "description": "明代三大佛教寺院之一，位于紫金山下，以无梁殿和灵谷塔闻名，环境清幽。"},
                "en": {"name": "Linggu Temple", "description": "One of the three great Buddhist temples of the Ming dynasty, located at the foot of Purple Mountain, famous for its Beamless Hall and Linggu Pagoda."},
            },
        },
        {
            "slug": "nanjing-city-wall",
            "sort_order": 15,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="nanjing-city-wall"),
            "translations": {
                "zh": {"name": "南京城墙", "description": "世界最长、规模最大、保存最完整的古代城垣之一，全长35公里，是明初都城的宏伟屏障。"},
                "en": {"name": "Nanjing City Wall", "description": "One of the longest, largest and best-preserved ancient city walls in the world, stretching 35 km as the grand defense of the Ming capital."},
            },
        },
    ],
    "xian": [
        {
            "slug": "terracotta-warriors",
            "sort_order": 1,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="terracotta-warriors"),
            "translations": {
                "zh": {"name": "秦始皇兵马俑博物馆", "description": "世界第八大奇迹，秦始皇陵的陪葬坑，出土数千件真人大小陶俑，1978年被列为世界文化遗产。"},
                "en": {"name": "Terracotta Warriors Museum", "description": "The Eighth Wonder of the World, thousands of life-sized terracotta figures guarding the tomb of Emperor Qin Shi Huang, a UNESCO World Heritage site since 1978."},
            },
        },
        {
            "slug": "giant-wild-goose-pagoda",
            "sort_order": 2,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="giant-wild-goose-pagoda"),
            "translations": {
                "zh": {"name": "大雁塔", "description": "唐代高僧玄奘为保存从印度带回的佛经而建，西安的标志性建筑，世界文化遗产。"},
                "en": {"name": "Giant Wild Goose Pagoda", "description": "Built by the Tang dynasty monk Xuanzang to store Buddhist scriptures brought from India, the iconic landmark of Xi'an, a UNESCO World Heritage site."},
            },
        },
        {
            "slug": "huaqing-palace",
            "sort_order": 3,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="huaqing-palace"),
            "translations": {
                "zh": {"name": "华清宫", "description": "唐代皇家温泉行宫，以唐玄宗与杨贵妃的爱情故事闻名，'春寒赐浴华清池'即指此地。"},
                "en": {"name": "Huaqing Palace", "description": "A Tang dynasty imperial hot spring palace, famous for the love story of Emperor Xuanzong and Yang Guifei, 'bathing in the Huaqing pool in spring chill'."},
            },
        },
        {
            "slug": "xian-city-wall",
            "sort_order": 4,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="xian-city-wall"),
            "translations": {
                "zh": {"name": "西安城墙", "description": "中国现存规模最大、保存最完整的古代城墙，全长13.7公里，可骑行游览。"},
                "en": {"name": "Xi'an City Wall", "description": "The largest and best-preserved ancient city wall in China, stretching 13.7 km, perfect for cycling tours."},
            },
        },
        {
            "slug": "shaanxi-history-museum",
            "sort_order": 5,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="shaanxi-history-museum"),
            "translations": {
                "zh": {"name": "陕西历史博物馆", "description": "中国第一座大型现代化国家级博物馆，藏品170万件，被誉为古都明珠、华夏宝库。"},
                "en": {"name": "Shaanxi History Museum", "description": "China's first large modern national museum, housing 1.7 million artifacts, known as the 'Pearl of the Ancient Capital and Treasure House of China'."},
            },
        },
        {
            "slug": "muslim-quarter",
            "sort_order": 6,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="muslim-quarter"),
            "translations": {
                "zh": {"name": "回民街", "description": "西安著名的美食文化街区，以清真美食闻名，肉夹馍、羊肉泡馍、Biangbiang面是必尝的特色。"},
                "en": {"name": "Muslim Quarter", "description": "Xi'an's famous food and culture street, renowned for halal cuisine — must-try specialties include roujiamo, yangrou paomo and biangbiang noodles."},
            },
        },
        {
            "slug": "bell-drum-towers",
            "sort_order": 7,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="bell-drum-towers"),
            "translations": {
                "zh": {"name": "西安钟鼓楼", "description": "位于西安市中心，是古城的标志性建筑，钟楼和鼓楼遥相呼应，见证了西安的千年历史。"},
                "en": {"name": "Bell and Drum Towers", "description": "Located in the center of Xi'an, these iconic structures have witnessed a thousand years of the city's history, standing in mutual witness."},
            },
        },
        {
            "slug": "small-wild-goose-pagoda",
            "sort_order": 8,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="small-wild-goose-pagoda"),
            "translations": {
                "zh": {"name": "小雁塔", "description": "唐代密檐式砖塔，与大雁塔同为唐代长安城的重要佛教建筑，现为西安博物院的一部分。"},
                "en": {"name": "Small Wild Goose Pagoda", "description": "A Tang dynasty close-eaves brick pagoda, together with the Giant Wild Goose Pagoda a key Buddhist structure of Chang'an, now part of Xi'an Museum."},
            },
        },
        {
            "slug": "tang-paradise",
            "sort_order": 9,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="tang-paradise"),
            "translations": {
                "zh": {"name": "大唐不夜城", "description": "以盛唐文化为主题的步行街，夜晚灯光璀璨，是西安最具人气的文化旅游地标之一。"},
                "en": {"name": "Tang Paradise & Night Walk", "description": "A Tang dynasty culture-themed pedestrian street, brilliantly lit at night, one of Xi'an's most popular cultural tourism landmarks."},
            },
        },
        {
            "slug": "lishan-mountain",
            "sort_order": 10,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="lishan-mountain"),
            "translations": {
                "zh": {"name": "骊山", "description": "秦岭山脉的支脉，华清宫所在地，周幽王烽火戏诸侯的故事发生于此，山上有老母殿等古迹。"},
                "en": {"name": "Lishan Mountain", "description": "A branch of the Qinling Mountains, site of Huaqing Palace and the famous story of the beacon towers, home to ancient temples and scenic views."},
            },
        },
        {
            "slug": "famen-temple",
            "sort_order": 11,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="famen-temple"),
            "translations": {
                "zh": {"name": "法门寺", "description": "世界著名的佛教寺院，以珍藏释迦牟尼佛指骨舍利而闻名，唐代被视为皇家寺院。"},
                "en": {"name": "Famen Temple", "description": "A world-famous Buddhist temple, renowned for housing the finger bone relic of Shakyamuni Buddha, revered as a royal temple during the Tang dynasty."},
            },
        },
        {
            "slug": "stele-forest",
            "sort_order": 12,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="stele-forest"),
            "translations": {
                "zh": {"name": "西安碑林博物馆", "description": "中国最大的石碑书法艺术宝库，收藏汉代至清代碑石4000余方，被誉为中国书法艺术的殿堂。"},
                "en": {"name": "Stele Forest Museum", "description": "China's largest collection of stone steles and calligraphy, housing over 4,000 steles from the Han to Qing dynasties."},
            },
        },
        {
            "slug": "daming-palace",
            "sort_order": 13,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="daming-palace"),
            "translations": {
                "zh": {"name": "大明宫国家遗址公园", "description": "唐代最宏伟的皇宫建筑群遗址，是北京紫禁城的4.5倍，世界文化遗产，丝绸之路上的重要地标。"},
                "en": {"name": "Daming Palace National Heritage Park", "description": "The ruins of the most magnificent Tang dynasty imperial palace, 4.5 times the size of the Forbidden City, a UNESCO World Heritage site on the Silk Road."},
            },
        },
        {
            "slug": "huashan-mountain",
            "sort_order": 14,
            "rating": 5,
            "image_url": _PLACEHOLDER.format(slug="huashan-mountain"),
            "translations": {
                "zh": {"name": "华山", "description": "中国五岳之一，以险峻著称，长空栈道和鹞子翻身是极限爱好者的挑战，从西安出发一日可往返。"},
                "en": {"name": "Huashan Mountain", "description": "One of China's Five Sacred Mountains, famous for its precipitous cliffs and the thrilling Plank Walk — a day trip from Xi'an."},
            },
        },
        {
            "slug": "qin-shi-huang-mausoleum",
            "sort_order": 15,
            "rating": 4,
            "image_url": _PLACEHOLDER.format(slug="qin-shi-huang-mausoleum"),
            "translations": {
                "zh": {"name": "秦始皇陵", "description": "秦始皇嬴政的陵墓，中国历史上第一座规模庞大、设计完善的帝王陵寝，尚未发掘的主陵下方据推测有宏大的地下宫殿。"},
                "en": {"name": "Mausoleum of Qin Shi Huang", "description": "The tomb of Ying Zheng, the First Emperor of China, the first grand imperial mausoleum in Chinese history, with an enormous underground palace yet to be excavated."},
            },
        },
    ],
}

# ── 用户 ──────────────────────────────────────────────────────────────────

USERS = [
    {
        "email": "admin@echotours.com",
        "name": "系统管理员",
        "password": "Admin123!",
        "is_admin": True,
        "is_active": True,
        "locale": "zh",
    },
    {
        "email": "zhangsan@example.com",
        "name": "张三",
        "password": "Test1234!",
        "is_admin": False,
        "is_active": True,
        "locale": "zh",
    },
    {
        "email": "lisi@example.com",
        "name": "李四",
        "password": "Test1234!",
        "is_admin": False,
        "is_active": True,
        "locale": "zh",
    },
    {
        "email": "john@example.com",
        "name": "John Smith",
        "password": "Test1234!",
        "is_admin": False,
        "is_active": True,
        "locale": "en",
    },
]

# ── 评论 ──────────────────────────────────────────────────────────────────

REVIEWS_DATA = [
    {
        "tour_slug": "forbidden-city-royal-walk",
        "user_email": "zhangsan@example.com",
        "rating": 5,
        "title": "非常棒的故宫体验",
        "comment": "导游讲解非常专业，对故宫的历史了如指掌。三个小时的行程收获满满，特别是珍宝馆的展品令人叹为观止。强烈推荐！",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "forbidden-city-royal-walk",
        "user_email": "john@example.com",
        "rating": 5,
        "title": "Amazing Forbidden City experience",
        "comment": "Our guide was incredibly knowledgeable and brought the history of the Forbidden City to life. The fast-track entry saved us hours of waiting. Highly recommended!",
        "locale": "en",
        "status": "approved",
    },
    {
        "tour_slug": "great-wall-badaling-hike",
        "user_email": "lisi@example.com",
        "rating": 4,
        "title": "长城很壮观，值得一去",
        "comment": "八达岭长城非常壮观，缆车上山很方便。只是节假日人真的很多，建议工作日去。导游服务很好，午餐也不错。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "summer-palace-royal-garden",
        "user_email": "zhangsan@example.com",
        "rating": 5,
        "title": "颐和园太美了",
        "comment": "昆明湖游船非常惬意，佛香阁俯瞰整个园区视野极好。长廊的彩绘精美绝伦，十步一景名不虚传。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "temple-of-heaven-cultural",
        "user_email": "john@example.com",
        "rating": 4,
        "title": "Fascinating cultural experience",
        "comment": "The Temple of Heaven is a masterpiece of ancient Chinese architecture. The Echo Wall phenomenon was really cool. A must-visit in Beijing.",
        "locale": "en",
        "status": "approved",
    },
    {
        "tour_slug": "beijing-essence-3-day",
        "user_email": "lisi@example.com",
        "rating": 5,
        "title": "性价比超高的三日游",
        "comment": "三天时间把北京主要景点都走到了，行程安排合理不赶。酒店干净舒适，烤鸭和涮肉都非常正宗。导游小王特别负责，给整个旅程增色不少。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "prince-gong-mansion-hutong",
        "user_email": "zhangsan@example.com",
        "rating": 4,
        "title": "胡同游很有意思",
        "comment": "恭王府很气派，和珅的故事特别有趣。三轮车胡同游是很独特的体验，穿越在老北京胡同里感觉很棒。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "mutianyu-great-wall-premium",
        "user_email": "john@example.com",
        "rating": 5,
        "title": "Best Great Wall experience",
        "comment": "Mutianyu is far less crowded than Badaling. The toboggan ride down was an absolute blast! Our small group made it feel very personal. Worth every penny.",
        "locale": "en",
        "status": "approved",
    },
    {
        "tour_slug": "xian-terracotta-warriors-2day",
        "user_email": "zhangsan@example.com",
        "rating": 5,
        "title": "西安太震撼了",
        "comment": "兵马俑远比想象中更震撼，千人千面的陶俑令人难以置信。古城墙骑行也是独特的体验，回民街的小吃太好吃了。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "nanjing-historical-essence",
        "user_email": "lisi@example.com",
        "rating": 4,
        "title": "南京的文化底蕴深厚",
        "comment": "中山陵气势磅礴，明孝陵神道石像很有历史感，秦淮河的夜景很美。南京博物院藏品丰富，值得花时间慢慢看。",
        "locale": "zh",
        "status": "approved",
    },
    {
        "tour_slug": "olympic-park-modern-beijing",
        "user_email": "john@example.com",
        "rating": 3,
        "title": "Interesting modern architecture",
        "comment": "The Bird's Nest and Water Cube are impressive architectural feats. The tour was informative but relatively short. Good for half a day.",
        "locale": "en",
        "status": "approved",
    },
    {
        "tour_slug": "old-summer-palace-history",
        "user_email": "zhangsan@example.com",
        "rating": 4,
        "title": "历史的警醒",
        "comment": "圆明园的遗址让人感慨万千，大水法的残垣断壁见证了一段屈辱的历史。导游的讲解很深刻，让人深思。",
        "locale": "zh",
        "status": "approved",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 种子逻辑
# ═══════════════════════════════════════════════════════════════════════════


async def clear_existing_data(db):
    """清空已有种子数据（按外键顺序删除）。"""
    logger.info("清空已有数据...")
    await db.execute(text("DELETE FROM order_passengers"))
    await db.execute(text("DELETE FROM orders"))
    await db.execute(text("DELETE FROM wishlists"))
    await db.execute(text("DELETE FROM reviews"))
    await db.execute(text("DELETE FROM tour_dates"))
    await db.execute(text("DELETE FROM tour_images"))
    await db.execute(text("DELETE FROM tour_translations"))
    await db.execute(text("DELETE FROM tours"))
    await db.execute(text("DELETE FROM custom_tour_services"))
    await db.execute(text("DELETE FROM custom_tour_attractions"))
    await db.execute(text("DELETE FROM custom_tour_segment_tours"))
    await db.execute(text("DELETE FROM custom_tour_segments"))
    await db.execute(text("DELETE FROM custom_tour_requests"))
    await db.execute(text("DELETE FROM base_services"))
    await db.execute(text("DELETE FROM attraction_wishlists"))
    await db.execute(text("DELETE FROM attraction_tickets"))
    await db.execute(text("DELETE FROM attraction_translations"))
    await db.execute(text("DELETE FROM attractions"))
    await db.execute(text("DELETE FROM destination_translations"))
    await db.execute(text("DELETE FROM destinations"))
    await db.execute(text("DELETE FROM users"))
    await db.flush()
    logger.info("已清空所有数据。")


async def seed_destinations(db) -> dict[str, uuid.UUID]:
    """创建目的地，返回 {slug: id} 映射。"""
    logger.info("=" * 50)
    logger.info("创建目的地...")
    slug_to_id = {}

    for slug, data in DESTINATIONS.items():
        dest = Destination(
            id=uuid.uuid4(),
            slug=data["slug"],
            area_code=data.get("area_code"),
            image_url=data["image_url"],
            status="active",
        )
        db.add(dest)
        await db.flush()
        slug_to_id[slug] = dest.id

        for locale, trans in data["translations"].items():
            translation = DestinationTranslation(
                id=uuid.uuid4(),
                destination_id=dest.id,
                locale=locale,
                name=trans["name"],
                description=trans["description"],
                meta_title=trans.get("meta_title"),
                meta_description=trans.get("meta_description"),
            )
            db.add(translation)

        logger.info(f"  ✅ {data['translations']['zh']['name']} ({data['slug']})")

    await db.flush()
    return slug_to_id


async def seed_users(db) -> dict[str, uuid.UUID]:
    """创建用户，返回 {email: id} 映射。"""
    logger.info("=" * 50)
    logger.info("创建用户...")
    email_to_id = {}

    for u in USERS:
        user = User(
            id=uuid.uuid4(),
            email=u["email"],
            name=u["name"],
            hashed_password=hash_password(u["password"]),
            is_admin=u["is_admin"],
            is_active=u["is_active"],
            locale=u["locale"],
        )
        db.add(user)
        await db.flush()
        email_to_id[u["email"]] = user.id

        role = "管理员" if u["is_admin"] else "用户"
        logger.info(f"  ✅ [{role}] {u['name']} ({u['email']}) / 密码: {u['password']}")

    await db.flush()
    return email_to_id


async def seed_tours(db, dest_slug_to_id: dict, email_to_id: dict) -> dict[str, uuid.UUID]:
    """创建旅游产品、翻译、图片和价格日历，返回 {slug: id} 映射。"""
    logger.info("=" * 50)
    logger.info("创建旅游产品和价格日历...")
    tour_slug_to_id = {}

    today = date.today()

    for t in TOURS:
        tour = Tour(
            id=uuid.uuid4(),
            slug=t["slug"],
            type=t["type"],
            status=t.get("status", "published"),
            duration_days=t["duration_days"],
            duration_nights=t["duration_nights"],
            max_pax=t["max_pax"],
            min_pax=t["min_pax"],
            start_price=t["start_price"],
            currency=t["currency"],
            difficulty=t["difficulty"],
            highlights=t.get("highlights", []),
            includes=t.get("includes", []),
            excludes=t.get("excludes", []),
            serial_number=t.get("serial_number"),
            destination_ids=[dest_slug_to_id[s] for s in t["destination_slugs"]],
            avg_rating=0.0,
            review_count=0,
            published_at=datetime.now(timezone.utc),
        )
        db.add(tour)
        tour_slug_to_id[t["slug"]] = tour.id

        # 多语言翻译
        for locale, trans in t["translations"].items():
            translation = TourTranslation(
                id=uuid.uuid4(),
                tour_id=tour.id,
                locale=locale,
                name=trans["name"],
                subtitle=trans.get("subtitle"),
                description=trans.get("description"),
                itinerary=trans.get("itinerary"),
                highlights=trans.get("highlights"),
                includes=trans.get("includes"),
                excludes=trans.get("excludes"),
                meta_title=trans.get("meta_title"),
                meta_description=trans.get("meta_description"),
            )
            db.add(translation)

        # 图片
        for img in t.get("images", []):
            image = TourImage(
                id=uuid.uuid4(),
                tour_id=tour.id,
                url=img["url"],
                alt_text=img.get("alt_text"),
                sort_order=img.get("sort_order", 0),
            )
            db.add(image)

        # 价格日历
        for dt in t.get("dates", []):
            start = today + timedelta(days=dt["start_date_offset"])
            days = float(t["duration_days"])
            end = start + timedelta(days=int(days) if days >= 1 else 0)
            tour_date = TourDate(
                id=uuid.uuid4(),
                tour_id=tour.id,
                start_date=start,
                end_date=end,
                price_per_pax=dt["price"],
                currency=t["currency"],
                availability=dt["availability"],
                status="available",
            )
            db.add(tour_date)

        name_zh = t["translations"]["zh"]["name"]
        logger.info(f"  ✅ {name_zh} ({t['slug']}) — ${t['start_price']} 起 / {len(t.get('dates', []))}个团期")

    await db.flush()

    # 更新点评统计
    logger.info("")
    logger.info("=" * 50)
    logger.info("创建评论...")
    review_count_map: dict[uuid.UUID, list[int]] = {}

    for rv in REVIEWS_DATA:
        tour_id = tour_slug_to_id.get(rv["tour_slug"])
        user_id = email_to_id.get(rv["user_email"])
        if not tour_id or not user_id:
            continue

        review = Review(
            id=uuid.uuid4(),
            tour_id=tour_id,
            user_id=user_id,
            rating=rv["rating"],
            title=rv.get("title"),
            comment=rv.get("comment"),
            locale=rv.get("locale", "zh"),
            status=rv.get("status", "approved"),
        )
        db.add(review)

        if tour_id not in review_count_map:
            review_count_map[tour_id] = []
        review_count_map[tour_id].append(rv["rating"])
        logger.info(f"  ⭐ {'⭐' * rv['rating']} {rv.get('title', '')[:30]}...")

    # 更新 Tour 的评分统计
    for tour_id, ratings in review_count_map.items():
        avg = sum(ratings) / len(ratings)
        tour_obj = await db.get(Tour, tour_id)
        if tour_obj:
            tour_obj.avg_rating = round(avg, 1)
            tour_obj.review_count = len(ratings)

    await db.flush()
    logger.info(f"  💬 共创建 {len(REVIEWS_DATA)} 条评论")
    return tour_slug_to_id


async def seed_attractions(db, dest_slug_to_id: dict):
    """创建景点数据（每城市 Top 15）。"""
    logger.info("=" * 50)
    logger.info("创建景点数据（每城市 Top 15）...")
    count = 0

    for city_slug, attractions in ATTRACTIONS.items():
        dest_id = dest_slug_to_id.get(city_slug)
        if not dest_id:
            logger.warning(f"  ⚠️  目的地 {city_slug} 不存在，跳过")
            continue

        for i, attr in enumerate(attractions):
            # 按排名递减定价（排名越高门票越贵）
            base_price = max(5, 25 - i * 2)
            attraction = Attraction(
                id=uuid.uuid4(),
                slug=attr["slug"],
                destination_id=dest_id,
                image_url=attr["image_url"],
                sort_order=attr["sort_order"],
                rating=attr["rating"],
                status="active",
                ticket_price=base_price,
                ticket_currency="USD",
            )
            db.add(attraction)

            for locale, trans in attr["translations"].items():
                translation = AttractionTranslation(
                    id=uuid.uuid4(),
                    attraction_id=attraction.id,
                    locale=locale,
                    name=trans["name"],
                    description=trans.get("description"),
                )
                db.add(translation)

            # 创建默认门票类型（标准票 + VIP 票）
            standard_ticket = AttractionTicket(
                id=uuid.uuid4(),
                attraction_id=attraction.id,
                ticket_type="standard",
                price=base_price,
                currency="USD",
                availability=500,
                status="available",
            )
            db.add(standard_ticket)

            vip_ticket = AttractionTicket(
                id=uuid.uuid4(),
                attraction_id=attraction.id,
                ticket_type="vip",
                price=base_price * 2,
                currency="USD",
                availability=50,
                status="available",
            )
            db.add(vip_ticket)

            # 创建景点媒体资源（照片/短视频），每个景点 4~6 个
            media_count = min(6, 4 + i % 3)  # 4~6 个
            for mi in range(media_count):
                media_url = attr["image_url"].replace(".svg", f"-{mi+1}.svg") if mi > 0 else attr["image_url"]
                media = AttractionMedia(
                    id=uuid.uuid4(),
                    attraction_id=attraction.id,
                    url=media_url,
                    media_type="image",
                    alt_text=f"{attr['translations'].get('en', {}).get('name', attr['slug'])} - View {mi+1}",
                    sort_order=mi,
                )
                db.add(media)

            count += 1

    await db.flush()
    logger.info(f"  ✅ 共创建 {count} 个景点（城市: {len(ATTRACTIONS)}）")


# ═══════════════════════════════════════════════════════════════════════════
# 基础服务种子数据（超管可编辑）
# ═══════════════════════════════════════════════════════════════════════════

BASE_SERVICES = [
    {
        "name": "One-way Airport Transfer",
        "name_zh": "单程接送机",
        "name_es": "Traslado Aeropuerto (Ida)",
        "name_fr": "Transfert Aéroport (Simple)",
        "description": "Private one-way transfer between airport and hotel. Includes meet & greet and luggage assistance.",
        "description_zh": "机场与酒店之间的单程专车接送，含接机举牌和行李协助。",
        "description_es": "Traslado privado de ida entre el aeropuerto y el hotel. Incluye recepción y asistencia con equipaje.",
        "description_fr": "Transfert privé simple entre l'aéroport et l'hôtel. Accueil personnalisé et assistance bagages.",
        "unit_type": "per_trip",
        "unit_price": 60.0,
        "category": "transport",
        "sort_order": 1,
    },
    {
        "name": "One-way Train Station Transfer",
        "name_zh": "单程接送火车站",
        "name_es": "Traslado Estación de Tren (Ida)",
        "name_fr": "Transfert Gare (Simple)",
        "description": "Private one-way transfer between train station and hotel. Includes luggage assistance.",
        "description_zh": "火车站与酒店之间的单程专车接送，含行李协助。",
        "description_es": "Traslado privado de ida entre la estación de tren y el hotel. Incluye asistencia con equipaje.",
        "description_fr": "Transfert privé simple entre la gare et l'hôtel. Assistance bagages incluse.",
        "unit_type": "per_trip",
        "unit_price": 40.0,
        "category": "transport",
        "sort_order": 2,
    },
    {
        "name": "English Guide Service (per day)",
        "name_zh": "一天英语导游服务",
        "name_es": "Guía de Habla Inglesa (por día)",
        "name_fr": "Guide Anglophone (par jour)",
        "description": "Professional English-speaking guide for a full day (8 hours). Includes expert commentary and local insights.",
        "description_zh": "专业英语导游全天服务（8小时），含专业讲解和当地文化分享。",
        "description_es": "Guía profesional de habla inglesa por un día completo (8 horas). Incluye comentarios expertos y conocimientos locales.",
        "description_fr": "Guide professionnel anglophone pour une journée complète (8 heures). Commentaires d'expert et connaissances locales.",
        "unit_type": "per_day",
        "unit_price": 120.0,
        "category": "guide",
        "sort_order": 3,
    },
    {
        "name": "Spanish Guide Service (per day)",
        "name_zh": "一天西班牙语导游服务",
        "name_es": "Guía de Habla Española (por día)",
        "name_fr": "Guide Hispanophone (par jour)",
        "description": "Professional Spanish-speaking guide for a full day (8 hours). Native-level fluency and cultural expertise.",
        "description_zh": "专业西班牙语导游全天服务（8小时），母语级别流利度及文化专业讲解。",
        "description_es": "Guía profesional de habla española por un día completo (8 horas). Fluidez nativa y experiencia cultural.",
        "description_fr": "Guide professionnel hispanophone pour une journée complète (8 heures). Niveau natif et expertise culturelle.",
        "unit_type": "per_day",
        "unit_price": 140.0,
        "category": "guide",
        "sort_order": 4,
    },
    {
        "name": "French Guide Service (per day)",
        "name_zh": "一天法语导游服务",
        "name_es": "Guía de Habla Francesa (por día)",
        "name_fr": "Guide Francophone (par jour)",
        "description": "Professional French-speaking guide for a full day (8 hours). Native-level fluency and cultural expertise.",
        "description_zh": "专业法语导游全天服务（8小时），母语级别流利度及文化专业讲解。",
        "description_es": "Guía profesional de habla francesa por un día completo (8 horas). Fluidez nativa y experiencia cultural.",
        "description_fr": "Guide professionnel francophone pour une journée complète (8 heures). Niveau natif et expertise culturelle.",
        "unit_type": "per_day",
        "unit_price": 140.0,
        "category": "guide",
        "sort_order": 5,
    },
    {
        "name": "Vehicle Service (per person per day)",
        "name_zh": "每人每天车辆服务",
        "name_es": "Servicio de Vehículo (por persona por día)",
        "name_fr": "Service Véhicule (par personne par jour)",
        "description": "Air-conditioned private vehicle with driver for a full day (8 hours). Cost shared per person.",
        "description_zh": "空调专车含司机全天服务（8小时），费用按人均摊。",
        "description_es": "Vehículo privado con aire acondicionado y conductor por un día completo (8 horas). Costo compartido por persona.",
        "description_fr": "Véhicule privé climatisé avec chauffeur pour une journée complète (8 heures). Coût réparti par personne.",
        "unit_type": "per_pax",
        "unit_price": 35.0,
        "category": "transport",
        "sort_order": 6,
    },
    {
        "name": "Hotel Service (per night)",
        "name_zh": "每人每晚酒店住宿",
        "name_es": "Servicio de Hotel (por noche)",
        "name_fr": "Service Hôtel (par nuit)",
        "description": "Standard 3-4 star hotel accommodation per person per night, twin share basis.",
        "description_zh": "标准3-4星级酒店住宿，每人每晚，双人共享。",
        "description_es": "Alojamiento en hotel estándar de 3-4 estrellas por persona por noche, en habitación compartida.",
        "description_fr": "Hébergement hôtelier standard 3-4 étoiles par personne par nuit, base partagée.",
        "unit_type": "per_pax",
        "unit_price": 65.0,
        "category": "hotel",
        "sort_order": 7,
    },
    {
        "name": "Lunch Service (per person)",
        "name_zh": "每人午餐服务",
        "name_es": "Servicio de Almuerzo (por persona)",
        "name_fr": "Service Déjeuner (par personne)",
        "description": "Set lunch at a local restaurant. Includes one main dish, rice, and a drink.",
        "description_zh": "当地餐厅套餐午餐，含一道主菜、米饭和饮品。",
        "description_es": "Almuerzo conjunto en un restaurante local. Incluye un plato principal, arroz y una bebida.",
        "description_fr": "Déjeuner fixe dans un restaurant local. Comprend un plat principal, riz et une boisson.",
        "unit_type": "per_pax",
        "unit_price": 15.0,
        "category": "meal",
        "sort_order": 8,
    },
    {
        "name": "Dinner Service (per person)",
        "name_zh": "每人晚餐服务",
        "name_es": "Servicio de Cena (por persona)",
        "name_fr": "Service Dîner (par personne)",
        "description": "Set dinner at a local restaurant. Three-course meal with beverage.",
        "description_zh": "当地餐厅套餐晚餐，三道式含饮品。",
        "description_es": "Cena conjunto en un restaurante local. Menú de tres platos con bebida.",
        "description_fr": "Dîner fixe dans un restaurant local. Menu trois plats avec boisson.",
        "unit_type": "per_pax",
        "unit_price": 25.0,
        "category": "meal",
        "sort_order": 9,
    },
]


async def seed_base_services(db):
    """创建基础服务种子数据。"""
    logger.info("=" * 50)
    logger.info("创建基础服务...")

    count = 0
    for svc in BASE_SERVICES:
        existing = await db.execute(
            select(BaseService).where(BaseService.name == svc["name"])
        )
        if existing.scalar_one_or_none():
            logger.info(f"  ⏭️  跳过（已存在）: {svc['name']}")
            continue

        service = BaseService(
            id=uuid.uuid4(),
            name=svc["name"],
            name_zh=svc.get("name_zh"),
            name_es=svc.get("name_es"),
            name_fr=svc.get("name_fr"),
            description=svc.get("description"),
            description_zh=svc.get("description_zh"),
            description_es=svc.get("description_es"),
            description_fr=svc.get("description_fr"),
            unit_type=svc["unit_type"],
            unit_price=svc["unit_price"],
            currency="USD",
            category=svc.get("category"),
            sort_order=svc.get("sort_order", 0),
            status="active",
        )
        db.add(service)
        count += 1
        logger.info(f"  ✅ {svc['name']} (${svc['unit_price']}/{svc['unit_type']})")

    await db.flush()
    logger.info(f"  ✅ 共创建 {count} 个基础服务")


async def seed():
    """主入口：依次创建所有种子数据。"""
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║        Echo Tours 种子数据生成脚本                      ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("")

    async with async_session() as db:
        try:
            await clear_existing_data(db)

            dest_map = await seed_destinations(db)
            email_to_id = await seed_users(db)
            tour_map = await seed_tours(db, dest_map, email_to_id)
            await seed_attractions(db, dest_map)
            await seed_base_services(db)

            # ── 汇总 ──
            logger.info("")
            logger.info("=" * 50)
            logger.info("📊 种子数据创建完成！")
            logger.info(f"   🏙️  目的地:      {len(DESTINATIONS)} 个")
            logger.info(f"   🏛️  旅游产品:    {len(TOURS)} 个")
            logger.info(f"   🏛️  景点:        {sum(len(v) for v in ATTRACTIONS.values())} 个")
            logger.info(f"   🔧  基础服务:    {len(BASE_SERVICES)} 个")
            logger.info(f"   👤  用户:        {len(USERS)} 个")
            logger.info(f"   💬 评论:        {len(REVIEWS_DATA)} 条")

            date_count = sum(len(t.get("dates", [])) for t in TOURS)
            image_count = sum(len(t.get("images", [])) for t in TOURS)
            logger.info(f"   📅 团期:        {date_count} 个")
            logger.info(f"   🖼️  产品图片:    {image_count} 张")
            logger.info("")
            logger.info("=" * 50)
            logger.info("登录凭据：")
            logger.info(f"   管理员: admin@echotours.com / Admin123!")
            logger.info(f"   演示用户: zhangsan@example.com / Test1234!")
            logger.info(f"   演示用户: john@example.com / Test1234!")
            logger.info("")

            await db.commit()
            logger.info("✅ 种子数据已全部写入数据库。")

            # ── 重建 ES 搜索索引 ──
            logger.info("")
            logger.info("🔍 正在重建 Elasticsearch 搜索索引...")
            try:
                from app.search.client import get_es, check_es_health
                from app.search.index import delete_index, create_index, bulk_index_tours

                if await check_es_health():
                    es = await get_es()
                    await delete_index(es)
                    await create_index(es)
                    count = await bulk_index_tours(db, es)
                    logger.info(f"✅ ES 搜索索引已重建，共索引 {count} 个文档（{count // 2} 个产品 × 2 语言）")
                else:
                    logger.warning("⚠️ Elasticsearch 不可用，跳过搜索索引重建。")
                    logger.warning("   启动 ES: docker compose up -d elasticsearch")
                    logger.warning("   手动重建: docker compose exec backend celery -A app.tasks.celery_app call app.tasks.search_tasks.reindex_all_tours")
            except Exception as es_err:
                logger.warning(f"⚠️ ES 搜索索引重建失败: {es_err}")
                logger.warning("   可稍后手动重建索引（见上方命令）。")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 种子数据生成失败: {e}")
            raise


def main():
    """同步入口，支持 'python seed_data.py' 直接运行。"""
    asyncio.run(seed())


if __name__ == "__main__":
    main()
