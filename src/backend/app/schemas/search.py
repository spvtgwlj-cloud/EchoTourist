"""搜索 API 的请求和响应模型。"""

from typing import Optional

from pydantic import BaseModel


class SearchImageItem(BaseModel):
    url: str
    alt_text: Optional[str] = None


class SearchTourItem(BaseModel):
    id: str
    slug: str
    name: str
    subtitle: Optional[str] = None
    duration_days: int
    duration_nights: int = 0
    start_price: float
    currency: str = "USD"
    sort_order: int = 0
    avg_rating: float = 0
    review_count: int = 0
    difficulty: str = "easy"
    theme: str = "citywalk"
    max_pax: Optional[int] = None
    highlights: str = ""
    images: list[SearchImageItem] = []


class FacetBucket(BaseModel):
    key: str
    count: int


class SearchResponse(BaseModel):
    tours: list[SearchTourItem]
    total: int
    page: int = 1
    page_size: int = 12
    facets: Optional[dict[str, list[FacetBucket]]] = None
