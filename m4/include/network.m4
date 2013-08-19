dnl m4/include/network.m4

dnl
dnl Copyright (c) 2010, 2011-2013
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
dnl Macros to implement networking
dnl

dnl
dnl POLLER_IMPLEMENT_INIT()
dnl
define(`POLLER_IMPLEMENT_INIT',
    ``def __init__(self):
        self.again = 1
        self.channels = {}
        self.readset = {}
        self.tasks = []
        self.timeout = 1
        self.writeset = {}
'')

dnl
dnl POLLER_IMPLEMENT_SCHED()
dnl
define(`POLLER_IMPLEMENT_SCHED',
    ``def sched(self, delay, function, arg):
        """ Call a function at a later time """
        event = (utils.ticks() + delay, function, arg)
        heapq.heappush(self.tasks, event)
        return event
'')

dnl
dnl POLLER_IMPLEMENT_RENDEZVOUS_PATTERN()
dnl
define(`POLLER_IMPLEMENT_RENDEZVOUS_PATTERN',
    ``def recv_message(self, channel, function):
        """ Wait for a message on the given channel """
        self.channels[channel] = function

    def send_message(self, channel, message):
        """ Send a message on the given channel """
        function = self.channels.pop(channel, None)
        if not function:
            return
        try:
            #
            # We pass the poller to function(), therefore function() can be
            # a plain function and does not need to be an object only to keep
            # a reference to the poller.
            #
            function(self, message)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning("poller: function() failed", exc_info=1)
'')

dnl
dnl POLLER_IMPLEMENT_SET_UNSET(<operation>)
dnl
define(`POLLER_IMPLEMENT_SET_UNSET',
    ``def set_$1(self, sock):
        """ Start monitoring for $1ability """
        self.$1set[sock.sock_fileno()] = sock

    def unset_$1(self, sock):
        """ Stop monitoring for $1ability """
        self.$1set.pop(sock.sock_fileno(), None)
'')

dnl
dnl POLLER_IMPLEMENT_CLOSE()
dnl
define(`POLLER_IMPLEMENT_CLOSE',
    ``def close(self, sock, error):
        """ Safely close a sock """
        self.unset_read(sock)
        self.unset_write(sock)
        try:
            sock.sock_handle_close(error)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error("sock_handle_close() failed", exc_info=1)
'')

dnl
dnl POLLER_DISPATCH()
dnl
define(`POLLER_DISPATCH',
``
            #
            # 1. Dispatch delayed tasks
            #

            while self.tasks:
                when, function, arg = self.tasks[0]
                if when > ticks:
                    break
                heapq.heappop(self.tasks)
                try:
                    #
                    # We pass the poller to function(), therefore function()
                    # can be a plain function and does not need to be an object
                    # only to keep a reference to the poller.
                    #
                    function(self, arg)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    logging.warning("poller: function() failed", exc_info=1)

            #
            # We do not want to leave references around for possibly a long
            # time (we do not expect to always have tasks).
            #
            when = None
            function = None
            arg = None
'')

