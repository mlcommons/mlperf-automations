@echo off

set CUR_DIR=%cd%
set SCRIPT_DIR=%MLC_TMP_CURRENT_SCRIPT_PATH%

if not exist install mkdir install

set INSTALL_DIR=%CUR_DIR%\install

cd %MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH%

if not "%MLC_DATASET_SIZE%" == "" (
  set MAX_IMAGES=--max-images %MLC_DATASET_SIZE% --seed 42
) else (
   set MAX_IMAGES=
)

%MLC_PYTHON_BIN% tools\openimages.py %MAX_IMAGES% --dataset-dir=%INSTALL_DIR% --output-labels=openimages-mlperf.json --classes %MLC_DATASET_OPENIMAGES_CLASSES%
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

rem Next is a hack to support MLPerf inference on Windows
cd %INSTALL_DIR%
if not exist validation\data\annotations mkdir validation\data\annotations
copy annotations\* validation\data\annotations
