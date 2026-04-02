@echo off
SETLOCAL EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

title JARVIS 4.0 - SOVEREIGN BOOT SEQUENCE
color 0B

echo ============================================================
echo    JARVIS 4.0  ^|  SOVEREIGN LOCAL AI  ^|  Ryzen 9 7950X
echo    Root: %ROOT%
echo ============================================================
echo.

:: ════════════════════════════════════════════════════════════
:: [0/6]  REBUILD-CHECK
::        Vergleicht Timestamps der Docker-Quelldateien gegen
::        .last_built  Sentinel.  Wenn eine Datei neuer ist
::        oder der Sentinel fehlt -> docker compose build.
:: ════════════════════════════════════════════════════════════
echo [0/6] Checking for Docker rebuild...

set "SENTINEL=%ROOT%\.last_built"
set "REBUILD=0"

:: Sentinel existiert noch nicht -> immer bauen
if not exist "%SENTINEL%" (
    echo       Sentinel fehlt - erster Start, baue Images.
    set "REBUILD=1"
    goto DO_REBUILD_CHECK_DONE
)

:: PowerShell: pruefe ob eine der Quelldateien neuer als Sentinel ist
powershell -NoProfile -NonInteractive -Command ^
  "$s = (Get-Item '%SENTINEL%').LastWriteTime; ^
   $watch = @( ^
     '%ROOT%\docker\Dockerfile.core', ^
     '%ROOT%\docker\Dockerfile.rag', ^
     '%ROOT%\docker\supervisord.rag.conf', ^
     '%ROOT%\requirements.txt' ^
   ); ^
   $newer = $watch | Where-Object { (Get-Item $_ -EA SilentlyContinue).LastWriteTime -gt $s }; ^
   if ($newer) { Write-Host ('  Rebuild ausgeloest durch: ' + ($newer -join ', ')); exit 1 } else { exit 0 }"

if !ERRORLEVEL!==1 (
    set "REBUILD=1"
) else (
    echo       Keine Aenderungen - ueberspringe Build.
)

:DO_REBUILD_CHECK_DONE

:: ════════════════════════════════════════════════════════════
:: [1/6]  OLLAMA CHECK
:: ════════════════════════════════════════════════════════════
echo.
echo [1/6] Checking Ollama Service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ollama laeuft nicht.
    echo         Start: ollama serve
    pause
    exit /b 1
)
echo       OK - Ollama erreichbar.

:: ════════════════════════════════════════════════════════════
:: [2/6]  DOCKER BUILD  (nur wenn REBUILD=1)
:: ════════════════════════════════════════════════════════════
echo.
if "!REBUILD!"=="1" (
    echo [2/6] Rebuilding Docker Images ^(--no-cache^)...
    echo       Das dauert 2-5 Minuten. Bitte warten...
    echo.

    docker compose -f "%ROOT%\docker-compose.yml" build --no-cache jarvis-rag
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Build jarvis-rag fehlgeschlagen.
        pause
        exit /b 1
    )

    docker compose -f "%ROOT%\docker-compose.yml" build --no-cache jarvis-core
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Build jarvis-core fehlgeschlagen.
        pause
        exit /b 1
    )

    :: Sentinel aktualisieren -> naechster Start baut nicht neu
    echo.> "%SENTINEL%"
    echo       Build OK - Sentinel aktualisiert.
) else (
    echo [2/6] Docker Build - uebersprungen ^(keine Aenderungen^).
)

:: ════════════════════════════════════════════════════════════
:: [3/6]  DOCKER STACK STARTEN
:: ════════════════════════════════════════════════════════════
echo.
echo [3/6] Starting Docker Stack ^(Core, RAG, Gateway, Sandbox^)...
docker compose -f "%ROOT%\docker-compose.yml" up -d
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] docker compose up fehlgeschlagen. Docker Desktop aktiv?
    pause
    exit /b 1
)
echo       OK - Stack laeuft.

:: ════════════════════════════════════════════════════════════
:: [4/6]  NEXT.JS FRONTEND
:: ════════════════════════════════════════════════════════════
echo.
echo [4/6] Launching Sovereign Glass UI ^(Next.js : 3001^)...
if not exist "%ROOT%\src\ui\node_modules" (
    echo       node_modules fehlt - npm install wird ausgefuehrt...
    pushd "%ROOT%\src\ui"
    call npm install --silent
    popd
)
start "JARVIS_UI" /min cmd /k "cd /d "%ROOT%\src\ui" && npm run dev"
echo       OK - UI gestartet auf http://localhost:3001

:: ════════════════════════════════════════════════════════════
:: [5/6]  HEALTH CHECK + WARTEN BIS CORE BEREIT
:: ════════════════════════════════════════════════════════════
echo.
echo [5/6] Waiting for jarvis-core health ^(max 60s^)...
set HEALTHY=0
for /L %%i in (1,1,12) do (
    if !HEALTHY!==0 (
        timeout /t 5 /nobreak >nul
        curl -s http://localhost:8000/health >nul 2>&1
        if !ERRORLEVEL!==0 (
            set HEALTHY=1
            echo       OK - API erreichbar nach %%i x 5s.
        ) else (
            echo       Warte... ^(%%i/12^)
        )
    )
)
if !HEALTHY!==0 (
    echo [WARN] jarvis-core antwortet noch nicht.
    echo        Container-Logs pruefen: docker logs jarvis-core
)

:: ════════════════════════════════════════════════════════════
:: [6/6]  HEARTBEAT + TTS  BEGRUESSUNG
:: ════════════════════════════════════════════════════════════
echo.
echo [6/6] System Heartbeat ^& Voice...

cd /d "%ROOT%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat

    python src\heartbeat.py 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo [WARN] Heartbeat meldet Fehler.
    )

    python -c ^
"import asyncio,sys,os;sys.path.insert(0,'src');os.environ['TTS_BACKEND']='pyttsx3';from tts_engine import speak;asyncio.run(speak('Jarvis 4.0 gestartet. Alle Systeme operational. Bereit fuer Ihre Befehle, Sir.'))" ^
2>nul
)

:: ════════════════════════════════════════════════════════════
::  FERTIG
:: ════════════════════════════════════════════════════════════
echo.
echo ============================================================
echo    SYSTEM IS FULLY SOVEREIGN.
echo.
echo    IDE  / Dashboard : http://localhost:3001
echo    Chat             : http://localhost:3001/chat
echo    RAG  / Upload    : http://localhost:3001/rag
echo    API  Docs        : http://localhost:8000/docs
echo    Gateway          : http://localhost:8080
echo ============================================================
echo.
echo    Rebuild erzwingen: .last_built loeschen und neu starten
echo    Stoppen          : stop_jarvis.bat
echo ============================================================
start "" "http://localhost:3001"
echo [READY] Strg+C zum Beenden dieses Fensters.
pause
