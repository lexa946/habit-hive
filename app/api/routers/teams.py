import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.database import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamResponse

router = APIRouter(
    tags=['Teams'],
)


@router.post("/users/{user_id}/teams", response_model=TeamResponse)
async def create_team(user_id: uuid.UUID, team_data: TeamCreate, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    team = Team(
        name=team_data.name,
        owner_id=user_id,
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    team = await db.scalar(select(Team).where(Team.id == team_id))
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/users/{user_id}/join/{team_id}", response_model=TeamResponse)
async def join_team(user_id: uuid.UUID, team_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Найдем команду по UUID
    team = await db.scalar(select(Team).where(Team.id == team_id))

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка, что пользователь не состоит уже в команде
    if user.team_id:
        raise HTTPException(status_code=400, detail="User is already in a team")

    # Присоединяем пользователя к команде
    user.team_id = team.id
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return team


@router.get("/teams", response_model=list[TeamResponse])
async def get_all_teams(db: AsyncSession = Depends(get_db)):
    teams = await db.scalars(select(Team))
    return teams.all()