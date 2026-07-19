del /Q /S rclone-v%MLC_VERSION%-windows-amd64.zip > NUL 2>&1

wget --no-check-certificate https://downloads.rclone.org/v%MLC_VERSION%/rclone-v%MLC_VERSION%-windows-amd64.zip
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

unzip -o rclone-v%MLC_VERSION%-windows-amd64.zip
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

move /Y rclone-v%MLC_VERSION%-windows-amd64\* .

del /Q /S rclone-v%MLC_VERSION%-windows-amd64.zip > NUL 2>&1

