@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

set "DOMAIN=ninja-primp-late.ngrok-free.dev"
set "PORT=8000"
set "BASE_URL=https://%DOMAIN%"

cd /d "%~dp0"

if /I "%1"=="stop" goto STOP

echo.
echo ==== Apple model server demo start ====
echo Project folder: %cd%
echo.

if not exist "docker-compose.yml" (
    echo ERROR: docker-compose.yml not found.
    echo Put this file into the model_server folder.
    pause
    exit /b 1
)

where docker > nul 2>&1
if errorlevel 1 (
    echo ERROR: docker command not found. Install/start Docker Desktop.
    pause
    exit /b 1
)

where ngrok > nul 2>&1
if errorlevel 1 (
    echo ERROR: ngrok command not found. Check ngrok installation and restart terminal.
    pause
    exit /b 1
)

echo Checking Docker Engine...
docker info > nul 2>&1
if errorlevel 1 (
    echo Docker Engine is not responding.
    echo Trying to start Docker Desktop...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    )

    echo Wait until Docker Desktop is fully started, then run this file again.
    pause
    exit /b 1
)

echo.
echo Starting Docker Compose...
docker compose up -d --build
if errorlevel 1 (
    echo ERROR: docker compose failed.
    pause
    exit /b 1
)

echo.
echo Running containers:
docker ps --filter "name=model-server"

echo.
echo Waiting for local API: http://localhost:%PORT%/health
set "LOCAL_OK=0"

for /L %%i in (1,1,40) do (
    curl.exe -s -f http://localhost:%PORT%/health > nul 2>&1
    if not errorlevel 1 (
        set "LOCAL_OK=1"
        goto LOCAL_READY
    )

    echo Local API is not ready yet... attempt %%i/40
    timeout /t 2 /nobreak > nul
)

:LOCAL_READY
if "%LOCAL_OK%"=="0" (
    echo.
    echo ERROR: local API did not respond after waiting.
    echo.
    echo Docker container status:
    docker ps -a --filter "name=model-server"
    echo.
    echo Last logs from model-server:
    docker logs model-server --tail 80
    echo.
    pause
    exit /b 1
)

echo Local API is ready.
curl.exe -s http://localhost:%PORT%/health

echo.
echo.
echo Checking local models list...
curl.exe -s http://localhost:%PORT%/models

echo.
echo.
echo Starting ngrok tunnel in a new window...
taskkill /IM ngrok.exe /F > nul 2>&1
start "ngrok tunnel" cmd /k ngrok http %PORT% --domain=%DOMAIN%

echo Waiting for ngrok public URL: %BASE_URL%/health
set "PUBLIC_OK=0"

for /L %%i in (1,1,40) do (
    curl.exe -s -f -H "ngrok-skip-browser-warning: 1" %BASE_URL%/health > nul 2>&1
    if not errorlevel 1 (
        set "PUBLIC_OK=1"
        goto PUBLIC_READY
    )

    echo Public API is not ready yet... attempt %%i/40
    timeout /t 2 /nobreak > nul
)

:PUBLIC_READY
if "%PUBLIC_OK%"=="0" (
    echo.
    echo WARNING: public ngrok API did not respond automatically.
    echo Check the separate ngrok window. If it says "Session Status online",
    echo open this manually:
    echo %BASE_URL%/health
    echo.
) else (
    echo Public API is ready.
    curl.exe -s -H "ngrok-skip-browser-warning: 1" %BASE_URL%/health
)

echo.
echo.
echo ==== READY FOR DEMO ====
echo Base URL for Aurora:
echo %BASE_URL%
echo.
echo Health:
echo %BASE_URL%/health
echo.
echo Models:
echo %BASE_URL%/models
echo.
echo FastAPI docs:
echo %BASE_URL%/docs
echo.
echo Example model download:
echo %BASE_URL%/models/yolo11n_cls_224e30/download
echo.
echo IMPORTANT for Aurora developer:
echo Add this header to all ngrok requests:
echo ngrok-skip-browser-warning: 1
echo.
echo To stop demo, run:
echo start_demo.bat stop
echo.
pause
exit /b 0

:STOP
echo.
echo ==== Stopping demo ====
taskkill /IM ngrok.exe /F > nul 2>&1
docker compose down
echo Demo stopped.
pause
exit /b 0