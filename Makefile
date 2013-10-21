# Makefile

#
# Copyright (c)
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     2010-2013 Simone Basso <bassosimone@gmail.com>
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

#
# The scripts/release script will automatically update the
# version number each time we tag with a new release.
#
VERSION	= 0.4.17.0

#
# The list of .PHONY targets.  This is also used to build the
# help message--and note that the targets named with a leading
# underscore are private.
#
# Here we list targets in file order because this makes it easier
# to maintain this list.
#
PHONIES += help
PHONIES += regress
PHONIES += clean
PHONIES += archive
PHONIES += _install
PHONIES += uninstall
PHONIES += _install_umask_ok
PHONIES += install
PHONIES += release

.PHONY: $(PHONIES)

help:
	@printf "Targets:"
	@for TARGET in `grep ^PHONIES Makefile|sed 's/^.*+= //'`; do	\
	     if echo $$TARGET|grep -qv ^_; then				\
	         printf " $$TARGET";					\
	     fi;							\
	 done
	@printf '\n'

regress:
	rm -rf -- regress/success regress/failure
	for FILE in $$(find regress -type f -perm +0111); do		\
	    echo "* Running regression test: $$FILE";			\
	    ./$$FILE;							\
	    if [ $$? -ne 0 ]; then					\
	        echo $$FILE >> regress/failure;				\
	    else							\
	        echo $$FILE >> regress/success;				\
	    fi;								\
	    echo "";							\
	    echo "";							\
	done
	if [ -f regress/failure ]; then					\
	    echo "*** At least one regression test has failed";		\
	    echo "*** Check regress/failure for more info";		\
	    exit 1;							\
	fi

clean:
	./scripts/cleanup

#                 _     _
#   __ _ _ __ ___| |__ (_)_   _____
#  / _` | '__/ __| '_ \| \ \ / / _ \
# | (_| | | | (__| | | | |\ V /  __/
#  \__,_|_|  \___|_| |_|_| \_/ \___|
#
# Create source archives
#

STEM = neubot-$(VERSION)
ARCHIVE = git archive --prefix=$(STEM)/

archive:
	install -d dist/
	for FMT in tar zip; do \
	 $(ARCHIVE) --format=$$FMT HEAD > dist/$(STEM).$$FMT; \
	done
	gzip -9 dist/$(STEM).tar

#  _           _        _ _
# (_)_ __  ___| |_ __ _| | |
# | | '_ \/ __| __/ _` | | |
# | | | | \__ \ || (_| | | |
# |_|_| |_|___/\__\__,_|_|_|
#
# Install neubot in the filesystem
#

#
# We need to override INSTALL with 'install -o 0 -g 0' when
# we install from sources because in this case we want to
# enforce root's ownership.
#
INSTALL	= install

#
# Some systems don't install a symlink for python and
# might want to override
#
PYTHON = python

#
# These are some of the variables accepted by the GNU
# build system, in order to follow the rule of the least
# surprise [1].
#
# We install neubot in $(DATADIR)/neubot following sect.
# 3.1.1 of Debian Python Policy which covers the shipping
# of private modules [2].
#
# [1] http://bit.ly/aLduJz (gnu.org)
# [2] http://bit.ly/ayYyAR (debian.org)
#
DESTDIR ?=
PREFIX ?= /usr/local

BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
LOCALSTATEDIR ?= $(PREFIX)/var
MANDIR ?= $(PREFIX)/share/man
SYSCONFDIR ?= $(PREFIX)/etc

