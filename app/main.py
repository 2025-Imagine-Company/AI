from fastapi import FastAPI
from .routers import train
from .core.config import settings  # 이미 생성된 settings 사용

def create_app():
    app = FastAPI(title="AudIon AI Server", version="0.1.0")
    app.include_router(train.router)
    return app

app = create_app()