@echo off
setlocal enabledelayedexpansion

set "CUR_DIR=%CD%"
echo %CUR_DIR%
set "SCRIPT_DIR=%MLC_TMP_CURRENT_SCRIPT_PATH%"
set "ENV_OUT_FILE=%CUR_DIR%\tmp-run-env.out"

set "folder=%MLC_GIT_CHECKOUT_FOLDER%"

if not exist "%MLC_TMP_GIT_PATH%" (
    if exist "%folder%" (
        echo rmdir /s /q "%folder%"
        rmdir /s /q "%folder%"
    )
    echo ******************************************************
    echo Current directory: %CUR_DIR%
    echo.
    echo Cloning %MLC_GIT_REPO_NAME% from %MLC_GIT_URL%
    echo.
    echo %MLC_GIT_CLONE_CMD%
    echo.

    %MLC_GIT_CLONE_CMD%
    
    :: Retry clone once on failure
    if ERRORLEVEL 1 (
        if exist "%folder%" rmdir /s /q "%folder%"
        %MLC_GIT_CLONE_CMD%
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!
    )

    :: /d ensures drive letter changes if necessary
    cd /d "%folder%"

    if not "%MLC_GIT_SHA%"=="" (
        echo.
        echo git checkout -b %MLC_GIT_SHA% %MLC_GIT_SHA%
        git checkout -b %MLC_GIT_SHA% %MLC_GIT_SHA%
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!

    ) else if not "%MLC_GIT_CHECKOUT_TAG%"=="" (
        echo.
        echo git fetch --all --tags
        git fetch --all --tags
        echo git checkout tags/%MLC_GIT_CHECKOUT_TAG% -b %MLC_GIT_CHECKOUT_TAG%
        git checkout tags/%MLC_GIT_CHECKOUT_TAG% -b %MLC_GIT_CHECKOUT_TAG%
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!
    )
) else (
    cd /d "%folder%"
)

:: ---------------------------------------------------------
:: Capture Checkout & SHA information
:: ---------------------------------------------------------
:: Determine the active branch name
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD') do set "ACTUAL_CHECKOUT=%%i"

:: Fallback to detached HEAD hash
if "%ACTUAL_CHECKOUT%"=="HEAD" (
    for /f "delims=" %%i in ('git rev-parse HEAD') do set "ACTUAL_CHECKOUT=%%i"
)

for /f "delims=" %%i in ('git rev-parse HEAD') do set "CURRENT_SHA=%%i"

:: Write to out file (No space before >> prevents trailing spaces in value)
echo MLC_GIT_CHECKOUT=!ACTUAL_CHECKOUT!>>"%ENV_OUT_FILE%"
echo MLC_GIT_SHA=!CURRENT_SHA!>>"%ENV_OUT_FILE%"

:: ---------------------------------------------------------
:: Apply PR, Cherry-picks, and Patches
:: ---------------------------------------------------------
if not "%MLC_GIT_PR_TO_APPLY%"=="" (
    echo.
    echo Fetching from %MLC_GIT_PR_TO_APPLY%
    git fetch origin %MLC_GIT_PR_TO_APPLY%:tmp-apply
    
    :: Log the PR applied
    echo MLC_GIT_APPLIED_PR=%MLC_GIT_PR_TO_APPLY%>>"%ENV_OUT_FILE%"
)

if not "%MLC_GIT_CHERRYPICKS%"=="" (
    :: Log the cherry-picks applied
    echo MLC_GIT_APPLIED_CHERRYPICKS=%MLC_GIT_CHERRYPICKS%>>"%ENV_OUT_FILE%"
    
    :: Replace semicolons with quoted spaces to safely loop in Windows
    set "CPS="%MLC_GIT_CHERRYPICKS:;=" "%""
    for %%c in (!CPS!) do (
        echo.
        echo Applying cherrypick %%~c
        git cherry-pick -n %%~c
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!
    )
)

if not "%MLC_GIT_SUBMODULES%"=="" (
    set "SUBS="%MLC_GIT_SUBMODULES:;=" "%""
    for %%s in (!SUBS!) do (
        echo.
        echo Initializing submodule %%~s
        git submodule update --init --recursive --checkout --force "%%~s"
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!
    )
)

if "%MLC_GIT_PATCH%"=="yes" (
    :: Log the patches applied
    echo MLC_GIT_APPLIED_PATCHES=%MLC_GIT_PATCH_FILEPATHS%>>"%ENV_OUT_FILE%"
    
    set "PATCHES="%MLC_GIT_PATCH_FILEPATHS:;=" "%""
    for %%p in (!PATCHES!) do (
        echo.
        echo Applying patch %%~p
        git apply "%%~p"
        if ERRORLEVEL 1 exit /b !ERRORLEVEL!
    )
)

cd /d "%CUR_DIR%"
