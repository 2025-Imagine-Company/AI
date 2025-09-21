# 1. dotenv 라이브러리에서 load_dotenv 함수를 가져옵니다.
from dotenv import load_dotenv
from fastapi import FastAPI
from .routers import train

# 2. 애플리케이션의 다른 코드가 실행되기 전에 .env 파일을 로드합니다.
load_dotenv()

def create_app():
    app = FastAPI(title="AudIon AI Server", version="0.1.0")
    app.include_router(train.router)
    return app

app = create_app()