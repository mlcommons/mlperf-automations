@echo off
setlocal

:: Define download URL and filename
set "URL=https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox-0.12.6-1.msvc2015-win64.exe"
set "FILE=wkhtmltox-0.12.6-1.msvc2015-win64.exe"

:: Download the installer if it doesn't already exist
if not exist "%FILE%" (
    echo Downloading %FILE%...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%URL%', '%CD%\%FILE%')"
    if %ERRORLEVEL% neq 0 (
        echo Download failed!
        exit /b %ERRORLEVEL%
    )
)

:: Install the software (silent mode)
echo Installing wkhtmltopdf...
start /wait %FILE% /S

if %ERRORLEVEL% neq 0 (
    echo Installation failed!
    exit /b %ERRORLEVEL%
)

echo Installation successful!

endlocal
exit /b 0
