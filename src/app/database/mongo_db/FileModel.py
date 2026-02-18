from .schema import File
from .BaseDataModel import BaseDataModel
from .DataBaseEnum import DataBaseEnum
from pymongo.asynchronous.database import AsyncDatabase

class FileModel(BaseDataModel):
    
    def __init__(self, db_client: AsyncDatabase):
        super().__init__(db_client, DataBaseEnum.COLLECTION_FILE_NAME.value, model=File)

    @classmethod
    async def create_instance(cls,db_client: AsyncDatabase):
        """Factory method to create an instance of ChatModel and initialize the collection."""
        # we use it because __init__ do not support async and we need to create indexes asynchronously
        instance = cls(db_client)
        await instance.init_collection()
        return instance
    
    async def insert_file(self, file: File):
        """Insert a new file document into the collection."""
        result = await self.collection.insert_one(file.model_dump(by_alias=True, exclude_unset=True))
        file.id = result.inserted_id
        return file
        
    async def find_file_by_id(self, file_id):
        """Find a file document by its ID."""
        file_data = await self.collection.find_one({"file_id": file_id})
        if file_data:
            return File(**file_data)
        return None
    
    async def find_files_by_chat_id(self, chat_id):
        """Find all files associated with a chat ID."""
        cursor = self.collection.find({"chat_id": chat_id})
        
        files_data = await cursor.to_list(length=None)
        return [File(**file_data) for file_data in files_data]
    
    async def delete_file_by_id(self, file_id):
        """Delete a file document by its ID."""
        result = await self.collection.delete_one({"file_id": file_id})
        return result.deleted_count > 0
    
    async def delete_files_by_chat_id(self, chat_id):
        """Delete all files associated with a chat ID."""
        result = await self.collection.delete_many({"chat_id": chat_id})
        return result.deleted_count

    async def update_file_status_by_id(self, file_id, new_status):
        """Update the status of a file document by its ID."""
        result = await self.collection.update_one(
            {"file_id": file_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0
    
    