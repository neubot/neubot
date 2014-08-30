#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

import ssl

class _SSLContext(object):

    def __init__(self, protocol):
        self._protocol = protocol
        self._certfile = None
        self._keyfile = None
        self._password = None

    def cert_store_stats(self):
        raise NotImplementedError

    def load_cert_chain(self, certfile, keyfile=None, password=None):
        self._certfile = certfile
        self._keyfile = keyfile
        self._password = password  # XXX ignored

    def load_default_certs(self, *args):
        raise NotImplementedError

    def load_verify_locations(self, cafile=None, capath=None, cadata=None):
        raise NotImplementedError

    def get_ca_certs(self, binary_form=False):
        raise NotImplementedError

    def set_default_verify_paths(self):
        raise NotImplementedError

    def set_ciphers(self, ciphers):
        raise NotImplementedError

    def set_npn_protocols(self, protocols):
        raise NotImplementedError

    def set_servername_callback(self, callback):
        raise NotImplementedError

    def load_dh_params(self, dhfile):
        raise NotImplementedError

    def set_ecdh_curve(self, curve_name):
        raise NotImplementedError

    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None):
        # XXX server_hostname is ignored
        return ssl.wrap_socket(sock, server_side=server_side,
          do_handshake_on_connect=do_handshake_on_connect,
          suppress_ragged_eofs=suppress_ragged_eofs,
          certfile=self._certfile, keyfile=self._keyfile)

    def session_stats(self):
        raise NotImplementedError

    @property
    def check_hostname(self):
        raise NotImplementedError
    @check_hostname.setter
    def check_hostname(self, value):
        raise NotImplementedError

    @property
    def options(self):
        raise NotImplementedError
    @options.setter
    def options(self, value):
        raise NotImplementedError

    @property
    def protocol(self):
        raise NotImplementedError
    @protocol.setter
    def protocol(self, value):
        raise NotImplementedError

    @property
    def verify_flags(self):
        raise NotImplementedError
    @verify_flags.setter
    def verify_flags(self, value):
        raise NotImplementedError

    @property
    def verify_mode(self):
        raise NotImplementedError
    @verify_mode.setter
    def verify_mode(self, value):
        raise NotImplementedError
