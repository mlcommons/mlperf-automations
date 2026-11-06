@echo off
if "%MLC_PYTHON_BIN_WITH_PATH%"=="" (set MLC_PYTHON_BIN=python) else (set MLC_PYTHON_BIN=%MLC_PYTHON_BIN_WITH_PATH%)
if "%MLC_TMP_CURRENT_SCRIPT_PATH%"=="" (set MLC_TMP_CURRENT_SCRIPT_PATH=%CD%)

echo WebArena run is delegated to the benchmark-program dependency (MLC_RUN_CMD).
exit /b 0
