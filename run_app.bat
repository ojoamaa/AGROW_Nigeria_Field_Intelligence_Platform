@echo off
setlocal
cd /d "%~dp0"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip=(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object {$_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' -and $_.InterfaceOperationalStatus -eq 'Up'} ^| Sort-Object InterfaceMetric ^| Select-Object -First 1 -ExpandProperty IPAddress); if($ip){$ip}else{'localhost'}"`) do set "AGROW_LAN_IP=%%I"

set "APP_DATA_DIR=%USERPROFILE%\AGROW_DATA"
set "AGROW_LOCAL_BASE_URL=http://%AGROW_LAN_IP%:8501"

echo.
echo ==========================================================
echo AGROW Local Pilot
 echo Laptop URL: http://localhost:8501
 echo Phone URL : %AGROW_LOCAL_BASE_URL%
echo Data folder: %APP_DATA_DIR%
echo ==========================================================
echo.
echo Keep this window open while testing the QR code.
echo If the phone URL does not open, run SETUP_WINDOWS_FIREWALL.bat as Administrator once.
echo.

python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
