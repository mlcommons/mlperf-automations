if defined MLC_LLVM_FORCE_VERSION (
    exit /b 0
)

"%MLC_LLVM_CLANG_BIN_WITH_PATH%" --version > tmp-ver.out
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

