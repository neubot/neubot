# XXX Usage: make -f neubot.app/Makefile
# TODO Make sure root is the owner and stuff

.PHONY: all
all:
	make -f Makefile archive
	cp dist/neubot-0.3.1.tar.gz neubot.app/Contents/Resources/
	cd neubot.app/Contents/Resources && \
	 tar xzf neubot-0.3.1.tar.gz && \
	 rm -rf neubot-0.3.1.tar.gz && \
	 ln -s neubot-0.3.1 neubot && \
	 rm -rf pax_global_header
