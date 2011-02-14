"C:\Python27\python.exe" setup.py py2exe --bundle-files 2
mkdir dist\www
mkdir dist\www\css
mkdir dist\www\img
mkdir dist\www\js
copy neubot\www dist\www
copy neubot\www\css dist\www\css
copy neubot\www\img dist\www\img
copy neubot\www\js dist\www\js
pause
