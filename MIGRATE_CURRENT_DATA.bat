@echo off
setlocal
cd /d "%~dp0"
set "TARGET=%USERPROFILE%\AGROW_DATA"

if not exist "%TARGET%" mkdir "%TARGET%"
if exist "agrow.db" copy /Y "agrow.db" "%TARGET%\agrow.db" >nul
if exist "data" robocopy "data" "%TARGET%\data" /E /NFL /NDL /NJH /NJS /NC /NS >nul
if exist "uploads" robocopy "uploads" "%TARGET%\uploads" /E /NFL /NDL /NJH /NJS /NC /NS >nul

echo Existing local AGROW data has been copied to:
echo %TARGET%
echo.
echo Future releases will reuse this location automatically.
pause
