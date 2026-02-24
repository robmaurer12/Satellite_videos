@echo off
echo Searching for Python...

set PYTHONPATH=

for /d %%d in ("%LocalAppData%\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set PYTHONPATH=%%d\python.exe
        goto :found
    )
)

for /d %%d in ("C:\Python*") do (
    if exist "%%d\python.exe" (
        set PYTHONPATH=%%d\python.exe
        goto :found
    )
)

for /d %%d in ("%ProgramFiles%\Python*") do (
    if exist "%%d\python.exe" (
        set PYTHONPATH=%%d\python.exe
        goto :found
    )
)

:found
if defined PYTHONPATH (
    echo Found Python: %PYTHONPATH%
    "%PYTHONPATH%" Test\main.py
) else (
    echo Python not found. Please install Python from https://www.python.org/
    pause
)
