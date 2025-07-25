@echo off
apptainer --version > tmp-ver.out
if %errorlevel% neq 0 exit /b 1
