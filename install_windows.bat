@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pytest -q
if errorlevel 1 goto :error
echo.
echo Install and test setup complete. Run run_windows.bat to open VIN 3D Studio.
pause
exit /b 0
:error
echo Setup failed. Copy the last error message and send it to Kai.
pause
exit /b 1
