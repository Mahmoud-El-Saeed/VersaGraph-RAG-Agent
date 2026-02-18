from .schema import Message
from .BaseDataModel import BaseDataModel
from .DataBaseEnum import DataBaseEnum
from pymongo.asynchronous.database import AsyncDatabase

class MessageModel(BaseDataModel):
    
    def __init__(self, db_client: AsyncDatabase):
        super().__init__(db_client, DataBaseEnum.COLLECTION_MESSAGE_NAME.value, model=Message)

    @classmethod
    async def create_instance(cls,db_client: AsyncDatabase):
        """Factory method to create an instance of ChatModel and initialize the collection."""
        # we use it because __init__ do not support async and we need to create indexes asynchronously
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def insert_message(self, message: Message):
        """Insert a new message document into the collection."""
        result = await self.collection.insert_one(message.model_dump(by_alias=True, exclude_unset=True))
        message.id = result.inserted_id
        return message
        
    async def find_message_by_id(self, message_id):
        """Find a message document by its ID."""
        message_data = await self.collection.find_one({"message_id": message_id})
        if message_data:
            return Message(**message_data)
        return None
    
    async def find_messages_by_chat_id(self, chat_id, limit: int = None):
        """Find all messages associated with a chat ID, optionally limited."""
        cursor = self.collection.find({"chat_id": chat_id}).sort("timestamp", 1)
        if limit:
            cursor = cursor.limit(limit)
        
        messages_data = await cursor.to_list(length=None)
        return [Message(**message_data) for message_data in messages_data]
    
    async def get_last_messages_by_chat_id(self, chat_id, limit: int):
        """Get the last N messages associated with a chat ID."""
        cursor = self.collection.find({"chat_id": chat_id}).sort("timestamp", -1).limit(limit)
        
        messages_data = await cursor.to_list(length=None)
        return [Message(**message_data) for message_data in messages_data]
    
    
    async def delete_message_by_id(self, message_id):
        """Delete a message document by its ID."""
        result = await self.collection.delete_one({"message_id": message_id})
        return result.deleted_count > 0
    
    async def delete_messages_by_chat_id(self, chat_id):
        """Delete all messages associated with a chat ID."""
        result = await self.collection.delete_many({"chat_id": chat_id})
        return result.deleted_count
