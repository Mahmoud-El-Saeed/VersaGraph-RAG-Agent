from .schema import Chat
from .BaseDataModel import BaseDataModel
from .DataBaseEnum import DataBaseEnum
from pymongo.asynchronous.database import AsyncDatabase

class ChatModel(BaseDataModel):
    
    def __init__(self, db_client: AsyncDatabase):
        super().__init__(db_client, DataBaseEnum.COLLECTION_CHAT_NAME.value,model=Chat)
        
    @classmethod
    async def create_instance(cls,db_client: AsyncDatabase):
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
        result = await self.collection.insert_one(chat.model_dump(by_alias=True,exclude_unset=True))
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