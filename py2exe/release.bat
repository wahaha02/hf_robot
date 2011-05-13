@echo off
set BUILD_FOLDER=build

if exist "%BUILD_FOLDER%" (
        rd /S /Q %BUILD_FOLDER%
        echo Remove forlder [%BUILD_FOLDER%] -- DONE
)
C:\python26\python.exe release.py
C:\python26\python.exe -O -OO setup.py py2exe

:: nsi scripts's current path is same as it.
"C:\Program Files\NSIS\makensis.exe" package\hf_setup_script.nsi

pause
