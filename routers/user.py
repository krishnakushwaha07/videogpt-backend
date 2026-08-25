from fastapi import APIRouter, Request, Depends, status, HTTPException, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from utility.env import settings

from db.db import get_db
from utility.helpers import create_access_token, verify_access_token
from model import models
from sqlalchemy import select

from schemas.user import user_response

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
async def callback(req : Request, res : Response, db : AsyncSession = Depends(get_db)):

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
            profile_link=picture
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)

        except Exception as e:
            print(e)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")
        
            


    # issue access token here
    access_token = create_access_token(
    {
        "sub" : str(user.id),
        "name" : user.name
        }
    )

    res = RedirectResponse(
        settings.REDIRECT_URL
    )

    res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24  # 24 hours
    )

    return res

    



   
@auth_router.get("/me", status_code=status.HTTP_200_OK, response_model=user_response)
async def get_current_user(user_id = Depends(verify_access_token), db : AsyncSession = Depends(get_db)):
    db_res = await db.execute(
        select(models.User)
        .filter(models.User.id == user_id)
        )
                
    user = db_res.scalars().first()
    return user


@auth_router.get("/logout")
async def logout(res : Response, user_id = Depends(verify_access_token)):
    res.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return {"message": "Logged out"}
