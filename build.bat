@echo off
echo ============================================================
echo SSH Bootstrap Tool - Build Script
echo Developed by M. Usman Sharif ^& M. Umair Khan
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

REM Build the executable
echo.
echo Building executable...
pyinstaller --onefile --windowed --name=SSH_Bootstrap_Tool --clean remote_ssh_gui.py

echo.
echo ============================================================
if exist dist\SSH_Bootstrap_Tool.exe (
    echo BUILD SUCCESSFUL!
    echo Executable location: dist\SSH_Bootstrap_Tool.exe
) else (
    echo BUILD FAILED!
)
echo ============================================================
echo.
pause
