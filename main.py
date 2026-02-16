from src.app.routes import data
from fastapi import FastAPI


app = FastAPI()

app.include_router(data.router)
