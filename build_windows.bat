@echo off
REM ---------------------------------------------------------------------------
REM Build a standalone Windows .exe for KeyCast Viewer.
REM Run this on a Windows machine with Python 3.9+ installed.
REM ---------------------------------------------------------------------------
setlocal

echo [1/4] Creating virtual environment...
python -m venv .venv || goto :error
call .venv\Scripts\activate.bat || goto :error

echo [2/4] Installing dependencies...
python -m pip install --upgrade pip || goto :error
pip install -r requirements.txt pyinstaller || goto :error

echo [3/4] Building executable with PyInstaller...
pyinstaller --noconfirm keycast.spec || goto :error

echo [4/4] Done.
echo Executable is at: dist\KeyCastViewer.exe
goto :eof

:error
echo.
echo Build FAILED. See the messages above.
exit /b 1
