import os
from pathlib import Path

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from uvicorn import run
from app.main import app

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Serve frontend files
@app.get("/{path:path}")
async def serve_frontend(path: str):
    static_path = Path("app/static") / path
    if static_path.exists():
        return FileResponse(static_path)
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    run(app, host='127.0.0.1', port=8000)
