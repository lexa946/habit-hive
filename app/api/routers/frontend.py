from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
from datetime import datetime, timedelta, date
import uuid

from app.models.user import User
from app.models.habit import Habit
from app.models.tracking import Tracking
from app.models.user_settings import UserSettings
from app.models.congratulation import Congratulation
from app.database import get_db

router = APIRouter(tags=["Фронт"])
templates = Jinja2Templates(directory="app/templates")

async def calculate_streak(user: User, db: AsyncSession) -> None:
    """Calculate and update user's streak based on completed habits."""
    today = datetime.now().date()
    
    # Initialize streak values if they are None
    if user.current_streak is None:
        user.current_streak = 0
    if user.max_streak is None:
        user.max_streak = 0
    if user.last_completed_date is None:
        user.last_completed_date = today
    
    # Get all active habits for the user
    habits = await db.scalars(
        select(Habit).where(
            and_(
                Habit.user_id == user.id,
                Habit.is_completed == False
            )
        )
    )
    habits_list = habits.all()
    
    if not habits_list:
        return
    
    # Get all trackings for today
    today_trackings = await db.scalars(
        select(Tracking).where(
            and_(
                Tracking.user_id == user.id,
                Tracking.date == today
            )
        )
    )
    completed_habits_ids = {tracking.habit_id for tracking in today_trackings.all()}
    
    # Check if all habits are completed today
    all_completed = all(habit.id in completed_habits_ids for habit in habits_list)
    
    if all_completed:
        # Check if we already congratulated today
        existing_congratulation = await db.scalar(
            select(Congratulation).where(
                and_(
                    Congratulation.user_id == user.id,
                    Congratulation.type == "all_habits_completed",
                    Congratulation.created_at >= today
                )
            )
        )
        
        if not existing_congratulation:
            # Create new congratulation
            congratulation = Congratulation(
                id=UUID(str(uuid.uuid4())),
                user_id=user.id,
                message="Поздравляем! Вы выполнили все свои привычки за сегодня! 🎉",
                type="all_habits_completed"
            )
            db.add(congratulation)
            await db.commit()
        
        # Update streak only if this is the first completion today
        if user.last_completed_date != today:
            # If last completion was yesterday, increment streak
            if (today - user.last_completed_date).days == 1:
                user.current_streak += 1
            # If last completion was more than a day ago, reset streak
            elif (today - user.last_completed_date).days > 1:
                user.current_streak = 1
            
            user.max_streak = max(user.max_streak, user.current_streak)
            user.last_completed_date = today
            await db.commit()
    else:
        # Reset streak if not all habits completed
        if user.last_completed_date != today:
            user.current_streak = 0
            await db.commit()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Get user's habits
    habits = await db.scalars(
        select(Habit).where(
            and_(
                Habit.user_id == user.id,
                Habit.is_completed == False
            )
        )
    )
    habits_list = habits.all()
    
    # Get today's trackings
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
    
    # Calculate progress
    completed = sum(1 for habit in habits_list if habit.id in completed_habits_ids)
    progress_percent = int((completed / len(habits_list)) * 100) if habits_list else 0
    
    # Calculate average mastery progress
    total_mastery_progress = sum(habit.mastery_progress for habit in habits_list)
    avg_mastery_progress = int(total_mastery_progress / len(habits_list)) if habits_list else 0
    
    # Mark completed habits
    for habit in habits_list:
        habit.completed = habit.id in completed_habits_ids
    
    # Get completed habits (limited to 4)
    completed_habits_query = await db.scalars(
        select(Habit).where(
            and_(
                Habit.user_id == user.id,
                Habit.is_completed == True
            )
        ).order_by(Habit.completed_at.desc()).limit(4)
    )
    completed_habits = completed_habits_query.all()
    
    # Check if there are more completed habits
    total_completed_count = await db.scalar(
        select(func.count()).select_from(Habit).where(
            and_(
                Habit.user_id == user.id,
                Habit.is_completed == True
            )
        )
    )
    has_more_completed = total_completed_count > 4
    
    # Get congratulations
    congratulations = await db.scalars(
        select(Congratulation).where(
            Congratulation.user_id == user.id
        ).order_by(Congratulation.created_at.desc())
    )
    
    # Calculate streak
    await calculate_streak(user, db)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "habits": habits_list,
        "completed_habits": completed_habits,
        "has_more_completed": has_more_completed,
        "congratulations": congratulations.all(),
        "user": user,
        "progress_percent": progress_percent,
        "completed": completed,
        "avg_mastery_progress": avg_mastery_progress,
        "current_streak": user.current_streak,
        "max_streak": user.max_streak,
        "today": today.strftime("%d.%m.%Y"),
        "all_habits_completed": completed == len(habits_list) if habits_list else False
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
    
    # Вычисляем прогресс освоения
    if habit.target_date:
        # Если есть целевая дата, считаем прогресс относительно нее
        total_days = (habit.target_date - habit.created_at.date()).days
        days_passed = (today - habit.created_at.date()).days
        if total_days > 0:
            progress = min(100, int((len(trackings_list) / total_days) * 100))
            habit.mastery_progress = progress
            await db.commit()
    else:
        # Если нет целевой даты, считаем за последние 30 дней
        total_days = 30
        completed_days = len(trackings_list)
        progress = min(100, int((completed_days / total_days) * 100))
        habit.mastery_progress = progress
        await db.commit()
    
    return templates.TemplateResponse("habit.html", {
        "request": request,
        "habit": habit,
        "completed_by": trackings_list,
        "is_completed_today": is_completed_today
    })

