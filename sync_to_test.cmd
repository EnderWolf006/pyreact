@echo off
setlocal

set "SOURCE_ROOT=f:\Minecraft\pyreact"
set "TARGET_ROOT=D:\MCStudioDownload\work\enderwolf006@163.com\Cpp\AddOn\9effce647b95499db6c3a2dbe360470e\behavior_pack_WiETU4v9"
set "TARGET_UI_ROOT=D:\MCStudioDownload\work\enderwolf006@163.com\Cpp\AddOn\9effce647b95499db6c3a2dbe360470e\resource_pack_oCenoEJz\ui"

if not "%~1"=="" set "SOURCE_ROOT=%~1"
if not "%~2"=="" set "TARGET_ROOT=%~2"
if not "%~3"=="" set "TARGET_UI_ROOT=%~3"

set "SRC_PYREACT=%SOURCE_ROOT%\pyreact"
set "SRC_RUNTIME=%SOURCE_ROOT%\PyreactRuntimeScript"
set "SRC_RUNTIME_NATIVE=%SRC_RUNTIME%\native_runtime"
set "SRC_EXAMPLE=%SOURCE_ROOT%\PyreactExampleScript"
set "SRC_JSON_UI=%SOURCE_ROOT%\JsonUI"

set "DST_PYREACT=%TARGET_ROOT%\pyreact"
set "DST_RUNTIME=%TARGET_ROOT%\PyreactRuntimeScript"
set "DST_RUNTIME_NATIVE=%DST_RUNTIME%\native_runtime"
set "DST_EXAMPLE=%TARGET_ROOT%\PyreactExampleScript"
set "DST_RUNTIME_PYREACT=%DST_RUNTIME%\pyreact"
set "DST_EXAMPLE_PYREACT=%DST_EXAMPLE%\pyreact"
set "DST_JSON_UI=%TARGET_UI_ROOT%"

if not exist "%SOURCE_ROOT%" (
  echo [ERROR] SourceRoot not found: %SOURCE_ROOT%
  exit /b 1
)
if not exist "%TARGET_ROOT%" (
  echo [ERROR] TargetRoot not found: %TARGET_ROOT%
  exit /b 1
)
if not exist "%SRC_PYREACT%" (
  echo [ERROR] source pyreact not found: %SRC_PYREACT%
  exit /b 1
)
if not exist "%SRC_RUNTIME%" (
  echo [ERROR] source PyreactRuntimeScript not found: %SRC_RUNTIME%
  exit /b 1
)
if not exist "%SRC_RUNTIME_NATIVE%" (
  echo [ERROR] source runtime native_runtime not found: %SRC_RUNTIME_NATIVE%
  exit /b 1
)
if not exist "%SRC_EXAMPLE%" (
  echo [ERROR] source PyreactExampleScript not found: %SRC_EXAMPLE%
  exit /b 1
)
if not exist "%SRC_JSON_UI%" (
  echo [ERROR] source JsonUI not found: %SRC_JSON_UI%
  exit /b 1
)

echo [SYNC] pyreact -^> pyreact
robocopy "%SRC_PYREACT%" "%DST_PYREACT%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP /XD __pycache__ /XF *.pyc >nul
if errorlevel 8 (
  echo [ERROR] Robocopy failed: top-level pyreact
  exit /b 8
)

if exist "%DST_RUNTIME_PYREACT%" (
  echo [CLEAN] remove legacy PyreactRuntimeScript\pyreact
  rmdir /S /Q "%DST_RUNTIME_PYREACT%"
)

if exist "%DST_EXAMPLE_PYREACT%" (
  echo [CLEAN] remove legacy PyreactExampleScript\pyreact
  rmdir /S /Q "%DST_EXAMPLE_PYREACT%"
)

echo [SYNC] runtime top-level .py
robocopy "%SRC_RUNTIME%" "%DST_RUNTIME%" *.py /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo [ERROR] Robocopy failed: runtime top-level .py
  exit /b 8
)

echo [SYNC] runtime native_runtime
robocopy "%SRC_RUNTIME_NATIVE%" "%DST_RUNTIME_NATIVE%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP /XD __pycache__ /XF *.pyc >nul
if errorlevel 8 (
  echo [ERROR] Robocopy failed: runtime native_runtime
  exit /b 8
)

echo [SYNC] example top-level .py
robocopy "%SRC_EXAMPLE%" "%DST_EXAMPLE%" *.py /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo [ERROR] Robocopy failed: example top-level .py
  exit /b 8
)

if not exist "%DST_JSON_UI%" (
  echo [MKDIR] create ui target: %DST_JSON_UI%
  mkdir "%DST_JSON_UI%"
)

echo [SYNC] JsonUI -^> resource_pack ui
robocopy "%SRC_JSON_UI%" "%DST_JSON_UI%" *.json /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo [ERROR] Robocopy failed: JsonUI
  exit /b 8
)

echo.
echo Sync completed successfully.
echo TargetRoot: %TARGET_ROOT%
echo TargetUIRoot: %TARGET_UI_ROOT%
exit /b 0
