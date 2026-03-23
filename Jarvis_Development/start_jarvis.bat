@echo off
SETLOCAL EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

title JARVIS 4.0 - SOVEREIGN BOOT SEQUENCE
color 0B

echo ============================================================
echo    JARVIS 4.0 - SYSTEM IGNITION (Ryzen 9 7950X)
echo    Root: %ROOT%
echo ============================================================

:: ── 1. Ollama Check ───────────────────────────────────────────────────────
echo [1/5] Checking Ollama Service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ollama laeuft nicht. Bitte Ollama starten und erneut versuchen.
    echo         Start: ollama serve
    pause
    exit /b 1
)
echo       OK - Ollama erreichbar.

:: ── 2. Docker Stack ───────────────────────────────────────────────────────
echo [2/5] Starting Docker Containers (Core, RAG, Gateway, Sandbox)...
docker compose -f "%ROOT%\docker-compose.yml" up -d
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] docker compose fehlgeschlagen. Docker Desktop aktiv?
    pause
    exit /b 1
)
echo       OK - Stack laeuft.

:: ── 3. Python Backend ─────────────────────────────────────────────────────
echo [3/5] Launching Backend ^& Agent-Orchestrator...
if not exist "%ROOT%\.venv\Scripts\activate.bat" (
    echo [ERROR] .venv fehlt. Ausfuehren:
    echo         py -3 -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)
start "JARVIS_BACKEND" /min cmd /k "cd /d "%ROOT%" && call .venv\Scripts\activate.bat && python src\api_main.py"
echo       OK - Backend gestartet.

:: ── 4. Next.js Frontend ───────────────────────────────────────────────────
echo [4/5] Launching Sovereign Glass UI (Next.js)...
if not exist "%ROOT%\src\ui\node_modules" (
    echo       node_modules fehlt - npm install wird ausgefuehrt...
    pushd "%ROOT%\src\ui"
    call npm install --silent
    popd
)
start "JARVIS_UI" /min cmd /k "cd /d "%ROOT%\src\ui" && npm run dev"
echo       OK - UI gestartet.

:: ── 5. Heartbeat + TTS ────────────────────────────────────────────────────
echo [5/5] Finalizing System Check...
timeout /t 8 /nobreak >nul

cd /d "%ROOT%"
call .venv\Scripts\activate.bat
python src\heartbeat.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Heartbeat meldet Fehler - Container moeglicherweise noch nicht bereit.
)

python -c ^
"import asyncio,sys,os;sys.path.insert(0,'src');os.environ['TTS_BACKEND']='pyttsx3';from tts_engine import speak;asyncio.run(speak('Jarvis 4.0 gestartet. Alle Systeme operational. Bereit fuer Ihre Befehle, Sir.'))" ^
2>nul

echo ============================================================
echo    SYSTEM IS FULLY SOVEREIGN.
echo    Dashboard : http://localhost:3000
echo    API Docs  : http://localhost:8000/docs
echo ============================================================
start "" "http://localhost:3000"
echo [READY] Dieses Fenster zeigt Live-Logs. Strg+C zum Beenden.
pause
