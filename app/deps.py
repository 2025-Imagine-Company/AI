from fastapi import HTTPException, Header
from typing import Optional

# 💡 1. config.py에서 settings 객체를 가져옵니다.
from .core.config import settings

def require_xauth(x_auth: Optional[str] = Header(None)) -> bool:
    """
    X-AUTH 헤더를 검증하는 의존성 함수
    Spring 서버와 공유하는 비밀 키로 인증
    """
    # 💡 2. os.getenv 대신 settings 객체를 사용합니다.
    expected_secret = settings.X_AUTH_SHARED_SECRET

    if not x_auth:
        raise HTTPException(
            status_code=401, 
            detail="X-AUTH header is required"
        )

    if x_auth != expected_secret:
        raise HTTPException(
            status_code=401, 
            detail="Invalid X-AUTH credentials"
        )

    return True