
set root=%~dp0
set projectname=aiowinreg
set repo=%root%..\..\%projectname%
IF NOT DEFINED __BUILDALL_VENV__ (
    set pyenv=%root%\env
    python -m venv %pyenv%
    %pyenv%\Scripts\activate.bat &^
    pip install pyinstaller
) &^
cd %repo%\..\ &^
pip install . &^
cd %repo%\ &^
pyinstaller -F __main__.py %hiddenimports% &^
cd %repo%\dist & copy __main__.exe %root%\winregconsole.exe &^
IF NOT DEFINED __BUILDALL_VENV__ (
    deactivate
) &^
cd %root%