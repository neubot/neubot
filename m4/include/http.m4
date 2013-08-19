dnl m4/include/http.m4

dnl
dnl Copyright (c) 2011-2013
dnl     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
dnl     and Simone Basso <bassosimone@gmail.com>
dnl
dnl This file is part of Neubot <http://www.neubot.org/>.
dnl
dnl Neubot is free software: you can redistribute it and/or modify
dnl it under the terms of the GNU General Public License as published by
dnl the Free Software Foundation, either version 3 of the License, or
dnl (at your option) any later version.
dnl
dnl Neubot is distributed in the hope that it will be useful,
dnl but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
dnl GNU General Public License for more details.
dnl
dnl You should have received a copy of the GNU General Public License
dnl along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
dnl

dnl
dnl Macros to implement HTTP
dnl

dnl
dnl HTTP_DEFS()
dnl
define(`HTTP_DEFS',
``HTTP_ELINETOOLONG = 0
HTTP_ETOOMANYHEADERS = 1
HTTP_ENOHEADERS = 2
###HTTP_ETOOMANYLINES = 3
HTTP_EINVALIDFIRSTLINE = 4
HTTP_EINVALIDPROTOCOL = 5
HTTP_EUNSUPPORTEDVERSION = 6
HTTP_EINVALIDHEADER = 7
HTTP_ESOCKET = 8
HTTP_EEOF = 9
HTTP_EINVALIDLENGTH = 10
HTTP_ENEGATIVELENGTH = 11
HTTP_EINVALIDCHUNKLEN = 12
HTTP_ENEGATIVECHUNKLEN = 13
HTTP_EINVALIDCHUNKEND = 14
HTTP_EINTERNAL = 15
###HTTP_EINVALIDREQUEST = 16

HTTP_MAX_HEADERS = 128
HTTP_MAX_LINE_LENGTH = 512
HTTP_PIECE_MAX = 1 << 22
HTTP_RECV_MAX = 1 << 18
'')

dnl
dnl HTTP_IMPLEMENT_READN(<hook>, <vector>, <success>, <piece>, <indent>)
dnl
define(`HTTP_IMPLEMENT_READN',
        ``while True:
$4            amount = min(self.http_left, HTTP_PIECE_MAX)
$4            vector = self.buff_ibuff_readn(amount, False)
$4            if not vector:
$4                self.sock_recv_complete = $1
$4                self.sock_recv(HTTP_RECV_MAX)
$4                return
$4            for data in vector:
$4                self.http_left -= len(data)
$4                $2.append(data)
$4            self.http_handle_body_part()
$4            if self.http_left <= 0:
$4                break
$4        $3
'')

dnl
dnl HTTP_IMPLEMENT_READALL(<hook>, <vector>, <indent>)
dnl
define(`HTTP_IMPLEMENT_READALL',
        ``while True:
$3            amount = HTTP_PIECE_MAX
$3            vector = self.buff_ibuff_readn(amount, False)
$3            if not vector:
$3                self.sock_recv_complete = $1
$3                self.sock_recv(HTTP_RECV_MAX)
$3                return
$3            for data in vector:
$3                $2.append(data)
$3            self.http_handle_body_part()
'')

dnl
dnl HTTP_IMPLEMENT_HOOK_GENERIC(<impl-func>, <complete-hook>, <on-EOF))
dnl
define(`HTTP_IMPLEMENT_HOOK_GENERIC',
        ``if error:
            logging.warning("http: socket-level error")
            $2(HTTP_ESOCKET)
            return
        if not data:
            $2($3)
            return
        self.buff_ibuff_append(data)
        self.$1()
'')

