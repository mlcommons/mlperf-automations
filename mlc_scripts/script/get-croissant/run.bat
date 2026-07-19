@echo off

echo =======================================================

cd %MLC_MLCOMMONS_CROISSANT_PATH%\python\mlcroissant
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo.
echo Running %MLC_PYTHON_BIN_WITH_PATH% -m pip install -e .[git]

%MLC_PYTHON_BIN_WITH_PATH% -m pip install -e .[git]
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo.
echo Validating Croissant ...

mlcroissant validate --file ../../datasets/titanic/metadata.json
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo =======================================================
