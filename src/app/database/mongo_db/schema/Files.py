from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime, timezone

class File(BaseModel):
    
    id: Optional[ObjectId] = Field(None,alias='_id')
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    chat_id: str = Field(..., description="Identifier for the chat session this file is associated with")
    original_filename: str = Field(..., description="Original name of the uploaded file")
    file_path : str = Field(..., description="Path where the file is stored on the server")
    status: str = Field(..., description="Processing status of the file")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the file was uploaded")

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    
    @classmethod
    def get_indexes(cls):

        return [
            {
                'key':[('file_id',1)],
                'name':'file_id_index_1',
                'unique':True
            }
        ]