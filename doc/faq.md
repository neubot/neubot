The Frequently Asked Questions (FAQ) of Neubot <http://neubot.org/>.

- - -

Index
=====

- [1. General questions](#1-general-questions)
    - [1.1. What is Neubot?](#11-what-is-neubot)
    - [1.2. What is Measurement Lab?](#12-what-is-measurement-lab)
    - [1.3. What is network neutrality?](#13-what-is-network-neutrality)
    - [1.4. Why "the network neutrality bot"?](#14-why-the-network-neutrality-bot)
    - [1.5. Why is it crucial to monitor network neutrality?](#15-why-is-it-crucial-to-monitor-network-neutrality)
    - [1.6. Why might I want to install Neubot?](#16-why-might-i-want-to-install-neubot)
    - [1.7. What tests are implemented by the latest version?](#17-what-tests-are-implemented-by-the-latest-version)
    - [1.8. What is the roadmap to Neubot 1.0.0.0?](#18-what-is-the-roadmap-to-neubot-1000)
    - [1.9. When is the next release of Neubot?](#19-when-is-the-next-release-of-neubot)
    - [1.10. What is your versioning policy?](#110-what-is-your-versioning-policy)
    - [1.11. Which is the stable version of Neubot?](#111-which-is-the-stable-version-of-neubot)
    - [1.12. How long should I keep Neubot installed?](#112-how-long-should-i-keep-neubot-installed)
    - [1.13. How much do you test Neubot before release?](#113-how-much-do-you-test-neubot-before-release)
    - [1.14. Who develops Neubot?](#114-who-develops-neubot)
    - [1.15. Under what license is Neubot available?](#115-under-what-license-is-neubot-available)
    - [1.16. How much does Neubot cost?](#116-how-much-does-neubot-cost)
- [2. Installing Neubot](#2-installing-neubot)
    - [2.1. On what systems does neubot run?](#21-on-what-systems-does-neubot-run)
    - [2.2. How do I install neubot?](#22-how-do-i-install-neubot)
    - [2.3. How do I install Neubot on FreeBSD?](#23-how-do-i-install-neubot-on-freebsd)
    - [2.4. How do I build Neubot from sources on Windows?](#24-how-do-i-build-neubot-from-sources-on-windows)
- [3. Using Neubot](#3-using-neubot)
    - [3.1. Neubot installed. What should I do now?](#31-neubot-installed-what-should-i-do-now)
    - [3.2. How many resources does Neubot need?](#32-how-many-resources-does-neubot-need)
    - [3.3. How do I report bugs, ask questions, or make suggestions?](#33-how-do-i-report-bugs-ask-questions-or-make-suggestions)
    - [3.4. What are the issues if I use mobile broadband, 3G modem, Internet key?](#34-what-are-the-issues-if-i-use-mobile-broadband-3g-modem-internet-key)
    - [3.5. Do I need to tweak the configuration of my router?](#35-do-i-need-to-tweak-the-configuration-of-my-router)
    - [3.6. How do I read Neubot logs?](#36-how-do-i-read-neubot-logs)
    - [3.7. Do I have to periodically rotate log files?](#37-do-i-have-to-periodically-rotate-log-files)
    - [3.8. Do I have to periodically rotate the database?](#38-do-i-have-to-periodically-rotate-the-database)
- [4. Technical questions](#4-technical-questions)
    - [4.1. How does Neubot work?](#41-how-does-neubot-work)
    - [4.2. What does *speedtest* test measure?](#42-what-does-speedtest-test-measure)
    - [4.3. How does Neubot change my Windows registry?](#43-how-does-neubot-change-my-windows-registry)
    - [4.4. What is the path of Neubot database?](#44-what-is-the-path-of-neubot-database)
    - [4.5. How can I dump the content of the database?](#45-how-can-i-dump-the-content-of-the-database)
    - [4.6. What does *bittorrent* test measure?](#46-what-does-bittorrent-test-measure)
    - [4.7. What does measuring goodput mean?](#47-what-does-measuring-goodput-mean)
    - [4.8. Is it possible to compare speedtest and bittorrent results?](#48-is-it-possible-to-compare-speedtest-and-bittorrent-results)
    - [4.9. What does the *raw* test measure?](#49-what-does-the-raw-test-measure)
    - [4.10. What does the *dashtest* test measure?](#410-what-does-the-dashtest-test-measure)
- [5. Privacy questions](#5-privacy-questions)
    - [5.1. What personal data does Neubot collect?](#51-what-personal-data-does-neubot-collect)
    - [5.2. Will you publish my IP address?](#52-will-you-publish-my-ip-address)
- [6. Data questions](#6-data-questions)
    - [6.1. Where is data published?](#61-where-is-data-published)
    - [6.1. Is there any license attached to data?](#61-is-there-any-license-attached-to-data)
    - [6.2. What is the data format?](#62-what-is-the-data-format)
- [7. Web interface](#7-web-interface)
    - [7.1. What is the web interface?](#71-what-is-the-web-interface)
    - [7.2. How do I open the web interface?](#72-how-do-i-open-the-web-interface)
    - [7.3. What pages does the web interface contain?](#73-what-pages-does-the-web-interface-contain)
    - [7.4. How do I change the web interface language?](#74-how-do-i-change-the-web-interface-language)
- [8. Following development](#8-following-development)
    - [8.1. How do I clone Neubot repository?](#81-how-do-i-clone-neubot-repository)
    - [8.2. How do I prepare a diff for Neubot?](#82-how-do-i-prepare-a-diff-for-neubot)
- [9. Localhost web API](#9-localhost-web-api)

- - -


1. General questions
====================


1.1. What is Neubot?
--------------------

Neubot is a research project on network neutrality by the [Nexa Center for
Internet & Society, Politecnico di Torino (DAUIN)][nexa].  The
project is based on a lightweight [free software][license] computer program
that interested users can download and install on their computers.  The
program runs in the background and periodically performs transmission tests
with servers hosted by the distributed [Measurement Lab][mlab] platform,
and, in the future, with other instances of Neubot.  Transmission tests
measure network performance with various application-level protocols.  Test
results are saved both locally and on the test servers.  Data is collected
for research purposes and [published on the web][neubot-data] under Creative
Commons Zero allowing anyone to re-use it freely for the same purpose.

[license]: https://github.com/neubot/neubot/blob/master/COPYING
[mlab]: http://www.measurementlab.net
[nexa]: http://nexa.polito.it/
[neubot-data]: http://www.neubot.org/data


1.2. What is Measurement Lab?
-----------------------------

[Measurement Lab][mlab] (M-Lab) is a distributed server platform that provides
connectivity and servers around the world for projects that aim to
measure the quality and/or neutrality of broadband Internet connections
by probing the network with active tests.  It also provides additional
services; e.g., server discovery APIs, automatic data collection and
publishing, support for gathering network-stack level statistics.

From version 0.4.6 onward Neubot is hosted at Measurement Lab.  Since
version 0.4.8, all tests are carried out by Measurement Lab servers.


1.3. What is network neutrality?
--------------------------------

Network neutrality is the principle that the Internet should be neutral
with respect to kinds of applications, senders and destinations. In
other words, a network is neutral when [routers][router] forward packets
using a *first come, first served* strategy.  Instead, it is not neutral
when certain packets receive a preferential treatment.

The ancient Internet was strictly neutral, because it was designed
to minimize the interaction between applications and the network
(see [RFC3439][rfc3439]). This design choice allowed very fast packet
switching and enabled strong openness towards unforeseen uses of the
Internet Protocol. The result was an extraordinary outburst of innovation
and a level-playing field for citizens, associations, and companies
worldwide.

The modern Internet is not always neutral because some technologies
allow for fine-grained discrimination of traffic. When they enter into
the network of an Internet Service Provider, packets are *classified*
(i.e., assigned to a class like *web*, *video*, or *file-sharing*).
The most commonly exploited characteristics in traffic classification
are the content of packets headers and the payload. But a packet can
also inherit the class from the flow it belongs to if it is
already classified. Once a packet has been classified at the border
of the network it is treated accordingly by network routers.

The policy debate regarding network neutrality is on whether it is
preferable to continue with *laissez-faire* or to safeguard it.
This topic can be tackled from a variety of disciplines,
including competition law and innovation processes. To know more about
network neutrality, the related debate and the various positions go
to [Wikipedia's article][wikinn].

[router]: http://en.wikipedia.org/wiki/Router_(computing)
[rfc3439]: http://tools.ietf.org/html/rfc3439#section-2.1
[wikinn]: http://en.wikipedia.org/wiki/Network_neutrality


1.4. Why "the network neutrality bot"?
--------------------------------------

The program is called *network neutrality bot* because it is a
[software application that runs automated tasks over the Internet][bot]
to collect data meaningful to study network neutrality.

[bot]: http://en.wikipedia.org/wiki/Internet_bot


1.5. Why is it crucial to monitor network neutrality?
-----------------------------------------------------

Monitoring network neutrality is crucial because it enables a deeper
understanding of Internet Service Providers (ISPs) behavior. This
is paramount *ex-ante*; i.e., at a time when there is a broad discussion
regarding changes in network neutrality policies. The availability of
quantitative datasets collected by independent researchers should
rebalance, at least in part, the deep information asymmetry between
ISPs and other interested stakeholders (including regulators and
citizens). In turn, providing a more reliable basis for discussing
network neutrality policies.

Monitoring network neutrality is crucial in an *ex-post* scenario
as well. Indeed, it enables independent researchers to verify operators
behavior in light of regulatory decisions on the matter.


1.6. Why might I want to install Neubot?
----------------------------------------

You might want to install Neubot if you care about network neutrality,
wish to support this research project and are willing to donate it a
fraction of your network capacity to run its tests. You will contribute
to build a quantitative dataset of data meaningful to study the
network neutrality. The availability of which will allow for a more
democratic decisional process about the Internet, one of the key
infrastructures of our societies.

Another reason to install it is that it provides you with a brief
picture of how your Internet connection works at different hours
and using different protocols. You can compare Neubot results with
other tests' results to achieve a more in-depth understanding of
the behavior of your home network and ISP.

If you are interested, don't hesitate to install it. The success of
this project depends heavily on how many people install it.


1.7. What tests are implemented by the latest version?
------------------------------------------------------

The tests implemented by the last version of Neubot are briefly
described in the [IMPLEMENTED TESTS][man-tests] section of Neubot's
manual page.

We also provide more details on how the tests works in the [Technical
questions](#4-technical-questions) section of this FAQ.

[man-tests]: https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#implemented-tests


1.8. What is the roadmap to Neubot 1.0.0.0?
-------------------------------------------

Neubot 1.0.0.0 will be able to perform client-server and peer-to-peer
transmission tests using multiple application level protocols.
The [roadmap][roadmap] and [TODO][todo] list are updated and maintained
on [github's wiki][github-wiki].

[roadmap]: https://github.com/neubot/neubot/wiki/roadmap
[todo]: https://github.com/neubot/neubot/wiki/todo
[github-wiki]: https://github.com/neubot/neubot/wiki


1.9. When is the next release of Neubot?
----------------------------------------

We frequently update the [github repository][github-repo], and we
try to deploy a new release every quarter.

[github-repo]: https://github.com/neubot/neubot


1.10. What is your versioning policy?
------------------------------------

Neubot version number follows the *major*, *minor*, *patch*, and
*revision* scheme; e.g., Neubot 0.4.15.3 has major version number
0, minor version number 4, patch version number 15 and revision
version number 3.

The major version number will be zero until Neubot implements all
the features planned for 1.0.0.0.

We make a minor release (e.g. 0.4.0.0) when we believe that this
release incorporates significant changes since the previous minor
release of Neubot.

Otherwise, we make a patch release (e.g. 0.4.15.0).

Whatever release we make (be it 1.0.0.0, 0.4.0.0, or 0.4.15.0), the
code may need additional tweaks before the release can be made
generally available. When this is the case, we bump the patch version
number; e.g., 1.0.0.1, 0.4.0.1, or 0.4.15.1.


1.11. Which is the stable version of Neubot?
--------------------------------------------

We don't release unstable code and we don't make *unstable* or
*testing* releases. If you want to run unstable code, you should
track the master branch of the git repository.  Otherwise, we suggest
you to always install the latest generally available version of
Neubot.


1.12. How long should I keep Neubot installed?
----------------------------------------------

As long as possible; Neubot is not a limited-scope project but rather an
ongoing effort.


1.13. How much do you test Neubot before release?
-------------------------------------------------

Experimental features included in new releases are not enabled by
default until they become stable.

Typically, major and minor releases are tested for at least a
couple of weeks.


1.14. Who develops Neubot?
--------------------------

Neubot project lead is [Simone Basso][sbasso], a research fellow of the [Nexa
Center for Internet & Society][nexa]. He develops Neubot in collaboration with
and under the supervision of prof. [Antonio Servetti][aservetti], prof.
[Federico Morando][fmorando], and prof. [Juan Carlos De Martin][jcdemartin],
of Politecnico di Torino.

We list people who contributed patches in the [AUTHORS][authors] file.

[sbasso]: http://www.neubot.org/people#basso
[aservetti]: http://www.neubot.org/people#servetti
[fmorando]: http://www.neubot.org/people#morando
[jcdemartin]: http://www.neubot.org/people#de_martin
[authors]: https://github.com/neubot/neubot/blob/master/AUTHORS


1.15. Under what license is Neubot available?
---------------------------------------------

As a collection, Neubot is copyrighted by the [Nexa Center for Internet &
Society, Politecnico di Torino (DAUIN)][nexa], and it is released under the
[GNU General Public License version 3][license].

Invididual files are often dual copyrighted by their author and by the
Nexa Center. Also, there are some files that are under other open source
licenses (typically because they are derivative works).


1.16. How much does Neubot cost?
--------------------------------

Zero. Neubot is available for free.

- - -


2. Installing Neubot
====================

2.1. On what systems does neubot run?
-------------------------------------

Neubot is written in [Python][python] and therefore should run on all systems
supported by Python.

The Neubot team provides packages for [Ubuntu][ubuntu] >= 10.04 and
[Debian][debian], [MacOSX][macosx] >= 10.6, [Windows][windows] >= XP SP3.

Neubot is included in the [FreeBSD Ports Collection][freebsd-ports].

[python]: http://www.python.org/
[ubuntu]: http://www.ubuntu.com/
[debian]: http://www.debian.org/
[macosx]: http://www.apple.com/macosx/
[windows]: http://windows.microsoft.com/
[freebsd-ports]: http://www.freshports.org/net/neubot


2.2. How do I install neubot?
-----------------------------

The Neubot team provides packages for [MacOSX][macosx], [Windows][windows],
[Debian][debian] and distributions based on Debian (such as [Ubuntu][ubuntu]).
Neubot is part of the [FreeBSD port collection][freebsd-ports].  If there
are no binary packages available for your system, you can still install it
from sources.

Subsequent FAQ entries will deal with all these options.


2.3. How do I install Neubot on FreeBSD?
----------------------------------------

Neubot is part of [FreeBSD ports collection][freebsd-ports].  So it can be
installed easily, either by using `pkg_add` or by compiling the package
for the ports tree.  Of course, when in doubt, please refer to [FreeBSD
documentation][freebsd-docs] and [FreeBSD manpages][freebsd-man].  In
particular, the authoritative Neubot port page is:

    http://www.freshports.org/net/neubot/

For your convenience, here we mirror the two base commands to add Neubot
to your FreeBSD system.  To add the precompiled package to your system,
you should run the following command as root:

    pkg_add -r neubot

To compile and install the port, again as root, you need to type the
following command:

    cd /usr/ports/net/neubot/ && make install clean

Please, do not ask Neubot developers questions related to the FreeBSD
port because they may not be able to help.  We suggest instead to direct
questions to [FreeBSD ports mailing list][freebsd-ml].  Bugs should be
reported using the [send-pr] interface.

[freebsd-docs]: http://www.freebsd.org/docs.html
[freebsd-man]: http://www.freebsd.org/cgi/man.cgi
[freebsd-ml]: http://lists.freebsd.org/mailman/listinfo/freebsd-ports
[send-pr]: http://www.freebsd.org/send-pr.html


2.4. How do I build Neubot from sources on Windows?
---------------------------------------------------

This section describes the procedure to create your own Neubot Windows
binary distribution and installer.

### Prerequisites

Download [Python 2.7.4][python.msi], verify its [digital signature]
[python.msi.asc], and install it accepting default settings.

[python.msi]: http://www.python.org/ftp/python/2.7.4/python-2.7.4.msi
[python.msi.asc]: http://www.python.org/ftp/python/2.7.4/python-2.7.4.msi.asc

Download [PyWin32 build 218][pywin32] (for Win32 and Python 2.7) from
sourceforge, and install it accepting default settings.

[pywin32]: http://sourceforge.net/projects/pywin32/files/pywin32/Build%20218/pywin32-218.win32-py2.7.exe/download

Download [py2exe 0.6.9][py2exe] (for Win32 and Python 2.7) from sourceforge,
and install it accepting default settings.

[py2exe]: http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/py2exe-0.6.9.win32-py2.7.exe/download

Download [NSIS 2.46][nsis] from sourceforge, and install it accepting
default settings.

[nsis]: http://sourceforge.net/projects/nsis/files/NSIS%202/2.46/nsis-2.46-setup.exe/download

Download the latest version of [msysgit][msysgit] from code.google.com,
and install it accepting default settings.

[msysgit]: http://code.google.com/p/msysgit/downloads/list

From Git Bash, clone Neubot Win32 helper repository by using this command:

    git clone git://github.com/neubot/neubot_win32.git

Also, apply to py2exe distribution the [patch to make Stderr a blackbole]
[stderr-patch] (which also includes, at the beginning, instructions on how
to apply it).

[stderr-patch]: https://github.com/neubot/neubot_win32/blob/master/Win32/py2exe_stderr_blackhole.patch

### Create the installer

These are the instructions to build Neubot 0.4.15.6 for Windows.

From Git Bash, enter into Neubot Win32 helper repository (`neubot_win32`),
pull changes from upstream, and checkout the 0.4.15.6 tag:

    cd neubot_win32
    git checkout master
    git fetch origin
    git checkout 0.4.15.6

Run the configure script, which downloads the sources, verify their
integrity, and eventually applies patches:

    ./configure

Enter into Win32 subdirectory and run setup.py:

    cd Win32
    /c/Python27/python.exe setup.py

Return to the toplevel directory:

    cd ..

You will find the compressed binary distribution here:

    neubot-0.4.15.6/wdist/win32/0.004015006.tar.gz

You will find the installer here:

    neubot-0.4.15.6/wdist/neubot-0.4.15.6-setup.exe

The uncompressed binary distribution (i.e. the files that the installer
will install), instead, is here:

    neubot-0.4.15.6/wdist/tmp/0.004015006/

- - -


3. Using Neubot
===============


3.1. Neubot installed. What should I do now?
--------------------------------------------

You may want to compare Neubot results with the ones of other network
measurement tools. If so, we would appreciate it if you would share
your results with us, especially when Neubot results are not consistent
with the ones of other tools.


3.2. How many resources does Neubot need?
-----------------------------------------

Neubot has a minimal impact on system and network load. It spends most
of its time asleep or waiting for its turn to perform a test. During a
test Neubot consumes a lot of system and network resources but the
program tries to guarantee that the test does not take more than 10-15
seconds.

Here are a couple of screenshots captured from a netbook running Ubuntu
9.10 and attached to Politecnico di Torino network. In the first
screenshot you can see the resource usage during an on-demand test
invoked from the command line. The *init* phase of the test is the one
where Neubot generates the random data to send during the upload phase.

![Resources usage #1][resources1]
[resources1]: http://www.neubot.org/neubotfiles/resources1.png

The resource usage is much lower if you run the test at home, given
that Politecnico network is 5x/10x faster than most ADSLs.

The second screenshot shows the amount of consumed resources (in
particular memory) when Neubot is idle.

![Resources usage #2][resources2]
[resources2]: http://www.neubot.org/neubotfiles/resources2.png


3.3. How do I report bugs, ask questions, or make suggestions?
--------------------------------------------------------------

To report bugs and ask questions, please use our mailing list. The
official languages for the mailing list are English and Italian.

Note that you must subscribe to the mailing list first, otherwise
your message will not be accepted. To subscribe, go to:

      http://www.neubot.org/cgi-bin/mailman/listinfo/neubot

The mailing list subscription page uses an auto-signed SSL certificate
and your browser is likely to complain.  Don't be scared: it
is the page to register to the Neubot mailing list, not your bank account.

We advise you to search the public archive before posting a message,
because others might have already asked the same question or reported
the same bug. All posts to the mailing list are archived here:

      http://www.neubot.org/pipermail/neubot/


3.4. What are the issues if I use mobile broadband, 3G modem, Internet key?
---------------------------------------------------------------------------

One possible issue with mobile broadband is the following: if you use
Windows, you installed Neubot, you are not connected, and Neubot
starts a test, it's possible that Windows asks you to connect. If this
behavior annoys you, you can temporarily disable Neubot by using its
[web interface](#7-web-interface).

In future releases we plan to check whether there is an Internet
connection, and start a test only if it's available.


3.5. Do I need to tweak the configuration of my router?
-------------------------------------------------------

No.


3.6. How do I read Neubot logs?
-------------------------------

Under all operating systems you can read logs via the *Log* tab of the
[web interface](#7-web-interface), available since Neubot 0.3.7.  The
following screenshot provides an example:

![Neubot log][neubot-log]
[neubot-log]: http://www.neubot.org/neubotfiles/neubot-log.png

In addition, under UNIX Neubot saves logs with `syslog(3)` and
`LOG_DAEMON` facility. Logs end up in `/var/log`, typically in
`daemon.log`. When unsure, I run the following command (as root) to
lookup the exact file name:

    # grep neubot /var/log/* | awk -F: '{print $1}' | sort | uniq
    /var/log/daemon.log
    /var/log/syslog

In this example, there are interesting logs in both `/var/log/daemon.log`
and `/var/log/syslog`. Once I know the file names, I can grep the logs
out of each file, as follows:

    # grep neubot /var/log/daemon.log | less


3.7. Do I have to periodically rotate log files?
------------------------------------------------

No.  Logs are always saved in the database, but Neubot will periodically
prune old logs.  On UNIX logs are also saved using `syslog(3)`, which
should automatically rotate them.


3.8. Do I have to periodically rotate the database?
---------------------------------------------------

Only if you want to save space aggressively: Neubot should not consume
more than 50-100 MByte of data. To prune the database, run the following
command (as root):

    # neubot database prune

- - -


4. Technical questions
======================


4.1. How does Neubot work?
--------------------------

Neubot runs in the background. Under Linux, BSD, and other Unix
systems, Neubot is started at boot time, becomes a daemon and drops
root privileges (typically running as the `_neubot` user). Under
MacOS, Neubot also runs two extra processes: one is the privileged
process that implements the auto-update functionality, the other
is an unprivileged process that is started on demand by the privileged
process to download the tarball of a new version.  Under Windows
Neubot is started when the user logs in and runs in the context of
the user's session.

Neubot has a minimal impact on system and network load. It spends
most of its time asleep, and it performs automatic tests every 23-27
minutes.  During a test Neubot consumes a lot of system and network
resources, but tests typically run for five-ten seconds at most.
The specific automatic test to run is currently chosen at random.

Before running an automatic test, Neubot performs an operation that
we call *rendezvous*. For speedtest and for the bittorrent test,
the rendezvous consists in connecting to the *master server* (which
is a single, central server) to retrieve the address of the closest
test server (and other information). For the *raw* and the *dashtest*
tests, the rendezvous consists in connecting to `mlab-ns` (Measurement
Lab's name service) to retrieve the address of a test server at random.

Once the address of the test server is known, Neubot connects to the
test server and waits for the authorization to perform the test it
wants to run. This phase can possibly last for a long time, because
each test server limits the number of concurrent tests that it
services.

When the test server authorizes the test, Neubot and the test server
start exchanging data (all tests emulate a specific protocol and
send random data in the protocol messages payload). At the end of
the test, Neubot and the test server exchange the data they collected
during the test.

We save the collected data both locally (so the user can browse it
via the web interface) and on the test server.


4.2. What does *speedtest* test measure?
----------------------------------------

The *speedtest* test emulates HTTP and estimates the round-trip
time, the download and the upload goodput. It estimates the round-trip
time in two ways:

1. by measuring the time that connect() takes to complete (like
   *bittorrent*); and

2. by measuring the average time elapsed between sending a small
   request and receiving a small response (like *raw*).

The *speedtest* test also estimates the goodput by dividing the
amount of transferred bytes by the elapsed time.

To avoid consuming too much user resources, the *speedtest* test adapts
the number of bytes to transfer such that the test runs for about ten
seconds.

This test always uses the closest-available Measurement Lab server. The
closest-available server should deliver better performance than a random
server. Therefore, this test should generally yield a higher average
speed than the tests that use a random Measurement Lab server.

4.3. How does Neubot change my Windows registry?
------------------------------------------------

The installer writes the following two registry keys:

    HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"
    HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Neubot"

The former makes Windows aware of the uninstaller program, while
the latter starts Neubot when you log in.

Both keys are removed by the uninstall process.


4.4. What is the path of Neubot database?
-----------------------------------------

Under Linux the database path is `/var/lib/neubot/database.sqlite3`,
while on other UNIX systems it is `/var/neubot/database.sqlite3`.

Under Windows, the database path is `%APPDATA%\neubot\database.sqlite3` (see
[Wikipedia's article on Windows special folders][wiki-appdata] for more info
on `%APPDATA`, the *Application Data* folder).

[wiki-appdata]: http://en.wikipedia.org/wiki/Special_folder#File_system_directories

For Neubot >= 0.3.7 you can query the location of the database running
the `neubot database` command, for example:

    # neubot database
    /var/lib/neubot/database.sqlite3


4.5. How can I dump the content of the database?
------------------------------------------------

You can dump the content of the database using the command
`neubot database dump`. The output is a JSON file that contains the
results. Use the `show` subcommand (rather than `dump`) if you
want a pretty-printed JSON.


4.6. What does *bittorrent* test measure?
-----------------------------------------

The *bittorrent* test emulates BitTorrent peer-wire protocol and
estimates the round-trip time, the download and the upload goodput
(i.e. the application-level speed measured at the receiver).
It uses the time that connect() takes to complete as an estimator of
the round-trip time.  It also estimates the goodput by dividing the
amount of transferred bytes by the elapsed time.
To avoid consuming too much user resources, the *bittorrent* test adapts
the number of bytes to transfer such that the test runs for about ten
seconds.

Since BitTorrent uses small messages, this test cannot request a
large resource, as the speedtest test does.  Instead, the test
initially sends many back to back requests to fill the space between
the client and the server of many flying responses. The measurement
starts only when the requester thinks there are enough responses
in flight to approximate a continuous transfer.

This test always uses the closest-available Measurement Lab server. The
closest-available server should deliver better performance than a random
server. Therefore, this test should generally yield a higher average
speed than the tests that use a random Measurement Lab server.

4.7. What does measuring goodput mean?
--------------------------------------

Neubot tests does not measure the speed of your broadband Internet
connection, but rather the goodput; i.e. the application-level
achievable speed in the moment of the measurement.

The goodput cannot be higher than the broadband speed, and actually it
is always a bit lower than that.

The first reason why the goodput is lower than the broadband speed
is that the goodput is measured at application level. That is, the
measurement does not count the number of bytes received and sent
by the lower levels of the protocol stack.

The second reason why the goodput is lower than the broadband speed
is that the goodput measurement also includes the initial transient (i.e.
when TCP is trying to estimate the available bandwdith).

Moreover, the measured goodput can also be lower than the goodput
you would expect given the network path between you and the server.
The following is a non-exhaustive list of conditions that can
reduce the goodput measured by Neubot:

1. your computer is overloaded;
1. when Neubor runs, you (or someone that shares your home connection
   with you) are already running a large download;
1. you have a bad wireless connection with high packet loss ratio;
1. there is congestion inside your provider network;
1. there is congestion outside your provider network;
1. the round-trip delay between you and the test server used by Neubot
   is high;
1. the test server used by Neubot is overloaded.

That is, you must take Neubot results with a grain of salt. In particular,
it is worth stressing that a lower-than-expected result is not automatically
the fault of your Internet Service Provider.

Also, note that the *raw* test is designed to use a random server
rather than the closest server. This design choice implies that,
when the round-trip delay between you and the randomly-selected server
is high, the measured goodput is smaller than the broadband speed.

A good introduction to the challanges posed by measuring broadband
(and especially broadband speed) is ["Understanding Broadband
Speed Measurements"][bauer-paper], by Steve Bauer, David Clark,
and William Lehr.

[bauer-paper]: http://mitas.csail.mit.edu/papers/Bauer_Clark_Lehr_Broadband_Speed_Measurements.pdf

The relation between the round-trip delay and the goodput is very
well explained, for example, by ["The Macroscopic Behavior of the
TCP Congestion Avoidance Algorithm"][mathis-paper], by
Matt Mathis, Jeffrey Semke, Jamshid Mahdavi and Teunis Ott.

[mathis-paper]: http://dl.acm.org/citation.cfm?id=264023


4.8. Is it possible to compare speedtest and bittorrent results?
----------------------------------------------------------------

The bittorrent test was released in 0.4.0. At that time the comparison
was not always possible because the speedtest test used two connections
while the bittorrent one used only one, resulting in worse performance
with high-speed, high-delay and/or more congested networks. Neubot 0.4.2
fixed this issue and modified speedtest to use just one connection.

This is not enough.  Before Neubot 0.5.0 more work must be done to make the
behavior of the two tests much more similar, allowing for a fair comparison
of them.

4.9. What does the *raw* test measure?
--------------------------------------

The *raw* test performs a raw 10-second TCP download to estimate
the download goodput.
It is called *raw* because it directly uses TCP and it does not
emulate any protocol.
During the download, this test also collects
statistics about the TCP sender by using Web100
(see `http://www.web100.org`), which is installed on all
Measurement Lab servers.

In addition, it estimates the round-trip time in two ways:

1. by measuring the time that connect() takes to complete (like
   *bittorrent*); and

2.  by measuring the average time elapsed between sending a small
    request and receiving a small response (like *speedtest*).

This test always uses a random Measurement Lab server. The
closest-available server should deliver better performance than a random
server. Therefore, this test should generally yield a lower average
speed than the tests that use the closest-available Measurement
Lab server. However, a random server allows us to probe more network
paths and to experiment with diverse latencies, therefore providing a
more comprehensive view of what can be done from your connection's
vantage point.

4.10. What does the *dashtest* test measure?
--------------------------------------------

The ``dashtest`` test emulates the download of a video payload using
the Dynamic Adaptive Streaming over HTTP (DASH) MPEG standard. This
test, in particular, uses the following DASH rate-adaptation logic: at
the beginning of the test, the dashtest client requests the first segment
using the lowest bitrate representation. During the download of the
first segment, the client calculates the estimated available bandwidth
of the downloaded segment by dividing the size of such segment (in kbit)
by the download time (in seconds). Next, the Dashtest requests
the next segment using, in the common case, the representation rate
that is closer to the download speed of the current segment. This process
is, of course, repeated for all subsequent segments, thereby adapting
the requested bitrate representation to the download speed.

This test always uses a random Measurement Lab server. The
closest-available server should deliver better performance than a random
server. Therefore, this test should generally yield a lower average
speed than the tests that use the closest-available Measurement
Lab server. However, a random server allows us to probe more network
paths and to experiment with diverse latencies, therefore providing a
more comprehensive view of what can be done from your connection's
vantage point.

- - -


5. Privacy questions
====================


5.1. What personal data does Neubot collect?
--------------------------------------------

Neubot does not inspect your traffic, does not monitor the sites you
have visited, etc. Neubot uses a fraction of your network capacity
to run periodic transmission tests and these tests use either random data
or data from our servers.

Neubot collects the Internet address of the computer where it is
running. We have to collect your Internet address (which is personal
data) because it tells us your Internet Service Provider and (roughly)
your location. Both information are imperative to our goal of monitoring
network neutrality.

We identify each instance of Neubot with a random unique identifier. We
use this identifier to perform time series analysis and to check whether
there are recurrent trends. We believe this identifier does not breach
your privacy: in the worst worst case, we would to able to say that a
given Neubot instance has changed Internet address (and hence Provider
and/or location). However, if you are concerned and you are running
Neubot >= 0.3.7, you can generate a new unique identifier running the
following command:

    # neubot database regen_uuid

Future versions of Neubot will also monitor and collect information
regarding your computer load (such as the amount of free memory, the
average load, the average network usage). We will monitor the load to
avoid starting tests when you are using your computer heavily. We will
collect load data in order to consider the effect of the load on
results.


5.2. Will you publish my IP address?
------------------------------------

Yes.  Neubot wants to publish your Internet addresss to enable other
individuals and institutions to carry alternative studies and/or peer
review its measurements and data analysis methodology.

Of course, Neubot cannot publish your Internet address without your
prior informed consent, in compliance with European privacy laws.
For this reason, it asks for permission during the installation,
if applicable, or during operation.  It goes without saying that it
will not start any test until you have read the privacy policy and
provided the permission to publish your Internet address.

One more reason why Neubot cannot run any test until you provide
the permission to publish your Internet address is that [Measurement
Lab][mlab] requires all results to be released as open data.

For more information, please refer to the [privacy policy][policy].

[policy]: https://github.com/neubot/neubot/blob/master/PRIVACY

- - -


6. Data questions
=================


6.1. Where is data published?
-----------------------------

Data is automatically harvested and published by Measurement Lab, as
explained here:

    http://measurementlab.net/data

The direct link to access Neubot data is:

    https://sandbox.google.com/storage/m-lab/neubot

The Neubot project publishes old data (collected before being accepted
into Measurement Lab) and mirrors recent results collected by Measurement
Lab at:

    http://neubot.org/data


6.1. Is there any license attached to data?
-------------------------------------------

Neubot data is available under the terms and provisions of Creative
Commons Zero license:

    http://data.neubot.org/mlab_mirror/LICENSE


6.2. What is the data format?
-----------------------------

Data is published in compressed tarballs, where each tarballs contains
all the results collected during a day by a test server.  Each result
is a text file that contains JSON-encoded dictionary, which is described
in the manual page:

    https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#bittorrent-data-format
    https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#raw-test-data-format
    https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#speedtest-data-format

Data published before the 27th January 2011 is published in different
format:

    http://data.neubot.org/master.neubot.org/odata/README

- - -


7. Web interface
================


7.1. What is the web interface?
-------------------------------

The web interface is a web-based interface that allows the user to
control *neubot* and shows recent results.  By default, when
*neubot* is started, it binds port `9774` on `127.0.0.1`
and waits for web requests.

Users can request raw information, using a `JSON` API, or regular
web pages.  If no page or API is specified, *neubot* will return
the content of the *status* page.  In turn, this page will
use `javascript` to query the `JSON` API and populate the page
itself.  Similarly, other web pages use `javascript` and the
`JSON` API to fill themselves with dynamic data; e.g., settings,
recent results, logs.


7.2. How do I open the web interface?
------------------------------------------

On *Windows*, the *Neubot* command on the start menu should open
the web interface in the default browser (On Windows 8 version, 
a new App called "Neubot" will appear on the start interface 
after installation).

On *MacOSX*, the *Neubot* application (`/Applications/Neubot.app`)
should open the web interface in the default browser.

On *Ubuntu and Debian*, if the user has installed the `neubot`
package (and not the `neubot-nox` package), the *Neubot* command
on the applications menu should open the web interface in
a custom `Gtk+` application that embeds `WebKit` and uses it
to show the web interface.

On *UNIX*, if `Gtk+` and `WebKit` bindings for Python are installed,
the following command:

    neubot viewer

opens a custom `Gtk+` application that embeds `WebKit` and uses
it to show the web interface.

On *any platform*, of course, the user can open his or her favorite web
browser and point it to the following URI:

    http://127.0.0.1:9774/


7.3. What pages does the web interface contain?
-----------------------------------------------

### The status page

The *status* page (which is the default one) shows the status of Neubot,
and the result of the latest transmission test.

![Status page][wui-status]
[wui-status]: http://www.neubot.org/neubotfiles/faq-wui-status.png

### The results page

The *results* page shows the results of recent tests; i.e., latency,
download and upload goodput, both in graphical and in tabular form.

![Results page][wui-results]
[wui-results]: http://www.neubot.org/neubotfiles/faq-wi-results.png

### The log page

The *log* page shows recent logs.  The color of each log entry reflects
severity.  In particular, the page uses:

    - *red* for error messages;
    - *yellow* for warning messages;
    - *blue* for notice messages;
    - *grey* for debug messages.

One can refresh the page by clicking on the `Refresh page` link.

![Log page][wui-log]
[wui-log]: http://www.neubot.org/neubotfiles/faq-wui-log.png

### The privacy page

The *privacy* page shows the privacy policy and allows to set privacy
permissions.  See the [Privacy questions](#5-privacy-questions) section for
more info.

![Privacy page][wui-privacy]
[wui-privacy]: http://www.neubot.org/neubotfiles/faq-wui-privacy.png

### The settings page

The *settings* page shows and allow to change Neubot settings.  One must
click on the `Save` button to make changes effective.

![Settings page][wui-settings]
[wui-settings]: http://www.neubot.org/neubotfiles/faq-wui-settings.png


7.4. How do I change the web interface language?
-----------------------------------------------------

Change the value of the `www.lang` setting, which can be modified
using the *settings* page.  Currently the value can be one of:

- *default*: uses the browser's default language;

- *en*: uses english;

- *it*: uses italian.

- - -


8. Following development
========================


8.1. How do I clone Neubot repository?
--------------------------------------

Install git and clone the git repository with the following command:

    git clone git://github.com/neubot/neubot.git

It contains the `master branch`, which holds the code that will be
included in next release.  There may be other branches, but
they are intended for internal development only.  Therefore, they will
be deleted or rebased without notice.

Specific repositories are available for ports on supported operating
systems:

    git clone git://github.com/neubot/neubot_debian.git
    git clone git://github.com/neubot/neubot_macos.git
    git clone git://github.com/neubot/neubot_win32.git

Each contains a `master` branch, which holds the code and patches
that will be included in next release.


8.2. How do I prepare a diff for Neubot?
----------------------------------------

Assuming you already cloned Neubot's git repository, the first step is to
sync your local copy with it:

    git fetch origin
    git checkout master
    git merge origin/master

The second step is to create a branch for your patches.  It is a good idea
to tag your starting point:

    git checkout -b feature_123
    git tag feature_123_start

The third step is to develop your patches.  Make sure that each patch
implements one single change and the rationale of the change is well
documented by the commit message.

When you think your patches are ready, subscribe to the public mailing
list, if needed, and send your patches with `git send-email`:

    git format-patch feature_123_start
    git send-email *.patch

Patches may be rejected or accepted, possibly with the indication of
performing additional changes.  Accepted patches are committed on some
testing branch of Neubot repository.  When we think that they are
stable enough to be included into a release, they are committed on
the master branch.

At this point, they are part of the official history of the project
and you can cleanup your work environment:

    git checkout master
    git branch -D feature_123
    git tag -d feature_123_start

- - -


9. Localhost web API
====================

The localhost web API is documented in the [WEB API][man-web-api] section of
Neubot's [manual page][manpage].

[man-web-api]: https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#web-api

[manpage]: https://github.com/neubot/neubot/blob/master/doc/neubot.1.rst#neubot
