# neubot/updater_install.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

''' Install a new version of Neubot '''

import compileall
import getopt
import os
import sys
import tarfile

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_path

def __verify(basedir, member):
    ''' Verify one member of the tarfile '''

    #
    # Make sure that the combination of basedir and member
    # name falls below basedir.
    #
    utils_path.append(basedir, member.name)

    #
    # The tar archive should contain directories and
    # regular files only.
    #
    if not member.isdir() and not member.isreg():
        raise RuntimeError('updater_install: %s: invalid type' % member.name)

def install(basedir, version, dryrun=False):
    ''' Install a new version of Neubot '''

    # Make file names
    targz = os.sep.join([
                         basedir,
                         '%s.tar.gz' % version,
                        ])
    versiondir = os.sep.join([
                              basedir,
                              '%s' % version,
                             ])

    # Verify the tarball
    archive = tarfile.open(targz, mode='r:gz')
    archive.errorlevel = 2
    for member in archive.getmembers():
        __verify(basedir, member)

    # Honor dryrun
    if dryrun:
        archive.close()
        return

    # Extract from the tarball
    archive.extractall(path=basedir)
    archive.close()

    # Compile all modules
    compileall.compile_dir(versiondir, quiet=1)

    # Write .neubot-installed-ok file
    filep = open('%s/.neubot-installed-ok' % versiondir, 'wb')
    filep.close()

    # Call sync
    if os.name == 'posix':
        os.system('sync')

USAGE = 'usage: neubot updater_install [-n] [-d basedir] version...'

def main(args):
    ''' Main function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'd:n')
    except getopt.error:
        sys.exit(USAGE)
    if not arguments:
        sys.exit(USAGE)

    basedir = '.'
    dryrun = 0
    for name, value in options:
        if name == '-d':
            basedir = value
        elif name == '-n':
            dryrun = 1

    for version in arguments:
        install(basedir, version, dryrun)

if __name__ == '__main__':
    main(sys.argv)