dnl
dnl HTTP_IMPLEMENT_HOOK(<impl-func>, <complete-hook>)
dnl
define(`HTTP_IMPLEMENT_HOOK',
    `HTTP_IMPLEMENT_HOOK_GENERIC($1, $2, HTTP_EEOF)')

dnl
dnl HTTP_IMPLEMENT_HOOK_EOF_OK(<impl-func>, <complete-hook>)
dnl
define(`HTTP_IMPLEMENT_HOOK_EOF_OK',
    `HTTP_IMPLEMENT_HOOK_GENERIC($1, $2, 0)')

dnl
dnl HTTP_IMPLEMENT_READHEADERS(<socket-hook>, <complete-hook>, <vector>,
dnl                            <indent>)
dnl
define(`HTTP_IMPLEMENT_READHEADERS',
        ``while True:
$4            line, count = self.buff_ibuff_readline(True)
$4            if not line:
$4                if count > HTTP_MAX_LINE_LENGTH:
$4                    logging.warning("http: line too long")
$4                    $2(HTTP_ELINETOOLONG)
$4                    return
$4                self.sock_recv_complete = $1
$4                self.sock_recv(HTTP_RECV_MAX)
$4                return
$4            line = line.rstrip()
$4            logging.debug("< %s", line)
$4            if not line:
$4                break
$4            $3.append(line)
$4            if len($3) > HTTP_MAX_HEADERS:
$4                logging.warning("http: received too many headers")
$4                $2(HTTP_ETOOMANYHEADERS)
$4                return
'')

dnl
dnl HTTP_IMPLEMENT_READLINE(<socket-hook>, <complete-hook>, <indent>)
dnl
define(`HTTP_IMPLEMENT_READLINE',
        ``line, count = self.buff_ibuff_readline(True)
$3        if not line:
$3            if count > HTTP_MAX_LINE_LENGTH:
$3                logging.warning("http: line too long")
$3                $2(HTTP_ELINETOOLONG)
$3                return
$3            self.sock_recv_complete = $1
$3            self.sock_recv(HTTP_RECV_MAX)
$3            return
$3        line = line.rstrip()
$3        logging.debug("< %s", line)
'')

dnl
dnl HTTP_IMPLEMENT_GROK_FIRSTLINE(<message>, <field-1>, <field-2>, <field-3>)
dnl
define(`HTTP_IMPLEMENT_GROK_FIRSTLINE',
        `#
        # Grok $1 line
        #

        if not self.http_$1_lines:
            logging.warning("http: received no headers")
            self.http_handle_headers(HTTP_ENOHEADERS)
            return

        line = self.http_$1_lines[0]
        vector = line.split(None, 2)
        if len(vector) != 3:
            logging.warning("http: invalid first line")
            self.http_handle_headers(HTTP_EINVALIDFIRSTLINE)
            return

        self.http_$1_$2 = vector[0]
        self.http_$1_$3 = vector[1]
        self.http_$1_$4 = vector[2]

        if not self.http_$1_protocol.startswith(six.b("HTTP/")):
            logging.warning("http: invalid protocol")
            self.http_handle_headers(HTTP_EINVALIDPROTOCOL)
            return

        if self.http_$1_protocol[5:] not in (six.b("1.1"), six.b("1.0")):
            logging.warning("http: unsupported protocol version")
            self.http_handle_headers(HTTP_EUNSUPPORTEDVERSION)
            return
')

dnl
dnl HTTP_IMPLEMENT_GROK_HEADERS(<message>, <dict>, <func>, <indent>)
dnl
define(`HTTP_IMPLEMENT_GROK_HEADERS',
        `#
$4        # Grok $1 headers (or trailers)
$4        #

$4        last_header = None
$4        for line in self.http_$1_lines[1:]:

$4            #
$4            # Line folding. Must preceed header parsing, otherwise one
$4            # cannot send the colon character in folded lines.
$4            #
$4            if last_header and line[0:1] in (six.b(" "), six.b("\t")):
$4                value  = self.http_$2[last_header]
$4                value += six.b(" ")
$4                value += line.strip()
$4                # Make sure there are no leading or trailing spaces
$4                self.http_$2[last_header] = value.strip()
$4                continue

$4            index = line.find(six.b(":"))
$4            if index >= 0:
$4                name, value = line.split(six.b(":"), 1)
$4                name = name.strip().lower()
$4                value = value.strip()
$4                if name not in self.http_$2:
$4                    self.http_$2[name] = value
$4                else:
$4                    #
$4                    # For headers whose value is a list of
$4                    # comma-separated values, multiple headers
$4                    # with the same name are equivalent to a
$4                    # comma-separated list of values.
$4                    #     (See: RFC2616, sect. 4.2)
$4                    #
$4                    self.http_$2[name] += six.b(", ")
$4                    self.http_$2[name] += value
$4                last_header = name
$4                continue

$4            logging.warning("http: received invalid header line")
$4            self.$3(HTTP_EINVALIDHEADER)
$4            return

$4        self.$3(0)
')

dnl
dnl HTTP_READ_HEADERS(<message>, <field-1>, <field-2>, <field-3>)
dnl
define(`HTTP_READ_HEADERS',
    `def http_read_headers(self):
        """ Read $1 headers """
        self.http_$1_lines = []
        self.http_$1_$2 = six.b("")
        self.http_$1_$3 = six.b("")
        self.http_$1_$4 = six.b("")
        self.http_$1_headers = {}
        self._http_read_headers_loop()

    def _http_read_headers_loop(self):
        """ Loop that reads $1 headers """

        HTTP_IMPLEMENT_READHEADERS(self._http_read_headers_hook,
          self.http_handle_headers, self.http_$1_lines)

        HTTP_IMPLEMENT_GROK_FIRSTLINE($1, $2, $3, $4)

        HTTP_IMPLEMENT_GROK_HEADERS($1, $1_headers, http_handle_headers)

    def _http_read_headers_hook(self, error, data):
        """ Socket-level hook for reading $1 headers """
        HTTP_IMPLEMENT_HOOK(_http_read_headers_loop,
          self.http_handle_headers)

    def http_handle_headers(self, error):
        """ We have read $1 headers """
')

dnl
dnl HTTP_CLEAR_BODY_STATE(<message>)
dnl
define(`HTTP_CLEAR_BODY_STATE',
        ``self.http_$1_body = []
        self.http_$1_lines = []
        self.http_$1_trailers = {}

        # Also reset the two state variables for consistency
        self.http_chunked_state = 0
        self.http_left = 0
'')

dnl
dnl HTTP_IMPLEMENT_READ_BODY_COMMON(<message>)
dnl
define(`HTTP_IMPLEMENT_READ_BODY_COMMON',
        ``tmp = self.http_$1_headers.get(six.b("transfer-encoding"))
        if tmp == six.b("chunked"):
            logging.debug("http: there is a chunked message body")
            self._http_read_chunked()
            return

        tmp = self.http_$1_headers.get(six.b("content-length"))
        if tmp:
            try:
                length = int(tmp)
            except ValueError:
                logging.warning("http: invalid Content-Length header")
                self.http_handle_body(HTTP_EINVALIDLENGTH)
                return

            if length > 0:
                logging.debug("http: there is a bounded message body")
                self._http_read_bounded(length)
                return
            if length == 0:
                logging.debug("http: the message body is empty")
                self.http_handle_body(0)
                return

            logging.warning("http: negative Content-Length header")
            self.http_handle_body(HTTP_ENEGATIVELENGTH)
            return
'')

dnl
dnl HTTP_CLIENT_READ_BODY()
dnl
define(`HTTP_CLIENT_READ_BODY',
    `def http_read_body(self):
        """ Read the HTTP response body """

        HTTP_CLEAR_BODY_STATE(response)

        #
        #     "[...] All responses to the HEAD request method MUST NOT include a
        # message-body, even though the presence of entity-header fields might
        # lead one to believe they do. All 1xx (informational), 204 (no content)
        # and 304 (not modified) responses MUST NOT include a message-body.  All
        # other responses do include a message-body, although it MAY be of zero
        # length." (RFC2616, sect. 4.3)
        #

        if (
            self.http_request_method == six.b("HEAD") or
            self.http_response_code[0:1] == six.b("1") or
            self.http_response_code == six.b("204") or
            self.http_response_code == six.b("304")
           ):
            logging.debug("http: there is no message body")
            self.http_handle_body(0)
            return

        HTTP_IMPLEMENT_READ_BODY_COMMON(response)

        logging.debug("http: there is an unbounded message body")
        self._http_read_unbounded()
')

dnl
dnl HTTP_SERVER_READ_BODY()
dnl
define(`HTTP_SERVER_READ_BODY',
    `def http_read_body(self):
        """ Read the HTTP request body """

        HTTP_CLEAR_BODY_STATE(request)

        HTTP_IMPLEMENT_READ_BODY_COMMON(request)

        logging.debug("http: assuming that the body is empty")
        self.http_handle_body(0)
')

dnl
dnl HTTP_READ_BOUNDED(<message>)
dnl
define(`HTTP_READ_BOUNDED',
    `def http_handle_body(self, error):
        """ We have received all the body """

    def http_handle_body_part(self):
        """ We have received a part of the body """

    def _http_read_bounded(self, amount):
        """ Read the bounded $1 body """
        self.http_left = amount
        self._http_read_bounded_loop()

    def _http_read_bounded_loop(self):
        """ Loop that reads the bounded $1 body """
        HTTP_IMPLEMENT_READN(self._http_read_bounded_hook,
          self.http_$1_body, self.http_handle_body(0))

    def _http_read_bounded_hook(self, error, data):
        """ Socket-level hook for reading the bounded $1 body """
        HTTP_IMPLEMENT_HOOK(_http_read_bounded_loop,
          self.http_handle_body)
')

dnl
dnl HTTP_READ_UNBOUNDED(<message>)
dnl
define(`HTTP_READ_UNBOUNDED',
    `def _http_read_unbounded(self):
        """ Read unbounded $1 body """
        self._http_read_unbounded_loop()

    def _http_read_unbounded_loop(self):
        """ Loop that reads unbounded $1 body """
        HTTP_IMPLEMENT_READALL(self._http_read_unbounded_hook,
          self.http_$1_body)

    def _http_read_unbounded_hook(self, error, data):
        """ Socket-level hook for reading unbounded $1 body """
        HTTP_IMPLEMENT_HOOK_EOF_OK(_http_read_unbounded_loop,
          self.http_handle_body)
')

dnl
dnl HTTP_READ_CHUNKED(<message>)
dnl
define(`HTTP_READ_CHUNKED',
    `def _http_read_chunked(self):
        """ Read chunked $1 body """
        self.http_chunked_state = 1
        self._http_read_chunked_loop()

    def _http_read_chunked_loop(self):
        """ Loop that reads the chunked $1 body """
        while True:

            if self.http_chunked_state == 1:
                HTTP_IMPLEMENT_READLINE(self._http_read_chunked_hook,
                  self.http_handle_body, `        ')

                vector = line.split()
                if not vector:
                    logging.warning("http: invalid chunk-length line")
                    self.http_handle_body(HTTP_EINVALIDCHUNKLEN)
                    return
                try:
                    tmp = int(vector[0], 16)
                except ValueError:
                    logging.warning("http: invalid chunk-length token")
                    self.http_handle_body(HTTP_EINVALIDCHUNKLEN)
                    return
                if tmp < 0:
                    logging.warning("http: negative chunk-length token")
                    self.http_handle_body(HTTP_ENEGATIVECHUNKLEN)
                    return

                if tmp > 0:
                    logging.debug("< {chunk len=%d}", tmp)
                    self.http_left = tmp
                    self.http_chunked_state = 2
                else:
                    logging.debug("< {last-chunk/}")
                    self.http_chunked_state = 4

            elif self.http_chunked_state == 2:
                HTTP_IMPLEMENT_READN(self._http_read_chunked_hook,
                  self.http_$1_body, self.http_chunked_state = 3, `        ')

            elif self.http_chunked_state == 3:
                HTTP_IMPLEMENT_READLINE(self._http_read_chunked_hook,
                  self.http_handle_body, `        ')
                if line:
                    logging.warning("http: invalid chunk-end line")
                    self.http_handle_body(HTTP_EINVALIDCHUNKEND)
                    return
                logging.debug("< {/chunk}")
                self.http_chunked_state = 1

            elif self.http_chunked_state == 4:
                HTTP_IMPLEMENT_READHEADERS(self._http_read_chunked_hook,
                  self.http_handle_body, self.http_$1_lines, `        ')

                HTTP_IMPLEMENT_GROK_HEADERS($1, $1_trailers, http_handle_body,
                  `        ')dnl
                return

            else:
                logging.warning("http: chunked internal error")
                self.http_handle_body(HTTP_EINTERNAL)
                return

    def _http_read_chunked_hook(self, error, data):
        """ Socket-level hook for reading chunked $1 body """
        HTTP_IMPLEMENT_HOOK(_http_read_chunked_loop,
          self.http_handle_body)
')

dnl
dnl HTTP_SEND(<message>, <field-1>, <field-2>, <field-3>)
dnl
define(`HTTP_SEND',
    ``#
    # This class only contains the methods to append HTTP data to the output
    # buffer, please use self.buff_obuff_*() to start flushing the ouput buffer
    # and to be notified when the flush operation is complete.
    #

    def http_append_$1(self, $2, $3, $4, headers, body):
        """ Append $1 to output buffer """
        vector = []

        self.http_$1_$2 = six.b($2)
        self.http_$1_$3 = six.b($3)
        self.http_$1_$4 = six.b($4)

        $1_line = six.b(" ").join([self.http_$1_$2,
          self.http_$1_$3, self.http_$1_$4])
        logging.debug("> %s", $1_line)
        vector.append($1_line)
        vector.append(six.b("\r\n"))

        self.http_$1_headers = {}
        for name, value in headers.items():
            name = six.b(name.strip())
            value = six.b(value.strip())
            header = six.b(": ").join([name, value])
            logging.debug("> %s", header)
            self.http_$1_headers[name] = value
            vector.append(header)
            vector.append(six.b("\r\n"))

        logging.debug("> ")
        vector.append(six.b("\r\n"))

        if body:
            vector.append(body)

        message = six.b("").join(vector)
        self.buff_obuff_append(message)

    def http_append_data(self, data):
        """ Append data to output buffer """
        self.buff_obuff_append(data)

    def http_append_chunk(self, data):
        """ Append chunk to output buffer """
        vector = []
        logging.debug("> {chunk len=%d}", len(data))
        vector.append(six.b("%x\r\n" % len(data)))
        vector.append(data)
        vector.append(six.b("\r\n"))
        bytez = six.b("").join(vector)
        self.buff_obuff_append(bytez)

    def http_append_last_chunk(self, trailers):
        """ Append the last chunk to output buffer """
        vector = []
        logging.debug("> {last-chunk}")
        vector.append(six.b("0\r\n"))
        for name, value in trailers.items():
            name = six.b(name.strip())
            value = six.b(value.strip())
            trailer = six.b(": ").join([name, value])
            logging.debug("> %s", trailer)
            vector.append(trailer)
            vector.append(six.b("\r\n"))

        vector.append(six.b("\r\n"))
        bytez = six.b("").join(vector)
        self.buff_obuff_append(bytez)
'')

dnl
dnl HTTP_INIT_CLEANUP_DEL(<base-class>, <written-message>, <field-1>,
dnl   <field-2>, <field-3>, <read-message>, <field-1>, <field-2>, <field-3>)
dnl
define(`HTTP_INIT_CLEANUP_DEL',
    ``def __init__(self, poller):
        logging.debug("http: init %s", self)
        $1.__init__(self, poller)
        self.http_chunked_state = 0
        self.http_left = 0

        # We save these fields just in case they are useful
        self.http_$2_$3 = six.b("")
        self.http_$2_$4 = six.b("")
        self.http_$2_$5 = six.b("")
        self.http_$2_headers = {}

        self.http_$6_lines = []
        self.http_$6_$7 = six.b("")
        self.http_$6_$8 = six.b("")
        self.http_$6_$9 = six.b("")
        self.http_$6_headers = {}
        self.http_$6_body = []
        self.http_$6_trailers = {}

    def sock_handle_close(self, error):
        $1.sock_handle_close(self, error)
        logging.debug("http: sock_handle_close(): %s", self)
        #
        # Remove the self-reference, therefore we do not need to wait for the
        # garbage collector, which, depending on the memory pressure may never
        # run (especially when we have few objects).
        #
        self.sock_recv_complete = None

    def __del__(self):
        logging.debug("http: del %s", self)
'')
