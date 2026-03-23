@echo off
SETLOCAL EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

title JARVIS 4.0 - SHUTDOWN SEQUENCE
color 0C

echo ============================================================
echo    JARVIS 4.0 - INITIATING SHUTDOWN
echo ============================================================

:: TTS Abmeldung
cd /d "%ROOT%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -c ^
"import asyncio,sys,os;sys.path.insert(0,'src');os.environ['TTS_BACKEND']='pyttsx3';from tts_engine import speak;asyncio.run(speak('Jarvis wird heruntergefahren. Auf Wiedersehen, Sir.'))" ^
2>nul
)

:: ── 1. Docker Stack ───────────────────────────────────────────────────────
echo [1/3] Stopping Docker Containers...
docker compose -f "%ROOT%\docker-compose.yml" down --timeout 10
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] docker compose down hatte Fehler - force kill...
    docker compose -f "%ROOT%\docker-compose.yml" kill
)
echo       OK.

:: ── 2. Python + Node Prozesse ────────────────────────────────────────────
echo [2/3] Terminating Python and Node processes...
taskkill /F /FI "WINDOWTITLE eq JARVIS_BACKEND*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq JARVIS_UI*"      /T >nul 2>&1
:: Fallback: alle python/node die zu diesem Projekt gehoeren
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe   /T >nul 2>&1
echo       OK.

:: ── 3. Bestaetigung ──────────────────────────────────────────────────────
echo [3/3] System cleared.
echo ------------------------------------------------------------
echo    ALL CORES RELEASED. STANDBY MODE ACTIVE.
echo ============================================================
timeout /t 3 /nobreak >nul
exit /b 0
