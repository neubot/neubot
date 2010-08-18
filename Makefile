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

VERSION	= 0.1.9

DEB     = dist/neubot-$(VERSION)-1_all.deb
DESTDIR =
PREFIX  = /usr/local
TAG     = `git tag|grep -v ^_|tail -n1`

PHONIES += _all
PHONIES += _archive
PHONIES += _docs
PHONIES += _install
PHONIES += archive
PHONIES += clean
PHONIES += deb
PHONIES += help
PHONIES += install
PHONIES += lint
PHONIES += patches
PHONIES += release

.PHONY: $(PHONIES)

_all: help
_archive:
	@install -d dist/neubot-$$ATAG
	@git archive --format=tar --prefix=neubot-$$ATAG/ $$ATAG        \
            | gzip -9 > dist/neubot-$$ATAG/neubot-$$ATAG.tar.gz
	@git archive --format=zip --prefix=neubot-$$ATAG/ $$ATAG        \
            > dist/neubot-$$ATAG/neubot-$$ATAG.zip
_docs:
	@echo "[DOCS]"
	@cd doc && for DIA in *.dia; do					\
	    dia --filter=png $$DIA;					\
	done
_install:
	@for D in `find neubot/ -type d`; do				\
	    install -m755 -d $(DESTDIR)$(PREFIX)/share/$$D || exit 1;	\
	done
	@for F in `find neubot/ -type f -name \*.py`; do		\
	    install -m644 $$F $(DESTDIR)$(PREFIX)/share/$$F || exit 1;	\
	done
	@install -d $(DESTDIR)/etc/neubot
	@install -d $(DESTDIR)/var/neubot
	@install -d $(DESTDIR)$(PREFIX)/bin
	@sed 's!/usr/local!$(PREFIX)!' bin/unix/neubot > binunixneubot
	@install binunixneubot $(DESTDIR)$(PREFIX)/bin/neubot
	@rm binunixneubot
	@# XXX Using BSD convention for installing manual page
	@install -d $(DESTDIR)$(PREFIX)/man/man1
	@pod2man --center="Neubot manual" --release="Neubot $(VERSION)" \
         doc/neubot.1.pod > $(DESTDIR)/$(PREFIX)/man/man1/neubot.1
	@install -d $(DESTDIR)$(PREFIX)/man/man3
	@pod2man -c"Neubot manual" -r"Neubot $(VERSION)" -s3 -n"NEUBOT.NET" \
         doc/neubot.net.3.pod > $(DESTDIR)/$(PREFIX)/man/man3/neubot.net.3
archive:
	@echo "[ARCHIVE] dist/neubot-HEAD/"
	@rm -rf dist/
	@make _archive ATAG=HEAD
clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm -f {} \;
	@rm -rf -- dist/
deb:
	@echo "[DEB] $(DEB)"
	@rm -rf dist/
	@make -f Makefile _install DESTDIR=dist/data PREFIX=/usr
	@# XXX Work-around using BSD convention for installing manual page
	@mv dist/data/usr/man dist/data/usr/share/
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
	@cd dist/control && tar czf ../control.tar.gz ./*
	@echo '2.0' > dist/debian-binary
	@ar r $(DEB) dist/debian-binary dist/*.tar.gz
help:
	@echo "[HELP] Available targets"
	@cat Makefile|grep '^[a-zA-Z0-9]*:'|sed 's/:.*$$//'|sed 's/^/  /'
install:
	@echo "[INSTALL]"
	@make -f Makefile _install
	@python2.6 -m compileall -q $(DESTDIR)$(PREFIX)/share/neubot
lint:
	@echo "[LINT]"
	@find . -type f -name \*.py -exec pychecker --limit 256 {} \;
patches:
	@echo "[PATCHES] dist/patches.tar.gz"
	@rm -rf dist/
	@git format-patch -o dist/ $(TAG) 1>/dev/null
	@cd dist && tar czf patches.tar.gz *.patch
release:
	@echo "[RELEASE] dist/neubot-$(TAG)/"
	@rm -rf dist/
	@make _archive ATAG=$(TAG)