_install:
	find . -type f -name .DS_Store -exec rm {} \;  # H A T E
	$(INSTALL) -d $(DESTDIR)$(BINDIR)
	$(INSTALL) UNIX/bin/neubot $(DESTDIR)$(BINDIR)/neubot
	$(INSTALL) -d $(DESTDIR)$(DATADIR)
	for DIR in `cd UNIX/share && find . -mindepth 1 -type d`; do \
	    $(INSTALL) -d $(DESTDIR)$(DATADIR)/$$DIR; \
	    test $$? || exit 1; \
	done
	for FILE in `cd UNIX/share && find . -type f`; do \
	    $(INSTALL) -m644 UNIX/share/$$FILE $(DESTDIR)$(DATADIR)/$$FILE; \
	    test $$? || exit 1; \
	done
	$(INSTALL) -d $(DESTDIR)$(MANDIR)
	for DIR in `cd UNIX/man && find . -mindepth 1 -type d`; do \
	    $(INSTALL) -d $(DESTDIR)$(MANDIR)/$$DIR; \
	    test $$? || exit 1; \
	done
	find UNIX/man -type f -name \*.gz | xargs rm -f
	for FILE in `cd UNIX/man && find . -type f`; do \
	    gzip -9c UNIX/man/$$FILE > UNIX/man/$$FILE.gz; \
	    test $$? || exit 1; \
	    $(INSTALL) -m644 UNIX/man/$$FILE.gz $(DESTDIR)$(MANDIR)/$$FILE.gz; \
	    test $$? || exit 1; \
	done
	$(INSTALL) -d $(DESTDIR)$(SYSCONFDIR)
	for DIR in `cd UNIX/etc && find . -mindepth 1 -type d`; do \
	    $(INSTALL) -d $(DESTDIR)$(SYSCONFDIR)/$$DIR; \
	    test $$? || exit 1; \
	done
	for FILE in `cd UNIX/etc && find . -type f`; do \
	    $(INSTALL) -m644 UNIX/etc/$$FILE $(DESTDIR)$(SYSCONFDIR)/$$FILE; \
	    test $$? || exit 1; \
	done
	$(INSTALL) -d $(DESTDIR)$(DATADIR)/neubot/neubot
	for DIR in `find neubot -type d`; do \
	    $(INSTALL) -d $(DESTDIR)$(DATADIR)/neubot/$$DIR; \
	    test $$? || exit 1; \
	done
	for FILE in `find neubot -type f`; do \
	    $(INSTALL) -m644 $$FILE $(DESTDIR)$(DATADIR)/neubot/$$FILE; \
	    test $$? || exit 1; \
	done
	for DIR in mod_*; do \
	    $(INSTALL) -d $(DESTDIR)$(DATADIR)/neubot/$$DIR; \
	    test $$? || exit 1; \
	    for FILE in `find $$DIR -type f`; do \
	        $(INSTALL) -m644 $$FILE $(DESTDIR)$(DATADIR)/neubot/$$FILE; \
	        test $$? || exit 1; \
	    done; \
	done
	$(INSTALL) -d $(DESTDIR)$(LOCALSTATEDIR)/neubot
	for PATTERN in 's|@BINDIR@|$(BINDIR)|g' 's|@DATADIR@|$(DATADIR)|g' \
	        's|@LOCALSTATEDIR@|$(LOCALSTATEDIR)|g' \
	        's|@SYSCONFDIR@|$(SYSCONFDIR)|g'; do \
	    ./scripts/sed_inplace $$PATTERN \
	        $(DESTDIR)$(BINDIR)/neubot \
	        $(DESTDIR)$(DATADIR)/applications/neubot.desktop \
	        $(DESTDIR)$(DATADIR)/neubot/neubot/notifier/unix.py \
	        $(DESTDIR)$(DATADIR)/neubot/neubot/utils_hier.py \
	        $(DESTDIR)$(DATADIR)/neubot/neubot/system_posix.py \
	        $(DESTDIR)$(DATADIR)/neubot/neubot/viewer_webkit_gtk.py \
	        $(DESTDIR)$(SYSCONFDIR)/xdg/autostart/neubot.desktop; \
	    test $$? || exit 1; \
	done

uninstall:
	make -f Makefile _install DESTDIR=dist/r
	$(PYTHON) -m compileall dist/r/$(DATADIR)/neubot
	rm -rf dist/f dist/d dist/UNINSTALL
	find dist/r/ -depth -type f -print -exec rm {} \; >> dist/f
	find dist/r/ -depth -mindepth 1 -type d -print >> dist/d
	sed 's|dist/r|rm -f $(DESTDIR)|g' dist/f >> dist/UNINSTALL
	sed 's|dist/r|rmdir $(DESTDIR)|g' dist/d >> dist/UNINSTALL
	sh dist/UNINSTALL

#
# Install should be invoked as root and will actually
# copy neubot on the filesystem, making sure that root
# owns the installed files.
#
# Moreover it will compile the modules into .pyc files
# using the compileall module.
#
_install_umask_ok:
	make -f Makefile _install INSTALL='install -o 0 -g 0'
	$(PYTHON) -m compileall $(DESTDIR)$(DATADIR)/neubot

install:
	( \
	 umask 022 && \
	 make -f Makefile _install_umask_ok \
	)

#           _
#  _ __ ___| | ___  __ _ ___  ___
# | '__/ _ \ |/ _ \/ _` / __|/ _ \
# | | |  __/ |  __/ (_| \__ \  __/
# |_|  \___|_|\___|\__,_|___/\___|
#
# Bless a new neubot release (sources).
#
release:
	if ! [ "$(VERSION)" = "$$(git describe --tags)" ]; then		\
	    echo "error: not at a release point" 2>&1;			\
	    echo "Makefile version is: $(VERSION)" 2>&1;		\
	    echo "git describe is: $$(git describe --tags)" 2>&1;	\
	    exit 1;							\
	fi
	make clean
	make archive
	./scripts/sign_all dist/*
	cd dist && chmod 644 *
