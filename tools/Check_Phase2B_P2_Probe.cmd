@echo off
"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0package_phase2b_p2.py" --check-installed
if errorlevel 1 goto done
"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0analyze_phase2b_p2.py" --check-ready
:done
pause
