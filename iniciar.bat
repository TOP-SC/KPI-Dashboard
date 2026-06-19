@echo off
setlocal EnableExtensions
title Tablero KPIs TOP
cd /d "%~dp0"

echo.
echo ========================================
echo   TABLERO KPIs TOP - Iniciando
echo ========================================
echo.

if not exist ".env" (
    if exist ".env.example" copy /Y ".env.example" ".env" >nul
)

set "PY=backend\venv\Scripts\python.exe"
set "VENV_OK=1"

if not exist "%PY%" (
    echo [1/4] Creando entorno Python...
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python no encontrado. Instale Python 3.11+ desde python.org
        pause
        exit /b 1
    )
    if exist "backend\venv" (
        echo Limpiando venv anterior corrupto...
        rmdir /s /q "backend\venv" 2>nul
    )
    python -m venv "backend\venv"
    if errorlevel 1 (
        echo AVISO: No se pudo crear venv. Usando Python del sistema.
        set "PY=python"
        set "VENV_OK=0"
    )
)

if "%VENV_OK%"=="1" (
    echo [2/4] Instalando dependencias backend...
    "%PY%" -m pip install -r backend\requirements.txt -q
) else (
    echo [2/4] Instalando dependencias backend en sistema...
    python -m pip install -r backend\requirements.txt -q
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm no encontrado. Instale Node.js desde nodejs.org
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [3/4] Instalando dependencias frontend...
    pushd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR al instalar npm
        popd
        pause
        exit /b 1
    )
    popd
) else (
    echo [3/4] Dependencias frontend OK
)

echo [4/4] Compilando frontend...
pushd frontend
call npm run build
if errorlevel 1 (
    echo ERROR al compilar frontend
    popd
    pause
    exit /b 1
)
popd

echo.
echo Levantando tablero - se abrira el navegador...
echo Cierre esta ventana para detener el servidor.
echo.

if "%VENV_OK%"=="1" (
    "%PY%" launcher.py
) else (
    python launcher.py
)

pause
