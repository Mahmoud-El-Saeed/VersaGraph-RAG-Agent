from datetime import datetime, timezone

from pymongo import cursor

from src.app.database.mongo_db.schema.Chats import Chat, ChatFile
from .BaseDataModel import BaseDataModel
from .DataBaseEnum import DataBaseEnum , FileStatus
from pymongo.asynchronous.database import AsyncDatabase


class ChatModel(BaseDataModel):
    def __init__(self, db_client: AsyncDatabase):
        super().__init__(db_client, DataBaseEnum.COLLECTION_CHAT_NAME.value, model=Chat)

    @classmethod
    async def create_instance(cls, db_client: AsyncDatabase):
        """Factory method to create an instance of ChatModel and initialize the collection."""
        # we use it because __init__ do not support async and we need to create indexes asynchronously
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def is_chat_exists(self, chat_id):
        """Check if a chat document exists by its ID."""
        chat_data = await self.collection.find_one({"chat_id": chat_id})
        return chat_data is not None

    async def insert_chat(self, chat: Chat):
        """Insert a new chat document into the collection."""
        result = await self.collection.insert_one(
            chat.model_dump(by_alias=True, exclude_unset=True)
        )
        chat.id = result.inserted_id
        return chat

    async def find_chat_by_id(self, chat_id):
        """Find a chat document by its ID."""
        chat_data = await self.collection.find_one({"chat_id": chat_id})
        if chat_data:
            return Chat(**chat_data)
        return None

    async def delete_chat_by_id(self, chat_id):
        """Delete a chat document by its ID."""
        result = await self.collection.delete_one({"chat_id": chat_id})
        return result.deleted_count > 0

    async def initialize_chat(
        self, chat_id: str, persona_name: str, persona_instructions: str
    ) -> Chat:
        """
        Smart Initialization: Creates the chat ONLY if it doesn't exist.
        This guarantees the Persona is locked and cannot be changed later.
        """
        existing_chat = await self.find_chat_by_id(chat_id)
        if existing_chat:
            return existing_chat  # Return existing, ignore new persona inputs

        new_chat = Chat(
            chat_id=chat_id,
            persona_name=persona_name,
            persona_instructions=persona_instructions,
            created_at=datetime.now(timezone.utc),
        )
        return await self.insert_chat(new_chat)

    async def add_file_to_chat(self, chat_id: str, file_id: str, filename: str) -> bool:
        """Appends a newly uploaded file to the chat's context."""
        new_file = ChatFile(
            file_id=file_id,
            filename=filename,
            added_at=datetime.now(timezone.utc)
        )

        # Using MongoDB $push to atomically add the file to the array
        result = await self.collection.update_one(
            {"chat_id": chat_id}, {"$push": {"files": new_file.model_dump()}}
        )
        return result.modified_count > 0

    async def update_chat_file_status(self, chat_id: str, file_id: str, new_status: str) -> bool:
        """Updates the processing status of a specific file INSIDE the chat."""
        # Using MongoDB positional operator $ to update the exact item in the array
        result = await self.collection.update_one(
            {"chat_id": chat_id, "files.file_id": file_id},
            {"$set": {"files.$.status": new_status}}
        )
        return result.modified_count > 0

    async def get_pending_files(self, chat_id: str) -> list[ChatFile]:
        """Returns only the files that need to be processed (uploaded but not indexed)."""
        chat = await self.find_chat_by_id(chat_id)
        if not chat:
            return []
        
        # Filter and return files that are not fully indexed
        return [f for f in chat.files if f.status != FileStatus.INDEXED.value]
    
    async def get_all_chats(self,limit: int = 50) -> list[Chat]:
        """Returns a list of all chat documents, limited to a specified number."""
        cursor = self.collection.find({}).sort("created_at", -1).limit(limit)
        chats_data = await cursor.to_list(length=None)
        return [Chat(**chat_data) for chat_data in chats_data]