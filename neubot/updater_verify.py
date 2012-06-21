# neubot/updater_verify.py

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

''' Verify digital signature '''

# Adapted from neubot/updater/unix.py

import getopt
import logging
import os
import subprocess
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_sysdirs
from neubot.config import CONFIG

if os.name == 'posix':
    import syslog

def __logging_info(message, args):
    ''' Wrapper that decides whether to use syslog or logging,
        depending on the operating system. '''
    #
    # XXX Ideally this should be fixed in updater/unix.py but
    # for now we will deal with that here.
    #
    if os.name == 'posix' and not os.isatty(sys.stdin.fileno()):
        syslog.syslog(syslog.LOG_INFO, message % args)
    else:
        logging.info(message, args)

def verify_rsa(signature, tarball, key=None):

    '''
     Call OpenSSL to verify the signature.  The public key
     is ``VERSIONDIR/pubkey.pem``.  We assume the signature
     algorithm is SHA256.
    '''

    if not utils_sysdirs.OPENSSL:
        raise RuntimeError('updater_verify: No OPENSSL defined')
    if not key:
        key = os.sep.join([utils_sysdirs.VERSIONDIR, 'pubkey.pem'])

    cmdline = [utils_sysdirs.OPENSSL, 'dgst', '-sha256', '-verify', key,
               '-signature', signature, tarball]

    __logging_info('Cmdline: %s', str(cmdline))

    retval = subprocess.call(cmdline)

    if retval != 0:
        raise RuntimeError('Signature does not match')

def dgst_sign(signature, tarball, key):

    '''
     Call OpenSSL to create the signature.  The private key
     must be supplied, i.e. there is no default key.  We use
     the SHA256 algorithm.
    '''

    if not utils_sysdirs.OPENSSL:
        raise RuntimeError('updater_verify: No OPENSSL defined')

    cmdline = [utils_sysdirs.OPENSSL, 'dgst', '-sha256', '-sign', key,
               '-out', signature, tarball]

    __logging_info('Cmdline: %s', str(cmdline))

    retval = subprocess.call(cmdline)

    if retval != 0:
        raise RuntimeError('Cannot create signature')

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], 'k:sv')
    except getopt.error:
        sys.exit('neubot updater_verify [-sv] [-k key] path')
    if len(arguments) != 1:
        sys.exit('neubot updater_verify [-sv] [-k key] path')

    key = None
    sign = 0
    for name, value in options:
        if name == '-k':
            key = value
        elif name == '-s':
            sign = 1
        elif name == '-v':
            CONFIG['verbose'] = 1

    tarball = arguments[0]
    signature = tarball + '.sig'

    if sign:
        dgst_sign(signature, tarball, key)
        sys.exit(0)

    verify_rsa(signature, tarball, key)

if __name__ == '__main__':
    main(sys.argv)
