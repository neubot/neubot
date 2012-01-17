// MacOS/Privacy/PrivacyPane.m

//
// Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
//  Universita` degli Studi di Milano
// Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

#import <Cocoa/Cocoa.h>
#import <InstallerPlugins/InstallerPlugins.h>

#import "PrivacyPane.h"

@implementation PrivacyPane

#define ERROR "Not enough permissions to continue installation"
#define DETAILS "To continue with the installation you must assert you " \
    "have read the privacy policy and provide the permission to " \
    "collect and publish your Internet address."

- (NSString *)title {
	return [NSString stringWithCString:"Privacy"
		encoding:NSUTF8StringEncoding];
}

//
// Allow the user to exit the pane iff she has given all
// the permissions, i.e. informed, collect, publish.
//
- (BOOL)shouldExitPane:(InstallerSectionDirection) inDirection {
	const char	*details = DETAILS;
	const char	*error = ERROR;
	NSAlert		*alert;

	// Allow to move if we have all permissions
	if ([informed state] == NSOnState &&
	    [canCollect state] == NSOnState &&
	    [canPublish state] == NSOnState)
		return YES;

	// Always allow the user to go backward
	if (inDirection == InstallerDirectionBackward)
		return YES;

	// Otherwise alert the user and stay in the current page
	alert = [[NSAlert alloc] init];
	if (alert) {
		[alert setMessageText: [NSString stringWithCString:error
					encoding:NSUTF8StringEncoding]];
		[alert setInformativeText: [NSString stringWithCString:details
					encoding:NSUTF8StringEncoding]];
		[alert addButtonWithTitle: @"OK"];
		[alert runModal];
		[alert release];
	}

	return NO;
}

@end
