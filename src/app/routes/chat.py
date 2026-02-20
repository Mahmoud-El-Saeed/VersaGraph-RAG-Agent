from langserve import add_routes
from src.app.chains.rag_chain import create_full_rag_chain
from src.app.chains.llm import LLMProvider
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from src.app.database.mongo_db.ChatModel import ChatModel
from src.app.database.mongo_db.MessageModel import MessageModel

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

def register_chat_routes(app):
    """Register chat routes with the FastAPI app."""

    qdrant_model = QdrantdbModel(app.qdrant_client)
    llm = LLMProvider().get_model()


    chain = create_full_rag_chain(
        llm=llm, 
        mongo_client=app.db_client, 
        qdrant_model=qdrant_model
    )


    add_routes(
        app,
        chain,
        path="/chat",
        playground_type="default",
    )

@router.get("/history")
async def get_chat_history(request: Request):
    """Returns a list of all recent chat sessions."""
    mongo_client = request.app.db_client
    chat_model = await ChatModel.create_instance(mongo_client)
    chats = await chat_model.get_all_chats()
    
    # Return list of chat_ids (and titles if available)
    return JSONResponse(
        content={"chats": [chat.chat_id for chat in chats]},
        status_code=status.HTTP_200_OK
    )

@router.get("/history/{chat_id}")
async def get_chat_messages(request: Request, chat_id: str):
    """Returns all messages for a specific chat session."""
    mongo_client = request.app.db_client
    message_model = await MessageModel.create_instance(mongo_client)
    messages = await message_model.find_messages_by_chat_id(chat_id)
    
    formatted_messages = [
        {"role": msg.role, "content": msg.content} 
        for msg in messages
    ]
    return JSONResponse(
        content={"messages": formatted_messages},
        status_code=status.HTTP_200_OK
    )