windres neubot-icon.rc neubot-icon.o
gcc.exe -Wall -c neubot-headless.c
gcc.exe -mwindows -o neubot-headless.exe neubot-headless.o neubot-icon.o
gcc.exe -Wall -c neubot-start.c
gcc.exe -mwindows -o neubot-start.exe neubot-start.o neubot-icon.o
gcc.exe -Wall -c neubot-stop.c
gcc.exe -mwindows -o neubot-stop.exe neubot-stop.o neubot-icon.o
del *.o
pause
