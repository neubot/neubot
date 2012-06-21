# neubot/utils_sysdirs.py

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' Location of system-dependent directories '''

# Formerly neubot/rootdir.py

import os
import sys

#
# ROOTDIR is the directory that contains the `neubot` directory,
# which, in turn, contains all Neubot sources.  When Neubot is
# a py2exe executable, ROOTDIR is `$ROOTDIR\\library.zip` so we
# need to trim it.  Note that frozen is an attribute of system
# when we are a py2exe executable only.
#
# The following is magic to compute the absolute root directory
# and has been suggested by Alessio Palmero.  Here is how it
# works::
#     __file__ -> $ROOTDIR/neubot/__file__.py -> $ROOTDIR
#
ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys, 'frozen'):
    ROOTDIR = os.path.dirname(ROOTDIR)

#
# WWWDIR is the directory that contains Neubot web files.  When we
# are not a py2exe executable, web files are contained within
# Neubot sources.  Otherwise, they are on the root directory in
# a folder called ``www``.
#
if not hasattr(sys, 'frozen'):
    WWWDIR = os.sep.join([ROOTDIR, 'neubot/www'])
else:
    WWWDIR = os.sep.join([ROOTDIR, 'www'])

#
# BASEDIR is the directory that contains ROOTDIR.  This directory
# is interesting for system where Neubot perform autoupdates, namely
# MacOS and Win32.  In those systems, ROOTDIR is a directory named
# after the current version number in numeric representation (see
# utils_version.py for more info).  While BASEDIR is typically named
# ``neubot`` and contains most recent versions.
#
BASEDIR = os.path.dirname(ROOTDIR)

#
# VERSIONDIR is meaningful only when Neubot perform autoupdates,
# namely on MacOS and Win32.  It is equal to ROOTDIR, but we
# define it as a separate name for clarity.  In particular, ROOTDIR
# is meant to be used always, while VERSIONDIR is meant to be used
# only in the context of autoupdates.
#
VERSIONDIR = ROOTDIR

#
# OPENSSL is the path to openssl executable in the current
# system.  Under UNIX we search for openssl in the usual
# locations (/bin, /usr/bin).  Under Win32 the executable
# must be in VERSIONDIR.
# Note that this variable is interesting only when we need
# to invoke OpenSSL in order to verify an autoupdate digital
# signature.  I.e. on MacOS and Win32.
# When we cannot find OPENSSL we simply set it to None and
# who needs to use this variable must deal with that.
#
if os.name == 'posix':
    if os.access('/bin/openssl', os.R_OK|os.X_OK):
        OPENSSL = '/bin/openssl'
    elif os.access('/usr/bin/openssl', os.R_OK|os.X_OK):
        OPENSSL = '/usr/bin/openssl'
    else:
        OPENSSL = None
elif os.name == 'nt':
    OPENSSL = os.sep.join([VERSIONDIR, 'openssl.exe'])
    if not os.access(OPENSSL, os.R_OK|os.X_OK):
        OPENSSL = None
else:
    raise RuntimeError('system not configured')

#
# SYSCONFDIR is the directory that contains Neubot configuration
# files (if needed for the system).  At the moment of writing
# this comment, configuration files are needed under MacOS only.
# But we always define it to keep the code plain and uniform.
#
if os.name == 'posix':
    SYSCONFDIR = '/etc/neubot'
elif os.name == 'nt':
    SYSCONFDIR = os.sep.join([os.environ['APPDATA'], 'neubot']) 
else:
    raise RuntimeError('system not configured')

#
# LOCALSTATEDIR is the directory that contains Neubot database.
# We use a directory and not just a file because sqlite3 must
# be able to create -journal files when writing into the database.
# Hence, the directory must be writable by the Neubot user.
#
# On POSIX systems, we follow BSD convention and put database in
# ``/var/neubot``.  Unless we're on a Linux system, where FHS
# mandates to create that kind of directories under ``/var/lib``.
#
# On Windows, we put the database in the roaming application data
# folder.  The exact location varies depending on the version of
# Windows and is ``C:\Users\foo\AppData\Roaming`` on Windows 7 for
# user ``foo``.
#
if os.name == 'posix':
    if sys.platform.startswith('linux'):
        LOCALSTATEDIR = '/var/lib/neubot'
    else:
        LOCALSTATEDIR = '/var/neubot'
elif os.name == 'nt':
    LOCALSTATEDIR = os.sep.join([os.environ['APPDATA'], 'neubot']) 
else:
    raise RuntimeError('system not configured')

def main(args):
    ''' Main function '''

    if len(args) > 1:
        sys.exit('usage: neubot utils_sysdirs')

    sys.stdout.write('''\
BASEDIR       : "%(BASEDIR)s"
LOCALSTATEDIR : "%(LOCALSTATEDIR)s"
OPENSSL       : "%(OPENSSL)s"
ROOTDIR       : "%(ROOTDIR)s"
SYSCONFDIR    : "%(SYSCONFDIR)s"
VERDSIONDIR   : "%(VERSIONDIR)s"
WWWDIR        : "%(WWWDIR)s"
''' % globals())

if __name__ == "__main__":
    main(sys.argv)
