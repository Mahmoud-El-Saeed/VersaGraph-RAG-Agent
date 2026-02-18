from enum import Enum

class DataBaseEnum(Enum):
    COLLECTION_CHAT_NAME = "chats"
    COLLECTION_FILE_NAME = "files"
    COLLECTION_MESSAGE_NAME = "messages"


class FileStatus(Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
