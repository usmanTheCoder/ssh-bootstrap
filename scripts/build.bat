@echo off
echo ============================================================
echo SSH Configuration Manager - Build Script
echo ============================================================
echo.

REM Change to project root
cd /d "%~dp0.."

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
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager --additional-hooks-dir=scripts --collect-all=customtkinter --clean --noconfirm main.py

echo.
echo ============================================================
if exist dist\SSH_Configuration_Manager.exe (
    echo BUILD SUCCESSFUL!
    echo Executable location: dist\SSH_Configuration_Manager.exe
) else (
    echo BUILD FAILED!
)
echo ============================================================
echo.
pause
