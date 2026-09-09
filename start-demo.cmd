@echo off
cd /d "%~dp0"
py -3 -m glinx_discovery demo --serve
if errorlevel 1 pause
