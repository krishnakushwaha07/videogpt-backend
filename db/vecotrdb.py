# to store documents as vector in database.

from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from utility.env import settings


#embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2",api_key=settings.GEMINI_API_KEY)

vector_store = PGVector(
    embeddings=embedding_model,
    connection=settings.DB_URL,
    collection_name="youtube_videos",
    use_jsonb=True,
    async_mode=True, # user async mode of pg vector.
    create_extension=False
)