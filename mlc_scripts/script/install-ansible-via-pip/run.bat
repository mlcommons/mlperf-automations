@echo off

echo Installing Ansible via pip...
"%MLC_PYTHON_BIN_WITH_PATH%" -m pip install %MLC_ANSIBLE_PIP_INSTALL_STRING%
IF %ERRORLEVEL% NEQ 0 EXIT /b 1

echo.
echo Ansible installed successfully.
ansible --version
