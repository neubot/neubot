rem create dist/neubot.exe and stuff
python setup.py py2exe --bundle-files 2

rem copy web user interface files into dist/
mkdir dist\www
copy neubot\www dist\www

rem create Neubot_Setup_x.y.z.exe
"c:\program files\nsis\makensis.exe" neubot.nsi

rem do not hide possible errors
pause
