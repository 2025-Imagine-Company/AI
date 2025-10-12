from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from .routers import train

# .env 파일을 자동으로 찾아 로드 (프로젝트 루트 어디에 있든 상관없이)
load_dotenv(find_dotenv(), override=True)

def create_app():
    app = FastAPI(title="AudIon AI Server", version="0.1.0")
    app.include_router(train.router)
    return app

app = create_app()
