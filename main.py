import os

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from uvicorn import run
from app.main import app

run(app, host='127.0.0.1', port=8000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Разрешаем фронту доступ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Путь до build
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "build")

# Подключаем как статические файлы
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# На любой неизвестный путь отдаём index.html (SPA-маршрутизация)
@app.get("/{full_path:path}")
async def serve_spa():
    return FileResponse(os.path.join(frontend_path, "index.html"))