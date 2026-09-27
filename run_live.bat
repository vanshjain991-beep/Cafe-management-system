@echo off
title COFFEE & LOVE - LIVE PUBLIC SERVER
cd /d "%~dp0"
echo =============================================================
echo   COFFEE & LOVE - Starting Live Public Server...
echo =============================================================
echo.
.\.venv\Scripts\python.exe start_live.py
pause
