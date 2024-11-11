from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .endpoints import websocket

app = FastAPI(title="Datapunk Stream")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Datapunk Stream API"}