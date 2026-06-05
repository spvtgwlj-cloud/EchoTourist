"""Service 层测试 —— Tour。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tour_service import tour_service
from app.core.exceptions import NotFoundException
from app.models.tour import Tour, TourDate


class TestTourService:
    """Tour Service 业务逻辑测试。"""

    async def test_list_tours_empty(self, db_session: AsyncSession):
        """功能测试：空列表返回正常结构。"""
        result = await tour_service.list_tours(db_session, locale="en")
        assert result.tours is not None
        assert result.total >= 0  # 可能有 fixture 创建的数据
        assert result.page == 1
        assert result.page_size == 12

    async def test_list_tours_with_data(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：有数据时返回正确结果。"""
        result = await tour_service.list_tours(db_session, locale="en")
        assert result.total >= 1
        assert any(t.slug == test_tour.slug for t in result.tours)

    async def test_list_tours_multilingual(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：多语言返回正确翻译。"""
        en_result = await tour_service.list_tours(db_session, locale="en")
        zh_result = await tour_service.list_tours(db_session, locale="zh")

        # 找同一个 tour
        en_tour = next((t for t in en_result.tours if t.slug == test_tour.slug), None)
        zh_tour = next((t for t in zh_result.tours if t.slug == test_tour.slug), None)

        assert en_tour is not None
        assert zh_tour is not None
        assert en_tour.name == "Test Great Tour"
        assert zh_tour.name == "测试精彩之旅"

    async def test_list_tours_pagination(self, db_session: AsyncSession):
        """边界测试：分页参数。"""
        result = await tour_service.list_tours(db_session, page=1, page_size=5)
        assert result.page == 1
        assert result.page_size == 5

        result_page2 = await tour_service.list_tours(db_session, page=2, page_size=5)
        assert result_page2.page == 2

    async def test_list_tours_difficulty_filter(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：难度筛选。"""
        result = await tour_service.list_tours(db_session, difficulty="moderate")
        if result.total > 0:
            assert all(t.difficulty == "moderate" for t in result.tours)

    async def test_get_tour_by_slug(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：通过 slug 获取。"""
        tour = await tour_service.get_tour(db_session, test_tour.slug, "en")
        assert tour is not None
        assert tour.slug == test_tour.slug
        assert tour.name == "Test Great Tour"

    async def test_get_tour_by_id(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：通过 UUID 字符串获取。"""
        tour = await tour_service.get_tour(
            db_session, str(test_tour.id), "en"
        )
        assert tour is not None
        assert tour.id == test_tour.id

    async def test_get_tour_not_found(self, db_session: AsyncSession):
        """鲁棒性测试：不存在的 slug 抛出 NotFoundException。"""
        import pytest
        with pytest.raises(NotFoundException):
            await tour_service.get_tour(db_session, "this-does-not-exist", "en")

    async def test_get_tour_invalid_id(self, db_session: AsyncSession):
        """鲁棒性测试：无效 UUID 字符串也返回 404。"""
        import pytest
        with pytest.raises(NotFoundException):
            await tour_service.get_tour(db_session, "00000000-0000-0000-0000-000000000000", "en")

    async def test_get_tour_with_images(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：返回的产品包含图片列表。"""
        tour = await tour_service.get_tour(db_session, test_tour.slug, "en")
        assert len(tour.images) >= 1
        assert tour.images[0].url.startswith("https://") or tour.images[0].url.startswith("/images")

    async def test_get_tour_with_itinerary(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：返回的产品包含行程安排。"""
        tour = await tour_service.get_tour(db_session, test_tour.slug, "en")
        assert tour.itinerary is not None
        assert len(tour.itinerary) == 2
        assert tour.itinerary[0].day == 1
        assert tour.itinerary[0].title == "Arrival"

    async def test_get_tour_dates(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：获取产品日期。"""
        result = await tour_service.get_tour_dates(db_session, test_tour.id)
        assert len(result.dates) >= 1
        assert result.dates[0].price_per_pax > 0

    async def test_get_tour_dates_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的产品返回空日期列表。"""
        result = await tour_service.get_tour_dates(db_session, uuid.uuid4())
        assert len(result.dates) == 0

    async def test_tour_response_price_format(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：价格格式正确。"""
        tour = await tour_service.get_tour(db_session, test_tour.slug, "en")
        assert tour.start_price >= 0
        assert tour.currency == "USD"
        assert isinstance(tour.start_price, float)

    async def test_tour_response_rating_format(self, db_session: AsyncSession, test_tour: Tour):
        """边界测试：评分边界值。"""
        tour = await tour_service.get_tour(db_session, test_tour.slug, "en")
        # avg_rating 应在 0-5 之间（由 fixture 设置为 4.5）
        assert 0 <= tour.avg_rating <= 5
        assert tour.review_count >= 0
