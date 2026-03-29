@echo off
:loop
:: 在这里调用你的目标脚本
call sync_to_test.cmd

:: 等待 2 秒
timeout /t 2 /nobreak >nul

:: 跳回循环开始处
goto loop