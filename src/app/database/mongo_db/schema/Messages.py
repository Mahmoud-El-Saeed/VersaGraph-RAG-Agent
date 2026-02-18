from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class Message(BaseModel):
    
    id: Optional[ObjectId] = Field(None,alias='_id')
    role: str = Field(..., description="Role of the message sender ('user' or 'agent')")
    chat_id: str = Field(..., description="Identifier for the chat session this message belongs to")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when the message was created")
    sources: Optional[list[dict]] = Field(None, description="List of sources used by the agent to generate the response (only for agent messages)")
    
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


    @classmethod
    def get_indexes(cls):

        return [
            {
                'key':[('chat_id',1)],
                'name':'chat_id_index_1',
                'unique':False
            },
            {
                'key':[('timestamp',-1)],
                'name':'timestamp_index_1',
                'unique':False
            }
        ]