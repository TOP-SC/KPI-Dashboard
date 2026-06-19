from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import HOST, PORT
from services.sheets import obtener_dashboard

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "frontend" / "dist"

app = FastAPI(title="Tablero KPIs TOP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(refresh: bool = False):
    return obtener_dashboard(force_refresh=refresh)


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        file_path = DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST / "index.html")


if __name__ == "__main__":
    import socket

    import uvicorn

    def puerto_libre(base: int) -> int:
        for port in range(base, base + 20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex((HOST, port)) != 0:
                    return port
        return base

    port = PORT
    env_port = __import__("os").getenv("PORT")
    if env_port:
        port = int(env_port)
    elif puerto_libre(PORT) != PORT:
        port = puerto_libre(PORT)
        print(f"Puerto {PORT} ocupado. Usando {port}...")

    print(f"Tablero KPIs TOP -> http://{HOST}:{port}")
    uvicorn.run("main:app", host=HOST, port=port, reload=False)
