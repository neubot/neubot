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

from neubot.config import CONFIG

from neubot import utils_hier
from neubot import utils_path

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

def dgst_verify(signature, tarball, key=None):

    '''
     Call OpenSSL to verify the signature.  The public key
     is ``VERSIONDIR/pubkey.pem``.  We assume the signature
     algorithm is SHA256.
    '''

    if not utils_hier.OPENSSL:
        raise RuntimeError('updater_verify: No OPENSSL defined')
    if not key:
        key = os.sep.join([utils_hier.VERSIONDIR, 'pubkey.pem'])

    #
    # By default subprocess.call() does not invoke the shell and
    # passes the command line to execve().  We set the command to
    # invoke and many arguments, but the caller "controls" some
    # other arguments.  In the common case, when we're invoked by
    # updater_runner.py, arguments are verified.  Still, for
    # additional correctness, here we also make sure we receive
    # file names below BASEDIR.
    #
    # TODO Here we can be even more paranoid^H^H obsessed by
    # correctness, and we can check (a) that we have received
    # normalized paths and (b) that signature, tarball, and
    # key follow certain patterns.
    #
    for path in (signature, tarball, key):
        path = utils_path.normalize(path)
        if not path.startswith(utils_hier.BASEDIR):
            raise RuntimeError('updater_verify: passed path outside of BASEDIR')

    #
    # We control the file names, typically.  If they're not controlled,
    # above there is code that restricts them inside BASEDIR.  Note that
    # the ``-verify`` switch should ensure that files are read and checked,
    # and not written.  Still, files we are going to verify may have
    # been crafted to crash openssl and run arbitratry code.  For this
    # reason, I wonder whether it makes sense to run the openssl subpro-
    # cess with reduced privileges.
    #
    cmdline = [utils_hier.OPENSSL, 'dgst', '-sha256', '-verify', key,
               '-signature', signature, tarball]

    __logging_info('updater_verify: exec: %s', str(cmdline))

    retval = subprocess.call(cmdline)

    if retval != 0:
        raise RuntimeError('updater_verify: signature does not match')

def __dgst_sign(signature, tarball, key):

    '''
     Call OpenSSL to create the signature.  The private key
     must be supplied, i.e. there is no default key.  We use
     the SHA256 algorithm.
    '''

    #
    # This function is private because it's designed just for
    # this module's main(), and it does not have the set of
    # correctness checks that the verify function implements.
    #

    if not utils_hier.OPENSSL:
        raise RuntimeError('updater_verify: No OPENSSL defined')

    cmdline = [utils_hier.OPENSSL, 'dgst', '-sha256', '-sign', key,
               '-out', signature, tarball]

    __logging_info('updater_verify: exec: %s', str(cmdline))

    retval = subprocess.call(cmdline)

    if retval != 0:
        raise RuntimeError('updater_verify: cannot create signature')

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
        __dgst_sign(signature, tarball, key)
        sys.exit(0)

    dgst_verify(signature, tarball, key)

if __name__ == '__main__':
    main(sys.argv)
