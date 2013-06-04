@echo off
rem Batch script to run "compare" Python utility
setlocal
call python %USERPROFILE%\Documents\md5compare\compare.py %*
endlocal