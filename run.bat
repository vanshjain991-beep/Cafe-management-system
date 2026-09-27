@echo off
title COFFEE & LOVE - Cafe Management Server
cd /d "%~dp0"
echo ========================================================
echo   COFFEE & LOVE - Cafe Management Server Starting...
echo ========================================================
echo.
echo Local PC URL:      http://localhost:5000
echo Mobile / Wi-Fi URL: http://10.207.88.213:5000
echo.
echo Admin Login:   ADMIN001 / admin123
echo Manager Login: MGR001   / mgr123
echo Staff Login:   STF101   / staff123
echo ========================================================
echo.
.\.venv\Scripts\python.exe app.py
pause