dnl
dnl POLLER_HANDLE_RW(<operation>)
dnl
define(`POLLER_HANDLE_RW',
                ``sock = self.$1set.get(fileno)
                if not sock:
                    continue
                try:
                    sock.sock_handle_$1()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    logging.warning("poller: sock_handle_$1() failed",
                                    exc_info=1)
                    self.close(sock, -1)
'')

dnl
dnl POLLER_SELECT()
dnl
define(`POLLER_SELECT',
            `#
            # 3. Dispatch I/O events
            #

            timeout = self.timeout
            if self.tasks:
                timeout = self.tasks[0][0] - ticks
                if timeout < 0:
                    timeout = 0

            if not self.readset and not self.writeset:
                time.sleep(timeout)
                continue

            try:
                res = select.select(list(self.readset), list(self.writeset),
                                    [], timeout)
            except select.error:
                NEUBOT_ERRNO(error)
                if error.args[0] != errno.EINTR:
                    NEUBOT_PERROR(warning, poller: select() failed, error)
                    time.sleep(1)
                continue
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                NEUBOT_ERRNO(error)
                NEUBOT_PERROR(warning, poller: select() failed, error)
                time.sleep(1)
                continue

            for fileno in res[0]:
                POLLER_HANDLE_RW(read)

            for fileno in res[1]:
                POLLER_HANDLE_RW(write)
')

dnl
dnl POLLER_PERIODIC()
dnl
define(`POLLER_PERIODIC',
            ``#
            # 2. Dispatch the periodic event
            #

            if ticks >= last + 10:
                last = ticks
                sockets = set()
                for sock in self.readset.values():
                    sockets.add(sock)
                for sock in self.writeset.values():
                    sockets.add(sock)
                for sock in sockets:
                    try:
                        sock.sock_handle_periodic(ticks)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except:
                        logging.warning("poller: sock_handle_periodic(ticks) "
                                        "failed", exc_info=1)
                        self.close(sock, -1)
                sockets = None
'')dnl

dnl
dnl POLLER_IMPLEMENT_SELECT_LOOP()
dnl
define(`POLLER_IMPLEMENT_SELECT_LOOP',
    `def loop(self):
        """ Dispatch I/O and timed events """

        last = utils.ticks()
        while self.again:
            ticks = utils.ticks()
            POLLER_DISPATCH()
            POLLER_PERIODIC()
            POLLER_SELECT()

    def break_loop(self):
        """ Break the poller loop """
        self.again = 0
')dnl

dnl
dnl SOCK_IMPLEMENT_INIT()
dnl
define(`SOCK_IMPLEMENT_INIT',
    ``def __init__(self, poller):
        self.sock_poller = poller
        self.sock_recv_param = 0
        self.sock_send_param = None
        self.sock_socket = None
'')

dnl
dnl SOCK_IMPLEMENT_COMMON_CODE()
dnl
define(`SOCK_IMPLEMENT_COMMON_CODE',
    ``def sock_close(self):
        """ Close this socket """
        self.sock_poller.close(self, 0)

    def sock_handle_close(self, error):
        """ Invoked when the connection is closed """
        logging.debug("network: sock_handle_close(): %s", self)
        try:
            self.sock_socket.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

    def sock_handle_periodic(self, ticks):
        """ Simple heartbeat mechanism """

    def sock_getpeername(self):
        """ Return the address of the peer socket """
        return utils_net.getpeername(self.sock_socket)

    def sock_getsockname(self):
        """ Return the address of this socket """
        return utils_net.getsockname(self.sock_socket)

    def sock_fileno(self):
        """ Return the fileno of the socket """
        return self.sock_socket.fileno()
'')

dnl
dnl SOCK_IMPLEMENT_BIND_AND_CONNECT()
dnl
define(`SOCK_IMPLEMENT_BIND_AND_CONNECT',
    `def sock_bind(self, family, proto, address, port):
        """ Bind at the specified family, proto, address, and port """
        self.sock_socket = socket.socket(family, proto, 0)
        self.sock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_socket.setblocking(False)
        try:
            self.sock_socket.bind((address, port))
        except socket.error:
            NEUBOT_ERRNO(error)
            #
            # Using debug() because, with hybrid dual stack, you never know
            # whether bind() at 0.0.0.0:<port> failed because of your previous
            # attempt with IPv6 or because of another daemon that is already
            # bound at 0.0.0.0:<port>.
            #
            NEUBOT_PERROR(debug, network: bind() failed, error)
            return error
        else:
            return None

    def sock_connect(self, family, proto, address, port):
        """ Connect to the specified family, proto, address, and port """
        #
        # Note: with UDP connect() completes immediately, conversely with TCP
        # you also need to invoke tcp_wait_connected().
        #
        self.sock_socket = socket.socket(family, proto, 0)
        self.sock_socket.setblocking(False)
        try:
            result = self.sock_socket.connect_ex((address, port))
            # Note: Winsock returns EWOULDBLOCK
            if result not in (0, errno.EINPROGRESS, errno.EWOULDBLOCK,
                              errno.EAGAIN):
                raise socket.error(result, os.strerror(result))
        except socket.error:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, network: connect() failed, error)
            return error
        else:
            return None
')

dnl
dnl SOCK_IMPLEMENT_RECV_AND_SEND(<recv-op-name>, <send-op-name>)
dnl
define(`SOCK_IMPLEMENT_RECV_AND_SEND',
    `def sock_recv(self, count):
        """ Start an asynchronous recv() operation """
        self.sock_recv_param = count
        self.sock_poller.set_read(self)

    def $1(self):
        """ Perform the recv() operation """
        self.sock_poller.unset_read(self)
        try:
            data = self.sock_socket.recv(self.sock_recv_param)
        except socket.error:
            NEUBOT_ERRNO(error)
            if error.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR):
                self.sock_poller.set_read(self)
            else:
                NEUBOT_PERROR(warning, network: recv() failed, error)
                self.sock_recv_param = 0
                self.sock_recv_complete(error, None)
        else:
            self.sock_recv_param = 0
            self.sock_recv_complete(None, data)

    def sock_recv_complete(self, error, data):
        """ Invoked when recv() is complete """

    def sock_send(self, data):
        """ Start an asynchronous send() operation """
        self.sock_send_param = data
        self.sock_poller.set_write(self)

    def $2(self):
        """ Perform the send() operation """
        self.sock_poller.unset_write(self)
        try:
            count = self.sock_socket.send(self.sock_send_param)
        except socket.error:
            NEUBOT_ERRNO(error)
            if error.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR):
                self.sock_poller.set_write(self)
            else:
                NEUBOT_PERROR(warning, network: send() failed, error)
                self.sock_send_param = None
                self.sock_send_complete(error, 0)
        else:
            self.sock_send_param = None
            self.sock_send_complete(None, count)

    def sock_send_complete(self, error, count):
        """ Invoked when send() is complete """
