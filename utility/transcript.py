from langchain_community.document_loaders.youtube import YoutubeLoader

async def get_yt_video_transcript(url : str, user_id : int, video_id : int):
    """Pass a Youtube url and method will return the transcript of yt video in list of documents"""

    loader = YoutubeLoader.from_youtube_url(youtube_url=url, language=["en"])
    data = loader.load()

    # add userid from access token.
    for d in data:
        d.metadata["user_id"] = user_id
        d.metadata["video_id"] = video_id

    return data