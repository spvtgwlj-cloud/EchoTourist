"""通用 CRUD 基类，提供标准数据访问操作。"""

from typing import Any, Generic, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[Any] = None,
    ) -> list[ModelType]:
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None:
                    column = getattr(self.model, field, None)
                    if column is not None:
                        query = query.where(column == value)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: Optional[dict] = None) -> int:
        query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None:
                    column = getattr(self.model, field, None)
                    if column is not None:
                        query = query.where(column == value)

        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        db.add(obj)
        await db.flush()
        return obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, update_data: dict) -> ModelType:
        for field, value in update_data.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await db.flush()
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj
