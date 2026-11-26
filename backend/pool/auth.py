from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_hex
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import Role
from .database import session_dependency
from .identity_models import Operator
from .settings import JWT_SECRET

router = APIRouter(prefix="/auth", tags=["登录"])
Db = Annotated[Session, Depends(session_dependency)]
Bearer = HTTPBearer()
PBKDF2_ROUNDS = 240000


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=150)


def hash_password(password, salt=None):
    salt = salt or token_hex(18)
    digest = pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ROUNDS)
    return f"{salt}:{digest.hex()}"


def identify(db: Db, credentials: Annotated[HTTPAuthorizationCredentials, Depends(Bearer)]):
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"],
                            options={"require": ["exp", "sub"]})
        operator_id = int(claims["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, "登录已失效，请重新登录。") from None
    operator = db.get(Operator, operator_id)
    if operator is None:
        raise HTTPException(401, "账号不可用。")
    return operator


def permit(*roles):
    def dependency(operator: Annotated[Operator, Depends(identify)]):
        if operator.role not in roles:
            raise HTTPException(403, "当前岗位不允许此操作。")
        return operator
    return dependency


Current = Annotated[Operator, Depends(identify)]
CanCapture = Annotated[Operator, Depends(permit(Role.TECHNICIAN, Role.SUPERVISOR))]
Technician = Annotated[Operator, Depends(permit(Role.TECHNICIAN))]
Supervisor = Annotated[Operator, Depends(permit(Role.SUPERVISOR))]


def badge(operator):
    return {"username": operator.username, "role": operator.role, "display_name": operator.display_name}


@router.post("/login")
def login(body: Credentials, db: Db):
    operator = db.scalar(select(Operator).where(Operator.username == body.username.strip().lower()))
    salt = operator.password_digest.split(":")[0] if operator else "0" * 36
    supplied = hash_password(body.password, salt)
    if operator is None or not compare_digest(operator.password_digest, supplied):
        raise HTTPException(401, "用户名或密码无效。")
    claims = {"sub": str(operator.id), "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return {"access_token": jwt.encode(claims, JWT_SECRET, algorithm="HS256"), "profile": badge(operator)}


@router.get("/me")
def me(operator: Current):
    return badge(operator)
