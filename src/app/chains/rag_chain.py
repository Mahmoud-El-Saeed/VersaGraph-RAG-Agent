from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from src.app.chains.prompts import qa_prompt
from src.app.chains.retriever import get_retriever_runnable
from src.app.chains.memory_manager import MemoryManager
from src.app.database.mongo_db import MessageModel
# from IPython.display import Image, display


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

    # Parallel execution of retrieval, history fetching, and user message saving
    input_prep = RunnableParallel(
        # Pass the retriever output through our formatting function
        context=retriever | RunnableLambda(format_docs_with_citations),
        chat_history=RunnableLambda(fetch_chat_history),
        _save_user=RunnableLambda(save_user_input),
        question=itemgetter("question"),
        chat_id=itemgetter("chat_id"),
        persona=lambda x: x.get("persona", "helpful assistant"),
    )

    # Assemble the complete chain
    full_chain = (
        input_prep
        | {
            "answer": qa_prompt | llm | StrOutputParser(),
            "chat_id": itemgetter("chat_id"),
        }
        | RunnableLambda(save_ai_output)
    )
    # need to save chain workflow in png format 
    # image_data = full_chain.get_graph().draw_mermaid_png()
    # # save the image to a file
    # with open("full_rag_chain.png", "wb") as f:
    #     f.write(image_data)
    # display(Image(image_data))
    
    return full_chain