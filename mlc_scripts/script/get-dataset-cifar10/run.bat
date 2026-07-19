wget -nc %MLC_DATASET_CIFAR10% --no-check-certificate
IF %ERRORLEVEL% NEQ 0 EXIT 1

del /Q /S %MLC_DATASET_FILENAME1%

gzip -d %MLC_DATASET_FILENAME%
IF %ERRORLEVEL% NEQ 0 EXIT 1

tar -xvf %MLC_DATASET_FILENAME1%
IF %ERRORLEVEL% NEQ 0 EXIT 1

del /Q /S %MLC_DATASET_FILENAME1%

echo MLC_DATASET_PATH=%CD%\cifar-10-batches-py > tmp-run-env.out
echo MLC_DATASET_CIFAR10_PATH=%CD%\cifar-10-batches-py >> tmp-run-env.out

if "%MLC_DATASET_CONVERT_TO_TINYMLPERF%" == "yes" (
 echo.
 echo Copying TinyMLPerf convertor ...
 echo.

 copy /B /Y %MLC_MLPERF_TINY_TRAINING_IC%\* .

 echo.
 echo Installing Python requirements ...
 echo.

 %MLC_PYTHON_BIN% -m pip install -r %MLC_TMP_CURRENT_SCRIPT_PATH%\requirements.txt
 IF %ERRORLEVEL% NEQ 0 EXIT 1

 echo.
 echo Converting ...
 echo.

 %MLC_PYTHON_BIN% perf_samples_loader.py
 IF %ERRORLEVEL% NEQ 0 EXIT 1

 copy /B /Y y_labels.csv perf_samples

 echo MLC_DATASET_CIFAR10_TINYMLPERF_PATH=%CD%\perf_samples >> tmp-run-env.out

 echo.
 echo Copying to EEMBC runner user space ...
 echo.
 
 copy /B /Y perf_samples\* %MLC_EEMBC_ENERGY_RUNNER_DATASETS%\ic01
)

