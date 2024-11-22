from fastapi import FastAPI
from .routes import health, predict

app = FastAPI(title="Datapunk Cortex")

app.include_router(health.router)
app.include_router(predict.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Datapunk Cortex"}