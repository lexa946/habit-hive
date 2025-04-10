from fastapi import FastAPI
from app.api.routers import users, habits, trackings, teams, frontend

app = FastAPI()

app.include_router(users.router)
app.include_router(habits.router)
app.include_router(trackings.router)
app.include_router(teams.router)
app.include_router(frontend.router)
