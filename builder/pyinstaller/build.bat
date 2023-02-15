@echo off
set root=%~dp0
set projectname=aiowinreg
set pyenv=%root%\env
set repo=%root%..\..\%projectname%
python -m venv %pyenv%
%pyenv%\Scripts\activate.bat &^
pip install pyinstaller &^
cd %repo%\..\ &^
pip install . &^
cd %repo%\ &^
pyinstaller -F __main__.py %hiddenimports% &^
cd %repo%\dist & copy __main__.exe %root%\winregconsole.exe