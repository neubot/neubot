/*-
 * win32/neubot-exec.h
 * Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
 *   NEXA Center for Internet & Society at Politecnico di Torino
 *
 * This file is part of Neubot <http://www.neubot.org/>.
 *
 * Neubot is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Neubot is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Neubot.exe should be a console program to let the interested user
 * play with it from command line.  But we don't want an ugly console
 * window to be created each time one just clicks on the neubot icon
 * and that's the purpose of this wrapper: execute neubot.exe in a
 * way that avoids the creation of the ugly console window.
 */

#include <windows.h>

/* shortcuts */
#define PINFO	PROCESS_INFORMATION
#define SINFO	STARTUPINFO

#ifndef NEUBOT_CMDLINE
# error "You MUST define NEUBOT_CMDLINE!"
#endif

INT WINAPI
WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmpdLine,
    int nCmdShow)
{
	int	cc;
	char	path[MAX_PATH];
	char	*pos;
	PINFO	pinfo;
	BOOL	rv;
	SINFO	sinfo;

	cc = GetModuleFileName(NULL, path, sizeof(path));
	if (cc <= 0 || cc >= sizeof (path))
		return EXIT_FAILURE;
	pos = strrchr(path, '\\');
	if (pos == NULL)
		return EXIT_FAILURE;
	*pos = '\0';
	rv = SetCurrentDirectory(path);
	if (rv == 0)
		return EXIT_FAILURE;
	memset(&sinfo, 0, sizeof (sinfo));
	memset(&pinfo, 0, sizeof (pinfo));
	/*
	 * We want to execute neubot without creating that ugly console
	 * window.  We initially tried with DETACHED_PROCESS to no avail
	 * because neubot creates a console in this case.  Then we used
	 * CREATE_NO_WINDOW and this seems to work because neubot does
	 * not create a console _and_ does not crash.
	 */
	rv = CreateProcess(NULL, NEUBOT_CMDLINE, NULL, NULL, FALSE,
	    CREATE_NO_WINDOW, NULL, NULL, &sinfo, &pinfo);
	if (rv == 0)
		return EXIT_FAILURE;
	CloseHandle(pinfo.hProcess);
	CloseHandle(pinfo.hThread);
	return EXIT_SUCCESS;
}
