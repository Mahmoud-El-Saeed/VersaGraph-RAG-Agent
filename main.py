from fastapi import FastAPI
from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager
from qdrant_client import AsyncQdrantClient
from src.app.routes import data
from src.helper.config import get_settings , Settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    app.mongo_conn = AsyncMongoClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
    app.qdrant_client = AsyncQdrantClient(
        url=settings.URL_QDRANT
    )
    
    yield
    await app.mongo_conn.close() 
    await app.qdrant_client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(data.router)
