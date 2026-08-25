from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException
from utility.helpers import verify_access_token
from schemas.video import video_link, query
from utility.aiintegration import save_transcript_vector_db, fetch_transcript
from model import models
from db.db import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

video_router = APIRouter()


# save video and transcript in database.
@video_router.post("/url", status_code=status.HTTP_200_OK)
async def get_video_link(url : video_link, background_tasks: BackgroundTasks, db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    
    url = str(url.url)

    # save video in db
    video = models.Video(
        video_link=url,
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
@video_router.get("/videos/{video_id}")
async def get_a_video(video_id : int, db : AsyncSession = Depends(get_db), user_id = Depends(verify_access_token)):
    try:
        db_res = await db.execute(
            select(models.Video)
            .filter(models.Video.user_id == video_id)
            )
            
        video = db_res.scalars().first()

        return video

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.Try again later.")
    
    


@video_router.post("/chat/{video_id}")
async def get_relevent_text(video_id : int, query : query, user_id = Depends(verify_access_token), db : AsyncSession = Depends(get_db),):

    print(query)
    db_res = await db.execute(
            select(models.Video)
            .filter(models.Video.id == video_id, models.Video.user_id == user_id)
            )
                
    video = db_res.scalars().first()

    if not video:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can not access this resource.")
    
    return await fetch_transcript(video_id, query.query, user_id)
