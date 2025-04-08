from uvicorn import run
from app.main import app

run(app, host='0.0.0.0', port=8000)