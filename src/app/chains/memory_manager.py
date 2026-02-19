import uuid
import asyncio
from datetime import datetime, timezone
from src.app.database.mongo_db import MessageModel
from src.app.database.mongo_db.schema import Message
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from src.app.utilities.embeder import Embeder
from src.helper.config import get_settings


class MemoryManager:
    def __init__(self, message_model: MessageModel, qdrant_model: QdrantdbModel):
        self.message_model = message_model
        self.qdrant_model = qdrant_model
        self.embeder = Embeder()
        self.settings = get_settings()

    async def save_turn(self, chat_id: str, role: str, content: str):
        """
        Does two things at the same time:
        1. Stores the message as text in MongoDB.
        2. Converts it to a vector and stores it in Qdrant.
        """

        msg_obj = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
        )
        mongo_task = self.message_model.insert_message(msg_obj)

        vector = self.embeder.embed_text(content)

        payload = {
            "chat_id": chat_id,
            "content": content,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "history_memory",
        }

        qdrant_task = self.qdrant_model.upsert_points(
            collection_name=self.settings.COLLECTION_CHATS_HISTORY_NAME,
            vectors=[vector],
            payloads=[payload],
            ids=[str(uuid.uuid4())],
        )

        # Run both in parallel
        await asyncio.gather(mongo_task, qdrant_task)
        return True

    async def get_short_term_memory(self, chat_id: str, limit: int = 6) -> str:
        """
        Retrieves the most recent messages for a given chat_id from MongoDB.
        Returns a formatted string of the conversation history.
        """

        messages = await self.message_model.get_last_messages_by_chat_id(
            chat_id=chat_id,
            limit=limit
        )

        # Format the messages into a single string
        formatted_history = []
        for msg in messages:
            role_prefix = "User" if msg.role == "user" else "Assistant"
            formatted_history.append(f"{role_prefix}: {msg.content}")
            
        return "\n".join(formatted_history)