"""Launcher one-click: compila frontend si hace falta e inicia el tablero."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
VENV_PY = BACKEND / "venv" / "Scripts" / "python.exe"
HOST = "127.0.0.1"
BASE_PORT = 8765


def puerto_libre(base: int) -> int:
    for port in range(base, base + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) != 0:
                return port
    return base


def asegurar_build() -> None:
    if DIST.exists() and (DIST / "index.html").exists():
        return
    print("Compilando frontend...")
    subprocess.check_call(["npm", "run", "build"], cwd=FRONTEND, shell=True)


def esperar_servidor(port: int, timeout: float = 30.0) -> bool:
    inicio = time.time()
    while time.time() - inicio < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) == 0:
                return True
        time.sleep(0.3)
    return False


def _python_backend() -> str:
    if VENV_PY.exists():
        return str(VENV_PY)
    return sys.executable


def main() -> None:
    py = _python_backend()
    asegurar_build()
    port = puerto_libre(BASE_PORT)
    url = f"http://{HOST}:{port}"
    print(f"Iniciando tablero en {url}")

    env = {**os.environ, "PORT": str(port)}
    proc = subprocess.Popen(
        [py, "main.py"],
        cwd=BACKEND,
        env=env,
    )

    if esperar_servidor(port):
        webbrowser.open(url)
    else:
        print("No se pudo verificar el servidor. Abrí manualmente:", url)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
