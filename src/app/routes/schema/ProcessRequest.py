from pydantic import BaseModel

class ProcessRequest(BaseModel):
    file_id: str
    chat_id: str