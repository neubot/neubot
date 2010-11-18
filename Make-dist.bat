"C:\Python27\python.exe" setup.py py2exe --bundle-files 2
copy win32\neubot-headless.exe dist\
copy win32\neubot-start.exe dist\
copy win32\neubot-stop.exe dist\
mkdir dist\www
mkdir dist\www\images
mkdir dist\www\jqplot
copy neubot\www dist\www
copy neubot\www\images dist\www\images
copy neubot\www\jqplot dist\www\jqplot
pause
