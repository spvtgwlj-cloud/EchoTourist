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
    Enquiry,
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
            "es": {
                "name": "Pekín",
                "description": "La capital de China, una capital antigua con más de 3.000 años de historia, hogar de numerosos sitios Patrimonio Mundial de la UNESCO y atracciones de primer nivel.",
                "meta_title": "Guía de Viaje de Pekín | Echo Tours",
                "meta_description": "Explora la Ciudad Prohibida, la Gran Muralla, el Palacio de Verano y más atracciones de clase mundial en Pekín."
            },
        },
    },
    "nanjing": {
        "slug": "nanjing",
        "area_code": "025",
        "image_url": "/images/destinations/nanjing.svg",
        "translations": {
            "zh": {"name": "南京", "description": "六朝古都，中国东部重要历史文化名城，拥有夫子庙、中山陵等著名景点。", "meta_title": "南京旅游攻略 | Echo Tours", "meta_description": "游六朝古都南京，访中山陵、夫子庙，感受金陵千年文化底蕴。"},
            "en": {"name": "Nanjing", "description": "Ancient capital of six dynasties, a historically and culturally significant city in eastern China.", "meta_title": "Nanjing Travel Guide | Echo Tours", "meta_description": "Visit Nanjing's Sun Yat-sen Mausoleum, Confucius Temple and experience millennia of culture."},
            "es": {
                "name": "Nankín",
                "description": "Capital antigua de seis dinastías, una ciudad histórica y culturalmente significativa en el este de China.",
                "meta_title": "Guía de Viaje de Nankín | Echo Tours",
                "meta_description": "Visita el Mausoleo de Sun Yat-sen, el Templo de Confucio y experimenta milenios de cultura en Nankín."
            },
        },
    },
    "xian": {
        "slug": "xian",
        "area_code": "029",
        "image_url": "/images/destinations/xian.svg",
        "translations": {
            "zh": {"name": "西安", "description": "十三朝古都，世界四大古都之一，以兵马俑和盛唐文化闻名于世。", "meta_title": "西安旅游攻略 | Echo Tours", "meta_description": "参观世界第八大奇迹兵马俑，漫步古城墙，品味盛唐风华。"},
            "en": {"name": "Xi'an", "description": "Ancient capital of 13 dynasties, one of the four great ancient capitals of the world, famous for the Terracotta Warriors.", "meta_title": "Xi'an Travel Guide | Echo Tours", "meta_description": "Visit the Eighth Wonder of the World — Terracotta Warriors, walk the ancient city wall."},
            "es": {
                "name": "Xi'an",
                "description": "Capital antigua de 13 dinastías, una de las cuatro grandes capitales antiguas del mundo, famosa por los Guerreros de Terracota.",
                "meta_title": "Guía de Viaje de Xi'an | Echo Tours",
                "meta_description": "Visita la Octava Maravilla del Mundo — los Guerreros de Terracota, camina por la antigua muralla de la ciudad."
            },
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
        "theme": "culture_history",
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
            "es": {
                "name": "Tour Cultural Profundo por la Ciudad Prohibida",
                "subtitle": "Recorre la Ciudad Púrpura Prohibida, descubre 600 años de secretos imperiales",
                "description": "La Ciudad Prohibida, Patrimonio Mundial de la UNESCO, fue el palacio imperial de 24 emperadores durante las dinastías Ming y Qing. Este tour ofrece una exploración guiada por expertos del Salón de la Suprema Armonía, el Jardín Imperial y la Galería del Tesoro.",
                "meta_title": "Tour Ciudad Prohibida | Echo Tours",
                "meta_description": "Tour guiado en profundidad por la Ciudad Prohibida, explorando el Salón de la Suprema Armonía, el Jardín Imperial y la Galería del Tesoro.",
                "highlights": [
                    "Tour guiado por experto de la Ciudad Prohibida",
                    "Salón de la Suprema Armonía y Jardín Imperial",
                    "Entrada a la Galería del Tesoro incluida",
                    "Acceso rápido sin colas",
                    "Guía bilingüe profesional",
                    "Regalo conmemorativo"
                ],
                "includes": [
                    "Entradas a la Ciudad Prohibida + Galería del Tesoro",
                    "Servicio de guía profesional",
                    "Receptor de auricular inalámbrico",
                    "Regalo de recuerdo",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Gastos personales",
                    "Comidas y bebidas",
                    "Recogida en hotel (disponible como complemento)"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour por la Ciudad Prohibida",
                                        "description": "Mañana: Encuentro en la Puerta del Meridiano → Salón de la Suprema Armonía → Salón de la Armonía Central → Salón de la Preservación de la Armonía\nTarde: Palacio de la Pureza Celestial → Salón de la Unión → Palacio de la Tranquilidad Terrenal → Jardín Imperial → Galería del Tesoro → Salida por la Puerta del Poder Divino"
                    }
                ]
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
        "theme": "adventure",
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
            "es": {
                "name": "Excursión de Senderismo por la Gran Muralla de Badaling",
                "subtitle": "Sube a la Gran Muralla y contempla los magníficos paisajes",
                "description": "Badaling es el tramo más representativo y mejor conservado de la Gran Muralla Ming. Ubicado en el distrito de Yanqing a 1.000 metros de altitud, ofrece vistas impresionantes e instalaciones bien mantenidas. Teleférico de ida y vuelta incluido.",
                "meta_title": "Excursión Gran Muralla Badaling | Echo Tours",
                "meta_description": "Camina por la icónica Gran Muralla de Badaling con teleférico de ida y vuelta y almuerzo estilo pekinés incluido.",
                "highlights": [
                    "Experiencia de senderismo en la Gran Muralla de Badaling",
                    "Oportunidad de fotos en el Paso Juyongguan",
                    "Certificado de héroe de la Gran Muralla",
                    "Viaje en teleférico/tobogán de ida y vuelta",
                    "Almuerzo estilo pekinés incluido"
                ],
                "includes": [
                    "Entrada a la Gran Muralla de Badaling",
                    "Billete de teleférico/tobogán de ida y vuelta",
                    "Servicio de guía profesional",
                    "Almuerzo estilo pekinés",
                    "Certificado de héroe de la Gran Muralla",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Compras personales",
                    "Recogida en hotel (disponible como complemento)",
                    "Bebidas adicionales"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Excursión de un día a la Gran Muralla",
                                        "description": "Mañana: Salida del centro de Pekín → Llegada a Badaling → Subida en teleférico\nTarde: Senderismo por la sección norte → Pendiente del Héroe → Tiempo libre para fotos → Bajada en tobogán → Regreso a Pekín"
                    }
                ]
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
        "theme": "nature",
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
            "es": {
                "name": "Tour Premium por la Gran Muralla de Mutianyu",
                "subtitle": "Evita las multitudes, disfruta de la Gran Muralla con estilo",
                "description": "La Gran Muralla de Mutianyu es una de las secciones mejor conservadas con menos turistas que Badaling. Este tour premium en grupo reducido (máx. 10 pax) incluye un emocionante descenso en tobogán y un almuerzo campestre.",
                "meta_title": "Tour Premium Gran Muralla Mutianyu | Echo Tours",
                "meta_description": "Tour premium en grupo reducido por la Gran Muralla de Mutianyu con teleférico, tobogán y almuerzo campestre.",
                "highlights": [
                    "Gran Muralla de Mutianyu: menos gente, paisajes impresionantes",
                    "Teleférico de ida y vuelta + descenso en tobogán",
                    "Tour premium en grupo reducido (máx. 10 pax)",
                    "Opciones de itinerario personalizables",
                    "Álbum de fotos de recuerdo gratuito"
                ],
                "includes": [
                    "Entrada a la Gran Muralla de Mutianyu",
                    "Teleférico de ida y vuelta + descenso en tobogán",
                    "Servicio exclusivo de guía senior",
                    "Almuerzo campestre",
                    "Álbum de fotos de recuerdo de la Gran Muralla",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Compras personales",
                    "Recogida en hotel (disponible como complemento)"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour Premium Mutianyu",
                                        "description": "Mañana: Recogida en hotel → Llegada a Mutianyu → Subida en teleférico\nTarde: Senderismo por la sección esencial → Exploración de torres de vigilancia → Bajada en tobogán → Regreso a Pekín"
                    }
                ]
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
        "theme": "culture_history",
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
            "es": {
                "name": "Tour Cultural de Medio Día por el Templo del Cielo",
                "subtitle": "Donde los emperadores se comunicaban con el cielo",
                "description": "El Templo del Cielo es el complejo de edificios ceremoniales más grande y mejor conservado de China. Este tour cubre el Salón de la Oración por las Buenas Cosechas, el Muro del Eco y el Altar Circular, ofreciendo una visión de la antigua filosofía china y los rituales imperiales.",
                "meta_title": "Tour Cultural Templo del Cielo | Echo Tours",
                "meta_description": "Explora el Templo del Cielo, el Muro del Eco y el Altar Circular con guía experto.",
                "highlights": [
                    "Salón de la Oración y Altar Circular",
                    "Explicación de la cultura ceremonial imperial",
                    "Antiguas arboledas de cipreses en el parque",
                    "Observación de tai chi de los locales",
                    "Cinta de bendición del templo incluida"
                ],
                "includes": [
                    "Entrada combinada al Templo del Cielo (Salón de Oración + Muro del Eco + Altar Circular)",
                    "Servicio de guía profesional",
                    "Auricular inalámbrico",
                    "Cinta de bendición",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Comidas y bebidas",
                    "Gastos personales",
                    "Recogida en hotel"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour por el Templo del Cielo",
                                        "description": "Mañana: Encuentro en la Puerta Sur → Altar Circular → Muro del Eco → Bóveda Imperial del Cielo\nTarde: Salón de la Oración por las Buenas Cosechas → Puente Danbi → Exploración libre"
                    }
                ]
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
        "theme": "nature",
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
            "es": {
                "name": "Tour por el Palacio de Verano y Jardín Imperial",
                "subtitle": "Pasea por el último jardín imperial de China",
                "description": "El Palacio de Verano es el jardín imperial mejor conservado de China, conocido como el 'Museo de los Jardines Reales'. Este tour incluye un paseo en barco por el lago Kunming, la subida a la Torre del Incienso Budista y un recorrido por el corredor pintado más largo del mundo.",
                "meta_title": "Tour Palacio de Verano | Echo Tours",
                "meta_description": "Explora el magnífico Palacio de Verano con crucero por el lago Kunming y subida a la Torre del Incienso Budista.",
                "highlights": [
                    "Exploración completa del Palacio de Verano",
                    "Paseo en barco por el lago Kunming",
                    "Galería pintada del Corredor Largo",
                    "Subida a la Torre del Incienso Budista",
                    "Punto fotográfico del Puente de los Diecisiete Arcos"
                ],
                "includes": [
                    "Entradas al Palacio de Verano + Torre del Incienso Budista",
                    "Billete de crucero por el lago Kunming",
                    "Servicio de guía profesional",
                    "Auricular inalámbrico",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Comidas y bebidas",
                    "Compras personales",
                    "Recogida en hotel"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour por el Palacio de Verano",
                                        "description": "Mañana: Puerta del Palacio Este → Salón de la Benevolencia → Salón de la Larga Vida Feliz\nTarde: Corredor Largo → Pabellón de las Nubes Dispersas → Torre del Incienso Budista → Barco de Mármol → Crucero por el lago Kunming → Puente de los Diecisiete Arcos"
                    }
                ]
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
        "theme": "citywalk",
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
            "es": {
                "name": "Tour por la Mansión del Príncipe Gong y los Hutongs",
                "subtitle": "Una mansión, la mitad de la historia de la dinastía Qing",
                "description": "La Mansión del Príncipe Gong es la residencia principesca más grande y mejor conservada de la dinastía Qing. Este tour combina una exploración profunda de la mansión con un paseo en rickshaw por los históricos hutongs de Shichahai.",
                "meta_title": "Tour Mansión Príncipe Gong y Hutongs | Echo Tours",
                "meta_description": "Explora la magnífica Mansión del Príncipe Gong y recorre en rickshaw los históricos hutongs de Pekín.",
                "highlights": [
                    "Tour en profundidad de la Mansión del Príncipe Gong",
                    "Fascinante historia de la antigua residencia de Heshen",
                    "Distrito cultural de los hutongs de Shichahai",
                    "Paseo en rickshaw por calles históricas",
                    "Degustación de snacks tradicionales pekineses"
                ],
                "includes": [
                    "Entrada a la Mansión del Príncipe Gong",
                    "Guía chino profesional",
                    "Tour en rickshaw por los hutongs (~30 min)",
                    "Degustación de snacks tradicionales pekineses",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Compras personales",
                    "Coste de comidas completas",
                    "Recogida en hotel"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour Mansión y Hutongs",
                                        "description": "Mañana: Encuentro en la Mansión del Príncipe Gong → Salón de la Paz Plateada → Jardín Trasero → Estela Fuzi\nTarde: Tour en rickshaw por los hutongs → Yandai Xiejie → Campanario y Torre del Tambor"
                    }
                ]
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
        "theme": "photography",
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
            "es": {
                "name": "Tour del Parque Olímpico: Pekín Moderno",
                "subtitle": "De 2008 a 2022, el orgullo de la ciudad dual olímpica",
                "description": "El Parque Olímpico de Pekín albergó tanto los Juegos Olímpicos de Verano de 2008 como los de Invierno de 2022, convirtiendo a Pekín en la primera 'Ciudad Dual Olímpica' del mundo. Visita el icónico Estadio del Nido de Pájaro y el Centro Acuático Cubo de Agua.",
                "meta_title": "Tour Parque Olímpico Pekín | Echo Tours",
                "meta_description": "Visita el Nido de Pájaro y el Cubo de Agua en el icónico Parque Olímpico de Pekín.",
                "highlights": [
                    "Nido de Pájaro (Estadio Nacional)",
                    "Cubo de Agua / Cubo de Hielo",
                    "Torre de observación olímpica",
                    "Sede de los Juegos Olímpicos de Invierno 2022",
                    "Fotografía de arquitectura moderna"
                ],
                "includes": [
                    "Entrada de visita al Nido de Pájaro",
                    "Entrada de visita al Cubo de Agua",
                    "Servicio de guía profesional",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Comidas y bebidas",
                    "Entrada a la Torre Olímpica",
                    "Gastos personales"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour Parque Olímpico",
                                        "description": "Mañana: Encuentro en el Parque Olímpico → Nido de Pájaro (visita interior) → Cubo de Agua (visita interior)\nTarde: Tiempo libre para fotos"
                    }
                ]
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
        "theme": "culture_history",
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
            "es": {
                "name": "Tour Histórico por el Antiguo Palacio de Verano",
                "subtitle": "Descubre la gloria del Jardín de los Jardines",
                "description": "El Antiguo Palacio de Verano, conocido como el 'Jardín de los Jardines', fue un magnífico complejo de jardines imperiales antes de su destrucción en 1860. Visita las ruinas de estilo occidental, el icónico Gran Acueducto y la maqueta panorámica del jardín original.",
                "meta_title": "Tour Antiguo Palacio de Verano | Echo Tours",
                "meta_description": "Explora las ruinas históricas del Antiguo Palacio de Verano, incluyendo los edificios de estilo occidental y el Gran Acueducto.",
                "highlights": [
                    "Ruinas de estilo occidental de Yuanmingyuan",
                    "Icono del Gran Acueducto",
                    "Experiencia de educación histórica",
                    "Visita al Templo Zhengjue",
                    "Maqueta panorámica del jardín original"
                ],
                "includes": [
                    "Entrada al parque del Antiguo Palacio de Verano",
                    "Entrada a la zona de ruinas occidentales",
                    "Servicio de guía profesional",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Comidas y bebidas",
                    "Billete de paseo en barco",
                    "Gastos personales"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour Antiguo Palacio de Verano",
                                        "description": "Mañana: Puerta Sur → Templo Zhengjue → Jardín Qichun → Jardín Changchun\nTarde: Ruinas de estilo occidental (Gran Acueducto, Haiyantang, Xiejiqu) → Exposición de maqueta panorámica"
                    }
                ]
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
        "theme": "culture_history",
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
            "es": {
                "name": "Tour por el Cementerio Real de las Tumbas Ming",
                "subtitle": "Explora los palacios subterráneos de la dinastía Ming",
                "description": "Las Tumbas Ming albergan los lugares de enterramiento de 13 emperadores Ming. Visita Changling (tumba del emperador Yongle) y Dingling (la única tumba excavada con un palacio subterráneo abierto), y recorre el Camino Sagrado flanqueado por estatuas de piedra.",
                "meta_title": "Tour Tumbas Ming | Echo Tours",
                "meta_description": "Visita las Tumbas Ming de Changling y el palacio subterráneo de Dingling, explora la cultura funeraria real de la dinastía Ming.",
                "highlights": [
                    "Changling: tumba del emperador Yongle",
                    "Dingling: único palacio subterráneo abierto",
                    "Avenida de estatuas de piedra del Camino Sagrado",
                    "Réplica de la corona dorada del emperador Wanli",
                    "Historia y cultura de la dinastía Ming"
                ],
                "includes": [
                    "Entradas a Changling + Dingling",
                    "Visita al palacio subterráneo de Dingling",
                    "Servicio de guía profesional",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Comidas y bebidas",
                    "Entrada al Camino Sagrado",
                    "Gastos personales"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Tour Tumbas Ming",
                                        "description": "Mañana: Camino Sagrado (estatuas de piedra) → Changling (Salón Ling'en, Torre Ming)\nTarde: Dingling (tour por el palacio subterráneo) → Exposición de la cultura Ming"
                    }
                ]
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
        "theme": "family",
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
            "es": {
                "name": "Tour Esencial de Pekín en 3 Días",
                "subtitle": "Experimenta lo mejor de Pekín en solo 3 días",
                "description": "Un tour cuidadosamente seleccionado que cubre las 6 principales atracciones de Pekín: Ciudad Prohibida, Templo del Cielo, Palacio de Verano, Gran Muralla de Badaling, Mansión del Príncipe Gong y Parque Olímpico. Incluye alojamiento en hotel de 4 estrellas y auténtica cena de pato laqueado.",
                "meta_title": "Tour Esencial Pekín 3 Días | Echo Tours",
                "meta_description": "Un tour de 3 días que cubre las principales atracciones de Pekín: Ciudad Prohibida, Gran Muralla, Palacio de Verano y Templo del Cielo con hotel de 4 estrellas.",
                "highlights": [
                    "Ciudad Prohibida + Gran Muralla + Palacio de Verano + Templo del Cielo",
                    "Autobús turístico de lujo con aire acondicionado",
                    "Hotel de 4 estrellas con desayuno incluido",
                    "Auténtica cena de pato laqueado y hotpot",
                    "Guía senior durante todo el viaje"
                ],
                "includes": [
                    "Dos noches en hotel de 4 estrellas (con desayuno)",
                    "Todas las entradas a las atracciones listadas",
                    "Servicio de guía profesional a tiempo completo",
                    "Autobús turístico con aire acondicionado",
                    "Comidas según lo listado (Día 1 A/C, Día 2 A/C, Día 3 A)",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Gastos personales",
                    "Suplemento de habitación individual",
                    "Recogida/regreso al hotel",
                    "Actividades opcionales no listadas"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Eje Central Imperial",
                                        "description": "Mañana: Templo del Cielo\nTarde: Ciudad Prohibida → Vista panorámica del Parque Jingshan\nNoche: Mercado nocturno de Wangfujing"
                    },
                    {
                                        "day": 2,
                                        "title": "Jardines Reales y Gran Muralla",
                                        "description": "Mañana: Gran Muralla de Badaling (teleférico)\nTarde: Palacio de Verano (crucero por el lago Kunming)\nNoche: Auténtica cena de pato laqueado"
                    },
                    {
                                        "day": 3,
                                        "title": "Mansión y Olímpicos",
                                        "description": "Mañana: Mansión del Príncipe Gong → Tour por los hutongs de Shichahai\nTarde: Parque Olímpico (Nido de Pájaro y Cubo de Agua) → Fin del tour"
                    }
                ]
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
# ==================================================
# 雍和宫+国子监文化半日游
# ==================================================
{
    "slug": "lama-temple-guozijian",
    "serial_number": "0011",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 49.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "culture_history",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "雍和宫藏传佛教艺术",
        "国子监+孔庙",
        "成贤街历史文化街区",
        "乾隆皇帝御笔碑刻",
        "万福阁26米高弥勒佛"
    ],
    "includes": [
        "雍和宫门票",
        "孔庙+国子监门票",
        "专业导游讲解",
        "无线耳麦",
        "旅游意外险"
    ],
    "excludes": [
        "餐饮费用",
        "个人消费",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "雍和宫+国子监文化半日游",
            "subtitle": "探访北京最完整的藏传佛教寺院与古代最高学府",
            "description": "雍和宫是北京规模最大、保存最完整的藏传佛教寺院，原为雍正皇帝府邸。毗邻的国子监是中国古代最高学府，孔庙则是祭孔圣地。本行程带您领略藏传佛教艺术与儒家文化的交融。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "雍和宫+国子监半日",
                    "description": "上午：雍和宫参观（牌楼/昭泰门/雍和宫殿/万福阁）\n中午：国子监+孔庙（琉璃牌坊/辟雍殿/大成殿/进士碑林）"
                }
            ],
            "meta_title": "雍和宫+国子监文化游 | Echo Tours",
            "meta_description": "深度游览雍和宫藏传佛教寺院与国子监古代最高学府，感受北京历史文化的魅力。"
        },
        "en": {
            "name": "Lama Temple & Imperial College Tour",
            "subtitle": "Explore Beijing finest Tibetan Buddhist temple and ancient imperial academy",
            "description": "The Lama Temple is the largest and best-preserved Tibetan Buddhist monastery in Beijing, originally the residence of Emperor Yongzheng. The Imperial College was the highest educational institution in ancient China. This tour offers a unique blend of Buddhist art and Confucian heritage.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Lama Temple & Imperial College",
                    "description": "Morning: Lama Temple (Memorial Archway/Devaraja Hall/Yonghe Hall/Pavilion of Ten Thousand Happinesses)\nAfternoon: Imperial College & Confucius Temple (Glazed Archway/Pi Yong Hall/Dacheng Hall)"
                }
            ],
            "meta_title": "Lama Temple & Imperial College Tour | Echo Tours",
            "meta_description": "Visit Lama Temple and the ancient Imperial College in this half-day cultural tour."
        },
        "es": {
            "name": "Tour Cultural del Templo de Lama y la Universidad Imperial",
            "subtitle": "Explora el mejor templo budista tibetano de Pekín y la antigua academia imperial",
            "description": "El Templo de Lama es el monasterio budista tibetano más grande y mejor conservado de Pekín, originalmente la residencia del emperador Yongzheng. La Universidad Imperial fue la institución educativa más alta de la China antigua. Este tour ofrece una combinación única de arte budista y herencia confuciana.",
            "meta_title": "Tour Templo de Lama y Universidad Imperial | Echo Tours",
            "meta_description": "Visita el Templo de Lama y la antigua Universidad Imperial en este tour cultural de medio día.",
            "highlights": [
                "Arte budista tibetano del Templo de Lama",
                "Universidad Imperial y Templo de Confucio",
                "Distrito histórico de la calle Chengxian",
                "Estela grabada del emperador Qianlong",
                "Buda Maitreya de 26 m en el Pabellón Wanfu"
            ],
            "includes": [
                "Entrada al Templo de Lama",
                "Entrada al Templo de Confucio + Universidad Imperial",
                "Servicio de guía profesional",
                "Auricular inalámbrico",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Comidas y bebidas",
                "Gastos personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Templo de Lama y Universidad Imperial",
                                "description": "Mañana: Templo de Lama (Arco Memorial/Sala Devaraja/Sala Yonghe/Pabellón de las Diez Mil Felicidades)\nTarde: Universidad Imperial y Templo de Confucio (Arco de Vidrio/Sala Pi Yong/Sala Dacheng)"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/lama-temple-1.svg",
            "alt_text": "雍和宫万福阁",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 3,
            "price": 49,
            "availability": 20
        },
        {
            "start_date_offset": 10,
            "price": 49,
            "availability": 25
        },
        {
            "start_date_offset": 17,
            "price": 49,
            "availability": 22
        },
        {
            "start_date_offset": 31,
            "price": 49,
            "availability": 18
        }
    ]
}
,
# ==================================================
# 中国国家博物馆探宝之旅
# ==================================================
{
    "slug": "national-museum-tour",
    "serial_number": "0012",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 25,
    "min_pax": 2,
    "start_price": 39.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "culture_history",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "中国古代青铜器精品",
        "国家博物馆特展",
        "天安门广场游览",
        "后母戊鼎等国宝文物",
        "五千年文明史全景"
    ],
    "includes": [
        "国家博物馆免费预约（代操作）",
        "专业导游讲解",
        "无线耳麦",
        "旅游意外险"
    ],
    "excludes": [
        "特展门票（如有）",
        "餐饮费用",
        "个人消费"
    ],
    "translations": {
        "zh": {
            "name": "中国国家博物馆探宝之旅",
            "subtitle": "一日看尽中华五千年",
            "description": "中国国家博物馆位于天安门广场东侧，是世界最大的博物馆之一，藏品逾140万件。从远古石器到近现代文物，完整呈现中华五千年文明史。行程将重点讲解古代中国展厅的国宝级文物。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "国家博物馆半日",
                    "description": "上午：天安门广场集合 → 国家博物馆（古代中国展厅/青铜器/陶俑/玉器）\n中午：自由参观或特展区"
                }
            ],
            "meta_title": "国家博物馆探宝之旅 | Echo Tours",
            "meta_description": "参观中国国家博物馆，欣赏从远古到明清的国宝级文物，一日看尽中华五千年。"
        },
        "en": {
            "name": "National Museum Treasure Tour",
            "subtitle": "5000 years of Chinese civilization in one day",
            "description": "The National Museum of China, located on Tiananmen Square, is one of the world largest museums with over 1.4 million artifacts. This tour focuses on the ancient China gallery most treasured pieces.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "National Museum Tour",
                    "description": "Morning: Tiananmen Square -> National Museum (Ancient China gallery: bronzes/pottery/jade/figurines)\nAfternoon: Free exploration or special exhibitions"
                }
            ],
            "meta_title": "National Museum Tour | Echo Tours",
            "meta_description": "Visit the National Museum of China on Tiananmen Square to explore 5000 years of Chinese civilization."
        },
        "es": {
            "name": "Tour del Tesoro del Museo Nacional",
            "subtitle": "5000 años de civilización china en un día",
            "description": "El Museo Nacional de China, ubicado en la Plaza de Tiananmen, es uno de los museos más grandes del mundo con más de 1,4 millones de artefactos. Este tour se centra en las piezas más valiosas de la galería de la China antigua.",
            "meta_title": "Tour Museo Nacional | Echo Tours",
            "meta_description": "Visita el Museo Nacional de China en la Plaza de Tiananmen para explorar 5000 años de civilización china.",
            "highlights": [
                "Obras maestras de bronce de la antigua China",
                "Exposiciones especiales del Museo Nacional",
                "Visita a la Plaza de Tiananmen",
                "Tesoros nacionales como el caldero Houmuwu",
                "Panorama de 5000 años de civilización"
            ],
            "includes": [
                "Reserva gratuita del Museo Nacional (gestionada por nosotros)",
                "Servicio de guía profesional",
                "Auricular inalámbrico",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Entradas a exposiciones especiales (si las hay)",
                "Comidas y bebidas",
                "Gastos personales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Museo Nacional",
                                "description": "Mañana: Plaza de Tiananmen → Museo Nacional (Galería de la China antigua: bronces/cerámica/jade/figurillas)\nTarde: Exploración libre o exposiciones especiales"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/national-museum-1.svg",
            "alt_text": "国家博物馆外观",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 2,
            "price": 39,
            "availability": 25
        },
        {
            "start_date_offset": 9,
            "price": 39,
            "availability": 30
        },
        {
            "start_date_offset": 16,
            "price": 49,
            "availability": 28
        },
        {
            "start_date_offset": 30,
            "price": 39,
            "availability": 25
        }
    ]
}
,
# ==================================================
# 景山+北海皇城全景摄影半日游
# ==================================================
{
    "slug": "jingshan-beihai-view",
    "serial_number": "0013",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 35.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "photography",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "景山万春亭俯瞰故宫全景",
        "北海公园白塔+琼岛春阴",
        "中轴线最佳摄影点",
        "北海划船体验（可选）",
        "拍摄故宫日落全景"
    ],
    "includes": [
        "景山公园门票",
        "北海公园门票",
        "专业导游讲解",
        "旅游意外险"
    ],
    "excludes": [
        "划船费用",
        "餐饮费用",
        "个人消费"
    ],
    "translations": {
        "zh": {
            "name": "景山+北海皇城全景摄影半日游",
            "subtitle": "北京中轴线上的最佳观景台",
            "description": "景山公园位于北京中轴线上，万春亭是俯瞰故宫全景的最佳地点。北海公园是中国现存最古老的皇家园林之一，白塔与琼岛春阴相映成趣。本行程特别适合摄影爱好者，可拍到故宫全景与中轴线日落。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "景山+北海摄影游",
                    "description": "上午：景山公园登山 → 万春亭俯瞰故宫全景 → 中轴线摄影\n中午：北海公园（琼华岛/白塔/九龙壁）→ 湖边自由活动"
                }
            ],
            "meta_title": "景山+北海皇城全景摄影游 | Echo Tours",
            "meta_description": "登景山万春亭俯瞰故宫全景，游北海公园赏白塔，北京中轴线摄影之旅。"
        },
        "en": {
            "name": "Jingshan & Beihai Panoramic Photography Tour",
            "subtitle": "Best viewpoints along Beijing central axis",
            "description": "Jingshan Park sits on Beijing central axis, with Wanchun Pavilion offering the best panoramic view of the Forbidden City. Beihai Park is one of China oldest imperial gardens. Perfect for photography enthusiasts.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Jingshan & Beihai Tour",
                    "description": "Morning: Jingshan Park climb -> Wanchun Pavilion -> Forbidden City panorama -> Central axis photography\nAfternoon: Beihai Park (Qiong Island/White Pagoda/Nine-Dragon Screen) -> Free lakeside time"
                }
            ],
            "meta_title": "Jingshan Beihai Photography Tour | Echo Tours",
            "meta_description": "Climb Jingshan Park for panoramic Forbidden City views and explore ancient Beihai Park."
        },
        "es": {
            "name": "Tour Fotográfico Panorámico de Jingshan y Beihai",
            "subtitle": "Los mejores miradores del eje central de Pekín",
            "description": "El Parque Jingshan se asienta sobre el eje central de Pekín, con el Pabellón Wanchun ofreciendo la mejor vista panorámica de la Ciudad Prohibida. El Parque Beihai es uno de los jardines imperiales más antiguos de China. Perfecto para entusiastas de la fotografía.",
            "meta_title": "Tour Fotográfico Jingshan y Beihai | Echo Tours",
            "meta_description": "Sube al Parque Jingshan para vistas panorámicas de la Ciudad Prohibida y explora el antiguo Parque Beihai.",
            "highlights": [
                "Pabellón Wanchun con vistas a la Ciudad Prohibida",
                "Pagoda Blanca del Parque Beihai y Primavera de la Isla Qiong",
                "Mejores puntos de fotografía del eje central",
                "Paseo opcional en barca por el lago Beihai",
                "Fotos del atardecer sobre la Ciudad Prohibida"
            ],
            "includes": [
                "Entrada al Parque Jingshan",
                "Entrada al Parque Beihai",
                "Servicio de guía profesional",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Tarifa de paseo en barca",
                "Comidas y bebidas",
                "Gastos personales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Jingshan y Beihai",
                                "description": "Mañana: Subida al Parque Jingshan → Pabellón Wanchun → Panorámica de la Ciudad Prohibida → Fotografía del eje central\nTarde: Parque Beihai (Isla Qiong/Pagoda Blanca/Pantalla de los Nueve Dragones) → Tiempo libre junto al lago"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/jingshan-1.svg",
            "alt_text": "景山俯瞰故宫",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 4,
            "price": 35,
            "availability": 20
        },
        {
            "start_date_offset": 11,
            "price": 35,
            "availability": 25
        },
        {
            "start_date_offset": 18,
            "price": 35,
            "availability": 22
        }
    ]
}
,
# ==================================================
# 簋街美食探秘夜游
# ==================================================
{
    "slug": "ghost-street-food-night",
    "serial_number": "0014",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 15,
    "min_pax": 2,
    "start_price": 59.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "food",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "簋街麻辣小龙虾",
        "花家怡园四合院晚餐",
        "老北京特色小吃品尝",
        "东直门内大街夜市探访",
        "胡大饭馆等网红店打卡"
    ],
    "includes": [
        "簋街特色晚餐（含饮品）",
        "5道老北京小吃品尝",
        "在地美食向导陪同",
        "旅游意外险"
    ],
    "excludes": [
        "额外点餐/酒水",
        "个人消费",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "簋街美食探秘夜游",
            "subtitle": "吃遍京城最火爆的美食街",
            "description": "簋街是北京最著名的不夜美食街，全长1.5公里汇集上百家餐厅。从麻辣小龙虾到老北京炸酱面，从四川火锅到东北烧烤，这里能满足你对美食的所有想象。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "簋街美食之夜",
                    "description": "傍晚：东直门集合 -> 簋街美食漫步\n晚上：胡大饭馆（小龙虾）-> 老北京小吃体验 -> 花家怡园四合院晚餐 -> 甜品收尾"
                }
            ],
            "meta_title": "簋街美食夜游 | Echo Tours",
            "meta_description": "漫步北京最著名的美食街簋街，品尝麻辣小龙虾、老北京小吃等特色美食。"
        },
        "en": {
            "name": "Ghost Street Food Night Tour",
            "subtitle": "Feast at Beijing most famous food street",
            "description": "Ghost Street (Guijie) is Beijing most famous food street, stretching 1.5 km with hundreds of restaurants. From spicy crayfish to traditional Beijing noodles, this evening tour takes you on a culinary journey.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Ghost Street Food Night",
                    "description": "Late afternoon: Meet at Dongzhimen -> Ghost Street food walk\nEvening: Hu Da Restaurant (crayfish) -> Beijing snack tasting -> Hua Family Yiyuan courtyard dinner"
                }
            ],
            "meta_title": "Ghost Street Food Tour | Echo Tours",
            "meta_description": "Explore Beijing famous Ghost Street food scene with crayfish, Beijing snacks and a courtyard dinner."
        },
        "es": {
            "name": "Tour Nocturno Gastronómico por la Calle Fantasma",
            "subtitle": "Banquete en la calle de comida más famosa de Pekín",
            "description": "La Calle Fantasma (Guijie) es la calle de comida más famosa de Pekín, con 1,5 km de largo y cientos de restaurantes. Desde cangrejos de río picantes hasta fideos tradicionales pekineses, este tour nocturno te lleva a un viaje culinario.",
            "meta_title": "Tour Gastronómico Calle Fantasma | Echo Tours",
            "meta_description": "Explora la famosa Calle Fantasma de Pekín con cangrejos de río, snacks pekineses y cena en un patio tradicional.",
            "highlights": [
                "Cangrejos de río picantes de la Calle Fantasma",
                "Cena en el patio de Hua Family Yiyuan",
                "Degustación de snacks tradicionales pekineses",
                "Exploración del mercado nocturno de Dongzhimen",
                "Visita al famoso restaurante Hu Da"
            ],
            "includes": [
                "Cena especial en la Calle Fantasma (con bebidas)",
                "5 tipos de snacks tradicionales pekineses",
                "Acompañante guía gastronómico local",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Pedidos/bebidas adicionales",
                "Gastos personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Noche Gastronómica Calle Fantasma",
                                "description": "Atardecer: Encuentro en Dongzhimen → Paseo gastronómico por la Calle Fantasma\nNoche: Restaurante Hu Da (cangrejos de río) → Degustación de snacks pekineses → Cena en el patio de Hua Family Yiyuan"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/ghost-street-1.svg",
            "alt_text": "簋街美食",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 5,
            "price": 59,
            "availability": 12
        },
        {
            "start_date_offset": 12,
            "price": 59,
            "availability": 15
        },
        {
            "start_date_offset": 19,
            "price": 69,
            "availability": 14
        },
        {
            "start_date_offset": 26,
            "price": 59,
            "availability": 18
        },
        {
            "start_date_offset": 40,
            "price": 69,
            "availability": 16
        }
    ]
}
,
# ==================================================
# 前门大栅栏京味美食文化游
# ==================================================
{
    "slug": "qianmen-dazhalan-food",
    "serial_number": "0015",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 15,
    "min_pax": 2,
    "start_price": 55.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "food",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "全聚德烤鸭起源店体验",
        "大栅栏老字号美食街",
        "北京炸酱面+豆汁儿挑战",
        "前门大街铛铛车体验",
        "百年老店瑞蚨祥/同仁堂"
    ],
    "includes": [
        "全聚德烤鸭品尝套餐",
        "3道老北京小吃",
        "美食向导陪同讲解",
        "旅游意外险"
    ],
    "excludes": [
        "额外点餐",
        "个人购物",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "前门大栅栏京味美食文化游",
            "subtitle": "品百年老字号，尝地道北京味儿",
            "description": "前门大街和大栅栏是北京最具历史底蕴的商业街区，聚集了全聚德烤鸭、东来顺涮肉等众多百年老字号。本行程不仅带您品尝最正宗的北京美食，还将探访这些老字号背后的历史故事。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "前门美食文化游",
                    "description": "上午：前门大街 -> 全聚德起源店（烤鸭品尝）\n中午：大栅栏老字号探访（瑞蚨祥/同仁堂/内联升）-> 老北京小吃集锦（炸酱面/豆汁/焦圈/豌豆黄）"
                }
            ],
            "meta_title": "前门大栅栏美食文化游 | Echo Tours",
            "meta_description": "品尝全聚德烤鸭等京城老字号美食，探访前门大栅栏的历史文化。"
        },
        "en": {
            "name": "Qianmen Dazhalan Food & Culture Tour",
            "subtitle": "Century-old brands and authentic Beijing flavors",
            "description": "Qianmen Avenue and Dazhalan are Beijing most historic commercial districts, home to century-old establishments like Quanjude Peking Duck. This tour combines authentic food tasting with stories of the city merchant history.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Qianmen Food & Culture",
                    "description": "Morning: Qianmen Avenue -> Quanjude original restaurant (Peking Duck tasting)\nAfternoon: Dazhalan old brands (Ruifuxiang/Tongrentang/Neiliansheng) -> Beijing snack collection"
                }
            ],
            "meta_title": "Qianmen Food & Culture Tour | Echo Tours",
            "meta_description": "Taste authentic Peking Duck and explore century-old shops in Beijing historic Qianmen district."
        },
        "es": {
            "name": "Tour Gastronómico y Cultural de Qianmen Dazhalan",
            "subtitle": "Marcas centenarias y auténticos sabores de Pekín",
            "description": "La Avenida Qianmen y Dazhalan son los distritos comerciales más históricos de Pekín, hogar de establecimientos centenarios como Quanjude Peking Duck. Este tour combina degustación de comida auténtica con historias de la historia mercantil de la ciudad.",
            "meta_title": "Tour Gastronómico Qianmen | Echo Tours",
            "meta_description": "Degusta auténtico pato laqueado y explora tiendas centenarias en el histórico distrito de Qianmen en Pekín.",
            "highlights": [
                "Restaurante original de pato laqueado Quanjude",
                "Calle gastronómica de marcas antiguas de Dazhalan",
                "Desafío de fideos zhajiangmian y douzhi",
                "Experiencia en tranvía de la Avenida Qianmen",
                "Tiendas centenarias Ruifuxiang/Tongrentang"
            ],
            "includes": [
                "Set de degustación de pato laqueado Quanjude",
                "3 tipos de snacks tradicionales pekineses",
                "Comentarios de guía gastronómico",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Pedidos adicionales",
                "Compras personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Gastronomía y Cultura Qianmen",
                                "description": "Mañana: Avenida Qianmen → Restaurante original Quanjude (degustación de pato laqueado)\nTarde: Marcas antiguas de Dazhalan (Ruifuxiang/Tongrentang/Neiliansheng) → Colección de snacks pekineses"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/qianmen-1.svg",
            "alt_text": "前门大街",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 6,
            "price": 55,
            "availability": 15
        },
        {
            "start_date_offset": 13,
            "price": 55,
            "availability": 18
        },
        {
            "start_date_offset": 20,
            "price": 65,
            "availability": 16
        },
        {
            "start_date_offset": 34,
            "price": 55,
            "availability": 20
        }
    ]
}
,
# ==================================================
# 南锣鼓巷+什刹海胡同深度游
# ==================================================
{
    "slug": "nanluoguxiang-hutong-deep",
    "serial_number": "0016",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 15,
    "min_pax": 2,
    "start_price": 45.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "citywalk",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "南锣鼓巷老北京风情",
        "四合院入内参观+下午茶",
        "齐白石旧居纪念馆",
        "后海日落漫步",
        "烟袋斜街+钟鼓楼"
    ],
    "includes": [
        "四合院参观+下午茶费用",
        "齐白石纪念馆门票",
        "在地向导讲解",
        "旅游意外险"
    ],
    "excludes": [
        "南锣鼓巷个人购物",
        "餐饮费用",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "南锣鼓巷+什刹海胡同深度游",
            "subtitle": "钻进老北京的胡同里弄，感受最地道的京城生活",
            "description": "南锣鼓巷是北京最古老的街区之一，至今已有700多年历史。周边遍布蜈蚣巷般的胡同和保存完好的四合院。本行程将带您深入探索胡同文化，参观传统四合院并享用茶点，最后漫步什刹海看日落。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "胡同深度游",
                    "description": "上午：南锣鼓巷 -> 齐白石旧居 -> 帽儿胡同（文煜宅/可园）\n中午：四合院参观+传统茶点\n下午：烟袋斜街 -> 钟鼓楼 -> 什刹海日落漫步"
                }
            ],
            "meta_title": "南锣鼓巷+什刹海胡同游 | Echo Tours",
            "meta_description": "深入南锣鼓巷和什刹海胡同区，参观传统四合院，体验最地道的老北京生活。"
        },
        "en": {
            "name": "Nanluoguxiang & Shichahai Hutong Deep Tour",
            "subtitle": "Dive into old Beijing alleyways for an authentic local experience",
            "description": "Nanluoguxiang is one of Beijing oldest neighborhoods with over 700 years of history, surrounded by hutong alleyways and traditional courtyard homes. This tour includes a visit inside a traditional siheyuan courtyard home.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Deep Hutong Tour",
                    "description": "Morning: Nanluoguxiang -> Qi Baishi Former Residence -> Maoer Hutong\nAfternoon: Courtyard home visit with traditional tea -> Yandai Xiejie -> Bell & Drum Towers -> Shichahai sunset walk"
                }
            ],
            "meta_title": "Nanluoguxiang Hutong Tour | Echo Tours",
            "meta_description": "Explore Beijing historic hutong alleys with a courtyard home visit, tea experience and Shichahai sunset walk."
        },
        "es": {
            "name": "Tour Profundo por los Hutongs de Nanluoguxiang y Shichahai",
            "subtitle": "Sumérgete en los callejones del viejo Pekín para una experiencia local auténtica",
            "description": "Nanluoguxiang es uno de los barrios más antiguos de Pekín con más de 700 años de historia, rodeado de callejones hutong y casas tradicionales con patio. Este tour incluye una visita al interior de una casa tradicional siheyuan.",
            "meta_title": "Tour Hutongs Nanluoguxiang | Echo Tours",
            "meta_description": "Explora los históricos callejones hutong de Pekín con visita a una casa con patio, experiencia de té y paseo al atardecer por Shichahai.",
            "highlights": [
                "Ambiente del viejo Pekín en Nanluoguxiang",
                "Visita a casa con patio con té",
                "Museo de la Antigua Residencia de Qi Baishi",
                "Paseo al atardecer por Houhai",
                "Yandai Xiejie y Campanario"
            ],
            "includes": [
                "Visita al patio + tarifa de té de la tarde",
                "Entrada al Memorial Hall de Qi Baishi",
                "Comentarios de guía local",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Compras personales en Nanluoguxiang",
                "Comidas y bebidas",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Profundo por los Hutongs",
                                "description": "Mañana: Nanluoguxiang → Antigua Residencia de Qi Baishi → Maoer Hutong\nTarde: Visita a casa con patio con té tradicional → Yandai Xiejie → Campanario y Torre del Tambor → Paseo al atardecer por Shichahai"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/nanluoguxiang-1.svg",
            "alt_text": "南锣鼓巷胡同",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 5,
            "price": 45,
            "availability": 15
        },
        {
            "start_date_offset": 12,
            "price": 45,
            "availability": 18
        },
        {
            "start_date_offset": 19,
            "price": 55,
            "availability": 16
        },
        {
            "start_date_offset": 33,
            "price": 45,
            "availability": 20
        }
    ]
}
,
# ==================================================
# 798艺术区文艺半日游
# ==================================================
{
    "slug": "798-art-district-tour",
    "serial_number": "0017",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 39.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "hidden_gems",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "798艺术区画廊群",
        "UCCA尤伦斯当代艺术中心",
        "751D·PARK时尚设计广场",
        "工业遗产建筑群拍照",
        "网红咖啡馆打卡"
    ],
    "includes": [
        "UCCA当日展览门票",
        "专业艺术向导讲解",
        "旅行意外险"
    ],
    "excludes": [
        "餐饮费用",
        "个人艺术品购买",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "798艺术区文艺半日游",
            "subtitle": "在北京最潮的艺术区感受创意与灵感",
            "description": "798艺术区是由旧电子工厂改造而成的当代艺术聚集区，包豪斯风格的厂房如今变身为画廊、设计工作室和时尚店铺。参观UCCA尤伦斯当代艺术中心，感受北京最前卫的艺术氛围。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "798艺术区半日",
                    "description": "上午：798艺术区漫步 -> 包豪斯工业建筑群参观\n中午：UCCA尤伦斯当代艺术中心（当前展览）-> 751D·PARK -> 艺术书店+咖啡馆自由活动"
                }
            ],
            "meta_title": "798艺术区文艺游 | Echo Tours",
            "meta_description": "漫步北京798艺术区，参观UCCA尤伦斯当代艺术中心，感受前卫艺术与工业遗产的碰撞。"
        },
        "en": {
            "name": "798 Art District Half-Day Tour",
            "subtitle": "Contemporary art meets industrial heritage in Beijing coolest district",
            "description": "The 798 Art District is a contemporary art hub converted from old factory buildings. Bauhaus-style industrial architecture now houses galleries, design studios and trendy shops. Visit UCCA Center for Contemporary Art.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "798 Art District Tour",
                    "description": "Morning: 798 district walk -> Bauhaus industrial architecture tour\nAfternoon: UCCA Center for Contemporary Art -> 751 D·PARK -> Art bookstore & cafe free time"
                }
            ],
            "meta_title": "798 Art District Tour | Echo Tours",
            "meta_description": "Explore Beijing 798 Art District with UCCA gallery visit, Bauhaus architecture and trendy cafes."
        },
        "es": {
            "name": "Tour de Medio Día por el Distrito de Arte 798",
            "subtitle": "El arte contemporáneo se encuentra con la herencia industrial en el distrito más moderno de Pekín",
            "description": "El Distrito de Arte 798 es un centro de arte contemporáneo convertido a partir de antiguas fábricas. La arquitectura industrial de estilo Bauhaus ahora alberga galerías, estudios de diseño y tiendas de moda. Visita el Centro UCCA de Arte Contemporáneo.",
            "meta_title": "Tour Distrito de Arte 798 | Echo Tours",
            "meta_description": "Explora el Distrito de Arte 798 de Pekín con visita a la galería UCCA, arquitectura Bauhaus y cafeterías de moda.",
            "highlights": [
                "Paseo por las galerías del Distrito de Arte 798",
                "Centro UCCA de Arte Contemporáneo",
                "Plaza de Diseño de Moda 751 D·PARK",
                "Fotografía de arquitectura de patrimonio industrial",
                "Visita a cafeterías de moda"
            ],
            "includes": [
                "Entrada a la exposición actual de UCCA",
                "Servicio de guía de arte profesional",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Comidas y bebidas",
                "Compras de arte personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Distrito de Arte 798",
                                "description": "Mañana: Paseo por el distrito 798 → Tour de arquitectura industrial Bauhaus\nTarde: Centro UCCA de Arte Contemporáneo → 751 D·PARK → Librería de arte y tiempo libre en cafetería"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/798-art-1.svg",
            "alt_text": "798艺术区",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 7,
            "price": 39,
            "availability": 20
        },
        {
            "start_date_offset": 14,
            "price": 39,
            "availability": 25
        },
        {
            "start_date_offset": 21,
            "price": 49,
            "availability": 22
        },
        {
            "start_date_offset": 35,
            "price": 39,
            "availability": 20
        }
    ]
}
,
# ==================================================
# 法源寺+天宁寺古刹探幽
# ==================================================
{
    "slug": "ancient-temples-peace",
    "serial_number": "0018",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 15,
    "min_pax": 2,
    "start_price": 35.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "hidden_gems",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "法源寺（北京最古老寺庙之一）",
        "天宁寺塔（辽代密檐砖塔）",
        "法源寺丁香花（春季限定）",
        "北京城内静谧之地",
        "寺庙素斋体验（可选）"
    ],
    "includes": [
        "法源寺门票",
        "天宁寺门票",
        "向导讲解",
        "旅游意外险"
    ],
    "excludes": [
        "素斋费用（可选）",
        "个人消费",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "法源寺+天宁寺古刹探幽",
            "subtitle": "寻访京城最古老的寺庙，感受千年宁静",
            "description": "法源寺建于唐代，是北京最古老的佛教寺院之一，以丁香花闻名。天宁寺塔是北京现存最古老的辽代建筑之一，千年古塔见证京城变迁。本行程带您避开热门景点的人潮，在古寺中寻找内心的宁静。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "古刹探幽半日",
                    "description": "上午：法源寺参观（大雄宝殿/悯忠台/丁香园）\n中午：天宁寺塔 -> 千年古塔摄影 -> 可选购寺庙素斋体验"
                }
            ],
            "meta_title": "法源寺+天宁寺古刹游 | Echo Tours",
            "meta_description": "寻访北京最古老的法源寺和天宁寺塔，在千年古刹中感受宁静与历史。"
        },
        "en": {
            "name": "Ancient Temples Peace Tour",
            "subtitle": "Discover Beijing oldest temples and find inner peace",
            "description": "Fayuan Temple, built in the Tang dynasty, is one of Beijing oldest Buddhist temples. Tianning Temple Pagoda is the oldest surviving Liao dynasty structure in Beijing. A peaceful escape from crowded tourist attractions.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Ancient Temples Tour",
                    "description": "Morning: Fayuan Temple (Great Hall/Minzhong Terrace/Lilac Garden)\nAfternoon: Tianning Temple Pagoda -> Photography -> Optional temple vegetarian lunch"
                }
            ],
            "meta_title": "Ancient Temples Tour | Echo Tours",
            "meta_description": "Visit Beijing oldest temples - Fayuan Temple and Tianning Temple Pagoda for a peaceful cultural experience."
        },
        "es": {
            "name": "Tour de Paz por los Templos Antiguos",
            "subtitle": "Descubre los templos más antiguos de Pekín y encuentra la paz interior",
            "description": "El Templo Fayuan, construido en la dinastía Tang, es uno de los templos budistas más antiguos de Pekín. La Pagoda del Templo Tianning es la estructura más antigua de la dinastía Liao que sobrevive en Pekín. Un escape pacífico de las atracciones turísticas masificadas.",
            "meta_title": "Tour Templos Antiguos | Echo Tours",
            "meta_description": "Visita los templos más antiguos de Pekín: el Templo Fayuan y la Pagoda del Templo Tianning para una experiencia cultural de paz.",
            "highlights": [
                "Templo Fayuan (uno de los más antiguos de Pekín)",
                "Pagoda del Templo Tianning (dinastía Liao)",
                "Flores de lila del Templo Fayuan (primavera)",
                "Escape pacífico en la ciudad",
                "Comida vegetariana opcional en el templo"
            ],
            "includes": [
                "Entrada al Templo Fayuan",
                "Entrada al Templo Tianning",
                "Servicio de guía",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Comida vegetariana (opcional)",
                "Gastos personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Templos Antiguos",
                                "description": "Mañana: Templo Fayuan (Gran Salón/Terrazas Minzhong/Jardín de Lila)\nTarde: Pagoda del Templo Tianning → Fotografía → Almuerzo vegetariano opcional en el templo"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/ancient-temples-1.svg",
            "alt_text": "法源寺",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 8,
            "price": 35,
            "availability": 15
        },
        {
            "start_date_offset": 15,
            "price": 35,
            "availability": 18
        },
        {
            "start_date_offset": 22,
            "price": 35,
            "availability": 16
        }
    ]
}
,
# ==================================================
# 司马台长城+古北水镇一日游
# ==================================================
{
    "slug": "simatai-gubei-water-town",
    "serial_number": "0019",
    "type": "group_tour",
    "status": "published",
    "duration_days": 1,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 159.0,
    "currency": "USD",
    "difficulty": "moderate",
    "theme": "adventure",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "司马台长城（唯一保留明代原貌）",
        "古北水镇江南水乡风情",
        "夜游司马台长城（夏季限定）",
        "水镇温泉体验（可选）",
        "鸳鸯湖水库美景"
    ],
    "includes": [
        "司马台长城门票",
        "古北水镇门票",
        "往返交通大巴",
        "专业导游服务",
        "旅游意外险"
    ],
    "excludes": [
        "索道/游船费用",
        "温泉费用",
        "餐饮费用",
        "个人消费"
    ],
    "translations": {
        "zh": {
            "name": "司马台长城+古北水镇一日游",
            "subtitle": "登保留明代原貌的野长城，游北方水镇",
            "description": "司马台长城是唯一保留明代原貌的长城段落，以险峻著称，1987年被列入世界文化遗产。山下的古北水镇仿江南水乡而建，小桥流水、青砖黛瓦，是京郊最受欢迎的度假目的地。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "司马台+古北水镇",
                    "description": "上午：市区出发 -> 抵达司马台长城 -> 乘索道上山 -> 登城游览\n中午：古北水镇午餐\n下午：水镇漫步（司马小烧/染坊/镖局）-> 自由活动 -> 返回市区"
                }
            ],
            "meta_title": "司马台长城+古北水镇一日游 | Echo Tours",
            "meta_description": "登保留原貌的司马台长城，游古北水镇江南风情，一日体验长城与水乡的双重魅力。"
        },
        "en": {
            "name": "Simatai Great Wall & Gubei Water Town",
            "subtitle": "Climb the original Ming Great Wall and explore a northern water town",
            "description": "Simatai Great Wall is the only section that retains its original Ming dynasty appearance. Gubei Water Town is a charming replica of a Jiangnan-style water town, offering a perfect blend of adventure and relaxation.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Simatai & Water Town",
                    "description": "Morning: Depart Beijing -> Arrive at Simatai -> Cable car up -> Great Wall hike\nAfternoon: Lunch at Gubei Water Town -> Explore water town -> Return to Beijing"
                }
            ],
            "meta_title": "Simatai Great Wall & Gubei Water Town | Echo Tours",
            "meta_description": "Climb the original Ming dynasty Simatai Great Wall and explore the charming Gubei Water Town."
        },
        "es": {
            "name": "Gran Muralla de Simatai y Ciudad Acuática de Gubei",
            "subtitle": "Sube a la Gran Muralla Ming original y explora una ciudad acuática del norte",
            "description": "La Gran Muralla de Simatai es la única sección que conserva su apariencia original de la dinastía Ming. La Ciudad Acuática de Gubei es una encantadora réplica de una ciudad acuática de estilo Jiangnan, que ofrece una combinación perfecta de aventura y relax.",
            "meta_title": "Tour Simatai y Gubei | Echo Tours",
            "meta_description": "Sube a la original Gran Muralla Ming de Simatai y explora la encantadora Ciudad Acuática de Gubei.",
            "highlights": [
                "Gran Muralla de Simatai (apariencia Ming original)",
                "Encanto Jiangnan de la Ciudad Acuática de Gubei",
                "Tour nocturno de Simatai (solo verano)",
                "Experiencia opcional de aguas termales",
                "Paisaje del embalse Yuanyang"
            ],
            "includes": [
                "Entrada a la Gran Muralla de Simatai",
                "Entrada a la Ciudad Acuática de Gubei",
                "Transporte en autobús de ida y vuelta",
                "Servicio de guía profesional",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Tarifas de teleférico/barco",
                "Tarifa de aguas termales",
                "Comidas y bebidas",
                "Gastos personales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Simatai y Ciudad Acuática",
                                "description": "Mañana: Salida de Pekín → Llegada a Simatai → Subida en teleférico → Senderismo por la Gran Muralla\nTarde: Almuerzo en la Ciudad Acuática de Gubei → Exploración de la ciudad → Regreso a Pekín"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/simatai-1.svg",
            "alt_text": "司马台长城",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 10,
            "price": 159,
            "availability": 15
        },
        {
            "start_date_offset": 24,
            "price": 179,
            "availability": 18
        },
        {
            "start_date_offset": 38,
            "price": 159,
            "availability": 12
        },
        {
            "start_date_offset": 55,
            "price": 189,
            "availability": 20
        }
    ]
}
,
# ==================================================
# 香山公园+北京植物园自然之旅
# ==================================================
{
    "slug": "fragrant-hills-botanical",
    "serial_number": "0020",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 45.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "nature",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "香山红叶（秋日限定美景）",
        "碧云寺五百罗汉堂",
        "北京植物园热带温室",
        "樱桃沟水杉林",
        "香炉峰登顶俯瞰京城"
    ],
    "includes": [
        "香山公园门票",
        "植物园门票",
        "专业导游讲解",
        "旅游意外险"
    ],
    "excludes": [
        "索道费用",
        "餐饮费用",
        "个人消费"
    ],
    "translations": {
        "zh": {
            "name": "香山公园+北京植物园自然之旅",
            "subtitle": "京城西郊的绿色明珠",
            "description": "香山公园是北京西郊著名的皇家山林公园，以秋日红叶闻名天下。毗邻的北京植物园收集了全球各地的珍稀植物。本行程带您感受北京的自然之美。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "香山+植物园",
                    "description": "上午：香山公园（静翠湖/双清别墅/香炉峰）-> 碧云寺\n中午：北京植物园（热带温室/牡丹园/樱桃沟水杉林）"
                }
            ],
            "meta_title": "香山公园+植物园游 | Echo Tours",
            "meta_description": "游览香山公园与北京植物园，赏红叶（秋季）、观珍稀植物，感受北京西郊的自然之美。"
        },
        "en": {
            "name": "Fragrant Hills & Botanical Garden Nature Tour",
            "subtitle": "Beijing western hills green paradise",
            "description": "Fragrant Hills Park is Beijing most famous mountain park, renowned for its autumn red leaves. The Beijing Botanical Garden houses rare plants from around the world. This nature tour offers seasonal beauty throughout the year.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Fragrant Hills & Botanical Garden",
                    "description": "Morning: Fragrant Hills Park (Jingcui Lake/Shuangqing Villa/Incense Burner Peak) -> Biyun Temple\nAfternoon: Beijing Botanical Garden (Tropical greenhouse/Peony Garden/Cherry Brook metasequoia forest)"
                }
            ],
            "meta_title": "Fragrant Hills & Botanical Garden Tour | Echo Tours",
            "meta_description": "Visit Fragrant Hills Park and Beijing Botanical Garden for a nature escape in Beijing western hills."
        },
        "es": {
            "name": "Tour Naturalista de las Colinas Fragantes y el Jardín Botánico",
            "subtitle": "El paraíso verde de las colinas occidentales de Pekín",
            "description": "El Parque de las Colinas Fragantes es el parque de montaña más famoso de Pekín, renombrado por sus hojas rojas otoñales. El Jardín Botánico de Pekín alberga plantas raras de todo el mundo. Este tour naturalista ofrece belleza estacional durante todo el año.",
            "meta_title": "Tour Colinas Fragantes y Jardín Botánico | Echo Tours",
            "meta_description": "Visita el Parque de las Colinas Fragantes y el Jardín Botánico de Pekín para una escapada natural en las colinas occidentales.",
            "highlights": [
                "Hojas rojas de las Colinas Fragantes (otoño)",
                "Sala de los 500 Arhats del Templo Biyun",
                "Invernadero tropical del Jardín Botánico de Pekín",
                "Bosque de metasecuoyas del Arroyo Cereza",
                "Panorámica de la ciudad desde el Pico del Incensario"
            ],
            "includes": [
                "Entrada al Parque de las Colinas Fragantes",
                "Entrada al Jardín Botánico",
                "Servicio de guía profesional",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Tarifa de teleférico",
                "Comidas y bebidas",
                "Gastos personales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Colinas Fragantes y Jardín Botánico",
                                "description": "Mañana: Parque de las Colinas Fragantes (Lago Jingcui/Villa Shuangqing/Pico del Incensario) → Templo Biyun\nTarde: Jardín Botánico de Pekín (Invernadero tropical/Jardín de Peonías/Bosque de metasecuoyas del Arroyo Cereza)"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/fragrant-hills-1.svg",
            "alt_text": "香山红叶",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 5,
            "price": 45,
            "availability": 20
        },
        {
            "start_date_offset": 12,
            "price": 45,
            "availability": 25
        },
        {
            "start_date_offset": 19,
            "price": 55,
            "availability": 22
        },
        {
            "start_date_offset": 40,
            "price": 45,
            "availability": 18
        }
    ]
}
,
# ==================================================
# 北京高端私人定制一日游
# ==================================================
{
    "slug": "beijing-luxury-private-day",
    "serial_number": "0021",
    "type": "private_tour",
    "status": "published",
    "duration_days": 1,
    "duration_nights": 0,
    "max_pax": 6,
    "min_pax": 1,
    "start_price": 399.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "luxury",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "私人豪华专车全程接送",
        "资深金牌导游专属服务",
        "精选高端餐厅午餐",
        "可定制专属行程",
        "赠送精美旅行相册"
    ],
    "includes": [
        "私家车全程服务（奔驰/别克GL8）",
        "金牌导游专属陪同",
        "精选高端午餐（含酒水）",
        "景点门票全含",
        "矿泉水+湿巾",
        "旅行意外险"
    ],
    "excludes": [
        "个人购物",
        "额外餐费",
        "小费（自愿）"
    ],
    "translations": {
        "zh": {
            "name": "北京高端私人定制一日游",
            "subtitle": "尊享专属座驾与金牌导游的奢华体验",
            "description": "本行程为追求高品质旅行体验的客人设计。由奔驰专车全程接送，金牌导游专属服务。行程完全根据您的兴趣定制——无论是故宫深度游、长城探险，还是美食探访、艺术之旅，一切由您决定。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "高端定制日",
                    "description": "全天：专车上门接送 -> 根据客人需求量身定制行程\n可选方向：故宫深度/长城之旅/美食体验/艺术文化\n午餐：精选高端餐厅\n下午：继续定制行程 -> 送回酒店"
                }
            ],
            "meta_title": "北京高端定制一日游 | Echo Tours",
            "meta_description": "尊享私人奔驰专车与金牌导游，按您的需求量身定制北京一日奢华体验。"
        },
        "en": {
            "name": "Beijing Luxury Private Day Tour",
            "subtitle": "Premium car, top guide, and a fully customizable itinerary",
            "description": "Designed for travelers seeking the highest quality experience. Includes a private Mercedes vehicle, a top-rated guide, and a fully customizable itinerary. Choose your focus - Forbidden City, Great Wall, food or art.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Luxury Private Day",
                    "description": "Full day: Door-to-door pickup in luxury vehicle -> Custom itinerary based on your interests\nLunch: Handpicked fine dining restaurant\nAfternoon: Continue custom itinerary -> Drop-off at hotel"
                }
            ],
            "meta_title": "Beijing Luxury Private Tour | Echo Tours",
            "meta_description": "Experience Beijing in luxury with a private Mercedes vehicle, top-rated guide and fully customizable itinerary."
        },
        "es": {
            "name": "Tour Privado de Lujo por Pekín en un Día",
            "subtitle": "Coche premium, guía estrella y un itinerario totalmente personalizable",
            "description": "Diseñado para viajeros que buscan la experiencia de máxima calidad. Incluye un vehículo Mercedes privado, un guía de primera categoría y un itinerario totalmente personalizable. Elige tu enfoque: Ciudad Prohibida, Gran Muralla, gastronomía o arte.",
            "meta_title": "Tour Privado de Lujo Pekín | Echo Tours",
            "meta_description": "Experimenta Pekín con lujo: vehículo Mercedes privado, guía de primera categoría e itinerario totalmente personalizable.",
            "highlights": [
                "Coche privado de lujo con conductor",
                "Servicio exclusivo de guía senior premium",
                "Almuerzo seleccionado de alta cocina",
                "Itinerario totalmente personalizable",
                "Álbum de fotos de recuerdo de cortesía"
            ],
            "includes": [
                "Servicio de coche privado (Mercedes/Buick GL8)",
                "Acompañamiento exclusivo de guía premium",
                "Almuerzo seleccionado (con bebidas)",
                "Todas las entradas a atracciones incluidas",
                "Agua embotellada + toallitas",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Compras personales",
                "Costes de comidas adicionales",
                "Propinas (voluntarias)"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Día Privado de Lujo",
                                "description": "Día completo: Recogida puerta a puerta en vehículo de lujo → Itinerario personalizado según tus intereses\nAlmuerzo: Restaurante de alta cocina seleccionado\nTarde: Continuación del itinerario personalizado → Regreso al hotel"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/luxury-1.svg",
            "alt_text": "豪华专车",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 3,
            "price": 399,
            "availability": 4
        },
        {
            "start_date_offset": 10,
            "price": 449,
            "availability": 3
        },
        {
            "start_date_offset": 17,
            "price": 399,
            "availability": 5
        },
        {
            "start_date_offset": 24,
            "price": 449,
            "availability": 4
        }
    ]
}
,
# ==================================================
# 北京太极养生文化体验
# ==================================================
{
    "slug": "beijing-wellness-tai-chi",
    "serial_number": "0022",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 12,
    "min_pax": 2,
    "start_price": 55.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "wellness",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "天坛公园晨练太极体验",
        "太极拳名师亲授",
        "中医养生文化讲座",
        "老北京茶馆品茶",
        "八段锦/五禽戏体验"
    ],
    "includes": [
        "太极课程（约1小时）",
        "中医养生讲座",
        "茶馆品茶费用",
        "中文太极拳服装（赠送）",
        "专业翻译陪同",
        "旅游意外险"
    ],
    "excludes": [
        "餐饮费用",
        "个人消费",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "北京太极养生文化体验",
            "subtitle": "在天坛晨练太极，品味中医养生智慧",
            "description": "清晨的天坛公园是北京当地人晨练的场所。本行程由太极拳名师带领，在天坛古柏下学习太极基础招式，感受身心合一的美妙。之后前往老北京茶馆品茶，聆听中医养生讲座。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "太极养生半日",
                    "description": "清晨：天坛公园集合 -> 太极拳名师指导（古柏下晨练）\n上午：天坛游览 -> 中医养生讲座\n中午：老北京茶馆品茶 -> 结束"
                }
            ],
            "meta_title": "北京太极养生文化体验 | Echo Tours",
            "meta_description": "在天坛公园跟随名师学习太极拳，体验中医养生智慧和老北京茶文化。"
        },
        "en": {
            "name": "Beijing Tai Chi Wellness Experience",
            "subtitle": "Morning tai chi at the Temple of Heaven, followed by tea and wellness wisdom",
            "description": "Start your day with an authentic tai chi session led by a master instructor at the Temple of Heaven park. Learn fundamental movements amidst ancient cypress trees, then relax at a traditional tea house with a Chinese wellness lecture.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Wellness Half-Day",
                    "description": "Early morning: Meet at Temple of Heaven -> Tai chi master class (under ancient cypress trees)\nLate morning: Temple of Heaven tour -> Chinese wellness lecture\nMidday: Traditional tea house experience -> Tour ends"
                }
            ],
            "meta_title": "Beijing Tai Chi Wellness Tour | Echo Tours",
            "meta_description": "Learn tai chi at the Temple of Heaven with a master instructor, enjoy tea and discover Chinese wellness traditions."
        },
        "es": {
            "name": "Experiencia de Bienestar con Tai Chi en Pekín",
            "subtitle": "Tai chi matutino en el Templo del Cielo, seguido de té y sabiduría de bienestar",
            "description": "Comienza tu día con una auténtica sesión de tai chi dirigida por un instructor maestro en el parque del Templo del Cielo. Aprende movimientos fundamentales entre antiguos cipreses, luego relájate en una casa de té tradicional con una charla sobre bienestar chino.",
            "meta_title": "Experiencia Tai Chi Pekín | Echo Tours",
            "meta_description": "Aprende tai chi en el Templo del Cielo con un instructor maestro, disfruta del té y descubre las tradiciones de bienestar chinas.",
            "highlights": [
                "Clase magistral de tai chi en el Templo del Cielo",
                "Charla sobre cultura de bienestar chino",
                "Experiencia en casa de té tradicional pekinesa",
                "Práctica de Ba Duan Jin / Wu Qin Xi",
                "Rutina matutina local auténtica"
            ],
            "includes": [
                "Clase de tai chi (~1 hora)",
                "Charla de bienestar chino",
                "Tarifa de té en casa de té",
                "Vestimenta de tai chi (cortesía)",
                "Acompañante intérprete profesional",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Comidas y bebidas",
                "Gastos personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Medio Día de Bienestar",
                                "description": "Madrugada: Encuentro en el Templo del Cielo → Clase magistral de tai chi (bajo antiguos cipreses)\nMedia mañana: Tour por el Templo del Cielo → Charla de bienestar chino\nMediodía: Experiencia en casa de té tradicional → Fin del tour"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/wellness-1.svg",
            "alt_text": "天坛太极",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 5,
            "price": 55,
            "availability": 10
        },
        {
            "start_date_offset": 12,
            "price": 55,
            "availability": 12
        },
        {
            "start_date_offset": 19,
            "price": 65,
            "availability": 10
        },
        {
            "start_date_offset": 33,
            "price": 55,
            "availability": 14
        }
    ]
}
,
# ==================================================
# 北京浪漫情侣一日游
# ==================================================
{
    "slug": "beijing-romantic-couples",
    "serial_number": "0023",
    "type": "private_tour",
    "status": "published",
    "duration_days": 1,
    "duration_nights": 0,
    "max_pax": 2,
    "min_pax": 2,
    "start_price": 149.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "honeymoon",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "什刹海日落手摇船",
        "鼓楼大街浪漫漫步",
        "后海酒吧街烛光晚餐",
        "南锣鼓巷甜蜜时光",
        "专属情侣摄影服务"
    ],
    "includes": [
        "什刹海手摇船（日落时段）",
        "情侣烛光晚餐（含红酒）",
        "专属情侣跟拍（电子版）",
        "旅行意外险"
    ],
    "excludes": [
        "其他餐饮费用",
        "个人购物",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "北京浪漫情侣一日游",
            "subtitle": "在古都北京，写下属于你们的浪漫故事",
            "description": "为情侣量身打造的浪漫之旅。下午漫步南锣鼓巷，傍晚乘坐手摇船欣赏什刹海日落，晚上在后海酒吧街享用烛光晚餐。全程配备专属跟拍。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "浪漫情侣日",
                    "description": "下午：南锣鼓巷甜蜜漫步 -> 鼓楼拍照\n傍晚：什刹海手摇船（日落）\n晚上：后海烛光晚餐 -> 自由活动"
                }
            ],
            "meta_title": "北京浪漫情侣一日游 | Echo Tours",
            "meta_description": "在南锣鼓巷漫步，什刹海日落手摇船，后海烛光晚餐——为情侣打造的北京浪漫之旅。"
        },
        "en": {
            "name": "Beijing Romantic Couples Tour",
            "subtitle": "Write your love story in the ancient capital",
            "description": "A specially crafted romantic day for couples. Stroll through Nanluoguxiang charming alleyways, enjoy a sunset rowboat ride on Shichahai Lake, and finish with a candlelit dinner by Houhai. Professional photography included.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Romantic Couples Day",
                    "description": "Afternoon: Nanluoguxiang stroll -> Drum Tower photos\nSunset: Shichahai rowboat ride\nEvening: Houhai candlelit dinner -> Free evening"
                }
            ],
            "meta_title": "Beijing Romantic Couples Tour | Echo Tours",
            "meta_description": "A romantic day in Beijing with Nanluoguxiang stroll, sunset rowboat on Shichahai and candlelit dinner by Houhai."
        },
        "es": {
            "name": "Tour Romántico para Parejas en Pekín",
            "subtitle": "Escribe tu historia de amor en la capital antigua",
            "description": "Un día romántico especialmente diseñado para parejas. Pasea por los encantadores callejones de Nanluoguxiang, disfruta de un paseo en barca de remos al atardecer en el lago Shichahai y termina con una cena a la luz de las velas junto a Houhai. Fotografía profesional incluida.",
            "meta_title": "Tour Romántico Parejas Pekín | Echo Tours",
            "meta_description": "Un día romántico en Pekín con paseo por Nanluoguxiang, barca al atardecer en Shichahai y cena a la luz de las velas junto a Houhai.",
            "highlights": [
                "Paseo en barca de remos al atardecer en Shichahai",
                "Paseo romántico por la Torre del Tambor",
                "Cena a la luz de las velas en la calle de bares de Houhai",
                "Momentos dulces en Nanluoguxiang",
                "Servicio de fotografía para parejas"
            ],
            "includes": [
                "Barca de remos en Shichahai (horario atardecer)",
                "Cena a la luz de las velas para parejas (con vino)",
                "Sesión de fotos para parejas (copias digitales)",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Otros costes de comidas",
                "Compras personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Día Romántico para Parejas",
                                "description": "Tarde: Paseo por Nanluoguxiang → Fotos en la Torre del Tambor\nAtardecer: Paseo en barca de remos por Shichahai\nNoche: Cena a la luz de las velas en Houhai → Tarde libre"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/romantic-1.svg",
            "alt_text": "什刹海日落",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 7,
            "price": 149,
            "availability": 4
        },
        {
            "start_date_offset": 14,
            "price": 149,
            "availability": 6
        },
        {
            "start_date_offset": 21,
            "price": 179,
            "availability": 4
        },
        {
            "start_date_offset": 28,
            "price": 149,
            "availability": 5
        }
    ]
}
,
# ==================================================
# 北京动物园+天文馆亲子半日游
# ==================================================
{
    "slug": "beijing-family-zoo",
    "serial_number": "0024",
    "type": "group_tour",
    "status": "published",
    "duration_days": 0.5,
    "duration_nights": 0,
    "max_pax": 20,
    "min_pax": 2,
    "start_price": 49.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "family",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "北京动物园大熊猫馆",
        "北京天文馆探索宇宙",
        "海洋馆海豚表演",
        "儿童科普互动体验",
        "亲子专属趣味讲解"
    ],
    "includes": [
        "动物园+熊猫馆门票",
        "天文馆门票",
        "海洋馆门票",
        "亲子向导服务",
        "旅游意外险"
    ],
    "excludes": [
        "餐饮费用",
        "个人购物",
        "酒店接送"
    ],
    "translations": {
        "zh": {
            "name": "北京动物园+天文馆亲子半日游",
            "subtitle": "带宝贝看大熊猫，探索宇宙奥秘",
            "description": "专为亲子家庭设计的半日游。在北京动物园看国宝大熊猫，在北京天文馆探索宇宙的奥秘。趣味讲解配合互动体验，让孩子在游玩中学习知识。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "亲子半日游",
                    "description": "上午：北京动物园（大熊猫馆/猴山/狮虎山/海洋馆）\n中午：北京天文馆（宇宙剧场/天文展览/互动体验）"
                }
            ],
            "meta_title": "北京动物园+天文馆亲子游 | Echo Tours",
            "meta_description": "带孩子在动物园看大熊猫，在天文馆探索宇宙，寓教于乐的北京亲子半日游。"
        },
        "en": {
            "name": "Beijing Zoo & Planetarium Family Tour",
            "subtitle": "Meet giant pandas and explore the universe with your kids",
            "description": "A perfect half-day for families. Visit the giant pandas at Beijing Zoo and explore the wonders of space at the Beijing Planetarium. Fun, educational commentary keeps children engaged throughout.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Family Half-Day Tour",
                    "description": "Morning: Beijing Zoo (Giant Panda Hall/Monkey Hill/Lion & Tiger Mountain/Aquarium)\nLate morning: Beijing Planetarium (Space Theater/Astronomy exhibitions/Interactive experiences)"
                }
            ],
            "meta_title": "Beijing Zoo & Planetarium Family Tour | Echo Tours",
            "meta_description": "A family-friendly tour of Beijing Zoo giant pandas and the Planetarium space exploration exhibits."
        },
        "es": {
            "name": "Tour Familiar del Zoo y Planetario de Pekín",
            "subtitle": "Conoce a los pandas gigantes y explora el universo con tus hijos",
            "description": "Un medio día perfecto para familias. Visita los pandas gigantes del Zoo de Pekín y explora las maravillas del espacio en el Planetario de Pekín. Comentarios divertidos y educativos mantienen a los niños comprometidos durante todo el recorrido.",
            "meta_title": "Tour Familiar Zoo y Planetario | Echo Tours",
            "meta_description": "Un tour familiar por el Zoo de Pekín con pandas gigantes y las exposiciones de exploración espacial del Planetario.",
            "highlights": [
                "Sala del panda gigante del Zoo de Pekín",
                "Exploración espacial en el Planetario de Pekín",
                "Espectáculo de delfines en el Acuario",
                "Experiencia científica interactiva infantil",
                "Comentarios divertidos para toda la familia"
            ],
            "includes": [
                "Entradas al Zoo + Sala del Panda",
                "Entrada al Planetario",
                "Entrada al Acuario",
                "Servicio de guía familiar",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Comidas y bebidas",
                "Compras personales",
                "Recogida en hotel"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Tour Familiar de Medio Día",
                                "description": "Mañana: Zoo de Pekín (Sala del Panda Gigante/Colina de los Monos/Montaña del León y Tigre/Acuario)\nMedia mañana: Planetario de Pekín (Teatro del Espacio/Exposiciones de astronomía/Experiencias interactivas)"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/zoo-1.svg",
            "alt_text": "北京动物园大熊猫",
            "sort_order": 1
        }
    ],
    "dates": [
        {
            "start_date_offset": 4,
            "price": 49,
            "availability": 20
        },
        {
            "start_date_offset": 11,
            "price": 49,
            "availability": 25
        },
        {
            "start_date_offset": 18,
            "price": 59,
            "availability": 22
        },
        {
            "start_date_offset": 25,
            "price": 49,
            "availability": 18
        }
    ]
}
,
# ==================================================
# 北京全景精华五日深度游
# ==================================================
{
    "slug": "beijing-essence-5-day",
    "serial_number": "0025",
    "type": "group_tour",
    "status": "published",
    "duration_days": 5,
    "duration_nights": 4,
    "max_pax": 16,
    "min_pax": 4,
    "start_price": 1499.0,
    "currency": "USD",
    "difficulty": "moderate",
    "theme": "culture_history",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "故宫+长城+颐和园+天坛全覆盖",
        "雍和宫+国子监+恭王府+圆明园",
        "四晚四星级酒店含早餐",
        "正宗北京烤鸭+涮肉+宫廷菜",
        "胡同深度游+四合院体验"
    ],
    "includes": [
        "四晚四星级酒店（含早）",
        "全程所列景点门票",
        "全程专业中文导游",
        "空调旅游大巴",
        "行程所列正餐",
        "旅游意外险"
    ],
    "excludes": [
        "单房差",
        "个人消费",
        "额外酒水"
    ],
    "translations": {
        "zh": {
            "name": "北京全景精华五日深度游",
            "subtitle": "五天时间，全面领略北京的千年古都魅力与现代活力",
            "description": "最全面、最深度的北京之旅。五天时间覆盖北京所有核心景点——从故宫博物院到八达岭长城，从天坛到颐和园，从雍和宫到恭王府。住宿四星级酒店，品尝北京烤鸭、铜锅涮肉和宫廷菜。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "皇城中轴线",
                    "description": "上午：天坛祈年殿+回音壁\n下午：故宫博物院（三大殿+后三宫+珍宝馆）-> 景山公园俯瞰故宫全景\n晚上：王府井夜市"
                },
                {
                    "day": 2,
                    "title": "长城+明十三陵",
                    "description": "上午：八达岭长城（含缆车）\n中午：长城脚下午餐\n下午：明十三陵（定陵地宫）\n晚上：全聚德烤鸭"
                },
                {
                    "day": 3,
                    "title": "皇家园林+古刹",
                    "description": "上午：颐和园（昆明湖游船+长廊+佛香阁）\n下午：圆明园遗址公园\n晚上：东来顺铜锅涮肉"
                },
                {
                    "day": 4,
                    "title": "寺庙+王府+胡同",
                    "description": "上午：雍和宫-> 国子监+孔庙\n中午：恭王府+什刹海\n下午：南锣鼓巷胡同深度游+四合院参观\n晚上：老北京炸酱面"
                },
                {
                    "day": 5,
                    "title": "博物馆+奥运",
                    "description": "上午：中国国家博物馆或天安门广场\n下午：奥林匹克公园（鸟巢+水立方）-> 结束行程"
                }
            ],
            "meta_title": "北京全景5日深度游 | Echo Tours",
            "meta_description": "五天全面游览北京故宫、长城、天坛、颐和园、雍和宫等所有核心景点，含四星级住宿和美食。"
        },
        "en": {
            "name": "Beijing Essence 5-Day In-Depth Tour",
            "subtitle": "Five days to fully experience Beijing ancient charm and modern vitality",
            "description": "The most comprehensive Beijing tour. Cover all major attractions from the Forbidden City to the Great Wall, Temple of Heaven to Summer Palace. Includes 4-star hotel accommodation, Peking Duck dinner, hutong exploration.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Imperial Central Axis",
                    "description": "Morning: Temple of Heaven\nAfternoon: Forbidden City -> Jingshan Park panorama\nEvening: Wangfujing Night Market"
                },
                {
                    "day": 2,
                    "title": "Great Wall & Ming Tombs",
                    "description": "Morning: Badaling Great Wall (cable car)\nAfternoon: Ming Tombs (Dingling underground palace)\nEvening: Quanjude Peking Duck"
                },
                {
                    "day": 3,
                    "title": "Royal Gardens & Ruins",
                    "description": "Morning: Summer Palace (Kunming Lake cruise)\nAfternoon: Old Summer Palace ruins\nEvening: Donglaishun hotpot"
                },
                {
                    "day": 4,
                    "title": "Temples & Hutongs",
                    "description": "Morning: Lama Temple -> Imperial College\nAfternoon: Prince Gong Mansion -> Nanluoguxiang hutong tour\nEvening: Beijing zhajiangmian dinner"
                },
                {
                    "day": 5,
                    "title": "Museum & Olympics",
                    "description": "Morning: National Museum or Tiananmen Square\nAfternoon: Olympic Park (Bird Nest & Water Cube) -> Tour ends"
                }
            ],
            "meta_title": "Beijing 5-Day In-Depth Tour | Echo Tours",
            "meta_description": "A comprehensive 5-day Beijing tour covering all major attractions with 4-star hotel and premium dining."
        },
        "es": {
            "name": "Tour Profundo Esencial de Pekín en 5 Días",
            "subtitle": "Cinco días para experimentar plenamente el encanto antiguo y la vitalidad moderna de Pekín",
            "description": "El tour más completo de Pekín. Cubre todas las atracciones principales desde la Ciudad Prohibida hasta la Gran Muralla, desde el Templo del Cielo hasta el Palacio de Verano. Incluye alojamiento en hotel de 4 estrellas, cena de pato laqueado y exploración de hutongs.",
            "meta_title": "Tour Profundo Pekín 5 Días | Echo Tours",
            "meta_description": "Un tour completo de 5 días por Pekín que cubre todas las atracciones principales con hotel de 4 estrellas y cenas premium.",
            "highlights": [
                "Ciudad Prohibida + Gran Muralla + Palacio de Verano + Templo del Cielo",
                "Templo de Lama + Universidad Imperial + Mansión del Príncipe Gong + Antiguo Palacio de Verano",
                "Cuatro noches en hotel de 4 estrellas con desayuno",
                "Auténtico pato laqueado + Hotpot + Cocina imperial",
                "Tour profundo por hutongs + experiencia en casa con patio"
            ],
            "includes": [
                "Cuatro noches en hotel de 4 estrellas (con desayuno)",
                "Todas las entradas a atracciones listadas",
                "Guía chino profesional a tiempo completo",
                "Autobús turístico con aire acondicionado",
                "Comidas según lo listado",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Suplemento de habitación individual",
                "Gastos personales",
                "Bebidas adicionales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Eje Central Imperial",
                                "description": "Mañana: Templo del Cielo\nTarde: Ciudad Prohibida → Panorámica del Parque Jingshan\nNoche: Mercado nocturno de Wangfujing"
                },
                {
                                "day": 2,
                                "title": "Gran Muralla y Tumbas Ming",
                                "description": "Mañana: Gran Muralla de Badaling (teleférico)\nTarde: Tumbas Ming (palacio subterráneo de Dingling)\nNoche: Pato laqueado Quanjude"
                },
                {
                                "day": 3,
                                "title": "Jardines Reales y Ruinas",
                                "description": "Mañana: Palacio de Verano (crucero por el lago Kunming)\nTarde: Ruinas del Antiguo Palacio de Verano\nNoche: Hotpot Donglaishun"
                },
                {
                                "day": 4,
                                "title": "Templos y Hutongs",
                                "description": "Mañana: Templo de Lama → Universidad Imperial\nTarde: Mansión del Príncipe Gong → Tour por hutongs de Nanluoguxiang\nNoche: Cena de fideos zhajiangmian pekineses"
                },
                {
                                "day": 5,
                                "title": "Museo y Olímpicos",
                                "description": "Mañana: Museo Nacional o Plaza de Tiananmen\nTarde: Parque Olímpico (Nido de Pájaro y Cubo de Agua) → Fin del tour"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/beijing-5day-1.svg",
            "alt_text": "故宫全景",
            "sort_order": 1
        },
        {
            "url": "/images/tours/beijing-5day-2.svg",
            "alt_text": "长城与日落",
            "sort_order": 2
        }
    ],
    "dates": [
        {
            "start_date_offset": 15,
            "price": 1499,
            "availability": 10
        },
        {
            "start_date_offset": 30,
            "price": 1699,
            "availability": 12
        },
        {
            "start_date_offset": 50,
            "price": 1499,
            "availability": 8
        },
        {
            "start_date_offset": 70,
            "price": 1799,
            "availability": 14
        }
    ]
}
,
# ==================================================
# 北京美食探索三日游
# ==================================================
{
    "slug": "beijing-food-3day",
    "serial_number": "0026",
    "type": "group_tour",
    "status": "published",
    "duration_days": 3,
    "duration_nights": 2,
    "max_pax": 14,
    "min_pax": 2,
    "start_price": 599.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "food",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "簋街+前门+王府井三大美食聚集地",
        "全聚德烤鸭+东来顺涮肉+宫廷菜",
        "老北京小吃全方位体验",
        "胡同美食探秘",
        "美食文化讲解"
    ],
    "includes": [
        "两晚三星级酒店（含早）",
        "行程所列全部餐饮",
        "导游美食向导服务",
        "各景点门票",
        "旅游意外险"
    ],
    "excludes": [
        "单房差",
        "个人购物",
        "额外酒水"
    ],
    "translations": {
        "zh": {
            "name": "北京美食探索三日游",
            "subtitle": "舌尖上的北京，一场味蕾的盛宴",
            "description": "为美食爱好者量身打造的北京美食之旅。三天时间吃遍北京最具代表性的美食——从全聚德烤鸭到东来顺涮肉，从簋街夜市到胡同小吃。在品味美食的同时，了解北京饮食文化的千年传承。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "皇城美食初探",
                    "description": "上午：前门大街 -> 全聚德烤鸭起源店\n下午：大栅栏老字号美食探访\n晚上：簋街美食夜市（小龙虾/烧烤）"
                },
                {
                    "day": 2,
                    "title": "宫廷+胡同美食",
                    "description": "上午：天坛游览 -> 天坛附近老北京小吃\n中午：胡同私房菜（四合院餐厅）\n下午：南锣鼓巷美食小吃\n晚上：东来顺铜锅涮肉"
                },
                {
                    "day": 3,
                    "title": "美食文化收官",
                    "description": "上午：王府井小吃街 -> 北京特产采购\n中午：官府菜/宫廷菜体验\n下午：自由活动 -> 结束行程"
                }
            ],
            "meta_title": "北京美食探索3日游 | Echo Tours",
            "meta_description": "三天吃遍北京——全聚德烤鸭、东来顺涮肉、簋街夜市、胡同小吃，一场舌尖上的盛宴。"
        },
        "en": {
            "name": "Beijing Food Explorer 3-Day Tour",
            "subtitle": "A culinary journey through Beijing most iconic flavors",
            "description": "Designed for food lovers, this 3-day tour covers Beijing most iconic culinary experiences - from Quanjude Peking Duck to Donglaishun hotpot, from Ghost Street night market to hidden hutong eateries.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Imperial Cuisine Introduction",
                    "description": "Morning: Qianmen Avenue -> Quanjude original Peking Duck\nAfternoon: Dazhalan old brand food tour\nEvening: Ghost Street night market"
                },
                {
                    "day": 2,
                    "title": "Hutong & Palace Cuisine",
                    "description": "Morning: Temple of Heaven -> Local breakfast\nAfternoon: Hutong private kitchen (courtyard restaurant)\nEvening: Donglaishun hotpot"
                },
                {
                    "day": 3,
                    "title": "Culinary Finale",
                    "description": "Morning: Wangfujing snack street -> Beijing specialty shopping\nAfternoon: Imperial court cuisine lunch -> Tour ends"
                }
            ],
            "meta_title": "Beijing Food Explorer 3-Day Tour | Echo Tours",
            "meta_description": "A 3-day culinary tour of Beijing featuring Peking Duck, hotpot, night markets and hutong food."
        },
        "es": {
            "name": "Tour Explorador Gastronómico de Pekín en 3 Días",
            "subtitle": "Un viaje culinario por los sabores más icónicos de Pekín",
            "description": "Diseñado para amantes de la gastronomía, este tour de 3 días cubre las experiencias culinarias más icónicas de Pekín: desde el pato laqueado Quanjude hasta el hotpot Donglaishun, desde el mercado nocturno de la Calle Fantasma hasta los restaurantes escondidos en los hutongs.",
            "meta_title": "Tour Gastronómico Pekín 3 Días | Echo Tours",
            "meta_description": "Un tour culinario de 3 días por Pekín con pato laqueado, hotpot, mercados nocturnos y comida de hutongs.",
            "highlights": [
                "Calle Fantasma + Qianmen + Wangfujing: tres centros gastronómicos",
                "Pato laqueado Quanjude + Hotpot Donglaishun + Cocina imperial",
                "Experiencia completa de snacks tradicionales pekineses",
                "Exploración gastronómica de hutongs",
                "Comentarios sobre cultura gastronómica"
            ],
            "includes": [
                "Dos noches en hotel de 3 estrellas (con desayuno)",
                "Todas las comidas según lo listado",
                "Servicio de guía y acompañante gastronómico",
                "Todas las entradas a atracciones",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Suplemento de habitación individual",
                "Compras personales",
                "Bebidas adicionales"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Introducción a la Cocina Imperial",
                                "description": "Mañana: Avenida Qianmen → Pato laqueado original Quanjude\nTarde: Tour gastronómico de marcas antiguas de Dazhalan\nNoche: Mercado nocturno de la Calle Fantasma (cangrejos de río/BBQ)"
                },
                {
                                "day": 2,
                                "title": "Cocina de Hutongs y Palacio",
                                "description": "Mañana: Templo del Cielo → Desayuno local\nTarde: Cocina privada en hutong (restaurante con patio)\nNoche: Hotpot Donglaishun"
                },
                {
                                "day": 3,
                                "title": "Final Culinario",
                                "description": "Mañana: Calle de snacks de Wangfujing → Compras de especialidades pekinesas\nTarde: Almuerzo de cocina imperial → Fin del tour"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/food-3day-1.svg",
            "alt_text": "北京烤鸭",
            "sort_order": 1
        },
        {
            "url": "/images/tours/food-3day-2.svg",
            "alt_text": "簋街夜市",
            "sort_order": 2
        }
    ],
    "dates": [
        {
            "start_date_offset": 12,
            "price": 599,
            "availability": 12
        },
        {
            "start_date_offset": 26,
            "price": 649,
            "availability": 14
        },
        {
            "start_date_offset": 45,
            "price": 599,
            "availability": 10
        },
        {
            "start_date_offset": 60,
            "price": 699,
            "availability": 16
        }
    ]
}
,
# ==================================================
# 北京豪华精选四日游
# ==================================================
{
    "slug": "beijing-luxury-4day",
    "serial_number": "0027",
    "type": "private_tour",
    "status": "published",
    "duration_days": 4,
    "duration_nights": 3,
    "max_pax": 6,
    "min_pax": 1,
    "start_price": 1599.0,
    "currency": "USD",
    "difficulty": "easy",
    "theme": "luxury",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "豪华专车全程服务",
        "五星级酒店住宿",
        "金牌导游+专属管家",
        "精选米其林/黑珍珠餐厅",
        "行程完全量身定制"
    ],
    "includes": [
        "三晚五星级酒店（含早）",
        "奔驰专车全程服务",
        "金牌导游全程陪同",
        "每日精选高端餐厅（午+晚）",
        "所有景点VIP通道",
        "旅行意外险"
    ],
    "excludes": [
        "个人购物",
        "国际/国内机票",
        "单房差"
    ],
    "translations": {
        "zh": {
            "name": "北京豪华精选四日游",
            "subtitle": "五星酒店+专车+米其林餐厅，极致北京体验",
            "description": "为追求极致旅行体验的客人打造的豪华之旅。入住五星级酒店，全程奔驰专车接送，金牌导游与专属管家双人服务。精选米其林/黑珍珠餐厅，享受VIP通道免排队游览故宫、长城等景点。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "经典皇城",
                    "description": "VIP通道游览故宫 -> 景山公园\n午餐：米其林餐厅\n下午：天坛 -> 前门大街\n晚餐：黑珍珠餐厅"
                },
                {
                    "day": 2,
                    "title": "长城尊享",
                    "description": "上午：慕田峪长城VIP游览\n午餐：长城脚下精致午餐\n下午：明十三陵（私人讲解）\n晚餐：全聚德烤鸭（包间）"
                },
                {
                    "day": 3,
                    "title": "文化与艺术",
                    "description": "上午：雍和宫+国子监私人导览\n午餐：胡同四合院私房菜\n下午：798艺术区+画廊VIP导览\n晚餐：后海酒吧街"
                },
                {
                    "day": 4,
                    "title": "自由+收官",
                    "description": "上午：自由活动/按需安排\n中午：欢送午餐 -> 送机/送站"
                }
            ],
            "meta_title": "北京豪华四日游 | Echo Tours",
            "meta_description": "五星酒店+奔驰专车+米其林餐饮+VIP通道，极致奢华的北京之旅。"
        },
        "en": {
            "name": "Beijing Luxury Selection 4-Day Tour",
            "subtitle": "5-star hotel, private car, Michelin dining - the ultimate Beijing experience",
            "description": "The ultimate luxury Beijing experience. Stay in 5-star hotels, travel by private Mercedes, enjoy Michelin-starred dining, and skip all lines with VIP access. A personal guide and dedicated concierge ensure every detail is perfect.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Classic Imperial",
                    "description": "VIP Forbidden City tour -> Jingshan Park\nLunch: Michelin restaurant\nAfternoon: Temple of Heaven -> Qianmen\nDinner: Black Pearl restaurant"
                },
                {
                    "day": 2,
                    "title": "Great Wall Premium",
                    "description": "Morning: Mutianyu Great Wall VIP visit\nAfternoon: Ming Tombs private tour\nDinner: Quanjude Peking Duck (private room)"
                },
                {
                    "day": 3,
                    "title": "Culture & Art",
                    "description": "Morning: Lama Temple + Imperial College private tour\nAfternoon: 798 Art District VIP gallery tour\nEvening: Houhai cocktail bar"
                },
                {
                    "day": 4,
                    "title": "Departure",
                    "description": "Morning: Free time / On-demand arrangement\nAfternoon: Farewell lunch -> Airport/train station transfer"
                }
            ],
            "meta_title": "Beijing Luxury 4-Day Tour | Echo Tours",
            "meta_description": "5-star hotel, Mercedes transport, Michelin dining and VIP access - Beijing ultimate luxury experience."
        },
        "es": {
            "name": "Tour Selección de Lujo de Pekín en 4 Días",
            "subtitle": "Hotel 5 estrellas, coche privado, cenas Michelin: la experiencia definitiva en Pekín",
            "description": "La experiencia de lujo definitiva en Pekín. Alójate en hoteles de 5 estrellas, viaja en Mercedes privado, disfruta de cenas con estrella Michelin y salta todas las colas con acceso VIP. Un guía personal y un conserje dedicado aseguran que cada detalle sea perfecto.",
            "meta_title": "Tour de Lujo Pekín 4 Días | Echo Tours",
            "meta_description": "Hotel 5 estrellas, transporte Mercedes, cenas Michelin y acceso VIP: la experiencia de lujo definitiva en Pekín.",
            "highlights": [
                "Coche privado de lujo durante todo el recorrido",
                "Alojamiento en hotel de 5 estrellas",
                "Guía premium + conserje dedicado",
                "Restaurantes seleccionados Michelin/Black Pearl",
                "Itinerario totalmente personalizable"
            ],
            "includes": [
                "Tres noches en hotel de 5 estrellas (con desayuno)",
                "Mercedes privado durante todo el recorrido",
                "Acompañamiento de guía premium a tiempo completo",
                "Comidas seleccionadas diarias (A+C)",
                "Acceso VIP rápido en todas las atracciones",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Compras personales",
                "Vuelos nacionales/internacionales",
                "Suplemento de habitación individual"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Imperio Clásico",
                                "description": "Tour VIP por la Ciudad Prohibida → Parque Jingshan\nAlmuerzo: Restaurante Michelin\nTarde: Templo del Cielo → Qianmen\nCena: Restaurante Black Pearl"
                },
                {
                                "day": 2,
                                "title": "Gran Muralla Premium",
                                "description": "Mañana: Visita VIP a la Gran Muralla de Mutianyu\nTarde: Tour privado por las Tumbas Ming\nCena: Pato laqueado Quanjude (salón privado)"
                },
                {
                                "day": 3,
                                "title": "Cultura y Arte",
                                "description": "Mañana: Tour privado del Templo de Lama + Universidad Imperial\nTarde: Tour VIP por galerías del Distrito de Arte 798\nNoche: Bar de cócteles en Houhai"
                },
                {
                                "day": 4,
                                "title": "Salida",
                                "description": "Mañana: Tiempo libre / Actividad bajo demanda\nTarde: Almuerzo de despedida → Traslado al aeropuerto/estación"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/luxury-4day-1.svg",
            "alt_text": "五星级酒店",
            "sort_order": 1
        },
        {
            "url": "/images/tours/luxury-4day-2.svg",
            "alt_text": "米其林餐厅",
            "sort_order": 2
        }
    ],
    "dates": [
        {
            "start_date_offset": 20,
            "price": 1599,
            "availability": 4
        },
        {
            "start_date_offset": 40,
            "price": 1899,
            "availability": 3
        },
        {
            "start_date_offset": 60,
            "price": 1699,
            "availability": 5
        }
    ]
}
,
# ==================================================
# 北京摄影采风四日游
# ==================================================
{
    "slug": "beijing-photography-4day",
    "serial_number": "0028",
    "type": "group_tour",
    "status": "published",
    "duration_days": 4,
    "duration_nights": 3,
    "max_pax": 10,
    "min_pax": 2,
    "start_price": 899.0,
    "currency": "USD",
    "difficulty": "moderate",
    "theme": "photography",
    "destination_slugs": [
        "beijing"
    ],
    "highlights": [
        "故宫+长城+天坛+颐和园全摄影覆盖",
        "景山日出与故宫全景",
        "长城日落拍摄",
        "什刹海夜景与胡同人文",
        "专业摄影向导全程指导"
    ],
    "includes": [
        "三晚三星级酒店（含早）",
        "景点门票（含特殊时段拍摄许可）",
        "专业摄影向导全程陪同",
        "空调旅游大巴",
        "行程所列正餐",
        "旅游意外险"
    ],
    "excludes": [
        "个人摄影器材",
        "额外门票",
        "单房差"
    ],
    "translations": {
        "zh": {
            "name": "北京摄影采风四日游",
            "subtitle": "用镜头捕捉古都北京的四季之美",
            "description": "专为摄影爱好者设计的采风之旅。从景山公园的故宫日出全景到长城的日落余晖，从天坛的对称之美到什刹海的人文生活。行程涵盖北京最具摄影价值的景点，由专业摄影向导指导构图与拍摄技巧。",
            "itinerary": [
                {
                    "day": 1,
                    "title": "皇城建筑摄影",
                    "description": "清晨：景山公园拍故宫日出全景\n上午：故宫建筑细节摄影（金瓦红墙/飞檐斗拱）\n下午：天坛祈年殿对称构图\n傍晚：前门大街夜景"
                },
                {
                    "day": 2,
                    "title": "长城+陵寝摄影",
                    "description": "清晨：出发前往八达岭长城\n上午：长城全景+敌楼特写\n中午：农家午餐\n下午：明十三陵神道石像\n傍晚：长城日落拍摄"
                },
                {
                    "day": 3,
                    "title": "园林+人文摄影",
                    "description": "清晨：颐和园昆明湖晨雾\n上午：佛香阁+长廊构图\n下午：圆明园西洋楼残垣\n傍晚：什刹海胡同人文"
                },
                {
                    "day": 4,
                    "title": "现代+收官",
                    "description": "清晨：雍和宫晨光+香客\n上午：798艺术区工业风+街头艺术\n下午：奥林匹克公园现代建筑\n傍晚：结束行程"
                }
            ],
            "meta_title": "北京摄影采风4日游 | Echo Tours",
            "meta_description": "专业摄影之旅：故宫日出、长城日落、天坛对称、胡同人文——用镜头记录北京的美。"
        },
        "en": {
            "name": "Beijing Photography 4-Day Tour",
            "subtitle": "Capture Beijing beauty through your lens across four seasons",
            "description": "Designed for photography enthusiasts, this tour covers Beijing most photogenic spots. From Forbidden City sunrise at Jingshan Park to Great Wall sunset, from Temple of Heaven symmetry to hutong street life. Professional photography guide provides composition tips.",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Imperial Architecture",
                    "description": "Sunrise: Jingshan Park for Forbidden City panorama\nMorning: Forbidden City architectural details\nAfternoon: Temple of Heaven symmetry shots\nEvening: Qianmen night photography"
                },
                {
                    "day": 2,
                    "title": "Great Wall & Tombs",
                    "description": "Morning: Badaling Great Wall panoramic views\nAfternoon: Ming Tombs Sacred Way stone statues\nSunset: Great Wall golden hour photography"
                },
                {
                    "day": 3,
                    "title": "Gardens & Humanity",
                    "description": "Sunrise: Summer Palace morning mist\nMorning: Long Corridor composition\nAfternoon: Old Summer Palace ruins\nEvening: Shichahai hutong street photography"
                },
                {
                    "day": 4,
                    "title": "Modern Beijing",
                    "description": "Morning: Lama Temple morning light\nLate morning: 798 Art District industrial style\nAfternoon: Olympic Park modern architecture\nEvening: Tour ends"
                }
            ],
            "meta_title": "Beijing Photography 4-Day Tour | Echo Tours",
            "meta_description": "A photography-focused tour of Beijing capturing Forbidden City, Great Wall, Temple of Heaven and hutong life."
        },
        "es": {
            "name": "Tour Fotográfico de Pekín en 4 Días",
            "subtitle": "Captura la belleza de Pekín a través de tu objetivo en las cuatro estaciones",
            "description": "Diseñado para entusiastas de la fotografía, este tour cubre los lugares más fotogénicos de Pekín. Desde el amanecer sobre la Ciudad Prohibida en el Parque Jingshan hasta el atardecer en la Gran Muralla, desde la simetría del Templo del Cielo hasta la vida callejera de los hutongs. Un guía fotográfico profesional ofrece consejos de composición.",
            "meta_title": "Tour Fotográfico Pekín 4 Días | Echo Tours",
            "meta_description": "Un tour enfocado en fotografía que captura la Ciudad Prohibida, la Gran Muralla, el Templo del Cielo y la vida en los hutongs de Pekín.",
            "highlights": [
                "Cobertura completa: Ciudad Prohibida + Gran Muralla + Templo del Cielo + Palacio de Verano",
                "Amanecer en Jingshan y panorama de la Ciudad Prohibida",
                "Fotografía del atardecer en la Gran Muralla",
                "Escenas nocturnas de Shichahai y cultura de hutongs",
                "Guía fotográfico profesional durante todo el recorrido"
            ],
            "includes": [
                "Tres noches en hotel de 3 estrellas (con desayuno)",
                "Entradas a atracciones (incl. horarios especiales)",
                "Guía fotográfico profesional",
                "Autobús turístico con aire acondicionado",
                "Comidas según lo listado",
                "Seguro de accidentes de viaje"
            ],
            "excludes": [
                "Equipo fotográfico personal",
                "Entradas adicionales",
                "Suplemento de habitación individual"
            ],
            "itinerary": [
                {
                                "day": 1,
                                "title": "Arquitectura Imperial",
                                "description": "Amanecer: Parque Jingshan para panorama de la Ciudad Prohibida\nMañana: Detalles arquitectónicos de la Ciudad Prohibida\nTarde: Fotos de simetría del Templo del Cielo\nNoche: Fotografía nocturna de Qianmen"
                },
                {
                                "day": 2,
                                "title": "Gran Muralla y Tumbas",
                                "description": "Mañana: Vistas panorámicas de la Gran Muralla de Badaling\nTarde: Estatuas de piedra del Camino Sagrado de las Tumbas Ming\nAtardecer: Fotografía de la hora dorada en la Gran Muralla"
                },
                {
                                "day": 3,
                                "title": "Jardines y Humanidad",
                                "description": "Amanecer: Niebla matutina en el Palacio de Verano\nMañana: Composición del Corredor Largo\nTarde: Ruinas del Antiguo Palacio de Verano\nNoche: Fotografía callejera en hutongs de Shichahai"
                },
                {
                                "day": 4,
                                "title": "Pekín Moderno",
                                "description": "Mañana: Luz matutina en el Templo de Lama\nMedia mañana: Estilo industrial del Distrito de Arte 798\nTarde: Arquitectura moderna del Parque Olímpico\nNoche: Fin del tour"
                }
            ]
        },
    },
    "images": [
        {
            "url": "/images/tours/photo-4day-1.svg",
            "alt_text": "景山拍故宫全景",
            "sort_order": 1
        },
        {
            "url": "/images/tours/photo-4day-2.svg",
            "alt_text": "长城摄影",
            "sort_order": 2
        }
    ],
    "dates": [
        {
            "start_date_offset": 18,
            "price": 899,
            "availability": 8
        },
        {
            "start_date_offset": 35,
            "price": 999,
            "availability": 10
        },
        {
            "start_date_offset": 55,
            "price": 899,
            "availability": 6
        },
        {
            "start_date_offset": 75,
            "price": 1099,
            "availability": 12
        }
    ]
}
,
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
        "theme": "culture_history",
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
            "es": {
                "name": "Tour Esencial Histórico de Nankín en 2 Días",
                "subtitle": "Inmersión profunda en la antigua capital de seis dinastías",
                "description": "Nankín, una de las cuatro grandes capitales antiguas de China, cuenta con más de 6.000 años de civilización. Este tour cubre el Mausoleo del Dr. Sun Yat-sen, el Mausoleo Ming Xiaoling, el Templo de Confucio y el Río Qinhuai.",
                "meta_title": "Tour Histórico Nankín 2 Días | Echo Tours",
                "meta_description": "Un tour de 2 días por los lugares históricos de Nankín: Mausoleo de Sun Yat-sen, Tumbas Ming y Templo de Confucio.",
                "highlights": [
                    "Mausoleo del Dr. Sun Yat-sen",
                    "Templo de Confucio y paisaje del Río Qinhuai",
                    "Mausoleo Ming Xiaoling (Patrimonio UNESCO)",
                    "Museo de Nankín",
                    "Degustación de pato salado de Nankín"
                ],
                "includes": [
                    "Todas las entradas a atracciones listadas",
                    "1 noche en hotel de 3 estrellas",
                    "Servicio de guía profesional",
                    "Comidas según lo listado",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Gastos personales",
                    "Suplemento de habitación individual",
                    "Transporte de ida y vuelta"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Área Escénica de Zhongshan",
                                        "description": "Mañana: Mausoleo de Sun Yat-sen\nTarde: Mausoleo Ming Xiaoling\nNoche: Crucero nocturno por el Río Qinhuai"
                    },
                    {
                                        "day": 2,
                                        "title": "Museo y Lago Xuanwu",
                                        "description": "Mañana: Museo de Nankín\nTarde: Parque del Lago Xuanwu → Fin del tour"
                    }
                ]
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
        "theme": "food",
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
            "es": {
                "name": "Tour de los Guerreros de Terracota de Xi'an en 2 Días",
                "subtitle": "Viaje a través de las dinastías Zhou, Qin, Han y Tang",
                "description": "Xi'an, una de las cuatro grandes capitales antiguas del mundo, fue hogar de 13 dinastías. Visita la Octava Maravilla del Mundo — los Guerreros de Terracota, el Palacio Huaqing, recorre en bicicleta la antigua muralla de la ciudad y explora el Barrio Musulmán.",
                "meta_title": "Tour Guerreros Terracota Xi'an 2 Días | Echo Tours",
                "meta_description": "Un tour de 2 días por Xi'an que cubre los Guerreros de Terracota, la Muralla Antigua y el Barrio Musulmán.",
                "highlights": [
                    "Museo de los Guerreros de Terracota (Octava Maravilla del Mundo)",
                    "Palacio Huaqing: historia de amor del emperador Tang",
                    "Paseo en bicicleta por la Muralla Antigua de Xi'an",
                    "Tour gastronómico por el Barrio Musulmán",
                    "Gran Pagoda del Ganso Salvaje y fuente musical"
                ],
                "includes": [
                    "Entradas a Guerreros de Terracota + Palacio Huaqing",
                    "1 noche en hotel de 3 estrellas con desayuno",
                    "Servicio de guía profesional",
                    "Alquiler de bicicleta en la muralla",
                    "Seguro de accidentes de viaje"
                ],
                "excludes": [
                    "Gastos personales",
                    "Suplemento de habitación individual",
                    "Transporte de ida y vuelta"
                ],
                "itinerary": [
                    {
                                        "day": 1,
                                        "title": "Guerreros de Terracota",
                                        "description": "Mañana: Museo de los Guerreros de Terracota (Fosos 1-3, Carros de Bronce)\nTarde: Palacio Huaqing → Montaña Lishan\nNoche: Plaza de la Gran Pagoda del Ganso Salvaje"
                    },
                    {
                                        "day": 2,
                                        "title": "Muralla y Barrio Musulmán",
                                        "description": "Mañana: Muralla Antigua de Xi'an (en bicicleta)\nTarde: Tour gastronómico por el Barrio Musulmán → Campanario y Torre del Tambor → Fin del tour"
                    }
                ]
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
                "es": {
                    "name": "Ciudad Prohibida",
                    "description": "El palacio imperial de las dinastías Ming y Qing, el complejo de estructuras de madera más grande y mejor conservado del mundo, Patrimonio Mundial de la UNESCO desde 1987."
                },
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
                "es": {
                    "name": "Gran Muralla de Badaling",
                    "description": "El tramo más representativo de la Gran Muralla Ming a 1.000 m de altitud, la sección abierta más temprana y mejor conservada."
                },
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
                "es": {
                    "name": "Templo del Cielo",
                    "description": "El complejo de edificios de sacrificio más grande y mejor conservado de China, donde los emperadores Ming y Qing oraban por buenas cosechas, Patrimonio UNESCO."
                },
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
                "es": {
                    "name": "Palacio de Verano",
                    "description": "El jardín imperial más grande y mejor conservado de China, conocido como el 'Museo de los Jardines Reales', Patrimonio Mundial de la UNESCO."
                },
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
                "es": {
                    "name": "Tumbas Ming",
                    "description": "El lugar de enterramiento de 13 emperadores Ming, uno de los complejos de tumbas imperiales más grandes y mejor conservados del mundo, Patrimonio UNESCO."
                },
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
                "es": {
                    "name": "Mansión del Príncipe Gong",
                    "description": "La residencia principesca más grande y mejor conservada de la dinastía Qing, hogar del famoso oficial Heshen y el Príncipe Gong."
                },
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
                "es": {
                    "name": "Parque Olímpico",
                    "description": "La sede principal de los Juegos Olímpicos de Verano 2008 y de Invierno 2022, con estructuras icónicas como el Nido de Pájaro y el Cubo de Agua."
                },
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
                "es": {
                    "name": "Antiguo Palacio de Verano",
                    "description": "Un magnífico complejo de jardines imperiales conocido como el 'Jardín de los Jardines', destruido en 1860 por fuerzas anglo-francesas, ahora sitio histórico y museo."
                },
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
                "es": {
                    "name": "Gran Muralla de Mutianyu",
                    "description": "Una de las mejores secciones de la Gran Muralla Ming, conocida por sus densas torres de vigilancia, menos multitudes y paisajes impresionantes."
                },
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
                "es": {
                    "name": "Parque Beihai",
                    "description": "Uno de los jardines imperiales más antiguos y mejor conservados de China, famoso por la Pagoda Blanca y la antigua Isla Qiong."
                },
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
                "es": {
                    "name": "Templo de Lama",
                    "description": "El templo budista tibetano más grande y mejor conservado de Pekín, originalmente la residencia del emperador Yongzheng."
                },
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
                "es": {
                    "name": "Museo Nacional de China",
                    "description": "Uno de los museos más grandes del mundo, ubicado en el lado este de la Plaza de Tiananmen, que abarca 5.000 años de civilización china."
                },
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
                "es": {
                    "name": "Parque Jingshan",
                    "description": "Ubicado en el eje central de Pekín, el Pabellón Wanchun ofrece una vista panorámica de toda la Ciudad Prohibida."
                },
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
                "es": {
                    "name": "Shichahai",
                    "description": "Un área histórica que comprende tres lagos, rodeada de hutongs, residencias con patio y bares: el mejor lugar para experimentar el viejo Pekín."
                },
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
                "es": {
                    "name": "Parque de las Colinas Fragantes",
                    "description": "Un famoso jardín imperial y parque de montaña en el oeste de Pekín, renombrado por sus hojas rojas otoñales que atraen visitantes de todo el mundo."
                },
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
                "es": {
                    "name": "Mausoleo de Sun Yat-sen",
                    "description": "El lugar de descanso del Dr. Sun Yat-sen, ubicado al pie sur de la Montaña Púrpura, una obra maestra de la arquitectura china moderna."
                },
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
                "es": {
                    "name": "Templo de Confucio y Río Qinhuai",
                    "description": "El área histórica y cultural más famosa de Nankín, que combina templos, cultura de exámenes imperiales, paisajes nocturnos del Río Qinhuai y gastronomía."
                },
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
                "es": {
                    "name": "Mausoleo Ming Xiaoling",
                    "description": "La tumba de Zhu Yuanzhang, fundador de la dinastía Ming. Las estatuas de piedra del Camino Sagrado son un tesoro del arte antiguo chino de talla en piedra."
                },
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
                "es": {
                    "name": "Museo de Nankín",
                    "description": "Uno de los tres grandes museos de China, que alberga más de 430.000 artefactos que abarcan desde la antigüedad hasta los tiempos modernos."
                },
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
                "es": {
                    "name": "Parque del Lago Xuanwu",
                    "description": "El lago de jardín imperial más grande de China, ubicado en el corazón de Nankín, rodeado de montañas y la antigua muralla de la ciudad."
                },
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
                "es": {
                    "name": "Palacio Presidencial",
                    "description": "Testigo clave de la historia moderna china, sirvió como palacio del Reino Celestial Taiping y el Palacio Presidencial de la República de China."
                },
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
                "es": {
                    "name": "Río Qinhuai",
                    "description": "El río madre de Nankín, conocido como el 'Polvo Dorado de las Seis Dinastías'. Un crucero nocturno es la forma clásica de experimentar el encanto de Jinling."
                },
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
                "es": {
                    "name": "Templo Jiming",
                    "description": "Uno de los templos budistas más antiguos de Nankín, construido en la dinastía Jin Occidental, ubicado junto al Lago Xuanwu con impresionantes cerezos en flor primaverales."
                },
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
                "es": {
                    "name": "Montaña Púrpura",
                    "description": "La perla verde de Nankín, hogar del Mausoleo de Sun Yat-sen, Ming Xiaoling y el Templo Linggu: un parque forestal nacional en el centro de la ciudad."
                },
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
                "es": {
                    "name": "Puente del Río Yangtsé de Nankín",
                    "description": "El primer puente ferroviario y de carretera de doble propósito sobre el Río Yangtsé diseñado y construido por China, un símbolo del logro tecnológico chino."
                },
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
                "es": {
                    "name": "Salón Conmemorativo de las Víctimas de la Masacre de Nankín",
                    "description": "Construido en memoria de las víctimas de la Masacre de Nankín, una importante base educativa para el patriotismo y una advertencia para la paz mundial."
                },
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
                "es": {
                    "name": "Jardín Zhan Yuan",
                    "description": "El jardín clásico existente más antiguo de la dinastía Ming en Nankín, antigua residencia del Rey Oriental Taiping, uno de los cuatro jardines famosos de Jiangnan."
                },
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
                "es": {
                    "name": "Puerta Zhonghua",
                    "description": "La puerta de la ciudad existente más grande de China, el barbacana antiguo mejor conservado y más complejo del mundo, conocido como el 'Número Uno bajo el Cielo'."
                },
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
                "es": {
                    "name": "Templo Linggu",
                    "description": "Uno de los tres grandes templos budistas de la dinastía Ming, ubicado al pie de la Montaña Púrpura, famoso por su Salón sin Vigas y la Pagoda Linggu."
                },
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
                "es": {
                    "name": "Muralla de Nankín",
                    "description": "Una de las murallas urbanas antiguas más largas, grandes y mejor conservadas del mundo, que se extiende 35 km como la gran defensa de la capital Ming."
                },
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
                "es": {
                    "name": "Museo de los Guerreros de Terracota",
                    "description": "La Octava Maravilla del Mundo, miles de figuras de terracota de tamaño real que custodian la tumba del Emperador Qin Shi Huang, Patrimonio UNESCO desde 1978."
                },
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
                "es": {
                    "name": "Gran Pagoda del Ganso Salvaje",
                    "description": "Construida por el monje Xuanzang de la dinastía Tang para almacenar escrituras budistas traídas de la India, el icono emblemático de Xi'an, Patrimonio UNESCO."
                },
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
                "es": {
                    "name": "Palacio Huaqing",
                    "description": "Un palacio imperial de baños termales de la dinastía Tang, famoso por la historia de amor del Emperador Xuanzong y Yang Guifei."
                },
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
                "es": {
                    "name": "Muralla de Xi'an",
                    "description": "La muralla urbana antigua más grande y mejor conservada de China, que se extiende 13,7 km, perfecta para recorridos en bicicleta."
                },
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
                "es": {
                    "name": "Museo de Historia de Shaanxi",
                    "description": "El primer museo nacional moderno y grande de China, que alberga 1,7 millones de artefactos, conocido como la 'Perla de la Capital Antigua y Tesoro de China'."
                },
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
                "es": {
                    "name": "Barrio Musulmán",
                    "description": "La famosa calle gastronómica y cultural de Xi'an, renombrada por su cocina halal. Especialidades imperdibles: roujiamo, yangrou paomo y fideos biangbiang."
                },
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
                "es": {
                    "name": "Campanario y Torre del Tambor",
                    "description": "Ubicadas en el centro de Xi'an, estas estructuras icónicas han sido testigos de mil años de historia de la ciudad, erguidas como testimonio mutuo."
                },
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
                "es": {
                    "name": "Pequeña Pagoda del Ganso Salvaje",
                    "description": "Una pagoda de ladrillo de aleros cerrados de la dinastía Tang, junto con la Gran Pagoda del Ganso Salvaje, una estructura budista clave de Chang'an, ahora parte del Museo de Xi'an."
                },
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
                "es": {
                    "name": "Paraíso Tang y Paseo Nocturno",
                    "description": "Una calle peatonal temática de la cultura de la dinastía Tang, brillantemente iluminada por la noche, uno de los hitos turísticos culturales más populares de Xi'an."
                },
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
                "es": {
                    "name": "Montaña Lishan",
                    "description": "Una rama de las Montañas Qinling, sede del Palacio Huaqing y la famosa historia de las torres de baliza, hogar de templos antiguos y vistas escénicas."
                },
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
                "es": {
                    "name": "Templo Famen",
                    "description": "Un templo budista de fama mundial, renombrado por albergar la reliquia del dedo de Shakyamuni Buda, venerado como templo real durante la dinastía Tang."
                },
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
                "es": {
                    "name": "Museo del Bosque de Estelas",
                    "description": "La colección más grande de China de estelas de piedra y caligrafía, que alberga más de 4.000 estelas desde las dinastías Han hasta Qing."
                },
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
                "es": {
                    "name": "Parque del Patrimonio Nacional del Palacio Daming",
                    "description": "Las ruinas del palacio imperial más magnífico de la dinastía Tang, 4,5 veces el tamaño de la Ciudad Prohibida, Patrimonio UNESCO en la Ruta de la Seda."
                },
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
                "es": {
                    "name": "Montaña Huashan",
                    "description": "Una de las Cinco Montañas Sagradas de China, famosa por sus acantilados escarpados y el emocionante Paseo de Tablones: una excursión de un día desde Xi'an."
                },
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
                "es": {
                    "name": "Mausoleo de Qin Shi Huang",
                    "description": "La tumba de Ying Zheng, el Primer Emperador de China, el primer gran mausoleo imperial de la historia china, con un enorme palacio subterráneo aún por excavar."
                },
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
            theme=t.get("theme", "citywalk"),
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


# ── 示例咨询 ─────────────────────────────────────────────────────────────

ENQUIRIES = [
    {
        "name": "张明",
        "email": "zhangming@example.com",
        "phone": "+86 138-0000-0001",
        "destination": "北京、西安",
        "pax_count": 4,
        "message": "您好，我们一家四口（两个大人两个小孩）计划暑假去北京和西安玩一周，想要定制一个私人团，请问大概多少钱？",
        "status": "new",
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.j@example.com",
        "phone": "+1 415-555-0102",
        "destination": "Beijing",
        "pax_count": 2,
        "message": "Hi, I'm interested in a 5-day private tour of Beijing in September. We'd like to see the Great Wall, Forbidden City, and Temple of Heaven. Please send us a quote.",
        "status": "new",
    },
    {
        "name": "Carlos García",
        "email": "carlos@example.com",
        "phone": "+34 91-555-0103",
        "destination": "Xi'an",
        "pax_count": 3,
        "message": "Estoy interesado en un tour privado de 3 días por Xi'an para ver los Guerreros de Terracota y la ciudad antigua.",
        "status": "read",
    },
]


async def seed_enquiries(db):
    """创建示例咨询数据。"""
    logger.info("=" * 50)
    logger.info("创建示例咨询...")

    count = 0
    for data in ENQUIRIES:
        enquiry = Enquiry(**data)
        db.add(enquiry)
        count += 1
        logger.info(f"  ✅ {data['name']} ({data['email']})")

    await db.flush()
    logger.info(f"  ✅ 共创建 {count} 条咨询")


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
            await seed_enquiries(db)

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
            logger.info(f"   📋  咨询:        {len(ENQUIRIES)} 条")

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
                    logger.info(f"✅ ES 搜索索引已重建，共索引 {count} 个文档（{count // 3} 个产品 × 3 语言）")
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
