from fastapi import APIRouter, Request, Depends, status, HTTPException, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from utility.env import settings

from db.db import get_db
from utility.helpers import create_access_token, verify_access_token
from model import models
from sqlalchemy import select

from schemas.user import user_response, auth_token


from datetime import datetime, timedelta, timezone
import secrets

auth_router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_params={"scope": "openid email profile"},
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
)


@auth_router.get("/auth/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# authentication with google.
@auth_router.get("/auth/google/callback", name="google_callback")
async def callback(req : Request, db : AsyncSession = Depends(get_db)):

    # get auth token
    token = await oauth.google.authorize_access_token(req)

    # extract user info
    user = token.get("userinfo")
        
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")
        
    google_id = user["sub"]
    email = user["email"]
    name = user.get("name")
    picture = user.get("picture")

    # create token for redirect
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Find user in database
    db_res = await db.execute(
        select(models.User)
        .filter(models.User.email == email, models.User.google_sub == google_id)
        )
        
    user = db_res.scalars().first()

    # If user doesn't exist → create user
    if not user :
        user = models.User(
            name=name,
            email= email,
            google_sub = google_id,
            profile_link=picture,
            token = token,
            token_expires_at = expires_at
        )

        try:
            db.add(user)
            await db.commit()

        except Exception as e:
            print(e)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")

    else:
        user.token = token
        user.token_expires_at = expires_at
        await db.commit()

    
    return RedirectResponse(
                f"{settings.REDIRECT_URL}?token={token}"
            )

    

   
@auth_router.post("/verify-auth", status_code=status.HTTP_200_OK)
async def get_current_user(auth_token : auth_token, db : AsyncSession = Depends(get_db)):
    token = auth_token.token

    db_res = await db.execute(
                select(models.User).where(
                models.User.token == token
            )
        )
    user = db_res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if (not user.token_expires_at or user.token_expires_at <= datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    access_token = create_access_token(
    {
        "sub" : str(user.id),
        "name" : user.name
        }
    )

    # One-time token → invalidate it
    user.token = None
    user.token_expires_at = None
    await db.commit()

    return access_token




@auth_router.get("/me", status_code=status.HTTP_200_OK, response_model=user_response)
async def get_current_user(user_id = Depends(verify_access_token), db : AsyncSession = Depends(get_db)):
    db_res = await db.execute(
        select(models.User)
        .filter(models.User.id == user_id)
        )
                
    user = db_res.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use not found.")
    
    return user



# Note* - not useful for now.
@auth_router.get("/logout")
async def logout(res : Response, user_id = Depends(verify_access_token)):
    res.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # True in production with HTTPS
        samesite= "none" if settings.ENVIRONMENT == "production" else "lax",
    )

    return {"message": "Logged out"}
