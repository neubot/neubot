// Privacy/PrivacyPane.m

//
// Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
//  Universita` degli Studi di Milano
// Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
//  NEXA Center for Internet & Society at Politecnico di Torino
//
// This file is part of Neubot <http://www.neubot.org/>.
//
// Neubot is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Neubot is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
//

//
// Installer privacy pane
//

#include <sys/stat.h>
#include <syslog.h>

#import <Cocoa/Cocoa.h>
#import <InstallerPlugins/InstallerPlugins.h>

#import "PrivacyPane.h"

@implementation PrivacyPane

- (NSString *)title {
	return [NSString stringWithCString:"Privacy"
		encoding:NSUTF8StringEncoding];
}

//
// Invoked when we're about to enter the pane.
// The user cannot proceed unless she gives the permission
// to collect the results.
//
- (void) willEnterPane:(InstallerSectionDirection) inDirection {
	if ([canCollect state] == NSOnState) {
		[canShare setEnabled:YES];
		[self setNextEnabled:YES];
	}
	else {
		[canShare setState:NSOffState];		// reset
		[canShare setEnabled:NO];
		[self setNextEnabled:NO];
	}
}

//
// Invoked each time the user checks/unchecks the can_collect
// permission.  Calls willEnterPane that enables/disables the
// `forward` button accordingly.
//
- (IBAction) checkPrivacy: (id) aSnd {
	[self willEnterPane:InstallerDirectionForward];
}

//
// Allow the user to exit the pane iff she has at least
// given the permission to collect.
// We write in a temporary file the permission to share
// the results with others, as a boolean.
//
- (BOOL)shouldExitPane:(InstallerSectionDirection) inDirection {
	int              retval, save_errno;
	int              can_collect, can_share;
	const char      *error, *pname;
	struct stat      statbuf;
	FILE            *fp;
	NSAlert		*alert;

	// Clear errno, we'll restore it later
	save_errno = errno;
	errno = 0;

	// Always allow the user to go backward
	if (inDirection == InstallerDirectionBackward)
		goto done;

	pname = "/tmp/neubot-can-share";
	error = NULL;

	//
	// Init variables and make sure we're going to write
	// sane values to the output file.
	//
	can_collect = ([canCollect state] == NSOnState);
	can_share = ([canShare state] == NSOnState);

	// Sanity
	if (!can_collect) {
		error = "Internal error.  This should not happen.";
		goto fail;
	}

	//
	// XXX Using a regular file for this thing is not that greatest
	// idea but we've been unable to find an alternative to pass the
	// information to the post-flight script.
	// The best we can do is to lstat(2) the file we would like to
	// create and make sure it is a regular file.  Please note that
	// this process can go asleep between lstat(2) and fopen(3).
	// This means we cannot guarantee that we're going to fopen(3)
	// the file we've lstat(2)ed and declared safe.
	//                      -- Simone
	//
	memset(&statbuf, 0, sizeof (statbuf));
	retval = lstat(pname, &statbuf);
	if (retval != 0 && errno != ENOENT) {
		error = "Unexpected stat(2) failure";
		goto fail;
	}
	if (retval == 0 && ((statbuf.st_mode & S_IFMT) != S_IFREG)) {
		error = "Not a regular file";
		goto fail;
	}

	//
	// Open the file and make sure that the file is closed
	// without errors.
	//
	if ((fp = fopen(pname, "w")) == NULL) {
		error = "Failed to fopen(3) file for writing";
		goto fail;
	}

	if ((retval = fprintf(fp, "%d\n", can_share)) <= 0) {
		error = "Failed to fprintf(3) into file";
		goto fail1;
	}

	if ((retval = fclose(fp)) != 0) {
		error = "Failed to fclose(3) file";
		goto fail;
	}

done:	errno = save_errno;
	return YES;

	//
	// Handle error conditions.
	// Write a message to the system log where the user
	// can then see what went wrong.
	//
fail1:	(void)fclose(fp);
fail:	if (!error)
		error = "Unknown error";

	syslog(LOG_WARNING, "PrivacyPane: %s: %m", error);

	//
	// Write the message on a messagebox as well or
	// the user is going to be very confused ("why the
	// hell I cannot proceed at this point?")
	//
	alert = [[NSAlert alloc] init];
	if (alert) {
		[alert setMessageText: [NSString stringWithCString:error
					encoding:NSUTF8StringEncoding]];
		if (errno)
			[alert setInformativeText: [NSString
					stringWithCString:strerror(errno)
					encoding:NSUTF8StringEncoding]];
		[alert addButtonWithTitle: @"OK"];
		[alert runModal];
		[alert release];
	}

	errno = save_errno;
	return NO;
}

@end
