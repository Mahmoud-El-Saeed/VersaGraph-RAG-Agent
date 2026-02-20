from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from bson.objectid import ObjectId
from datetime import datetime
from src.app.database.mongo_db.DataBaseEnum import FileStatus

class ChatFile(BaseModel):
    """Sub-model to track files specifically attached to this chat session."""
    file_id: str = Field(..., description="Reference to the file document ID")
    filename: str = Field(..., description="Original name of the file")
    status: str = Field(default=FileStatus.UPLOADED.value, description="Status of the file in this specific chat context")
    added_at: datetime = Field(default_factory=datetime.now)

class Chat(BaseModel):
    
    id: Optional[ObjectId] = Field(None, alias='_id')
    chat_id: str = Field(..., description="Unique identifier for the chat session")
    title: Optional[str] = Field(None, description="Title of the chat session")
    
    # === Persona Configuration (Locked per session) ===
    persona_name: str = Field(default="General Assistant", description="Name of the assigned persona")
    persona_instructions: str = Field(default="You are a helpful assistant.", description="Strict instructions for the LLM")
    
    # === Multi-File Registry ===
    files: List[ChatFile] = Field(default_factory=list, description="List of files associated with this chat")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the chat session was created")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @classmethod
    def get_indexes(cls):
        return [
            {
                'key': [('chat_id', 1)],
                'name': 'chat_id_index_1',
                'unique': True
            }
        ]