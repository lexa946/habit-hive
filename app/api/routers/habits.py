from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from sqlalchemy import select
from app.database import get_db
from app.models.habit import Habit
from app.models.user import User
from app.schemas.habit import HabitCreate, HabitResponse

router = APIRouter(
    prefix="/users",
    tags=["Habits"]
)


@router.post("/{user_id}/habits", response_model=HabitResponse)
async def create_habit(user_id: str, habit: HabitCreate, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_habit = Habit(name=habit.name, description=habit.description, user_id=user_id)
    db.add(new_habit)
    await db.commit()
    await db.refresh(new_habit)

    return new_habit


@router.get("/{user_id}/habits", response_model=list[HabitResponse])
async def get_habits(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    habits = await db.scalars(
        select(Habit).where(Habit.user_id == user_id)
    )
    return habits.all()


@router.delete("/{user_id}/habits/{habit_id}", status_code=204)
async def delete_habit(user_id: str, habit_id: str, db: AsyncSession = Depends(get_db)):
    habit = await db.scalar(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    await db.delete(habit)
    await db.commit()
    return
