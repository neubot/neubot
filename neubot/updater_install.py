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
import os
import tarfile

def install(basedir, version):
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

    # Extract from the tarball
    archive = tarfile.open(targz, mode='r:gz')
    archive.errorlevel = 2
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
