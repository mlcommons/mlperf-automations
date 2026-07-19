@echo off

del /Q /S %MLC_BAZEL_DOWNLOAD_FILE%
del /Q /S bazel.exe

wget -c %MLC_BAZEL_DOWNLOAD_URL% -O %MLC_BAZEL_DOWNLOAD_FILE% --no-check-certificate
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

ren %MLC_BAZEL_DOWNLOAD_FILE% bazel.exe
