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
# TODO The plan is to modify MacOSX updater to use the code
# in this file as well.  But, currently, MacOSX updater runs
# the code located in ``updater/unix.py``.
#

import base64
import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.defer import Deferred
from neubot.poller import POLLER
from neubot.runner_core import RUNNER_CORE

from neubot import updater_install
from neubot import updater_utils
from neubot import updater_verify
from neubot import utils_hier
from neubot import utils_version

class UpdaterRunner(object):

    ''' An updater that uses the runner '''

    def __init__(self, system, basedir):
        ''' Initializer '''
        self.system = system
        self.basedir = basedir

    def _handle_failure(self, argument):
        ''' Handle callback failure '''
        logging.warning('updater_runner: callback failed: %s', argument)
        self._schedule()

    def start(self):
        ''' Schedule first check for updates '''
        self._schedule()

    def _schedule(self):
        ''' Schedule next check for updates '''
        interval = CONFIG['win32_updater_interval']
        logging.debug('updater_runner: next check in %d seconds',
                      interval)
        POLLER.sched(interval, self.retrieve_versioninfo)

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

        channel = CONFIG['win32_updater_channel']
        ctx = { 'uri': updater_utils.versioninfo_get_uri(self.system,
                                                         channel) }

        deferred = Deferred()
        deferred.add_callback(self._process_versioninfo)
        deferred.add_errback(self._handle_failure)

        RUNNER_CORE.run('dload', deferred, False, ctx)

    def _process_versioninfo(self, ctx):
        ''' Process version information '''

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return
        length, body, error = ctx.pop('result')
        if length == -1:
            logging.info('updater_runner: %s', str(error))
            self._schedule()
            return

        vinfo = updater_utils.versioninfo_extract(body)
        if not vinfo:
            logging.error('updater_runner: invalid versioninfo')
            self._schedule()
            return
        cur = utils_version.NUMERIC_VERSION
        if not updater_utils.versioninfo_is_newer(vinfo):
            logging.debug('updater_runner: no updates available')
            self._schedule()
            return
        logging.info('updater_runner: %s -> %s', cur, vinfo)
        self.retrieve_files(ctx, vinfo)

    def retrieve_files(self, ctx, vinfo):
        ''' Retrieve files for a given version '''
        # Note: this is a separate function for testability

        uri = updater_utils.signature_get_uri(self.system, vinfo)
        ctx['uri'] = uri
        ctx['vinfo'] = vinfo
        logging.info('updater_runner: GET %s', uri)

        deferred = Deferred()
        deferred.add_callback(self._retrieve_tarball)
        deferred.add_errback(self._handle_failure)

        RUNNER_CORE.run('dload', deferred, False, ctx)

    def _retrieve_tarball(self, ctx):
        ''' Retrieve tarball for a given version '''

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return

        length, body, error = ctx.pop('result')
        if length == -1:
            logging.info('updater_runner: %s', str(error))
            self._schedule()
            return

        logging.debug('updater_runner: signature (base64): %s',
                      base64.b64encode(body))

        ctx['signature'] = body
        ctx['uri'] = updater_utils.tarball_get_uri(self.system, ctx['vinfo'])

        logging.info('updater_runner: GET %s', ctx['uri'])

        deferred = Deferred()
        deferred.add_callback(self._process_files)
        deferred.add_errback(self._handle_failure)

        RUNNER_CORE.run('dload', deferred, False, ctx)

    def _process_files(self, ctx):
        ''' Process files for a given version '''

        if not 'result' in ctx:
            logging.error('updater_runner: no result')
            self._schedule()
            return

        length, body, error = ctx.pop('result')
        if length == -1:
            logging.error('updater_runner: %s', str(error))
            self._schedule()
            return

        logging.info('updater_runner: %d-bytes tarball', len(body))

        # Save tarball and signature on disk
        updater_utils.tarball_save(self.basedir, ctx['vinfo'], body)
        updater_utils.signature_save(self.basedir, ctx['vinfo'],
                                     ctx['signature'])

        # Verify signature using OpenSSL
        updater_verify.dgst_verify(updater_utils.signature_path(
          self.basedir, ctx['vinfo']), updater_utils.tarball_path(
          self.basedir, ctx['vinfo']))
        logging.info('updater_runner: signature OK')

        updater_install.install(self.basedir, ctx['vinfo'])
        logging.info('updater_win32: extracted tarball')

        self.install(ctx, body)

    def install(self, ctx, body):
        ''' Install and run the new version '''

USAGE = 'neubot updater_runner [-vy] [-C channel] [-O system] [version]'

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
