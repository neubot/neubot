# neubot/http/api.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Module's high-level API
#

import logging
import neubot
import os
import socket

def reply(message, method="", uri="", scheme="", address="", port="",
          pathquery="", code="", reason="", version="HTTP/1.1", nocache=True,
          body=None, mimetype="", date=True, keepalive=True,
          family=socket.AF_INET, certfile=None):
    return compose(method, uri, scheme, address, port, pathquery, code,
                   reason, version, nocache, body, mimetype, date, keepalive,
                   message, family, certfile)

from neubot.http.messages import compose as compose_

def compose(method="", uri="", scheme="", address="", port="", pathquery="",
            code="", reason="", version="HTTP/1.1", nocache=True, body=None,
            mimetype="", date=True, keepalive=True, inreplyto=None,
            family=socket.AF_INET, certfile=None):
    m = neubot.http.message()
    compose_(m, method=method, uri=uri, scheme=scheme, address=address,
             port=port, pathquery=pathquery, code=code, reason=reason,
             protocol=version, nocache=nocache, body=body, mimetype=mimetype,
             date=date, keepalive=keepalive, family=family)
    if inreplyto:
        m._proto = inreplyto._proto
        m.context = inreplyto.context
    m.certfile = certfile
    return m

#
# We keep cantbind() different from cantrecv() because from a server
# perspective the former might be an hard error while the latter is
# nearly always a soft error.
#

class Recv:
    def __init__(self, message, received, trylisten, cantbind, listening,
                 tryrecv, receiving, cantrecv, nochunks, maxclients, maxconn,
                 recvtimeo, maxlength, nounbounded):
        self.message = message
        self.received = received
        self.trylisten = trylisten
        self.cantbind = cantbind
        self.listening = listening
        self.tryrecv = tryrecv
        self.receiving = receiving
        self.cantrecv = cantrecv
        self.nochunks = nochunks
        self.maxclients = maxclients
        self.maxconn = maxconn
        self.recvtimeo = recvtimeo
        self.maxlength = maxlength
        self.nounbounded = nounbounded
        if not self.message._proto:
            secure = (message.scheme == "https")
            neubot.net.listen(message.address, message.port,
             accepted=self._got_connection, cantbind=self._cantbind,
             family=message.family, secure=secure,
             certfile=message.certfile)
        else:
            #
            # XXX Due to the implementation of protocol here we need to
            # "attach" it to get events back.  We probably need a less
            # rigid API.
            #
            self.message._proto.attach(self)
            if self.tryrecv:
                self.tryrecv(self.message)
            self.message._proto.recvmessage()

    def __del__(self):
        pass

    def _cantbind(self):
        if self.cantbind:
            self.cantbind(self.message)

    def _got_connection(self, stream):
        if self.message["connection"] == "close":
            keepalive=False
        else:
            keepalive=True
        # Do we need to copy other parameters from the original msg?
        message = compose(keepalive=keepalive)
        adaptor = neubot.http.adaptor(stream)
        protocol = neubot.http.protocol(adaptor)
        message._proto = protocol
        recv(message, receiving=self.receiving, cantrecv=self.cantrecv,
             received=self.received, nochunks=self.nochunks,
             recvtimeo=self.recvtimeo, maxlength=self.maxlength,
             nounbounded=self.nounbounded)

    #
    # There are some XXX below.  Here's the explanation.
    #
    #                application
    #        .-----------------------.
    #       v                         \
    #   +------+    +---------+    +--------+    +---------+
    #   | self | -> | message | -> | _proto | -> | message |
    #   +------+    +---------+    +--------+    +---------+
    #                                                ^^^
    #                                       This is what we've read
    #
    # In closing():
    # The protocol invokes our closing() method as a cleanup function,
    # and we must drop our reference to the protocol via self.message
    # for the prototocol refcount to become zero.
    #
    # In got_message():
    # We have finished our job since the message was received and so,
    # first of all, we break the chain that leads to us so that we can
    # die gracefully.
    # We also break the link between _proto and the message that we've
    # read because we want to decouple the life cycle of the message
    # from the one of the protocol that read it.
    # Finally we decouple our self.message from the protocol, again to
    # achieve lifecycle independence.
    #

    def closing(self, protocol):
        self.message._proto = None                                      # XXX
        if self.cantrecv:
            self.cantrecv(self.message)

    def got_message(self, protocol):
        # XXX
        self.message._proto.application = None
        message = self.message._proto.message
        self.message._proto.message = None
        protocol = self.message._proto
        self.message._proto = None
        # Client or server?
        if self.message.method:
            # TODO Implement connection keep-alive
            protocol.close()
        else:
            message._proto = protocol
        message.body.seek(0)
        if self.received:
            self.received(message)

    def got_data(self, protocol, octets):
        if self.receiving:
            self.receiving(octets)

    def got_metadata(self, protocol):
        neubot.http.prettyprinter(logging.debug, "< ", protocol.message)
        if self.message.method == "HEAD":
            self.message._proto.donthavebody()
        # Is request compliant with upstream's expectations?
        if (self.nochunks and
         protocol.message["transfer-encoding"] == "chunked"):
            protocol.close()
        elif (self.maxlength > 0 and
         protocol.message["content-length"]):
            try:
                length = int(protocol.message["content-length"])
            except ValueError:
                length = -1
            if length < 0 or length > self.maxlength:
                protocol.close()
        elif (self.nounbounded and neubot.http.response_unbounded(self.message,
         protocol.message)):
            protocol.close()

    def is_message_unbounded(self, protocol):
        # Client or server?
        if self.message.method:
            return neubot.http.response_unbounded(self.message,
             self.message._proto.message)
        else:
            return False

    def message_sent(self, protocol):
        raise Exception("Internal error")

