# neubot/updater_win32.py

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

''' Win32 updater '''

import getopt
import subprocess
import sys
import logging

if __name__ == '__main__':
    sys.path.insert(0, '.')

if sys.version_info[0] >= 3:
    import winreg as _winreg
else:
    import _winreg

from neubot import utils_version

from neubot.config import CONFIG
from neubot.poller import POLLER
from neubot.updater_runner import UpdaterRunner

from neubot import utils_path
from neubot import utils_hier

class UpdaterWin32(UpdaterRunner):

    ''' Win32 updater '''

    #
    # Most of the code is in UpdaterRunner, which is system-
    # independent, for testability.
    #

    def install(self, ctx, body):
        ''' Install new version on Windows '''

        # Make file names

        versiondir = utils_path.append(self.basedir, ctx['vinfo'], False)
        if not versiondir:
            raise RuntimeError("updater_win32: append() path failed")

        exefile = utils_path.join(versiondir, 'neubotw.exe')
        uninst = utils_path.join(versiondir, 'uninstall.exe')

        cmdline = '"%s" start' % exefile
        cmdline_k = '"%s" start -k' % exefile

        #
        # Overwrite the version of Neubot that is executed when
        # the user logs in.
        #
        regkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
          "Software\Microsoft\Windows\CurrentVersion\Run", 0,
          _winreg.KEY_WRITE)
        _winreg.SetValueEx(regkey, "Neubot", 0, _winreg.REG_SZ, cmdline)
        _winreg.CloseKey(regkey)

        # Update the registry to reference the new uninstaller
        regkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
          "Software\Microsoft\Windows\CurrentVersion\Uninstall\Neubot", 0,
          _winreg.KEY_WRITE)
        _winreg.SetValueEx(regkey, "DisplayName", 0, _winreg.REG_SZ,
          "Neubot " + utils_version.to_canonical(ctx['vinfo']))
        _winreg.SetValueEx(regkey, "UninstallString", 0, _winreg.REG_SZ,
          uninst)
        _winreg.CloseKey(regkey)

        logging.info('updater_win32: updated win32 registry')

        #
        # Run the new version of Neubot and tell it that this
        # version should be stopped before proceeding with normal
        # startup.
        #
        # We need to close_fds, because the child process must
        # not inherit the parent handles.  If it did, the listening
        # socket is inherited, and the child process cannot open
        # its own listening socket.  The ``-k`` argument on the
        # command line instructs the child process to request this
        # process to exit.  Of course the child does that before
        # attempting to listen a new socket.
        #
        logging.info('updater_win32: about to exec: %s', cmdline_k)
        subprocess.Popen(cmdline_k, close_fds=True)

USAGE = 'neubot updater_win32 [-vy] [-C channel] [-O system] [version]'

def main(args):
    ''' main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'C:O:vy')
    except getopt.error:
        sys.exit(USAGE)
    if len(arguments) > 1:
        sys.exit(USAGE)

    sysname = 'win32'
    channel = CONFIG['win32_updater_channel']
    privacy = False
    for tpl in options:
        if tpl[0] == '-C':
            channel = tpl[1]
        elif tpl[0] == '-O':
            sysname = tpl[1]
        elif tpl[0] == '-v':
            CONFIG['verbose'] = 1
        elif tpl[0] == '-y':
            privacy = True

    # Honor -y and force privacy permissions
    if privacy:
        CONFIG.conf.update({'privacy.informed': 1, 'privacy.can_collect': 1,
                            'privacy.can_publish': 1})

    CONFIG['win32_updater_channel'] = channel
    updater = UpdaterRunner(sysname, utils_hier.BASEDIR)

    if arguments:
        updater.retrieve_files({}, arguments[0])
    else:
        # Enable automatic updates if we arrive here
        CONFIG.conf['win32_updater'] = 1
        updater.retrieve_versioninfo()

    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
