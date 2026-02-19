from fastapi import FastAPI
from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager
from qdrant_client import AsyncQdrantClient
from src.app.routes import data
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from src.helper.config import get_settings, Settings
from src.app.routes.chat import register_chat_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    app.mongo_conn = AsyncMongoClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
    app.qdrant_client = AsyncQdrantClient(url=settings.URL_QDRANT)
    qdrant_model = QdrantdbModel(app.qdrant_client)
    await qdrant_model.create_collection_if_not_exists(
        collection_name=settings.COLLECTION_APP_NAME,
        vector_size=settings.EMBED_MODEL_SIZE
    )
    await qdrant_model.create_collection_if_not_exists(
        collection_name=settings.COLLECTION_CHATS_HISTORY_NAME,
        vector_size=settings.EMBED_MODEL_SIZE
    )
    register_chat_routes(app)

    yield
    await app.mongo_conn.close()
    await app.qdrant_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(data.router)
