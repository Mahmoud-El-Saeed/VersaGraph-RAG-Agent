from src.helper.config import Settings, get_settings
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from pydantic import BaseModel
class BaseDataModel:
    
    def __init__(self,db_client: AsyncDatabase, collection_name: str, model: BaseModel):
        self.db_client = db_client
        self.app_settings: Settings = get_settings()
        self.collection: AsyncCollection = self.db_client[collection_name]
        self.collection_name = collection_name
        self.model = model
        
    async def init_collection(self):
        """Initialize the collection and create indexes if the collection does not exist."""
        all_collection = await self.db_client.list_collection_names()
        if self.collection_name not in all_collection:
            self.collection = self.db_client[self.collection_name]
            indexes = self.model.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index['key'],
                    name=index['name'],
                    unique = index['unique']
                )
