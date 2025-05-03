from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import diagnose, kb, feedback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagnose.router, prefix=settings.API_V1_STR)
app.include_router(kb.router, prefix=settings.API_V1_STR)
app.include_router(feedback.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Diengg API"} 