from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class Chat(BaseModel):
    
    id: Optional[ObjectId] = Field(None,alias='_id')
    chat_id: str = Field(..., description="Unique identifier for the chat session")
    title: Optional[str] = Field(None, description="Title of the chat session")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the chat session was created")
    settings: Optional[dict] = Field(None, description="Settings for the chat session")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    
    @classmethod
    def get_indexes(cls):

        return [
            {
                'key':[('chat_id',1)],
                'name':'chat_id_index_1',
                'unique':True
            }
        ]