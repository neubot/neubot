# debian/Makefile
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

PACKAGE = neubot-0.0.4-1_all.deb

all: $(PACKAGE)

DIRS += etc/init.d
DIRS += etc/neubot
DIRS += usr/bin
DIRS += usr/share/neubot/application
DIRS += usr/share/neubot/http
DIRS += usr/share/neubot/network
DIRS += usr/share/neubot/testing

dist/data:
	install -d dist/data
	cd dist/data && install -d $(DIRS)
	for file in `find neubot -type f -name \*.py`; do		\
	  install -m644 $$file dist/data/usr/share/$$file || exit 1;	\
	done
	install bin/unix/neubot dist/data/usr/bin/neubot
	install etc/init.d/neubot dist/data/etc/init.d/neubot
	./bin/unix/neubot -EI. _writeconfig > dist/data/etc/neubot/config
	chmod 644 dist/data/etc/neubot/config
dist/data.tar: dist/data
	cd dist/data && tar cf ../data.tar ./*
dist/data.tar.gz: dist/data.tar
	cat dist/data.tar | gzip -9 > dist/data.tar.gz

dist/control: dist/data.tar.gz
	install -d dist/control
	find dist/data -type f -exec md5sum {} \; > dist/control/md5sums
	sed -i 's!dist\/data\/!!g' dist/control/md5sums
	chmod 644 dist/control/md5sums
	install -m644 debian/control dist/control/
	for file in postinst prerm; do					\
	  install debian/$$file dist/control/;				\
	done
dist/control.tar.gz: dist/control
	cd dist/control && tar czf ../control.tar.gz ./*

dist/debian-binary: dist/control.tar.gz
	echo '2.0' > dist/debian-binary

debian:
	ln -s ../debian debian

$(PACKAGE): debian dist/debian-binary
	ar r $(PACKAGE) dist/debian-binary dist/*.tar.gz
