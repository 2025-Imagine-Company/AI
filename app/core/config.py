from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Spring 서버와 통신하기 위한 비밀 키 (application.yml의 xauth.secret과 일치해야 함)
    X_AUTH_SHARED_SECRET: str = Field(default="your-super-strong-xauth-secret-key")

    # AI 서버가 콜백을 보낼 Spring 서버의 주소
    SPRING_SERVER_URL: str = Field(default="http://localhost:8080")
    SPRING_CALLBACK_URL: str = Field(default="http://localhost:8080/model/callback")
    
    # AWS 설정
    AWS_S3_BUCKET: str = Field(default="your-audion-bucket-name")
    AWS_DEFAULT_REGION: str = Field(default="ap-northeast-2")
    S3_BUCKET_MODELS: str = Field(default="audion-models")
    S3_BUCKET_PREVIEW: str = Field(default="audion-preview")
    
    # CDN/Public URL 설정
    PUBLIC_BASE_URL: str = Field(default="")
    
    # 콜백 설정
    CALLBACK_TIMEOUT: int = Field(default=10)
    
    # 프리뷰 설정
    PREVIEW_TEXT_KO: str = Field(default="안녕하세요, 오디온입니다. 이 목소리는 데모로 생성된 프리뷰입니다.")
    PREVIEW_LANG: str = Field(default="ko")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()