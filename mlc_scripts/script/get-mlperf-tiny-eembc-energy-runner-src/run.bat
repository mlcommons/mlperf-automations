@echo off

set CUR_DIR=%cd%
set SCRIPT_DIR=%MLC_TMP_CURRENT_SCRIPT_PATH%

echo ******************************************************
echo Cloning EEMBC Energy Runner from %MLC_GIT_URL% with branch %MLC_GIT_CHECKOUT% %MLC_GIT_DEPTH% %MLC_GIT_RECURSE_SUBMODULES% ...

set folder=src

if not exist %folder% (

  if not "%MLC_GIT_SHA%" == "" (
       git clone %MLC_GIT_RECURSE_SUBMODULES% -b "%MLC_GIT_CHECKOUT%" %MLC_GIT_URL% %MLC_GIT_DEPTH% %folder%
       IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
       cd %folder%
  ) else (
       git clone %MLC_GIT_RECURSE_SUBMODULES% %MLC_GIT_URL% %MLC_GIT_DEPTH% %folder%
       IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
       cd %folder%

       git checkout "%MLC_GIT_CHECKOUT%"
       IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
  )
) else (

  cd %folder%

)


if not "%MLC_GIT_SUBMODULES%" == "" (
  for /F %%s in ("%MLC_GIT_SUBMODULES%") do (
    echo.
    echo Initializing submodule %%s
    git submodule update --init %%s
    IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
  )
)


if "%MLC_GIT_PATCH%" == "yes" (
   echo Git patching is not yet implemented in CM script "get-mlperf-tiny-src" - please add it!
   pause

   rem  set patch_filename=%MLC_GIT_PATCH_FILENAME%
   rem  if [ ! -n ${MLC_GIT_PATCH_FILENAMES} ]; then
   rem    patchfile=${MLC_GIT_PATCH_FILENAME:-"git.patch"}
   rem    MLC_GIT_PATCH_FILENAMES=$patchfile
   rem  fi
   rem
   rem  IFS=', ' read -r -a patch_files <<< ${MLC_GIT_PATCH_FILENAMES}
   rem
   rem  for patch_filename in "${patch_files[@]}"
   rem  do
   rem    echo "Applying patch ${SCRIPT_DIR}/patch/$patch_filename"
   rem    git apply ${SCRIPT_DIR}/patch/"$patch_filename"
   rem    if [ "${?}" != "0" ]; then exit 1; fi
   rem  done

)

rem Based on https://github.com/mwangistan/inference
for %%f in (%SCRIPT_DIR%\patch\windows-*) do (
  echo %%f
  patch -p1 < %%f
)


cd %CUR_DIR%

exit /b 0
