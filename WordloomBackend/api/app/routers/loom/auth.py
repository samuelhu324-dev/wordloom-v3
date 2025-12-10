
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import os
import jwt

from app.schemas.loom import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "demo_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

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

security = HTTPBearer(auto_error=False)

def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = credentials.credentials

    if token == os.getenv("APP_TOKEN", "devtoken123"):
        return {"sub": "devuser", "via": "static"}

    try:
        import jwt as _jwt
        data = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"sub": data.get("sub"), "via": "jwt", "claims": data}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
