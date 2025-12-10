# auth.py —— 无破坏式微调版
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, jwt

router = APIRouter(tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "demo_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ✅ 登录请求体
class LoginRequest(BaseModel):
    username: str
    password: str

# ✅ 登录返回体
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    # 从 .env 读取演示账户
    demo_user = os.getenv("DEMO_USER", "admin")
    demo_pass = os.getenv("DEMO_PASS", "admin123")

    if req.username != demo_user or req.password != demo_pass:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # 生成演示级 token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": req.username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=token)

# --- Add: reusable Bearer dependency for other routers ---
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    统一的鉴权依赖：
    - 先允许使用 .env 里的 APP_TOKEN（方便本地调试）
    - 否则尝试用 JWT 验证（SECRET_KEY + HS256）
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = credentials.credentials

    # 1) 静态开发令牌（便于本地联调）
    if token == os.getenv("APP_TOKEN", "devtoken123"):
        return {"sub": "devuser", "via": "static"}

    # 2) JWT 验证
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 可按需返回更多 claims
        return {"sub": data.get("sub"), "via": "jwt", "claims": data}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
