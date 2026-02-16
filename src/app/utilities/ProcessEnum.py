from enum import Enum

class ProcessSignal(Enum):
    FILE_TYPE_NOT_SUPPORTED = "File type not supported."
    FILE_SIZE_EXCEEDED = "File size exceeded the limit."
    FILE_VALIDATE_SUCCESS = "File validation successful."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."