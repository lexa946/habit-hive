from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.tracking import Tracking
from app.models.habit import Habit
from app.schemas.tracking import TrackingCreate, TrackingResponse

router = APIRouter(
    tags=['Trackings'],
)


@router.post("/trackings", response_model=TrackingResponse)
async def create_tracking(tracking_data: TrackingCreate, db: AsyncSession = Depends(get_db)):
    habit = await db.scalar(select(Habit).where(Habit.id == tracking_data.habit_id))
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Проверка, чтобы не дублировать дату
    existing_tracking = await db.scalar(
        select(Tracking).where(
            and_(
                Tracking.habit_id == tracking_data.habit_id,
                Tracking.date == tracking_data.date
            )
        )
    )
    if existing_tracking:
        raise HTTPException(status_code=400, detail="Tracking already exists for this date")

    tracking = Tracking(
        habit_id=tracking_data.habit_id,
        user_id=tracking_data.user_id,
        date=tracking_data.date,
    )
    db.add(tracking)
    
    # Обновляем прогресс привычки
    trackings = await db.scalars(select(Tracking).where(Tracking.habit_id == habit.id))
    trackings_list = trackings.all()
    
    if habit.target_date:
        total_days = (habit.target_date - habit.created_at.date()).days
        if total_days > 0:
            progress = min(100, int((len(trackings_list) / total_days) * 100))
            habit.mastery_progress = progress
    else:
        total_days = 30
        progress = min(100, int((len(trackings_list) / total_days) * 100))
        habit.mastery_progress = progress
    
    # Проверяем, достигнута ли цель освоения
    if habit.mastery_progress >= habit.mastery_goal:
        habit.is_completed = True
    
    await db.commit()
    await db.refresh(tracking)

    return tracking


@router.get("/habits/{habit_id}/trackings", response_model=list[TrackingResponse])
async def get_trackings(habit_id: str, db: AsyncSession = Depends(get_db)):
    habit = await db.scalar(select(Habit).where(Habit.id == habit_id))
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    result = await db.scalars(select(Tracking).where(Tracking.habit_id == habit_id))
    return list(result)
