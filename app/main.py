from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, posts, comments, users

settings = get_settings()

app = FastAPI(
    title="Vegora Social API",
    description="Backend API for Vegora Bites social platform - a vegan community for sharing recipes, tips, and journeys",
    version="1.0.0",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
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


# Serve frontend static files (must be LAST, after all API routes)
FRONTEND_DIR = os.environ.get("FRONTEND_DIR", "/app/frontend")
if os.path.isdir(FRONTEND_DIR):
    # Serve static assets (css, js, images, etc.)
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    if os.path.isdir(os.path.join(FRONTEND_DIR, "images")):
        app.mount("/images", StaticFiles(directory=os.path.join(FRONTEND_DIR, "images")), name="images")
    if os.path.isdir(os.path.join(FRONTEND_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    # Serve sw.js with no-cache headers so browser always gets latest version
    @app.get("/sw.js")
    async def serve_service_worker():
        sw_path = os.path.join(FRONTEND_DIR, "sw.js")
        if os.path.isfile(sw_path):
            with open(sw_path, "r") as f:
                content = f.read()
            return Response(
                content=content,
                media_type="application/javascript",
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Service-Worker-Allowed": "/",
                },
            )
        return Response(
            content="// no service worker",
            media_type="application/javascript",
            headers={"Cache-Control": "no-store"},
        )

    # One-time endpoint to nuke service worker via Clear-Site-Data header
    @app.get("/api/clear-sw")
    async def clear_service_worker():
        return Response(
            content='{"cleared": true}',
            media_type="application/json",
            headers={
                "Clear-Site-Data": '"cache", "storage"',
            },
        )

    # Catch-all: serve HTML files or index.html
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Try exact file match (e.g., community.html, register.html)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            # Add Clear-Site-Data header on HTML pages to kill service workers
            if full_path.endswith('.html'):
                return FileResponse(
                    file_path,
                    headers={"Clear-Site-Data": '"cache", "storage"'},
                )
            return FileResponse(file_path)
        # Default to index.html
        index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(
                index,
                headers={"Clear-Site-Data": '"cache", "storage"'},
            )
        return {"detail": "Not found"}
