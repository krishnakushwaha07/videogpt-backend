from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from utility.env import settings

from utility.transcript import get_yt_video_transcript
from db.vecotrdb import vector_store
from fastapi import HTTPException, status

# text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500, 
    chunk_overlap=150,
)


# output parser
parser = StrOutputParser()


# chat model...
chat_model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite",api_key=settings.GEMINI_API_KEY)


async def save_transcript_vector_db(url : str, user_id : int, video_id : int):
    try:
        # load the transcript of the video.
        transcript =  await get_yt_video_transcript(url, user_id, video_id)

        # splite the transcript in chunks.
        split_docs = splitter.split_documents(transcript)

        await vector_store.aadd_documents(split_docs)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.")



# prompt...
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template= """You are an AI assistant that answers questions about YouTube videos.
Your job is to answer the user's question using ONLY the provided video transcript/context.

Rules:
1. Use the provided context as the primary and only source of information.
2. Do not make up information that is not present in the context.
3. If the answer cannot be found in the context, say:
   "I couldn't find the answer in this video."
4. Give clear, concise, and natural answers.
5. If the user asks for an explanation, explain the relevant part of the video in simple language.
6. If the user asks for a summary, summarize only the information available in the context.
7. If the question is unrelated to the video, politely say that it is not covered in the video.
8. Do not mention "retriever", "vector database", "embeddings", or internal system details.
9. When useful, organize the answer using bullet points or numbered steps.

Video context:
{context}

User question:
{question}"""
)

# model chain
model_chain =  prompt | chat_model | parser

# fetch relevent data from vector db and sent it to llm for response generation...
async def fetch_transcript(video_id : int, query : str, user_id : int):
    try:
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={
            "k": 3,
            "filter": {
                "video_id": video_id,
                "user_id": user_id
            }
        })

        # Retrieve documents first and pass their text to the prompt. Passing
        # the retriever directly can result in the prompt receiving a
        # retriever object instead of the retrieved transcript content.
        documents = await retriever.ainvoke(query)
        context = "\n\n".join(
            document.page_content for document in documents
        )

        print("context")
        return await model_chain.ainvoke({
            "context": context,
            "question": query,
        })

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.")