')

dnl
dnl TCP_IMPLEMENT_LISTEN_AND_ACCEPT()
dnl
define(`TCP_IMPLEMENT_LISTEN_AND_ACCEPT',
    `def tcp_listen(self, backlog):
        """ Setup listen queue for socket """
        self.sock_socket.listen(backlog)

    def tcp_wait_accept(self):
        """ Wait until a new client connects """
        self.sock_poller.set_read(self)
        self.tcp_accept_pending = 1

    def _tcp_accept(self):
        """ Accept a new TCP connection """
        self.sock_poller.unset_read(self)
        self.tcp_accept_pending = 0
        try:
            sock = self.sock_socket.accept()[0]
        except socket.error:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, network: accept() failed, error)
            self.tcp_accept_complete(error, None)
            return

        sock.setblocking(False)

        try:
            peername = utils_net.getpeername(sock)
            sockname = utils_net.getsockname(sock)
        except socket.error:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, network: get*name() failed, error)
            self.tcp_accept_complete(error, None)
            return

        logging.debug("network: accept %s <-> %s", sockname, peername)

        #
        # The following statement is very handy in subclasses, but
        # there is the side effect that all subclasses must have the
        # same constructor signature of the basic socket types.
        #
        stream = self.__class__(self.sock_poller)
        stream.sock_socket = sock
        self.tcp_accept_complete(None, stream)

    def tcp_accept_complete(self, error, stream):
        """ Invoked when accept() is complete """
')

