from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from src.app.chains.prompts import qa_prompt , rephrase_prompt
from src.app.chains.retriever import get_retriever_runnable
from src.app.chains.memory_manager import MemoryManager
from src.app.database.mongo_db import MessageModel, FileModel


class ChainInput(BaseModel):
    question: str
    chat_id: str
    persona: str = Field(default="expert assistant That Provides Detailed Answers")



async def get_memory_manager(mongo_client, qdrant_model):
    """Create a MemoryManager instance with initialized dependencies."""
    message_model = await MessageModel.create_instance(mongo_client)
    return MemoryManager(message_model, qdrant_model)





def format_docs_with_citations(docs: list[Document]) -> str:
    """
    Format the retrieved documents to include citation metadata 
    (filename and page number) alongside the text content.
    """
    formatted_texts = []
    for doc in docs:
        filename = doc.metadata.get("original_filename", "Unknown File")
        page = doc.metadata.get("page_number", "N/A")
        
        source_type = doc.metadata.get("source_type", "document")
        
        if source_type == "history":
            formatted_texts.append(f"{doc.page_content}")
        else:
            formatted_texts.append(
                f"[FILE: {filename} | PAGE: {page}]\n{doc.page_content}\n"
            )
            
    return "\n\n".join(formatted_texts)


def create_full_rag_chain(llm, mongo_client, qdrant_model):
    """Create a complete RAG chain with memory management and citations."""

    retriever = get_retriever_runnable(qdrant_model)

    async def fetch_file_names(inputs: dict) -> str:
        chat_id = inputs["chat_id"]
        file_model = await FileModel.create_instance(mongo_client)
        files = await file_model.find_files_by_chat_id(chat_id)
        return ", ".join([f.original_filename for f in files]) if files else "No files"
    
    async def save_user_input(inputs: dict) -> dict:
        """Save user message to storage."""
        memory_manager = await get_memory_manager(mongo_client, qdrant_model)
        await memory_manager.save_turn(inputs["chat_id"], "user", inputs["question"])
        return inputs

    async def save_ai_output(inputs: dict) -> str:
        """Save AI response to storage."""
        memory_manager = await get_memory_manager(mongo_client, qdrant_model)
        await memory_manager.save_turn(inputs["chat_id"], "assistant", inputs["answer"])
        return inputs["answer"]

    async def fetch_chat_history(inputs: dict) -> str:
        """Fetch recent chat history from MongoDB."""
        memory_manager = await get_memory_manager(mongo_client, qdrant_model)
        return await memory_manager.get_short_term_memory(inputs["chat_id"], limit=6)

    initial_prep = RunnableParallel({
        "chat_history": RunnableLambda(fetch_chat_history),
        "file_names": RunnableLambda(fetch_file_names),
        "question": itemgetter("question"),
        "chat_id": itemgetter("chat_id"),
        "persona": lambda x: x.get("persona", "expert assistant That Provides Detailed Answers")
    })
    
    rephrase_step = RunnableParallel({
            "standalone_question": rephrase_prompt | llm | StrOutputParser(),
            "original_inputs": RunnablePassthrough() 
        })
    retrieval_step = RunnableParallel({
            "context": RunnableLambda(lambda x: {
                "question": x["standalone_question"],
                "chat_id": x["original_inputs"]["chat_id"]
            }) | retriever | RunnableLambda(format_docs_with_citations),
            "question": lambda x: x["original_inputs"]["question"],
            "chat_history": lambda x: x["original_inputs"]["chat_history"],
            "file_names": lambda x: x["original_inputs"]["file_names"],
            "persona": lambda x: x["original_inputs"]["persona"],
            "chat_id": lambda x: x["original_inputs"]["chat_id"],
            "_save_user": RunnableLambda(lambda x: x["original_inputs"]) | RunnableLambda(save_user_input)
        })
    
    response_generation = {
        "answer": qa_prompt | llm | StrOutputParser(),
        "chat_id": itemgetter("chat_id"),
    }
    
    # Assemble the complete chain
    full_chain = (
        initial_prep
        | rephrase_step
        | retrieval_step
        | response_generation
        | RunnableLambda(save_ai_output)
    ).with_types(input_type=ChainInput)

    return full_chain