def recv(message, received=None, trylisten=None, cantbind=None,
         listening=None, tryrecv=None, receiving=None, cantrecv=None,
         nochunks=False, maxclients=7, maxconn=4, recvtimeo=300,
         maxlength=-1, nounbounded=False):
    Recv(message, received, trylisten, cantbind, listening, tryrecv, receiving,
         cantrecv, nochunks, maxclients, maxconn, recvtimeo, maxlength,
         nounbounded)

class Send:
    def __init__(self, message, sent, connecting, connected, trysend, sending,
                 cantsend, conntimeo, sendtimeo):
        self.message = message
        self.sent = sent
        self.connecting = connecting
        self.connected = connected
        self.trysend = trysend
        self.sending = sending
        self.cantsend = cantsend
        self.conntimeo = conntimeo
        self.sendtimeo = sendtimeo
        if not self.message._proto:
            secure = (message.scheme == "https")
            neubot.net.connect(message.address, message.port, self._connected,
             connecting=self._connecting, cantconnect=self._cantconnect,
             family=message.family, secure=secure, conntimeo=self.conntimeo)
        else:
            self._sendmessage()

    def __del__(self):
        pass

    def _connecting(self):
        if self.connecting:
            self.connecting(self.message)

    def _cantconnect(self):
        if self.cantsend:
            self.cantsend(self.message)

    def _connected(self, stream):
        if self.connected:
            self.connected(self.message)
        adaptor = neubot.http.adaptor(stream)
        self.message._proto = neubot.http.protocol(adaptor)
        self._sendmessage()

    #
    # XXX Due to the implementation of protocol here we need to
    # "attach" it to get events back.  We probably need a less
    # rigid API.
    #

    def _sendmessage(self):
        neubot.http.prettyprinter(logging.debug, "> ", self.message)
        self.message._proto.attach(self)
        if self.trysend:
            self.trysend(self.message)
        self.message._proto.sendmessage(self.message)

    def closing(self, protocol):
        self.message._proto = None
        if self.cantsend:
            self.cantsend(self.message)

    def got_message(self, protocol):
        raise Exception("Internal error")

    def got_metadata(self, protocol):
        raise Exception("Internal error")

    def is_message_unbounded(self, protocol):
        raise Exception("Internal error")

    #
    # XXX We must clear _protocol.application *before* invoking
    #  self.sent because self.sent might override the application
    #  and we don't want to loose the reference in this case.
    #

    def message_sent(self, protocol):
        self.message._proto.application = None
        if self.sent:
            self.sent(self.message)
        if self.message.code and self.message["connection"] == "close":
            protocol.passiveclose()

    def sent_data(self, protocol, octets):
        if self.sending:
            self.sending(octets)

def send(message, sent=None, connecting=None, connected=None, trysend=None,
         sending=None, cantsend=None, conntimeo=10, sendtimeo=10):
    Send(message, sent, connecting, connected, trysend, sending,
         cantsend, conntimeo, sendtimeo)
