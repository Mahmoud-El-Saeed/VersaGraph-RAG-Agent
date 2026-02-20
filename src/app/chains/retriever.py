import asyncio
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from src.app.utilities.embeder import Embeder
from src.helper.config import get_settings


class Retriever:
    def __init__(self, qdrant_model: QdrantdbModel):
        self.qdrant_model = qdrant_model
        self.embeder = Embeder()
        self.settings = get_settings()

    async def _search_documents(
        self, vector: List[float], chat_id: str
    ) -> List[Document]:
        """Search for relevant documents in the Qdrant collection based on the query vector and chat_id."""
        results = await self.qdrant_model.search(
            collection_name=self.settings.COLLECTION_APP_NAME,
            query_vector=vector,
            chat_id=chat_id,
            limit=10,
        )
        return [
            Document(
                page_content=point.payload.get("chunk_content", ""),
                metadata={
                    **point.payload.get("metadata", {}),
                    "relevance_score": point.score,  
                    "original_filename": point.payload.get("original_filename", ""),
                    "page_number": point.payload.get("page_number"),
                },
            )
            for point in results.points
        ]

    async def _search_history(
        self, vector: List[float], chat_id: str
    ) -> List[Document]:
        """Search for relevant conversation history in the Qdrant collection based on the query vector and chat_id."""
        results = await self.qdrant_model.search(
            collection_name=self.settings.COLLECTION_CHATS_HISTORY_NAME,
            query_vector=vector,
            chat_id=chat_id,
            limit=2,
        )
        return [
            Document(
                page_content=f"[Memory from past conversation]: {point.payload.get('chunk_content', '')}",
                metadata={"source_type": "history"},
            )
            for point in results.points
        ]

    async def search(self, inputs: Dict[str, Any]) -> List[Document]:
        """
        takes a question and chat_id, embeds the question, and retrieves relevant documents and conversation history.
        inputs: dict contains 'question' and 'chat_id'
        """
        query = inputs["question"]
        chat_id = inputs["chat_id"]

        query_vector = self.embeder.embed_text(query)

        docs_task = self._search_documents(query_vector, chat_id)
        history_task = self._search_history(query_vector, chat_id)

        docs_results, history_results = await asyncio.gather(docs_task, history_task)

        return history_results + docs_results


def get_retriever_runnable(qdrant_model: QdrantdbModel):
    retriever = Retriever(qdrant_model)

    return RunnableLambda(retriever.search)
