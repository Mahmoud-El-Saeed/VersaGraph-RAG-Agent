from pydantic import BaseModel

class ProcessRequest(BaseModel):
    chat_id: str