from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import jwt  # pip install PyJWT

router = APIRouter(tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "demo_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ---- 请求与响应模型 ----
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---- 登录：简单 Demo 账号（从 .env 读取）----
@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    demo_user = os.getenv("DEMO_USER", "admin")
    demo_pass = os.getenv("DEMO_PASS", "admin123")

    if req.username != demo_user or req.password != demo_pass:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": req.username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=token)

# ---- 可复用的 Bearer 依赖（其它路由可复用）----
security = HTTPBearer(auto_error=False)

def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    统一的鉴权入口：
    1) 若 token == APP_TOKEN（.env），视为本地联调直通
    2) 否则按 JWT（HS256）校验
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = credentials.credentials

    # 1) 开发直通 token
    if token == os.getenv("APP_TOKEN", "devtoken123"):
        return {"sub": "devuser", "via": "static"}

    # 2) JWT 校验
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"sub": data.get("sub"), "via": "jwt", "claims": data}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
