from langserve import add_routes
from src.app.chains.rag_chain import create_full_rag_chain
from src.app.chains.llm import LLMProvider
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel

def register_chat_routes(app):
    """Register chat routes with the FastAPI app."""

    qdrant_model = QdrantdbModel(app.qdrant_client)
    llm = LLMProvider().get_model()


    chain = create_full_rag_chain(
        llm=llm, 
        mongo_client=app.db_client, 
        qdrant_model=qdrant_model
    )


    add_routes(
        app,
        chain,
        path="/chat",
        playground_type="default",
    )