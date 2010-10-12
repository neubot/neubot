python setup.py py2exe --bundle-files 2
mkdir dist\www
copy neubot\www dist\www
"c:\program files\nsis\makensis.exe" neubot.nsi
pause
