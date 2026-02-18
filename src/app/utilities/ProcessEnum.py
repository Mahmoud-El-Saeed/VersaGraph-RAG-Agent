from enum import Enum

class ProcessSignal(Enum):
    FILE_TYPE_NOT_SUPPORTED = "File type not supported."
    FILE_SIZE_EXCEEDED = "File size exceeded the limit."
    FILE_VALIDATE_SUCCESS = "File validation successful."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."
    FILE_UPDLOAD_FAILED = "File upload failed."
    NO_FILE_FOUND = "The File Not Found"
    FILE_PROCESSING_SUCCESS = "File processed successfully."
    FILE_PROCESSING_FAILED = "File processing failed."
    FILE_ALREADY_PROCESSED = "File has already been processed."