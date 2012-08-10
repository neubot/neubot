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

import getopt
import logging
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.config import CONFIG
from neubot.poller import POLLER
from neubot.runner_core import RUNNER_CORE

from neubot import updater_utils
from neubot import updater_verify
from neubot import utils_sysdirs

class UpdaterRunner(object):

    ''' An updater that uses the runner '''

    #
    # TODO The updater fetches both the checksum and the digital
    # signature, which seems to be redundant.  When the signature
    # is good, we also know that the file checksum is good, by
    # definition of digital signature.  So, we can save the step
    # where we download the SHA256 checksum.
    #

    def __init__(self, system, basedir, channel):
        ''' Initializer '''
        #
        # TODO There's no point in passing the updater channel
        # to the initializer, since we re-read it before each
        # check for updates.
        #
        self.system = system
        self.basedir = basedir
        self.channel = channel

    def start(self):
        ''' Schedule first check for updates '''
        self._schedule()

    def _schedule(self):
        ''' Schedule next check for updates '''
        POLLER.sched(1800, self.retrieve_versioninfo)

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

        #
        # Fetch again parameters, just in case the user
        # has changed them via web user interface.  With
        # this fix, one does not need to restart Neubot
        # after the channel is changed.
        #
        self.channel = CONFIG['win32_updater_channel']

        ctx = { 'uri': updater_utils.versioninfo_get_uri(self.system,
                                                         self.channel) }
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

        logging.info('updater_runner: %s -> %s', '0.004013007', vinfo)
        self.retrieve_files(vinfo)

    def retrieve_files(self, vinfo):
        ''' Retrieve files for a given version '''
        # Note: this is a separate function for testability
        uri = updater_utils.sha256sum_get_uri(self.system, vinfo)
        ctx = {'vinfo': vinfo, 'uri': uri}
        logging.info('updater_runner: GET %s', uri)
        RUNNER_CORE.run('dload', self._retrieve_signature, False, ctx)

    def _retrieve_signature(self, ctx):
        ''' Retrieve signature for a given version '''

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

        logging.info('updater_runner: %s', sha256)

        # XXX We should not reuse the same CTX here
        ctx['sha256'] = sha256
        ctx['uri'] = updater_utils.signature_get_uri(self.system, ctx['vinfo'])

        logging.info('updater_runner: GET %s', ctx['uri'])

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

        logging.info('updater_runner: (signature)')

        # XXX We should not reuse the same CTX here
        ctx['signature'] = body
        ctx['uri'] = updater_utils.tarball_get_uri(self.system, ctx['vinfo'])

        logging.info('updater_runner: GET %s', ctx['uri'])

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

        logging.info('updater_runner: (tarball)')

        if not updater_utils.sha256sum_verify(ctx['sha256'], body):
            logging.error('updater_runner: sha256 mismatch')
            self._schedule()
            return

        logging.info('updater_runner: sha256 OK')

        # Save tarball and signature on disk
        updater_utils.tarball_save(self.basedir, ctx['vinfo'], body)
        updater_utils.signature_save(self.basedir, ctx['vinfo'],
                                     ctx['signature'])

        # Verify signature using OpenSSL
        # TODO once we deal with exceptions in the runner, remove
        # this try...catch clause
        try:
            updater_verify.dgst_verify(updater_utils.signature_path(
              self.basedir, ctx['vinfo']), updater_utils.tarball_path(
              self.basedir, ctx['vinfo']))
        except:
            logging.error('updater_runner: invalid signature')
            self._schedule()
            return

        logging.info('updater_runner: signature OK')

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

    channel = CONFIG['win32_updater_channel']
    updater = UpdaterRunner(sysname, utils_sysdirs.BASEDIR, channel)

    if arguments:
        updater.retrieve_files(arguments[0])
    else:
        # Enable automatic updates if we arrive here
        CONFIG.conf['win32_updater'] = 1
        updater.retrieve_versioninfo()

    POLLER.loop()

if __name__ == '__main__':
    main(sys.argv)
