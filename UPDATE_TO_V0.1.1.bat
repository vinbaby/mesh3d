@echo off
setlocal
cd /d "%~dp0"

echo.
echo VIN 3D Studio - incremental updater v0.1.1
echo This updates only app\main.py. It does not reinstall dependencies.
echo.

if not exist "app\main.py" (
  echo ERROR: app\main.py was not found.
  echo Put this updater in the root of your existing VIN 3D Studio folder.
  pause
  exit /b 1
)

set "UPDATE_URL=https://raw.githubusercontent.com/vinbaby/mesh3d/main/updates/v0.1.1/app/main.py"
set "TEMP_FILE=%TEMP%\vin3d-studio-main-v0.1.1.py"
set "BACKUP_FILE=app\main.py.before-v0.1.1.bak"

echo [1/4] Downloading the versioned update...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%UPDATE_URL%' -OutFile '%TEMP_FILE%'"
if errorlevel 1 goto download_failed
if not exist "%TEMP_FILE%" goto download_failed

findstr /c:"class StudioWindow" "%TEMP_FILE%" >nul
if errorlevel 1 goto invalid_payload
findstr /c:"Silhouette mesh" "%TEMP_FILE%" >nul
if errorlevel 1 goto invalid_payload

echo [2/4] Saving a backup of the current file...
if not exist "%BACKUP_FILE%" copy /y "app\main.py" "%BACKUP_FILE%" >nul
if errorlevel 1 goto backup_failed

echo [3/4] Replacing app\main.py...
copy /y "%TEMP_FILE%" "app\main.py" >nul
if errorlevel 1 goto restore_backup

echo [4/4] Checking Python syntax...
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe -m py_compile "app\main.py"
) else (
  py -3 -m py_compile "app\main.py"
)
if errorlevel 1 goto restore_backup

del "%TEMP_FILE%" >nul 2>&1
echo.
echo UPDATE SUCCESS: v0.1.1 has been applied.
echo Only app\main.py was updated. Dependencies were not reinstalled.
echo Backup: %BACKUP_FILE%
echo Run run_windows.bat to test the updated Studio.
echo.
pause
exit /b 0

:download_failed
echo ERROR: Could not download the update. Check your internet connection.
del "%TEMP_FILE%" >nul 2>&1
pause
exit /b 1

:invalid_payload
echo ERROR: The downloaded file did not pass basic validation. Nothing was changed.
del "%TEMP_FILE%" >nul 2>&1
pause
exit /b 1

:backup_failed
echo ERROR: Could not create the backup. Nothing was changed.
del "%TEMP_FILE%" >nul 2>&1
pause
exit /b 1

:restore_backup
echo ERROR: The update failed its syntax check. Restoring the previous app/main.py...
if exist "%BACKUP_FILE%" copy /y "%BACKUP_FILE%" "app\main.py" >nul
del "%TEMP_FILE%" >nul 2>&1
echo Previous file restored. Send Kai the error shown above.
pause
exit /b 1