dnl
dnl TCP_IMPLEMENT_WAIT_CONNECTED()
dnl
define(`TCP_IMPLEMENT_WAIT_CONNECTED',
    `def tcp_wait_connected(self):
        """ Wait until connect is complete """
        self.sock_poller.set_write(self)
        self.tcp_connect_pending = 1

    def _tcp_connect(self):
        """ Make sure that connect succeeded """
        self.sock_poller.unset_write(self)
        self.tcp_connect_pending = 0

        #
        # We use getpeername() to check whether we established the
        # connection(). If getpeername() succeeds, the connection
        # is OK. Instead, if getpeername() fails and the error
        # indicates that we are not connected, we use recv() to get
        # the actual connect() error; otherwise, if we get another
        # kind of error, we pass such error to the caller.
        #
        # For more information see:
        #
        #   http://cr.yp.to/docs/connect.html
        #
        try:
            utils_net.getpeername(self.sock_socket)
        except socket.error:
            NEUBOT_ERRNO(error)
            # Note: on MacOSX getpeername() fails with EINVAL
            if error.args[0] in (errno.ENOTCONN, errno.EINVAL):
                try:
                    self.sock_socket.recv(1)
                except socket.error:
                    NEUBOT_ERRNO(error)
                    NEUBOT_PERROR(warning, network: connect() failed, error)
                    self.tcp_connect_complete(error)
                else:
                    # This really SHOULD NOT happen
                    logging.warning("network: connect() internal error")
                    self.tcp_connect_complete(-1)
            else:
                NEUBOT_PERROR(warning, network: connect() failed, error)
                self.tcp_connect_complete(error)
        else:
            self.tcp_connect_complete(None)

    def tcp_connect_complete(self, error):
        """ Invoked when connect is complete """
')

dnl
dnl TCP_IMPLEMENT_READWRITE_HANDLERS(<read-handler>, <write-handler>)
dnl
define(`TCP_IMPLEMENT_READWRITE_HANDLERS',
    ``def sock_handle_read(self):
        """ Handle the read event """
        if not self.tcp_accept_pending:
            self.$1()
        else:
            self._tcp_accept()

    def sock_handle_write(self):
        """ Handle the write event """
        if not self.tcp_connect_pending:
            self.$2()
        else:
            self._tcp_connect()
'')

dnl
dnl SSL_IMPLEMENT_SENDRECV(<operation>, <IO-state>, <SSL-func>,
dnl   <other-operation>, <other-IO-state>, <simple-error-case>,
dnl   <hijack-error-case>, <empty-value-for-param>, <value-on-error>)
dnl
define(`SSL_IMPLEMENT_SENDRECV',
    `def sock_$1(self, param):
        """ Start an asynchronous $1() operation """
        self.sock_$1_param = param
        if not self.ssl_hijack_$1:
            self.sock_poller.set_$2(self)
        self.ssl_$1_pending = 1

    def _ssl_$1(self):
        """ Perform the $1() operation """

        if self.ssl_handshake_pending:
            self.ssl_handshake_pending = 0
            self.sock_poller.unset_$2(self)
            self._ssl_do_handshake()
            return

        if self.ssl_hijack_$1:
            self.ssl_hijack_$1 = 0
            self.sock_poller.set_$5(self)
            if not self.ssl_$1_pending:
                self.sock_poller.unset_$2(self)
            self._ssl_$4()
            return

        self.sock_poller.unset_$2(self)
        self.ssl_$1_pending = 0
        try:
            result = self.sock_socket.$3(self.sock_$1_param)
        except ssl.SSLError:
            NEUBOT_ERRNO(error)
            if error.args[0] == ssl.$6:
                self.sock_poller.set_$2(self)
                self.ssl_$1_pending = 1
            elif error.args[0] == ssl.$7:
                self.sock_poller.set_$5(self)
                self.ssl_$1_pending = 1
                self.ssl_hijack_$4 = 1
            else:
                NEUBOT_PERROR(warning, network: SSL_$3() failed, error)
                self.sock_$1_param = $8
                self.sock_$1_complete(error, $9)
        else:
            self.sock_$1_param = $8
            self.sock_$1_complete(None, result)

    def sock_$1_complete(self, error, result):
        """ Invoked when $1 is complete """
')

dnl
dnl BUFF_IBUFF_FOREACH()
dnl
define(`BUFF_IBUFF_FOREACH',
        ``for index, bucket in enumerate(self.buff_ibuff):'')

dnl
dnl BUFF_IBUFF_SPLIT(<index-in-list>, <pos-in-pivot-bucket>)
dnl
define(`BUFF_IBUFF_SPLIT',
            ``#
            # - We cannot use the buffer interface, because the buckets
            #   will go upstream where they are processed.
            #
            # - We expect the input buffer to contain, typically, less
            #   than 3-5 pieces, therefore we use a list.
            #
            front = bucket[:$2]
            remainder = bucket[$2:]
            result = self.buff_ibuff[:$1]
            result.append(front)
            self.buff_ibuff = self.buff_ibuff[$1:]
            self.buff_ibuff[0] = remainder
'')

dnl
dnl BUFF_IMPLEMENT_APPEND_JOIN(<buff-name>)
dnl
define(`BUFF_IMPLEMENT_APPEND_JOIN',
    ``def buff_$1_append(self, data):
        """ Append data to the $1 buffer """
        self.buff_$1.append(data)
        self.buff_$1_count += len(data)

    def buff_$1_join(self):
        """ Join data in the $1 buffer """
        data = six.b("").join(self.buff_$1)
        self.buff_$1 = [data]
'')

dnl
dnl BUFF_IMPLEMENT_IBUFF()
dnl
define(`BUFF_IMPLEMENT_IBUFF',
    `BUFF_IMPLEMENT_APPEND_JOIN(ibuff)

    def buff_ibuff_readline(self, join):
        """ Read a line from the input buffer """
        count = 0
        BUFF_IBUFF_FOREACH()
            pos = bucket.find(six.b("\n"))
            if pos == -1:
                count += len(bucket)
                continue

            BUFF_IBUFF_SPLIT(index, pos + 1)dnl

            count += len(result[-1])
            if join:
                result = six.b("").join(result)
            return result, count
        return None, count

    def buff_ibuff_readn(self, pos, join):
        """ Read N bytes from the input buffer """
        BUFF_IBUFF_FOREACH()
            if pos > len(bucket):
                pos -= len(bucket)
                continue

            BUFF_IBUFF_SPLIT(index, pos)dnl

            if join:
                result = six.b("").join(result)
            return result
')

dnl
dnl BUFF_IMPLEMENT_OBUFF()
dnl
define(`BUFF_IMPLEMENT_OBUFF',
    `BUFF_IMPLEMENT_APPEND_JOIN(obuff)

    def buff_obuff_flush(self):
        """ Flush the output buffer """
        if self.buff_flushing:
            return
        self.sock_send(self.buff_obuff[0])
        self.buff_flushing = True

    def sock_send_complete(self, error, count):
        #
        # - To avoid making too many copies of strings, which is never a good
        #   idea performance-wise, we use the buffer interface.
        #
        # - We expect the output buffer to contain, typically, less than 3-5
        #   pieces, therefore we implement the output buffer using a list.
        #
        if error:
            self.buff_flushing = False
            self.buff_flush_complete(error)
            return
        self.buff_obuff[0] = six.buff(self.buff_obuff[0], count)
        if not self.buff_obuff[0]:
            del self.buff_obuff[0]
        if not self.buff_obuff:
            self.buff_flushing = False
            self.buff_flush_complete(None)
            return
        self.sock_send(self.buff_obuff[0])

    def buff_flush_complete(self, error):
        """ Invoked when we flushed the output buffer """
')

dnl
dnl BUFF_IMPLEMENT_INIT(<parent-class-name>)
dnl
define(`BUFF_IMPLEMENT_INIT',
    ``def __init__(self, poller):
        $1.__init__(self, poller)
        self.buff_flushing = False
        self.buff_ibuff = []
        self.buff_ibuff_count = 0
        self.buff_obuff = []
        self.buff_obuff_count = 0
'')
