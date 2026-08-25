from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from utility.env import settings

# my routers
from routers.user import auth_router
from routers.video import video_router
from routers.health import health_router

app = FastAPI()

# session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET
)

# cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount routes on application.
app.include_router(health_router)
app.include_router(router=auth_router)
app.include_router(prefix="/video",router=video_router)
