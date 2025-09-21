import os
from fastapi import HTTPException, Header
from typing import Optional

def require_xauth(x_auth: Optional[str] = Header(None)) -> bool:
    """
    X-AUTH 헤더를 검증하는 의존성 함수
    Spring 서버와 공유하는 비밀 키로 인증
    """
    expected_secret = os.getenv("X_AUTH_SHARED_SECRET", "CHANGE_ME")
    
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