@router.get("/habits/new", response_class=HTMLResponse)
async def new_habit(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: Временное решение - используем первого пользователя
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Get user settings
    user_settings = await db.scalar(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    if not user_settings:
        raise HTTPException(status_code=404, detail="User settings not found")
    
    return templates.TemplateResponse("habit_new.html", {
        "request": request,
        "default_mastery_goal": user_settings.default_mastery_goal,
        "default_period": user_settings.default_period,
        "now": datetime.now(),
        "timedelta": timedelta
    })

@router.post("/habits/new", response_class=HTMLResponse)
async def create_habit(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    name = form_data.get("name")
    description = form_data.get("description", "")
    target_date = form_data.get("target_date")
    mastery_goal = form_data.get("mastery_goal")
    
    # TODO: Временное решение - используем первого пользователя
    # В будущем нужно будет получать текущего пользователя из сессии
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database")
    
    # Get user settings
    user_settings = await db.scalar(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    if not user_settings:
        raise HTTPException(status_code=404, detail="User settings not found")
    
    # Use default mastery goal from settings if not specified
    if not mastery_goal:
        mastery_goal = user_settings.default_mastery_goal
    
    # Calculate target date if not specified using default period
    if not target_date:
        target_date = (datetime.now() + timedelta(days=user_settings.default_period)).strftime("%Y-%m-%d")
    
    new_habit = Habit(
        name=name,
        description=description,
        user_id=user.id,
        target_date=datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else None,
        mastery_goal=int(mastery_goal)
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
        # При удалении отметки уменьшаем прогресс на 1
        habit.mastery_progress = max(0, habit.mastery_progress - 1)
    else:
        # Если привычка не отмечена, создаем новую отметку
        new_tracking = Tracking(
            habit_id=habit_id,
            user_id=user.id,
            date=today
        )
        db.add(new_tracking)
        # При создании отметки увеличиваем прогресс на 1
        habit.mastery_progress = min(100, habit.mastery_progress + 1)
        
        # Проверяем, достигнут ли целевой уровень освоения
        if habit.mastery_progress >= habit.mastery_goal and not habit.is_completed:
            habit.is_completed = True
            habit.completed_at = today
            
            # Создаем поздравление
            congratulation = Congratulation(
                id=UUID(str(uuid.uuid4())),
                user_id=user.id,
                message=f"Поздравляем! Вы достигли целевого уровня освоения привычки '{habit.name}'! 🎉",
                type="mastery_goal_achieved"
            )
            db.add(congratulation)
    
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

@router.post("/habit/{habit_id}/complete-permanently", response_class=HTMLResponse)
async def complete_habit_permanently(request: Request, habit_id: UUID, db: AsyncSession = Depends(get_db)):
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
    
    # Отмечаем привычку как полностью завершенную
    habit.is_completed = True
    habit.completed_at = datetime.now().date()
    
    # Создаем поздравление
    congratulation = Congratulation(
        id=UUID(str(uuid.uuid4())),
        user_id=user.id,
        message=f"Поздравляем! Вы завершили привычку '{habit.name}'! 🎉",
        type="habit_completed"
    )
    db.add(congratulation)
    
    await db.commit()
    
    # Редиректим на страницу привычек
    return RedirectResponse(url="/habits", status_code=303)

@router.get("/settings", response_class=HTMLResponse)
async def get_settings(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # TODO: Replace with actual user when auth is implemented
    user = await db.execute(select(User).limit(1))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = settings.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "theme": settings.theme,
            "daily_reminder": settings.daily_reminder,
            "reminder_time": settings.reminder_time.strftime("%H:%M"),
            "default_mastery_goal": settings.default_mastery_goal,
            "default_period": settings.default_period
        }
    )

@router.post("/settings", response_class=RedirectResponse)
async def update_settings(
    request: Request,
    theme: str = Form(...),
    daily_reminder: bool = Form(False),
    reminder_time: str = Form(...),
    default_mastery_goal: int = Form(...),
    default_period: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # TODO: Replace with actual user when auth is implemented
    user = await db.execute(select(User).limit(1))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = settings.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings.theme = theme
    settings.daily_reminder = daily_reminder
    settings.reminder_time = datetime.strptime(reminder_time, "%H:%M").time()
    settings.default_mastery_goal = default_mastery_goal
    settings.default_period = default_period

    await db.commit()
    return RedirectResponse(url="/settings", status_code=303)

@router.post("/habit/{habit_id}/edit", response_class=HTMLResponse)
async def edit_habit(
    request: Request,
    habit_id: UUID,
    description: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
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
    
    # Обновляем описание привычки
    habit.description = description
    await db.commit()
    
    # Редиректим обратно на страницу привычки
    return RedirectResponse(url=f"/habit/{habit_id}", status_code=303)