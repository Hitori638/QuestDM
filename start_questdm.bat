@echo off
setlocal EnableDelayedExpansion
title QuestDM Production Launcher
chcp 65001 >nul
cls

:: === Set environment variables for production ===
set FLASK_ENV=production
set FLASK_DEBUG=0

:: === Set up log file ===
set "LOGFILE=%~dp0questdm_log.txt"
if exist "%LOGFILE%" del "%LOGFILE%"
echo QuestDM Launcher Log > "%LOGFILE%"
echo Started on %date% %time% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo ========================================
echo         QuestDM Production Launcher        
echo ========================================
echo.

:: === Define BASE_DIR and REQ_FILE using relative paths ===
:: BASE_DIR points to the inner QuestDM folder containing Frontend and Backend.
set "BASE_DIR=%~dp0QuestDM"
:: REQ_FILE is located in the outer QuestDM folder.
set "REQ_FILE=%~dp0requirements.txt"

echo [INFO] BASE_DIR: %BASE_DIR%
echo [INFO] REQ_FILE: %REQ_FILE%
echo. >> "%LOGFILE%"
echo [INFO] BASE_DIR: %BASE_DIR% >> "%LOGFILE%"
echo [INFO] REQ_FILE: %REQ_FILE% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

:: === Scan BASE_DIR for subdirectories "Frontend" and "Backend" ===
set "foundFrontend="
set "foundBackend="

for /d %%A in ("%BASE_DIR%\*") do (
    if /i "%%~nA"=="Frontend" (
        set "foundFrontend=%%A"
    )
    if /i "%%~nA"=="Backend" (
        set "foundBackend=%%A"
    )
)

if defined foundFrontend (
    set "FRONTEND_DIR=!foundFrontend!"
    echo [OK] Found Frontend directory: !FRONTEND_DIR!
    echo [INFO] Found Frontend directory: !FRONTEND_DIR! >> "%LOGFILE%"
) else (
    echo ERROR: Frontend directory not found in %BASE_DIR%
    echo ERROR: Frontend directory not found in %BASE_DIR% >> "%LOGFILE%"
    pause
    exit /b
)

if defined foundBackend (
    set "BACKEND_DIR=!foundBackend!"
    echo [OK] Found Backend directory: !BACKEND_DIR!
    echo [INFO] Found Backend directory: !BACKEND_DIR! >> "%LOGFILE%"
) else (
    echo ERROR: Backend directory not found in %BASE_DIR%
    echo ERROR: Backend directory not found in %BASE_DIR% >> "%LOGFILE%"
    pause
    exit /b
)

:: (Optional) Display log file contents for review
echo.
echo ----- LOG FILE CONTENTS -----
type "%LOGFILE%"
echo -----------------------------

:: === 1. Install Backend Dependencies ===
echo.
echo [1/6] Setting up Backend Environment...
echo [INFO] Changing directory to Backend: %BACKEND_DIR% >> "%LOGFILE%"
cd /d "%BACKEND_DIR%"
echo Installing Python dependencies from %REQ_FILE%...
echo [INFO] Running: call pip install -r "%REQ_FILE%" >> "%LOGFILE%"
call pip install -r "%REQ_FILE%" >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies!
    pause
    exit /b
)
echo Backend dependencies installed.
echo [INFO] Backend dependencies installed. >> "%LOGFILE%"

:: === 2. Install Frontend Dependencies ===
echo.
echo [2/6] Setting up Frontend Environment...
echo [INFO] Changing directory to Frontend: %FRONTEND_DIR% >> "%LOGFILE%"
cd /d "%FRONTEND_DIR%"
echo Running npm install...
echo [INFO] Running: call npm install >> "%LOGFILE%"
call npm install >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies!
    pause
    exit /b
)
echo Frontend dependencies installed.
echo [INFO] Frontend dependencies installed. >> "%LOGFILE%"

:: === 3. Build Frontend Production Assets ===
echo.
echo [3/6] Building Frontend Production Assets...
cd /d "%FRONTEND_DIR%"
echo Running npm run build...
echo [INFO] Running: call npm run build >> "%LOGFILE%"
call npm run build >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend production assets!
    pause
    exit /b
)
echo Frontend production build completed.
echo [INFO] Frontend production build completed. >> "%LOGFILE%"

:: === 4. Launch Servers Silently Using VBScript ===
echo.
echo [4/6] Launching servers...
(
    echo Set WshShell = CreateObject("WScript.Shell")
    echo WshShell.Run "cmd /c cd /d %BACKEND_DIR% && waitress-serve --listen=127.0.0.1:5000 app:app", 0, False
    echo WshShell.Run "cmd /c cd /d %FRONTEND_DIR% && npm run preview", 0, False
) > "%~dp0launch_hidden.vbs"

cscript //nologo "%~dp0launch_hidden.vbs"
echo [INFO] Servers launched.

:: === 5. Open Browser with Vue Application ===
echo.
echo [5/6] Opening browser to the Vue application...
start "" "http://localhost:4173/"

:: === 6. Final Status: Remain open until exit ===
echo.
echo ========================================
echo         QuestDM is now running!        
echo ========================================
echo.
echo Access the Backend at: http://127.0.0.1:5000/
echo Check your browser for the Vue application.
echo.
echo [INFO] To quit QuestDM, press any key.
pause

:: --- Cleanup: Kill Python, Node.js, and ollama_llama_server.exe processes ---
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM ollama_llama_server.exe >nul 2>&1

endlocal
