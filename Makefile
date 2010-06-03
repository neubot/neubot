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

ARCHIVE = neubot
DEB     = neubot-0.0.4-2.deb
DESTDIR =
PREFIX  = /usr/local

.PHONY: _all _archives _docs _install _release clean deb help install

_all: help

_archives:
	@echo "[ARCHIVES] $(ARCHIVE).tar.gz $(ARCHIVE).zip"
	@git archive --format=tar --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).tar
	@gzip -9 $(ARCHIVE).tar
	@git archive --format=zip --prefix=$(ARCHIVE)/ HEAD > $(ARCHIVE).zip
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
	@install -d $(DESTDIR)$(PREFIX)/bin
	@sed 's!/usr/local!$(PREFIX)!' bin/unix/neubot > binunixneubot
	@install binunixneubot $(DESTDIR)$(PREFIX)/bin/neubot
	@rm binunixneubot
_release:
	@echo "[RELEASE]"
	@V=`git tag|tail -n1` 					&&	\
	ARCHIVENAME=neubot-$$V					&&	\
	git archive --format=tar --prefix=$$ARCHIVENAME/		\
	     HEAD | gzip -9 > $$ARCHIVENAME.tar.gz		&&	\
	git archive --format=zip --prefix=$$ARCHIVENAME/		\
	     HEAD > $$ARCHIVENAME.zip				&&	\
	sha256sum $$ARCHIVENAME.* > SHA256
clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm -f {} \;
	@rm -rf -- build/ dist/ $(ARCHIVE).tar.* $(ARCHIVE).zip $(DEB)
deb:
	@echo "[DEB] $(DEB)"
	@rm -rf dist/
	@make -f Makefile _install DESTDIR=dist/data PREFIX=/usr
	@install -d -m755 dist/data/etc/init.d
	@install -m755 debian/neubot dist/data/etc/init.d/
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
