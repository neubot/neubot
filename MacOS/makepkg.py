#!/usr/bin/env python

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

'''
 Creates Neubot-VERSION.pkg for MacOSX.
'''

import traceback
import tarfile
import compileall
import shutil
import os.path
import subprocess
import shlex
import sys

TOPDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MACOSDIR = os.sep.join([TOPDIR, 'MacOS'])
os.chdir(MACOSDIR)

if __name__ == '__main__':
    sys.path.insert(0, TOPDIR)

from neubot.libversion import LibVersion

VERSION = '0.4.1-rc3'
NUMERIC_VERSION = LibVersion.to_numeric(VERSION)

IGNORER = shutil.ignore_patterns('.DS_Store')

def __call(cmdline):
    ''' exit() if the subprocess fails '''
    retval = subprocess.call(shlex.split(cmdline))
    if retval != 0:
        sys.exit(1)

def _init():

    '''
     Make sure we start from a clean environment and that
     we have a sane umask.
    '''

    #
    # If we don't run the program as root we produce Archive.bom
    # with wrong ownership and we don't want that to happen.
    #
    if os.getuid() != 0:
        sys.exit('You must run this program as root')

    os.umask(0022)

    shutil.rmtree('Neubot-%s.pkg' % VERSION, ignore_errors=True)
    shutil.rmtree('neubot', ignore_errors=True)

    shutil.rmtree('Privacy/build', ignore_errors=True)

def _make_package():
    ''' Creates package copying from package skeleton '''
    shutil.copytree(
                    'Neubot-pkg',
                    'Neubot-%s.pkg' % VERSION,
                    ignore=IGNORER
                   )

def _make_sharedir():

    '''
     Creates and populates the directory that will be copied
     to /usr/local/share/neubot.  In particular, put there
     Neubot sources; compile them; and copy all the scripts
     we need to have in there.
    '''

    # Copy neubot sources
    shutil.copytree(
                    '../neubot/',
                    'neubot/%s/neubot' % NUMERIC_VERSION,
                    ignore=IGNORER
                   )

    # Compile sources
    compileall.compile_dir('neubot/%s' % NUMERIC_VERSION)

    #
    # Copy scripts.  Note that start.sh and the plist file
    # must be in /usr/local/share/neubot while the rest goes
    # into the version-specific directory.
    #
    shutil.copy('basedir-skel/start.sh', 'neubot')
    shutil.copy('basedir-skel/org.neubot.plist', 'neubot')

    shutil.copy('basedir-skel/versiondir-skel/cmdline.sh',
                'neubot/%s' % NUMERIC_VERSION)
    shutil.copy('basedir-skel/versiondir-skel/start.sh',
                'neubot/%s' % NUMERIC_VERSION)
    shutil.copy('basedir-skel/versiondir-skel/prerun.sh',
                'neubot/%s' % NUMERIC_VERSION)
    shutil.copy('basedir-skel/versiondir-skel/uninstall.sh',
                'neubot/%s' % NUMERIC_VERSION)

    # Build and copy Neubot.app too
    shutil.copytree(
                    'basedir-skel/versiondir-skel/Neubot-app',
                    'neubot/%s/Neubot.app' % NUMERIC_VERSION,
                    ignore=IGNORER,
                   )

    # Add manual page(s)
    shutil.copy('../man/man1/neubot.1', 'neubot/%s' % NUMERIC_VERSION)

    # Tell start.sh we've been installed OK
    filep = open('neubot/%s/.neubot-installed-ok' % NUMERIC_VERSION, 'w')
    filep.close()

def _make_archive_pax():
    ''' Create an archive containing neubot library '''
    __call('pax -wzf %s -x cpio %s' %
       (
        'Neubot-%s.pkg/Contents/Archive.pax.gz' % VERSION,
        'neubot'
       ))

def _make_archive_bom():
    ''' Create bill of materials for neubot library '''
    __call('mkbom %s %s' %
       (
        'neubot',
        'Neubot-%s.pkg/Contents/Archive.bom' % VERSION,
       ))

def _make_privacy_plugin():

    '''
     Compile privacy plugin and copy the needed files into the
     package so that the installer will ask for privacy permissions
     during the setup.
    '''

    os.chdir('Privacy')
    __call('xcodebuild')
    os.chdir('..')

    shutil.copytree(
                    'Privacy/build/Release/Privacy.bundle',
                    'Neubot-%s.pkg/Contents/Plugins/Privacy.bundle' % VERSION,
                   )
    shutil.copy(
                'Privacy/InstallerSections.plist',
                'Neubot-%s.pkg/Contents/Plugins/' % VERSION,
               )

def _fixup_perms():

    '''
     Fix group ownership: we want wheel and not staff.  This happens
     on MacOS because 'BSD derived systems always have the setgid
     directory behavior.'

     See <http://comments.gmane.org/gmane.os.openbsd.misc/187993>
    '''

    __call('find Neubot-%s.pkg -exec chown root:wheel {} \;' % VERSION)

def _create_tarball():
    ''' Create the zip file in ../dist ready for distribution '''

    if not os.path.exists('../dist'):
        os.mkdir('../dist')

    arch = tarfile.open('../dist/Neubot-%s.pkg.tgz' % VERSION, 'w:gz')
    arch.add('Neubot-%s.pkg' % VERSION)
    arch.close()

def main():
    ''' Make the package or clean '''
    _init()
    if len(sys.argv) == 2 and sys.argv[1] == '--clean':
        sys.exit(0)
    _make_package()
    _make_sharedir()
    _make_archive_pax()
    _make_archive_bom()
    _make_privacy_plugin()
    _fixup_perms()
    _create_tarball()

if __name__ == '__main__':
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        pass
    except:
        traceback.print_exc()
        sys.exit(1)
