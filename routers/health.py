from fastapi import APIRouter, status, Request

health_router = APIRouter()

@health_router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    return "Server is running fine :)"


@health_router.get("/debug-cookie")
async def debug_cookie(request: Request):
    return {
        "cookies": request.cookies
    }