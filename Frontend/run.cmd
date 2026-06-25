@echo off
setlocal

set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=dev"

set "NODE_DIR=%~dp0..\.tools\node"
if exist "%NODE_DIR%\npm.cmd" (
    set "PATH=%NODE_DIR%;%PATH%"
    if /I "%COMMAND%"=="install" (
        call "%NODE_DIR%\npm.cmd" install
    ) else (
        call "%NODE_DIR%\npm.cmd" run %COMMAND%
    )
) else (
    if /I "%COMMAND%"=="install" (
        call npm install
    ) else (
        call npm run %COMMAND%
    )
)

exit /b %ERRORLEVEL%
