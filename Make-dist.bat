"C:\Python27\python.exe" setup.py py2exe --bundle-files 2
mkdir dist\www
mkdir dist\www\images
mkdir dist\www\jqplot
copy neubot\www dist\www
copy neubot\www\images dist\www\images
copy neubot\www\jqplot dist\www\jqplot
pause
