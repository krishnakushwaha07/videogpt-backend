from fastapi import HTTPException, Depends, Request
from datetime import datetime, timedelta, timezone
from utility.env import settings
import jwt

from db.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from model import models


# function to create access token
def create_access_token(data: dict) -> str:
    now = datetime.now(timezone.utc)

    payload = data.copy()
    payload.update({
        "iat": now,
        "exp": now + timedelta(hours=settings.ACCESS_TOKEN_HR),
    })

    return jwt.encode(
        payload,
        settings.ACCESS_SECRET_KEY,
        algorithm=settings.ENCODING_ALGO,
    )



# function to verify access token.

async def verify_access_token(req : Request, db : AsyncSession = Depends(get_db)) -> int:
    """Returns user_id after verifying JWT token."""

    authorization = req.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization.split("Bearer ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_SECRET_KEY,
            algorithms=settings.ENCODING_ALGO,
            options={"require": ["exp", "sub"]}
        )
        user_id = int(payload.get("sub"))
        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Unauthorized access")