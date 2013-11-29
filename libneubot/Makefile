# libneubot/Makefile

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

DESTDIR =
PREFIX = /usr/local
LIBDIR = $(DESTDIR)/$(PREFIX)/lib

.PHONY: clean

CC = clang
CFLAGS = -Wall -pedantic -fPIC

LIBRARY = libneubot.so
OBJECTS = log.o poller.o strtonum.o utils.o

$(LIBRARY): $(OBJECTS)
	$(CC) -shared $(OBJECTS) -o $(LIBRARY) -levent -lm

log.o: log.c
poller.o: poller.c
strtonum.o: strtonum.c
utils.o: utils.c

clean:
	rm -f -- $(OBJECTS) $(LIBRARY) 
install: $(LIBRARY)
	install -m 644 $(LIBRARY) $(LIBDIR)/
uninstall:
	rm -f -- $(LIBDIR)/(LIBRARY)
