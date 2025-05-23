rem echo %MLC_PYTHON_BIN%
rem echo %MLC_DATASET_PATH%
rem echo %MLC_DATASET_AUX_PATH%
rem echo %MLC_ML_MODEL_FILE_WITH_PATH%

rem connect CM intelligent components with CK env
set CK_ENV_ONNX_MODEL_ONNX_FILEPATH=%MLC_ML_MODEL_FILE_WITH_PATH%
set CK_ENV_ONNX_MODEL_INPUT_LAYER_NAME=input_tensor:0
set CK_ENV_ONNX_MODEL_OUTPUT_LAYER_NAME=softmax_tensor:0
set CK_ENV_DATASET_IMAGENET_VAL=%MLC_DATASET_PATH%
set CK_CAFFE_IMAGENET_SYNSET_WORDS_TXT=%MLC_DATASET_AUX_PATH%\synset_words.txt
set ML_MODEL_DATA_LAYOUT=NCHW
set CK_BATCH_SIZE=%MLC_BATCH_SIZE%
set CK_BATCH_COUNT=%MLC_BATCH_COUNT%

IF NOT DEFINED MLC_TMP_CURRENT_SCRIPT_PATH SET MLC_TMP_CURRENT_SCRIPT_PATH=%CD%

IF DEFINED MLC_INPUT SET MLC_IMAGE=%MLC_INPUT%

echo.
%MLC_PYTHON_BIN_WITH_PATH% -m pip install -r %MLC_TMP_CURRENT_SCRIPT_PATH%\requirements.txt
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo.
%MLC_PYTHON_BIN_WITH_PATH% %MLC_TMP_CURRENT_SCRIPT_PATH%\src\onnx_classify.py
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

rem Just a demo to pass environment variables from native scripts back to CM workflows
echo MLC_APP_IMAGE_CLASSIFICATION_ONNX_PY=sucess > tmp-run-env.out
