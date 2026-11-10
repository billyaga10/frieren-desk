@echo off
setlocal
cd /d "%~dp0"

echo [Frieren Desk Companion] Memeriksa environment Windows...

if not exist ".venv\Scripts\python.exe" (
    echo [Frieren Desk] Virtual environment belum ditemukan. Membuat .venv...
    where python >nul 2>&1
    if not errorlevel 1 (
        python -m venv .venv
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m venv .venv
    ) else (
        echo [ERROR] Python belum terinstall atau belum ada di PATH Windows kamu.
        echo Silakan unduh Python di https://www.python.org/downloads/ lalu centang "Add Python to PATH".
        pause
        exit /b 1
    )
    echo [Frieren Desk] Menginstall dependencies...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\pip.exe install -r requirements.txt
)

echo [Frieren Desk] Menjalankan Frieren Desk Companion...
start "" ".venv\Scripts\pythonw.exe" "main.py"
if errorlevel 1 (
    .venv\Scripts\python.exe "main.py"
)
exit /b 0
