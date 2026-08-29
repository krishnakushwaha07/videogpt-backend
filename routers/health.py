from fastapi import APIRouter, status, Request

health_router = APIRouter()

@health_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return "Server is running fine :)"

