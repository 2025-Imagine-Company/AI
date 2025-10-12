from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from .routers import train

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from app.core.config import Settings
settings = Settings()

def create_app():
    app = FastAPI(title="AudIon AI Server", version="0.1.0")
    app.include_router(train.router)
    return app

app = create_app()
