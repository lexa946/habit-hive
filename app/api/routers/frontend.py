from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.habit import Habit
from app.models.tracking import Tracking
from app.database import get_db

router = APIRouter(tags=["Фронт"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Получаем все привычки пользователя
    habits = await db.scalars(
        select(Habit).where(Habit.user_id == user.id)
    )
    habits_list = habits.all()
    
    # Получаем все трекинги за сегодня
    today = datetime.now().date()
    today_trackings = await db.scalars(
        select(Tracking).where(
            and_(
                Tracking.user_id == user.id,
                Tracking.date == today
            )
        )
    )
    completed_habits_ids = {tracking.habit_id for tracking in today_trackings.all()}
    
    # Формируем список привычек с информацией о выполнении
    habits_with_status = []
    for habit in habits_list:
        habits_with_status.append({
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "completed": habit.id in completed_habits_ids
        })
    
    # Вычисляем прогресс
    completed = sum(1 for h in habits_with_status if h["completed"])
    progress = int(completed / len(habits_with_status) * 100) if habits_with_status else 0
    
    # Вычисляем стрик (количество дней подряд с выполнением хотя бы одной привычки)
    # TODO: Реализовать правильный подсчет стрика
    streak = 7  # Временное значение

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_name": user.name,
        "habits": habits_with_status,
        "progress_percent": progress,
        "streak": streak,
        "today": today.strftime("%d.%m.%Y")
    })

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/team", response_class=HTMLResponse)
async def team_page(request: Request):
    # В реальности подставишь данные из БД
    fake_team = {
        "name": "ЗОЖ-группа",
        "streak": 12,
        "completion_percent": 83,
        "members": [
            {"name": "Оля", "avatar_url": "/static/avatars/1.png"},
            {"name": "Игорь", "avatar_url": "/static/avatars/2.png"},
        ],
        "habits": [
            {
                "name": "Утренняя зарядка",
                "completed_by": [
                    {"name": "Оля", "avatar_url": "/static/avatars/1.png"},
                ]
            },
            {
                "name": "Без сахара",
                "completed_by": [
                    {"name": "Игорь", "avatar_url": "/static/avatars/2.png"},
                ]
            }
        ]
    }

    return templates.TemplateResponse("team.html", {
        "request": request,
        "team": fake_team
    })


@router.get("/habits", response_class=HTMLResponse)
async def user_habits(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    habits = await db.scalars(
        select(Habit).where(Habit.user_id == user.id)
    )
    habits_list = habits.all()
    await db.commit()
    
    return templates.TemplateResponse("habits.html", {
        "request": request,
        "habits": habits_list
    })

@router.get("/habit/{habit_id}", response_class=HTMLResponse)
async def habit_page(request: Request, habit_id: UUID, db: AsyncSession = Depends(get_db)):
    habit = await db.scalar(
        select(Habit).where(Habit.id == habit_id)
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Получаем все трекинги для привычки
    trackings = await db.scalars(
        select(Tracking).where(Tracking.habit_id == habit_id)
    )
    trackings_list = trackings.all()
    
    # Проверяем, выполнена ли привычка сегодня
    today = datetime.now().date()
    is_completed_today = any(tracking.date == today for tracking in trackings_list)
    
    # Вычисляем процент выполнения
    total_days = 30  # За последние 30 дней
    completed_days = len(trackings_list)
    completed_percentage = int((completed_days / total_days) * 100) if total_days > 0 else 0
    
    return templates.TemplateResponse("habit.html", {
        "request": request,
        "habit": habit,
        "completed_percentage": completed_percentage,
        "total_members": 1,  # Временное значение
        "completed_by": trackings_list,
        "is_completed_today": is_completed_today
    })

@router.get("/habits/new", response_class=HTMLResponse)
async def new_habit(request: Request):
    return templates.TemplateResponse("habit_new.html", {
        "request": request
    })

@router.post("/habits/new", response_class=HTMLResponse)
async def create_habit(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    name = form_data.get("name")
    description = form_data.get("description", "")
    
    # TODO: Временное решение - используем первого пользователя
    # В будущем нужно будет получать текущего пользователя из сессии
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    new_habit = Habit(
        name=name,
        description=description,
        user_id=user.id
    )
    
    db.add(new_habit)
    await db.commit()
    await db.refresh(new_habit)
    
    return RedirectResponse(url="/habits", status_code=303)

@router.post("/toggle/{habit_id}", response_class=HTMLResponse)
async def toggle_habit(request: Request, habit_id: UUID, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Проверяем существование привычки
    habit = await db.scalar(
        select(Habit).where(Habit.id == habit_id)
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Проверяем, не была ли привычка уже отмечена сегодня
    today = datetime.now().date()
    existing_tracking = await db.scalar(
        select(Tracking).where(
            and_(
                Tracking.habit_id == habit_id,
                Tracking.user_id == user.id,
                Tracking.date == today
            )
        )
    )
    
    if existing_tracking:
        # Если привычка уже отмечена сегодня, удаляем отметку
        await db.delete(existing_tracking)
    else:
        # Если привычка не отмечена, создаем новую отметку
        new_tracking = Tracking(
            habit_id=habit_id,
            user_id=user.id,
            date=today
        )
        db.add(new_tracking)
    
    await db.commit()
    
    # Редиректим обратно на главную страницу
    return RedirectResponse(url="/", status_code=303)

@router.post("/habit/{habit_id}/complete", response_class=HTMLResponse)
async def complete_habit(request: Request, habit_id: UUID, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Проверяем существование привычки
    habit = await db.scalar(
        select(Habit).where(Habit.id == habit_id)
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Проверяем, не была ли привычка уже отмечена сегодня
    today = datetime.now().date()
    existing_tracking = await db.scalar(
        select(Tracking).where(
            and_(
                Tracking.habit_id == habit_id,
                Tracking.user_id == user.id,
                Tracking.date == today
            )
        )
    )
    
    if existing_tracking:
        # Если привычка уже отмечена сегодня, удаляем отметку
        await db.delete(existing_tracking)
    else:
        # Если привычка не отмечена, создаем новую отметку
        new_tracking = Tracking(
            habit_id=habit_id,
            user_id=user.id,
            date=today
        )
        db.add(new_tracking)
    
    await db.commit()
    
    # Редиректим обратно на страницу привычки
    return RedirectResponse(url=f"/habit/{habit_id}", status_code=303)