from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.habit import Habit
from app.database import get_db

router = APIRouter(tags=["Фронт"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Здесь пока мок-данные
    habits = [
        {"id": 1, "name": "Утренняя зарядка", "completed": True},
        {"id": 2, "name": "Пить воду", "completed": False},
        {"id": 3, "name": "Читать 10 мин", "completed": True},
    ]

    completed = sum(1 for h in habits if h["completed"])
    progress = int(completed / len(habits) * 100)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_name": "Алексей",
        "habits": habits,
        "progress_percent": progress,
        "streak": 7
    })

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
    
    return templates.TemplateResponse("habits.html", {
        "request": request,
        "habits": habits.all()
    })

@router.get("/habit/{habit_id}", response_class=HTMLResponse)
async def habit_page(request: Request, habit_id: int):
    # Пример данных для привычки, в реальности подставишь данные из базы данных
    fake_habit = {
        "id": habit_id,
        "name": "Утренняя зарядка",
        "completed_by": [
            {"name": "Оля", "avatar_url": "/static/avatars/1.png"},
            {"name": "Игорь", "avatar_url": "/static/avatars/2.png"}
        ],
        "streak": 5,
        "last_completed": "2025-04-08"
    }
    total_members = 10  # Примерное количество участников команды

    return templates.TemplateResponse("habit.html", {
        "request": request,
        "habit": fake_habit,
        "total_members": total_members
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