@echo off
title Running Python Script with Logging

:: Check if tee is available
where tee >nul 2>nul
if errorlevel 1 goto no_tee

echo 'tee' found.
echo(
:: Continue normal script...

goto continue_script

:no_tee
echo(
echo =======================
echo   'tee' command not found!
echo =======================
echo(
echo This script requires 'tee' to log and display output.
echo(
echo How to install 'tee':
echo(
echo 1. Install Git for Windows: https://gitforwindows.org/
echo    (Recommended - comes with 'tee' and many useful tools)
echo(
echo 2. Or install Gow (Gnu On Windows): https://github.com/bmatzelle/gow/releases
echo(
echo After installing, please re-run this script.
echo(
pause
exit /b 1

:continue_script
:: If tee is found, continue
echo Continuing...
echo.

:: ------------------ Your existing script starts here ------------------
:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Enable logging
set LOGFILE=logs\Script_log.txt

:: Overwrite the log file if it exists at the start
echo _______________________________ > "%LOGFILE%"
echo Script started at %date% %time% | tee -a "%LOGFILE%"
echo _______________________________ | tee -a "%LOGFILE%"

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Check if virtual environment activated
if not defined VIRTUAL_ENV (
    echo Failed to activate the virtual environment. | tee -a "%LOGFILE%"
    exit /b 1
)

:: Log the activation
echo Virtual environment activated. | tee -a "%LOGFILE%"
echo _______________________________ | tee -a "%LOGFILE%"

:: Run the Python script and log its output
python main.py 2>&1 | tee -a "%LOGFILE%"
if errorlevel 1 (
    echo Python script failed to run. | tee -a "%LOGFILE%"
    exit /b 1
)

echo Python script executed successfully. | tee -a "%LOGFILE%"
echo _______________________________ | tee -a "%LOGFILE%"
echo Script finished at %date% %time% | tee -a "%LOGFILE%"
echo _______________________________ | tee -a "%LOGFILE%"

echo Log file created at %LOGFILE%
pause
exit /b 0
:: End of script
