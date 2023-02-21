@echo off
set projectname=aiowinreg
set root=%~dp0
set repo=%root%..\..\%projectname%

IF NOT DEFINED __BUILDALL_VENV__ (GOTO :CREATEVENV)
GOTO :BUILD

:CREATEVENV
python -m venv %root%\env
CALL %root%\env\Scripts\activate.bat
pip install pyinstaller
GOTO :BUILD

:BUILD
cd %repo%\..\
pip install .
cd %repo%\
pyinstaller -F __main__.py %hiddenimports%
cd %repo%\dist & copy __main__.exe %root%\winregconsole.exe
GOTO :CLEANUP

:CLEANUP
IF NOT DEFINED __BUILDALL_VENV__ (deactivate)
cd %root%
EXIT /B