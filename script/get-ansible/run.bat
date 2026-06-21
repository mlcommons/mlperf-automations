@echo off
ansible-playbook --version > tmp-ver.out
IF %ERRORLEVEL% NEQ 0 EXIT /b 1
