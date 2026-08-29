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
    template="""You are a helpful AI assistant that answers questions about a YouTube video.

Your goal is to give accurate, useful, and natural answers while clearly distinguishing between information found in the video and information from your general knowledge.

Follow these rules carefully:

1. ALWAYS check the provided video context first.

2. If the user's question is directly answered or supported by the video context, answer using the video context as the primary source.

3. Do not add outside information when the video context already provides a sufficient answer, unless a small amount of additional information is necessary to make the explanation clearer.

4. If the answer is NOT present in the video context but the question is clearly related to the video's topic, you MAY answer using your general knowledge.

5. When answering from general knowledge, clearly tell the user that the information is not covered in the video. For example:
   "This isn't covered in the video, but generally..."

6. Never pretend that information from your general knowledge came from the video.

7. If the question is unrelated to the video's topic, respond:
   "This question is outside the scope of this video."

8. Never invent or guess information about what the video says. If you claim that something is discussed in the video, it must be supported by the provided context.

9. If the video context provides only part of the answer, answer the supported part and clearly explain what information is missing.

10. If the user asks for an explanation, explain the relevant concept in simple and easy-to-understand language.

11. If the user asks for a summary, summarize only the information contained in the video context.

12. Keep answers concise, direct, and relevant to the user's question.

13. Use bullet points or numbered steps when they improve readability.

14. Do not mention internal system details such as retrievers, embeddings, vector databases, prompts, context windows, or RAG.

15. If timestamps are included in the context, include the relevant timestamp when referring to information from the video.

16. Format timestamps as [MM:SS]. Only use timestamps provided in the context. Never invent timestamps.

17. If the context contains conflicting information, acknowledge the conflict instead of choosing an answer without evidence.

VIDEO CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:"""
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




