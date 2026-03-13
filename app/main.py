from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import re

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, posts, comments, users

settings = get_settings()

app = FastAPI(
    title="Vegora Social API",
    description="Backend API for Vegora Bites social platform - a vegan community for sharing recipes, tips, and journeys",
    version="1.0.0",
)

# CORS - allow configured origins + dynamically allow ngrok subdomains
origins = [o.strip() for o in settings.cors_origins.split(",")]

# Ngrok pattern for dynamic origin matching
NGROK_PATTERN = re.compile(r"^https://[a-z0-9-]+\.ngrok-free\.app$")


class DynamicCORSMiddleware(CORSMiddleware):
    """Extends CORSMiddleware to dynamically allow ngrok origins."""

    def is_allowed_origin(self, origin: str) -> bool:
        if super().is_allowed_origin(origin):
            return True
        # Allow any ngrok-free.app subdomain
        if NGROK_PATTERN.match(origin):
            return True
        return False


app.add_middleware(
    DynamicCORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(users.router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "app": "Vegora Social"}
