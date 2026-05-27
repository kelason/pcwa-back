import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_cors(app: FastAPI) -> None:
    """Configures CORS middleware for the application."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    origins = [frontend_url]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )