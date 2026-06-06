@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo  NoirPlayer - Dual Video Player
echo ============================================================
echo.

:: Check for mpv-2.dll
if not exist "mpv\mpv-2.dll" (
    echo ERROR: mpv-2.dll not found in the mpv\ folder.
    echo.
    echo Please download the mpv portable build and place:
    echo   mpv.exe    -^> NoirPlayer\mpv\mpv.exe
    echo   mpv-2.dll  -^> NoirPlayer\mpv\mpv-2.dll
    echo.
    echo Download from: https://mpv.io/installation/
    echo ^(Use the Windows portable build^)
    echo.
    pause
    exit /b 1
)

:: Create venv if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python 3.8+ is installed and in your PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install/upgrade deps
echo Checking dependencies...
pip install --quiet --upgrade PyQt6 python-mpv pymediainfo
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies OK.
echo.

:: Run the player
echo Launching NoirPlayer...
echo.
python player.py
if errorlevel 1 (
    echo.
    echo NoirPlayer exited with an error.
    pause
)

endlocal
