from langchain_community.document_loaders.youtube import YoutubeLoader
from youtube_transcript_api import YouTubeTranscriptApi

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from utility.env import settings

from utility.helpers import get_yt_video_id

parser = StrOutputParser()

# prompt...
prompt = PromptTemplate(
    input_variables=["transcript_text"],
    template="""
            Translate this transcript into English.
    
            Rules:
            - Preserve all information.
            - Do not summarize.
            - Do not remove examples.
            - Preserve mathematical terminology.
            - Return only the translated transcript.
    
            Transcript:
            {transcript_text}
        """
    )

# chat model...
model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite",api_key=settings.GEMINI_API_KEY)
chat_model = prompt | model | parser



async def get_yt_video_transcript(url : str, user_id : int, video_id : int):
    """Pass a Youtube url and method will return the transcript of yt video in list of documents"""

    api = YouTubeTranscriptApi()

    yt_video_id : str = get_yt_video_id(url)

    transcript_list = api.list(yt_video_id)

    # Get the available transcript
    transcript_obj = next(iter(transcript_list))

    # Fetch it
    fetched_transcript = transcript_obj.fetch()

    # Convert to string
    transcript_text = " ".join(
    snippet.text for snippet in fetched_transcript
    )

    # convert the non english transcript into english.
    if transcript_obj.language_code != "en":
        print("executed....")
        response = await chat_model.ainvoke(transcript_text)
        transcript_text = response
   

    # Add your metadata
    metadata = {
        "yt_video_id" :  yt_video_id,
        "user_id": user_id,
        "video_id": video_id,
    }

    doc = Document(
        page_content=transcript_text,
        metadata=metadata
    )

    return [doc]



# get yt video captions in english from this method.
async def get_yt_video_caption(url: str, user_id: int, video_id: int):
    """Return the English YouTube transcript as documents.
    Return None if an English caption is not available.
    """

    try:
        loader = YoutubeLoader.from_youtube_url(
            youtube_url=url,
            language=["en"]
        )

        data = loader.load()

        # Add user and video IDs to metadata
        for d in data:
            d.metadata["user_id"] = user_id
            d.metadata["video_id"] = video_id

        return data

    except Exception as e:
        print(f"English caption not available: {e}")
        return None