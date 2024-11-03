from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from api.middleware.rate_limit import rate_limit_middleware
from api.middleware.pii import pii_middleware

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def middleware_stack(request: Request, call_next):
    # Apply rate limiting
    await rate_limit_middleware(request, call_next)
    
    # Apply PII detection and anonymization
    response = await pii_middleware(request, call_next)
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }