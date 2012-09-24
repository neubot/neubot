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
 Creates neubot-VERSION.pkg for MacOSX and, while there, also
 generates the update tarball for autoupdating clients.
'''

import traceback
import tarfile
import compileall
import shutil
import os.path
import subprocess
import hashlib
import shlex
import sys

TOPDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#
# This simplifies things a lot.
#
MACOSDIR = os.sep.join([TOPDIR, 'MacOS'])
os.chdir(MACOSDIR)

VERSION = '0.4.15'
NUMERIC_VERSION = '0.004015999'

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

    if os.path.lexists('neubot-%s.pkg' % VERSION):
        shutil.rmtree('neubot-%s.pkg' % VERSION)
    if os.path.lexists('neubot'):
        shutil.rmtree('neubot')

    if os.path.lexists('Privacy/build'):
        shutil.rmtree('Privacy/build')

def _make_package():
    ''' Creates package copying from package skeleton '''
    shutil.copytree(
                    'neubot-pkg',
                    'neubot-%s.pkg' % VERSION,
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
    shutil.copy('../pubkey.pem',
                'neubot/%s' % NUMERIC_VERSION)
    shutil.copy('basedir-skel/versiondir-skel/org.neubot.notifier.plist',
                'neubot/%s' % NUMERIC_VERSION)

    # Build and copy Neubot.app too
    shutil.copytree(
                    'basedir-skel/versiondir-skel/Neubot-app',
                    'neubot/%s/Neubot.app' % NUMERIC_VERSION,
                    ignore=IGNORER,
                   )

    # Add manual page(s)
    shutil.copy('../UNIX/man/man1/neubot.1', 'neubot/%s' % NUMERIC_VERSION)

def _add_okfile():
    ''' Add okfile to VERSIONDIR '''
    filep = open('neubot/%s/.neubot-installed-ok' % NUMERIC_VERSION, 'w')
    filep.close()

def _fixup_perms():

    '''
     Fix group ownership: we want wheel and not staff.  This happens
     on MacOS because 'BSD derived systems always have the setgid
     directory behavior.'

     See <http://comments.gmane.org/gmane.os.openbsd.misc/187993>
    '''

    __call('find neubot/ -exec chown root:wheel {} \;')

def _make_auto_update():

    ''' Create, checksum and sign the update for autoupdating clients '''

    if not os.path.exists('../dist'):
        os.mkdir('../dist')
    if not os.path.exists('../dist/macos'):
        os.mkdir('../dist/macos')

    tarball = '../dist/macos/%s.tar.gz' % NUMERIC_VERSION
    sha256sum = '../dist/macos/%s.tar.gz.sha256' % NUMERIC_VERSION
    sig = '../dist/macos/%s.tar.gz.sig' % NUMERIC_VERSION

    # Create tarball
    arch = tarfile.open(tarball, 'w:gz')
    os.chdir('neubot')
    arch.add('%s' % NUMERIC_VERSION)
    arch.close()
    os.chdir(MACOSDIR)

    # Calculate sha256sum
    filep = open(tarball, 'rb')
    hashp = hashlib.new('sha256')
    content = filep.read()
    hashp.update(content)
    digest = hashp.hexdigest()
    filep.close()

    # Write sha256sum
    filep = open(sha256sum, 'wb')
    filep.write('%s  %s\n' % (digest, os.path.basename(tarball)))
    filep.close()

    # Make digital signature
    try:
        filenam = os.sep.join([os.environ['HOME'], '.neubot-macos'])
        filep = open(filenam, 'r')
        privkey = filep.read().strip()
        filep.close()
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        privkey = None
    if not privkey:
        privkey = raw_input('Enter privkey location: ')
    if privkey:
        os.chdir('../dist/macos')
        __call('openssl dgst -sha256 -sign %s -out %s %s' %
           (privkey, os.path.basename(sig), os.path.basename(tarball)))
        os.chdir(MACOSDIR)

def _compile():

    '''
     Compile sources at VERSIONDIR.  This is a separate function
     because we need to compile sources after we've created the
     update tarball for automatic updates.
    '''

    compileall.compile_dir('neubot/%s' % NUMERIC_VERSION)

def _make_archive_pax():
    ''' Create an archive containing neubot library '''
    __call('pax -wzf %s -x cpio %s' %
       (
        'neubot-%s.pkg/Contents/Archive.pax.gz' % VERSION,
        'neubot'
       ))

def _make_archive_bom():
    ''' Create bill of materials for neubot library '''
    __call('mkbom %s %s' %
       (
        'neubot',
        'neubot-%s.pkg/Contents/Archive.bom' % VERSION,
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
                    'neubot-%s.pkg/Contents/Plugins/Privacy.bundle' % VERSION,
                   )
    shutil.copy(
                'Privacy/InstallerSections.plist',
                'neubot-%s.pkg/Contents/Plugins/' % VERSION,
               )

def _create_tarball():
    ''' Create the tgz file in ../dist ready for distribution '''

    if not os.path.exists('../dist'):
        os.mkdir('../dist')

    arch = tarfile.open('../dist/neubot-%s.pkg.tgz' % VERSION, 'w:gz')
    arch.add('neubot-%s.pkg' % VERSION)
    arch.close()

def main():
    ''' Make the package or clean '''
    _init()
    if len(sys.argv) == 2 and sys.argv[1] == '--clean':
        sys.exit(0)
    _make_package()

    #
    # We make autoupdate before compiling because we're not
    # interested in shipping .pyc files in the autoupdate.
    # The second _fixup_perms() is to fixup the permissions of
    # the .pyc compiled by __compile().
    # Similarly, we add okfile after we've created the auto
    # update because okfile should not be part of the set of
    # files distributed with an autoupdate.
    #
    _make_sharedir()
    _fixup_perms()
    _make_auto_update()
    _compile()
    _fixup_perms()
    _add_okfile()

    _make_archive_pax()
    _make_archive_bom()
    _make_privacy_plugin()
    _create_tarball()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except:
        traceback.print_exc()
        sys.exit(1)
