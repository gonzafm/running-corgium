"""SPA frontend static file serving."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()


def register_spa_routes(app, frontend_dist: Path):
    """Mount static files and SPA fallback route if frontend dist exists."""
    if not frontend_dist.is_dir():
        return

    app.mount(
        "/assets",
        StaticFiles(directory=frontend_dist / "assets"),
        name="static",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA files with fallback to index.html for client-side routing."""
        # Serve actual files (e.g. vite.svg) if they exist
        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
