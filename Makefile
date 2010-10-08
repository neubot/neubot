# Makefile
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
# Makefile
#

VERSION	= 0.2.5

DEB     = dist/neubot-$(VERSION)-1_all.deb
DESTDIR =
PREFIX  = /usr/local

PHONIES += _all
PHONIES += _install
PHONIES += _deb

PHONIES += clean
PHONIES += help
PHONIES += install
PHONIES += lint
PHONIES += release

.PHONY: $(PHONIES)

_all: help
_install:
	@for D in `find neubot/ -type d`; do				\
	    install -m755 -d $(DESTDIR)$(PREFIX)/share/$$D || exit 1;	\
	done
	@for F in `find neubot/ -type f`; do				\
	    install -m644 $$F $(DESTDIR)$(PREFIX)/share/$$F || exit 1;	\
	done
	@install -d $(DESTDIR)/etc/neubot
	@install -d $(DESTDIR)/var/neubot
	@install -d $(DESTDIR)$(PREFIX)/bin
	@sed 's!@PREFIX@!$(PREFIX)!' neubot/pathnames.py		\
	    > $(DESTDIR)$(PREFIX)/share/neubot/pathnames.py
	@sed 's!@PREFIX@!$(PREFIX)!' bin/neubot > binunixneubot
	@install binunixneubot $(DESTDIR)$(PREFIX)/bin/neubot
	@rm binunixneubot
	@# XXX Using BSD convention for installing manual page
	@install -d $(DESTDIR)$(PREFIX)/man/man1
	@pod2man --center="Neubot manual" --release="Neubot $(VERSION)" \
         doc/neubot.1.pod > $(DESTDIR)/$(PREFIX)/man/man1/neubot.1
	@install -d $(DESTDIR)$(PREFIX)/man/man3
	@pod2man -c"Neubot manual" -r"Neubot $(VERSION)" -s3 -n"NEUBOT.NET" \
         doc/neubot.net.3.pod > $(DESTDIR)/$(PREFIX)/man/man3/neubot.net.3
_deb:
	@make -f Makefile _install DESTDIR=dist/data PREFIX=/usr
	@# XXX Work-around using BSD convention for installing manual page
	@mv dist/data/usr/man dist/data/usr/share/
	@install -d -m755 dist/data/usr/share/applications/
	@install -m644 debian/neubot.desktop dist/data/usr/share/applications/
	@install -d -m755 dist/data/etc/init.d
	@install -m755 debian/neubot dist/data/etc/init.d/
	@install -d -m755 dist/data/etc/apt/sources.list.d/
	@install -m644 debian/neubot.list dist/data/etc/apt/sources.list.d/
	@cd dist/data && tar czf ../data.tar.gz ./*
	@install -d -m755 dist/control
	@find dist/data -type f -exec md5sum {} \; > dist/control/md5sums
	@sed -i 's!dist\/data\/!!g' dist/control/md5sums
	@chmod 644 dist/control/md5sums
	@install -m644 debian/control dist/control/
	@for file in postinst prerm; do					\
	    install debian/$$file dist/control/;			\
	done
	@SIZE=`du -s dist/data/|cut -f1` && sed -i "s/@SIZE@/$$SIZE/"	\
	                                        dist/control/control
	@cd dist/control && tar czf ../control.tar.gz ./*
	@echo '2.0' > dist/debian-binary
	@ar r $(DEB) dist/debian-binary dist/*.tar.gz
	@rm -rf dist/control* dist/data* dist/debian-binary

clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm -f {} \;
	@rm -rf -- dist/
help:
	@echo -n "Targets:"
	@for TARGET in `grep ^PHONIES Makefile|sed 's/^.*+= //'`; do	\
	     if echo $$TARGET|grep -qv ^_; then				\
	         echo -n " $$TARGET";					\
	     fi;							\
	 done
	@echo ""
install:
	@echo "[INSTALL]"
	@make -f Makefile _install
	@python2.6 -m compileall -q $(DESTDIR)$(PREFIX)/share/neubot
	@find $(DESTDIR)$(PREFIX)/share/neubot -type f -name \*.pyc	\
	                    -exec chmod go+r {} \;
lint:
	@echo "[LINT]"
	@find . -type f -name \*.py -exec pychecker {} \;

#
# XXX Probably this piece of code should be moved into some
# admin/release.sh script because it's unlikely that it works
# on machines different by mine, and so it should not be that
# easy to invoke it.
#

release:
	@echo "[RELEASE]"
	@make clean
#	@#Create Win32 installer using Wine
#	@install -d dist
#	@cp $$HOME/.wine/drive_c/windows/system32/python27.dll dist/
#	@wine cmd /c Build.bat
#	@install -d dist/neubot-$(VERSION)
#	@cd dist && mv *.zip *.exe *.dll neubot-$(VERSION)/
#	@cd dist && zip -r neubot-win32-$(VERSION).zip neubot-$(VERSION)/
#	@cd dist && rm -rf neubot-$(VERSION)/
#	@mv Neubot_Setup_* dist/
	@make _deb
	@cd dist && dpkg-scanpackages . > Packages
	@cd dist && gzip --stdout -9 Packages > Packages.gz
	@cp debian/Release dist/
	@for FILE in Packages Packages.gz; do				\
	     SHASUM=`sha256sum dist/$$FILE | awk '{print $$1}'` &&	\
	     KBYTES=`wc -c dist/$$FILE | awk '{print $$1}'` &&		\
	     echo " $$SHASUM $$KBYTES $$FILE" >> dist/Release;		\
	 done
	@gpg -abs -o dist/Release.gpg dist/Release
	@git archive --format=tar --prefix=neubot-$(VERSION)/ HEAD	\
            | gzip -9 > dist/neubot-$(VERSION).tar.gz
	@git archive --format=zip --prefix=neubot-$(VERSION)/ HEAD	\
            > dist/neubot-$(VERSION).zip
	@cd dist && sha256sum neubot-* >> SHA256.inc
