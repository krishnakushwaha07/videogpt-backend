from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException
from utility.helpers import verify_access_token
from schemas.video import video_link, query as QueryRequest
from utility.aiintegration import save_transcript_vector_db, fetch_transcript
from model import models
from db.db import get_db
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from utility.helpers import get_yt_video_id

video_router = APIRouter()


# save video and transcript in database.
@video_router.post("/url", status_code=status.HTTP_200_OK)
async def get_video_link(url : video_link, background_tasks: BackgroundTasks, db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    
    url = str(url.url)

    # save video in db
    video = models.Video(
        video_link=get_yt_video_id(url),
        user_id=user_id
    )

    try:
        db.add(video)
        await db.commit()
        await db.refresh(video)

    except Exception as e:
        await db.rollback()
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")
        

    background_tasks.add_task(save_transcript_vector_db, url, user_id, video.id)
    return {"message" : "video transcript saved successfully.", "video" : video}
    
   

@video_router.get("/videos")
async def get_all_saved_videos(db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    try:
        db_res = await db.execute(
            select(models.Video)
            .filter(models.Video.user_id == user_id)
            )
            
        videos = db_res.scalars().all()

        return videos

    except Exception as e:
        print(e)

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")


# get a single video
@video_router.get("/{video_id}")
async def get_a_video(video_id : int, db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    try:
        db_res = await db.execute(
            select(models.Video)
            .filter(models.Video.id == video_id)
            )
            
        video = db_res.scalars().first()

        return video

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")


    
# delete a single video
@video_router.delete("/{video_id}", status_code=status.HTTP_200_OK)
async def delete_a_video(video_id : int, db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    try:
        await db.execute(
            delete(models.Video)
            .filter(models.Video.id == video_id, models.Video.user_id == user_id)
            )

        """  # delete the embedding also...
        await vector_store.(
            filter={
                "video_id": int(video_id),
                "user_id": int(user_id)
            }
        ) """

        await db.commit()
        return {"message" : "Video deleted successfully."}
  
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")
    
    


@video_router.post("/chat/{video_id}")
async def get_relevent_text(
    video_id: int,
    request: QueryRequest,
    user_id=Depends(verify_access_token),
    db: AsyncSession = Depends(get_db),
):

    try:
        db_res = await db.execute(
            select(models.Video)
            .filter(models.Video.id == video_id, models.Video.user_id == user_id)
        )

        video = db_res.scalars().first()

        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You can not access this resource.",
            )

        return await fetch_transcript(video_id, request.query, user_id)

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.Try again later.",
        )
