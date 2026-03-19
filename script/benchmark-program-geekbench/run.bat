@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Geekbench (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

rem Register license if key is provided
if not "!MLC_GEEKBENCH_LICENSE_KEY!" == "" (
  echo.
  echo Registering Geekbench license...
  "!MLC_GEEKBENCH_BIN_WITH_PATH!" --unlock !MLC_GEEKBENCH_LICENSE_EMAIL! !MLC_GEEKBENCH_LICENSE_KEY!
  if !ERRORLEVEL! NEQ 0 (
    echo WARNING: Geekbench license registration failed, continuing anyway
  ) else (
    echo Geekbench license registered successfully.
  )
)

rem Info-only mode (sysinfo, gpu-list, workload-list, load)
if "%MLC_GEEKBENCH_INFO_ONLY_MODE%" == "yes" (
  echo.
  echo Running: %MLC_RUN_CMD%
  %MLC_RUN_CMD%
  exit /b !ERRORLEVEL!
)

set NUM_RUNS=%MLC_GEEKBENCH_NUM_RUNS%
set RESULTS_DIR=%MLC_GEEKBENCH_RESULTS_DIR%
set SPLIT_SC_MC=%MLC_GEEKBENCH_SPLIT_SC_MC%
set CORE_PINNING=%MLC_GEEKBENCH_CORE_PINNING%
set AFFINITY_MASK=%MLC_GEEKBENCH_AFFINITY_MASK%

if "%NUM_RUNS%" == "" set NUM_RUNS=1
if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%SPLIT_SC_MC%" == "" set SPLIT_SC_MC=no

set "HAS_LICENSE=no"
if defined MLC_GEEKBENCH_LICENSE_KEY set "HAS_LICENSE=yes"
echo.
echo ***********************************************************************
echo Running Geekbench benchmark
echo   Number of runs: %NUM_RUNS%
if "%SPLIT_SC_MC%" == "yes" (
  echo   Mode: Split SC ^(pinned^) + MC ^(unpinned^)
  echo   SC command: %MLC_GEEKBENCH_BASE_CMD_SC%
  echo   MC command: %MLC_GEEKBENCH_BASE_CMD_MC%
) else (
  echo   Base command: %MLC_GEEKBENCH_BASE_CMD%
)
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  rem Record run start time
  for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
    set /a "run_start_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
  )

  if "!SPLIT_SC_MC!" == "yes" (
    rem --- SPLIT MODE: SC pinned, MC unpinned ---

    rem Single-core run (with core pinning)
    set "SC_JSON=%RESULTS_DIR%\geekbench_run%%R_sc.json"
    set "SC_CSV=%RESULTS_DIR%\geekbench_run%%R_sc.csv"
    set "SC_TIMING=%RESULTS_DIR%\geekbench_run%%R_sc_timing.json"
    set "SC_EXPORT="
    if "!HAS_LICENSE!"=="yes" set "SC_EXPORT=--export-json "!SC_JSON!" --export-csv "!SC_CSV!"

    echo.
    echo --- Single-Core ^(pinned^) ---

    if "%CORE_PINNING%" == "yes" (
      set "SC_FULL=start "" /b /wait /affinity %AFFINITY_MASK% %MLC_GEEKBENCH_BASE_CMD_SC% !SC_EXPORT!"
    ) else (
      set "SC_FULL=%MLC_GEEKBENCH_BASE_CMD_SC% !SC_EXPORT!"
    )
    echo Command: !SC_FULL!

    for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
      set /a "sc_start_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
    )

    !SC_FULL!
    set sc_exit=!ERRORLEVEL!

    for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
      set /a "sc_end_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
    )
    set /a "sc_dur_ms=sc_end_ms-sc_start_ms"
    if !sc_dur_ms! LSS 0 set /a "sc_dur_ms+=86400000"
    set /a "sc_dur_sec=sc_dur_ms/1000"
    set /a "sc_dur_frac=sc_dur_ms%%1000"

    echo {"run": %%R, "phase": "SC", "duration_sec": !sc_dur_sec!.!sc_dur_frac!} > "!SC_TIMING!"
    echo SC duration: !sc_dur_sec!.!sc_dur_frac!s

    if !sc_exit! NEQ 0 (
      echo Geekbench single-core exited with status: !sc_exit! ^(run %%R^)
      exit /b !sc_exit!
    )

    if exist "!SC_JSON!" (
      echo SC JSON results saved: !SC_JSON!
    ) else (
      echo WARNING: SC JSON results not found at !SC_JSON!
    )

    rem Multi-core run (no core pinning)
    set "MC_JSON=%RESULTS_DIR%\geekbench_run%%R_mc.json"
    set "MC_CSV=%RESULTS_DIR%\geekbench_run%%R_mc.csv"
    set "MC_TIMING=%RESULTS_DIR%\geekbench_run%%R_mc_timing.json"
    set "MC_EXPORT="
    if "!HAS_LICENSE!"=="yes" set "MC_EXPORT=--export-json "!MC_JSON!" --export-csv "!MC_CSV!"
    set "MC_FULL=%MLC_GEEKBENCH_BASE_CMD_MC% !MC_EXPORT!"

    echo.
    echo --- Multi-Core ^(unpinned^) ---
    echo Command: !MC_FULL!

    for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
      set /a "mc_start_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
    )

    !MC_FULL!
    set mc_exit=!ERRORLEVEL!

    for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
      set /a "mc_end_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
    )
    set /a "mc_dur_ms=mc_end_ms-mc_start_ms"
    if !mc_dur_ms! LSS 0 set /a "mc_dur_ms+=86400000"
    set /a "mc_dur_sec=mc_dur_ms/1000"
    set /a "mc_dur_frac=mc_dur_ms%%1000"

    echo {"run": %%R, "phase": "MC", "duration_sec": !mc_dur_sec!.!mc_dur_frac!} > "!MC_TIMING!"
    echo MC duration: !mc_dur_sec!.!mc_dur_frac!s

    if !mc_exit! NEQ 0 (
      echo Geekbench multi-core exited with status: !mc_exit! ^(run %%R^)
      exit /b !mc_exit!
    )

    if exist "!MC_JSON!" (
      echo MC JSON results saved: !MC_JSON!
    ) else (
      echo WARNING: MC JSON results not found at !MC_JSON!
    )

  ) else (
    rem --- NORMAL MODE ---

    set "JSON_FILE=%RESULTS_DIR%\geekbench_run%%R.json"
    set "CSV_FILE=%RESULTS_DIR%\geekbench_run%%R.csv"
    set "EXPORT_ARGS="
    if "!HAS_LICENSE!"=="yes" set "EXPORT_ARGS=--export-json "!JSON_FILE!" --export-csv "!CSV_FILE!"

    if "%CORE_PINNING%" == "yes" (
      set "FULL_CMD=start "" /b /wait /affinity %AFFINITY_MASK% %MLC_GEEKBENCH_BASE_CMD% !EXPORT_ARGS!"
    ) else (
      set "FULL_CMD=%MLC_GEEKBENCH_BASE_CMD% !EXPORT_ARGS!"
    )

    echo Command: !FULL_CMD!

    !FULL_CMD!
    set exitstatus=!ERRORLEVEL!

    if !exitstatus! NEQ 0 (
      echo.
      echo Geekbench exited with status: !exitstatus! ^(run %%R^)
      exit /b !exitstatus!
    )

    if exist "!JSON_FILE!" (
      echo JSON results saved: !JSON_FILE!
    ) else (
      echo WARNING: JSON results file not found at !JSON_FILE!
    )

    if exist "!CSV_FILE!" (
      echo CSV results saved: !CSV_FILE!
    )
  )

  rem Record total run timing
  for /f "tokens=1-4 delims=:." %%a in ("!time!") do (
    set /a "run_end_ms=(((%%a*60)+%%b)*60+%%c)*1000+%%d*10"
  )
  set /a "run_dur_ms=run_end_ms-run_start_ms"
  if !run_dur_ms! LSS 0 set /a "run_dur_ms+=86400000"
  set /a "run_dur_sec=run_dur_ms/1000"
  set /a "run_dur_frac=run_dur_ms%%1000"

  set "TIMING_FILE=%RESULTS_DIR%\geekbench_run%%R_timing.json"
  echo {"run": %%R, "phase": "total", "duration_sec": !run_dur_sec!.!run_dur_frac!} > "!TIMING_FILE!"
  echo Run %%R total duration: !run_dur_sec!.!run_dur_frac!s
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% Geekbench run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
