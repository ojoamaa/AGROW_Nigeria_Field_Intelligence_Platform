@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo This setup must be run as Administrator.
  echo Right-click this file and choose "Run as administrator".
  pause
  exit /b 1
)

echo Creating Windows Firewall rule for AGROW Streamlit port 8501...
netsh advfirewall firewall delete rule name="AGROW Streamlit 8501" >nul 2>&1
netsh advfirewall firewall add rule name="AGROW Streamlit 8501" dir=in action=allow protocol=TCP localport=8501 profile=private

echo.
echo Firewall setup completed. Start AGROW again with run_app.bat.
pause
