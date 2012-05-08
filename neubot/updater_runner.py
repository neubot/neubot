# neubot/updater_runner.py

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

''' An updater that uses the runner '''

#
# This is basically the portable part of Win32 updater and has
# been separated from it for cross-platform testability.
#

import getopt
import logging
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.poller import POLLER
from neubot.rootdir import ROOTDIR
from neubot.runner_core import RUNNER_CORE

from neubot import updater_utils

class UpdaterRunner(object):

    ''' An updater that uses the runner '''

    def __init__(self, channel, basedir):
        ''' Initializer '''
        self.channel = channel
        self.basedir = basedir

    def start(self):
        ''' Schedule first check for updates '''
        self._schedule()

    def _schedule(self):
        ''' Schedule next check for updates '''
        # TODO remember to raise this to 1800 seconds
        POLLER.sched(60, self.retrieve_versioninfo)

    def retrieve_versioninfo(self):
        ''' Retrieve version information '''

        #
        # The windows updater is still experimental, so it
        # is disabled by default and one needs to enable it
        # explicitly using the Web UI.
        #
        if not CONFIG['win32_updater']:
            self._schedule()
            return

        ctx = { 'uri': updater_utils.versioninfo_get_uri(self.channel) }
        RUNNER_CORE.run('dload', self._process_versioninfo, False, ctx)

    def _process_versioninfo(self, ctx):
        ''' Process version information '''

        # TODO make this function more robust wrt unexpected errors

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return
        length, body, error = ctx.pop('result')
        if length == -1:
            logging.error('updater_runner: error: %s', str(error))
            self._schedule()
            return

        vinfo = updater_utils.versioninfo_extract(body)
        if not vinfo:
            logging.error('updater_runner: invalid versioninfo')
            self._schedule()
            return
        if not updater_utils.versioninfo_is_newer(vinfo):
            logging.debug('updater_runner: no updates available')
            self._schedule()
            return

        self.retrieve_files(vinfo)

    def retrieve_files(self, vinfo):
        ''' Retrieve files for a given version '''
        # Note: this is a separate function for testability
        uri = updater_utils.sha256sum_get_uri(self.channel, vinfo)
        ctx = {'vinfo': vinfo, 'uri': uri}
        RUNNER_CORE.run('dload', self._retrieve_tarball, False, ctx)

    def _retrieve_tarball(self, ctx):
        ''' Retrieve tarball for a given version '''

        # TODO make this function more robust wrt unexpected errors

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return

        length, body, error = ctx.pop('result')
        if length == -1:
            logging.error('updater_runner: error: %s', str(error))
            self._schedule()
            return
        sha256 = updater_utils.sha256sum_extract(ctx['vinfo'], body)
        if not sha256:
            logging.error('updater_runner: invalid sha256')
            self._schedule()
            return

        # XXX We should not reuse the same CTX here
        ctx['sha256'] = sha256
        ctx['uri'] = updater_utils.tarball_get_uri(self.channel, ctx['vinfo'])

        RUNNER_CORE.run('dload', self._process_files, False, ctx)

    def _process_files(self, ctx):
        ''' Process files for a given version '''

        # TODO make this function more robust wrt unexpected errors

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return

        length, body, error = ctx.pop('result')
        if length == -1:
            logging.error('updater_runner: error: %s', str(error))
            self._schedule()
            return
        if not updater_utils.sha256sum_verify(ctx['sha256'], body):
            logging.error('updater_runner: sha256 mismatch')
            self._schedule()
            return

        self.install(ctx, body)

    def install(self, ctx, body):
        ''' Install and run the new version '''

def main(args):
    ''' main() function '''

    try:
        options, arguments = getopt.getopt(args[1:], 'vy')
    except getopt.error:
        sys.exit('neubot updater_runner [-vy] [version]')
    if len(arguments) > 1:
        sys.exit('neubot updater_runner [-vy] [version]')

    privacy = False
    for tpl in options:
        if tpl[0] == '-v':
            logging.getLogger('').setLevel(logging.DEBUG)
        elif tpl[0] == '-y':
            privacy = True

    # Honor -y and force privacy permissions
    if privacy:
        CONFIG.conf.update({'privacy.informed': 1, 'privacy.can_collect': 1,
                            'privacy.can_publish': 1})

    updater = UpdaterRunner('win32', os.path.dirname(ROOTDIR))

    if arguments:
        updater.retrieve_files(arguments[0])
    else:
        # Enable automatic updates if we arrive here
        CONFIG.conf['win32_updater'] = 1
        updater.retrieve_versioninfo()

    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
