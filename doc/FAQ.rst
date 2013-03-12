0. Index
--------

* `0. Index`_

* `1. General questions`_

   * `1.1. What is Neubot?`_
   * `1.2. What is Measurement Lab?`_
   * `1.3. What is network neutrality?`_
   * `1.4. Why "the network neutrality bot"?`_
   * `1.5. Why is it crucial to monitor network neutrality?`_
   * `1.6. Why might I want to install Neubot?`_
   * `1.7. What tests are implemented by the latest version?`_
   * `1.8. What is the roadmap to Neubot 1.0.0.0?`_
   * `1.9. When is the next release of Neubot?`_
   * `1.10. What is your versioning policy?`_
   * `1.11. What is the best version of Neubot?`_
   * `1.12. How long should I keep Neubot installed?`_
   * `1.13. How much do you test Neubot before release?`_
   * `1.14. Who develops Neubot?`_
   * `1.15. Under what license is Neubot available?`_
   * `1.16. How much does Neubot cost?`_

* `2. Installing Neubot`_

   * `2.1. On what systems does neubot run?`_
   * `2.2. How do I install neubot?`_
   * `2.3. How do I install Neubot on FreeBSD?`_

* `3. Using Neubot`_

   * `3.1. Neubot installed. What should I do now?`_
   * `3.2. How many resources does Neubot need?`_
   * `3.3. How do I report bugs, ask questions, or make suggestions?`_
   * `3.4. What are the issues if I use mobile broadband, 3G modem, Internet key?`_
   * `3.5. Do I need to tweak the configuration of my router?`_
   * `3.6. How do I read Neubot logs?`_
   * `3.7. Do I have to periodically rotate log files?`_
   * `3.8. Do I have to periodically rotate the database?`_

* `4. Technical questions`_

   * `4.1. How does Neubot work?`_
   * `4.2. What does speedtest test measure?`_
   * `4.3. How does Neubot change my Windows registry?`_
   * `4.4. What is the path of Neubot database?`_
   * `4.5. How can I dump the content of the database?`_
   * `4.6. What does bittorrent test measure?`_
   * `4.7. What does measuring goodput mean?`_
   * `4.8. Is it possible to compare speedtest and bittorrent results?`_

* `5. Privacy questions`_

   * `5.1. What personal data does Neubot collect?`_
   * `5.2. Will you publish my IP address?`_

* `6. Data questions`_

   * `6.1. Where is data published?`_
   * `6.2. Is there any license attached to data?`_
   * `6.3. What is data format?`_

* `7. Web user interface`_

   * `7.1. What is the web user interface?`_
   * `7.2. How do I open the web user interface?`_
   * `7.3. What does the status page show?`_
   * `7.4. What does the speedtest page show?`_
   * `7.5. What does the bittorrent page show?`_
   * `7.6. What does the log page show?`_
   * `7.7. What does the privacy page show?`_
   * `7.8. What does the settings page show?`_
   * `7.9. How do I change the web user interface language?`_

* `8. Following development`_

   * `8.1. How do I clone Neubot repository?`_
   * `8.2. How do I prepare a diff for Neubot?`_

* `9. Localhost web API`_

   * `9.1. How do I get a a list of APIs?`_
   * `9.2. How do I get test data?`_
   * `9.3. How do I get/set configuration variables?`_
   * `9.4. How do I start a test?`_
   * `9.5. How do I get debugging info?`_
   * `9.6. Home page redirections`_
   * `9.7. How do I force Neubot to exit?`_
   * `9.8. How do I track Neubot state?`_

------------------------------------------------------------------------

1. General questions
--------------------

1.1. What is Neubot?
~~~~~~~~~~~~~~~~~~~~

Neubot is a research project on network neutrality by the `Nexa Center for
Internet & Society`_ at `Politecnico di Torino (DAUIN)`_.  The project is
based on a lightweight `free software`_ computer program that interested
users can download and install on their computers.  The program runs in the
background and periodically performs transmission tests with servers
hosted by the distributed `Measurement Lab`_ platform, and, in the future,
with other instances of Neubot.  Transmission tests measure network performance
with various application-level protocols.  Test results are saved both
locally and on the test servers.  Data is collected for research purposes
and `published on the web`_ under Creative Commons Zero allowing anyone
to re-use it freely for the same purpose.

1.2. What is Measurement Lab?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measurement Lab (M-Lab_) is a distributed server platform that provides
connectivity and servers around the world for projects that aim to
measure the quality and/or neutrality of broadband Internet connections
by probing the network with active tests.  It also provides additional
services, e.g., server discovery APIs, automatic data collection and
publishing, support for gathering network-stack level statistics.

From version 0.4.6 onward Neubot is hosted at Measurement Lab.  Since
version 0.4.8, all tests are carried out by Measurement Lab servers.

1.3. What is network neutrality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Network neutrality is the principle that the Internet should be neutral
with respect to kinds of applications, senders and destinations. In
other words, a network is neutral when routers_ forward packets using
a *first come, first served* strategy.  Instead, it is not neutral when
certain packets receive a preferential treatment.

The ancient Internet was strictly neutral, because it was designed
to minimize the interaction between applications and the network
(see RFC3439_). This design choice allowed very fast packet switching
and enabled strong openness towards unforeseen uses of the Internet
Protocol. The result was an extraordinary outburst of innovation
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
to `Wikipedia's article`_.

1.4. Why *"the network neutrality bot"*?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The program is called *network neutrality bot* because it is a
`software application that runs automated tasks over the Internet`_
to collect data meaningful to study network neutrality.

1.5. Why is it crucial to monitor network neutrality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitoring network neutrality is crucial because it enables a deeper
understanding of Internet Service Providers (ISPs) behavior. This
is paramount *ex-ante*, i.e., at a time when there is a broad discussion
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest version of Neubot implements the following tests:

**bittorrent**
  It emulates the `BitTorrent peer-wire protocol`_ and measures
  `round trip time`_, download and upload goodput_.

**raw**
  It does not emulate any protocol and performs a download-only
  *raw* TCP test.  It measures `round trip time`_ and download
  goodput_.  In addition, it also saves CPU uage information and
  TCP/IP stack statistics.

**speedtest**
  It is an HTTP client-server test and measures `round trip time`_,
  download and upload goodput_.

  The initial implementation was inspired to the test provided by
  speedtest.net_, hence the name.

If you're interested, you can get more details on them in
the `4. Technical questions`_ section.

1.8. What is the roadmap to Neubot 1.0.0.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot 1.0.0.0 will be able to perform client-server and peer-to-peer
transmission tests using multiple application level protocols.
The roadmap_ and TODO_ list are now updated and maintained on the
`github's wiki`_.

1.9. When is the next release of Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The release process strives to `release early, release often`_ to
maximize feedback.  The `github repository`_ is updated very frequently
and there is a commitment to deploy a new release every month.

1.10. What is your versioning policy?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot follows the well-known *major*, *minor* and *patch* version
number policy.  E.g. Neubot 0.4.8 has major version number 0, minor
version number 4 and patch version number 8.

A milestone release has patch number 0 and major, minor version numbers
match a milestone in the `roadmap`_.  Patch releases, instead, have nonzero
patch version number.  Therefore, 1.0.0 and 0.4.0 are milestone releases,
while 0.3.1 is a patch release.

1.11. What is the best version of Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best version of Neubot will always be the one with the highest
version number, e.g. 0.3.1 is better than 0.3.0. Patch releases might
include experimental features, but these features will not be enabled by
default until they graduate and become stable.

1.12. How long should I keep Neubot installed?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As long as possible. Neubot is not a limited-scope project but rather an
ongoing effort.

1.13. How much do you test Neubot before release?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Typically a new experimental feature is included in a patch release and
is not enabled by default until it graduates and becomes stable.  When
a milestone release ships, most stable features have been tested for at
least one release cycle, i.e. two to four weeks.

1.14. Who develops Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot project lead is `Simone Basso`_, a research fellow of the `NEXA
Center for Internet & Society`_. He develops Neubot in collaboration with
and under the supervision of prof. `Antonio Servetti`_, prof. `Federico
Morando`_, and prof. `Juan Carlos De Martin`_, of Politecnico di Torino.

See `people page`_ for more information.

1.15. Under what license is Neubot available?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We release Neubot under `GNU General Public License version 3`_.

1.16. How much does Neubot cost?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Zero. Neubot is available for free.

------------------------------------------------------------------------

2. Installing Neubot
--------------------

2.1. On what systems does neubot run?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot is written in Python_ and therefore should run on all systems
supported by Python.

The Neubot team provides packages for Ubuntu_ >= 10.04 (and Debian_),
MacOSX_ >= 10.6, Windows_ >= XP SP3.  Neubot is included in the `FreeBSD
Ports Collection`_ and is known to run on OpenBSD_ 5.1 current.

2.2. How do I install neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Neubot team provides packages for MacOSX_, Windows_, Debian_ and
distributions based on Debian_ (such as Ubuntu_).  Neubot is part
of the FreeBSD port collection.  If there are no binary packages available
for your system, you can still install it from sources.

Subsequent FAQ entries will deal with all these options.

2.3. How do I install Neubot on FreeBSD?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot is part of `FreeBSD ports collection`.  So it can be installed
easily, either by using ``pkg_add`` or by compiling the package for the
ports tree.  Of course, when in doubt, please refer to `FreeBSD
documentation`_ and `FreeBSD manpages`_.  In particular, the authoritative
Neubot port page is::

    http://www.freshports.org/net/neubot/

For your convenience, here we mirror the two base commands to add Neubot
to your FreeBSD system.  To add the precompiled package to your system,
you should run the following command as root::

    pkg_add -r neubot

To compile and install the port, again as root, you need to type the
following command::

    cd /usr/ports/net/neubot/ && make install clean

Please, do not ask Neubot developers questions related to the FreeBSD
port because they may not be able to help.  We suggest instead to direct
questions to `FreeBSD ports mailing list`_.  Bugs should be reported
using the `send-pr`_ interface.

------------------------------------------------------------------------

3. Using Neubot
---------------

3.1. Neubot installed. What should I do now?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot automatically downloads and installs updates on all platforms
but Microsoft Windows (and, of course, if you installed it from
source, you will not receive automatic updates).

If you are not using Windows, you should periodically make sure that
it automatically updated to the latest version.  As a rule of thumb, if
more than two weeks have passed since the last release and Neubot has not
updated, there's a bug.

If you are running Windows, the web user interface (see `7. Web user
interface`_) will be opened
automatically on the browser when an update is available. You will
see a message like the one in the following screenshot. Click on the
link, follow instructions, and you're done.

.. image:: http://www.neubot.org/neubotfiles/neubot-update-notification.png
   :align: center

You may also want to compare Neubot results with the ones of other online
speed tests and tools.  If so, we would appreciate it if you would share
your results with us, especially when Neubot results are not consistent
with the ones of other tools.

3.2. How many resources does Neubot need?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot has a minimal impact on system and network load. It spends most
of its time asleep or waiting for its turn to perform a test. During a
test Neubot consumes a lot of system and network resources but the
program tries to guarantee that the test does not take not too much
time.

Here are a couple of screenshots captured from a netbook running Ubuntu
9.10 and attached to Politecnico di Torino network. In the first
screenshot you can see the resource usage during an on-demand test
invoked from the command line. The *init* phase of the test is the one
where Neubot generates the random data to send during the upload phase.
(The resource usage is much lower if you run the test at home, given
that Politecnico network is 5x/10x faster than most ADSLs.)

.. image:: http://www.neubot.org/neubotfiles/resources1.png
   :align: center

The second screenshot shows the amount of consumed resources (in
particular memory) when Neubot is idle.

.. image:: http://www.neubot.org/neubotfiles/resources2.png
   :align: center

3.3. How do I report bugs, ask questions, or make suggestions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To report bugs and ask questions, please use our mailing list. The
official languages for the mailing list are English and Italian.

Note that you **must** subscribe to the mailing list first, otherwise
your message **will not** be accepted. To subscribe, go to:

      http://www.neubot.org/cgi-bin/mailman/listinfo/neubot

The mailing list subscription page does not have a valid SSL certificate
and your browser is likely to complain.  Don't be scared; it
is the page to register to the Neubot mailing list, not your bank account.

We advise you to search the public archive **before** posting a message,
because others might have already asked the same question or reported
the same bug. All posts to the mailing list are archived here:

      http://www.neubot.org/pipermail/neubot/

Thanks for your cooperation!

3.4. What are the issues if I use mobile broadband, 3G modem, Internet key?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One possible issue with mobile broadband is the following. If you use
Windows, you installed Neubot, and you are not connected, and Neubot
starts a test, it's possible that Windows asks you to connect. If this
behavior annoys you, stop Neubot from the start menu.

*In future releases we plan to check whether there is an Internet
connection or not, and start a test only if it's available.*

3.5. Do I need to tweak the configuration of my router?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No.

3.6. How do I read Neubot logs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under all operating systems you can read logs via the *Log* tab of the
web user interface (see `7. Web user interface`_), available since
``0.3.7``.  The following screenshot
provides an example:

.. image:: http://www.neubot.org/neubotfiles/neubot-log.png
   :align: center

In addition, under UNIX Neubot saves logs with ``syslog(3)`` and
``LOG_DAEMON`` facility. Logs end up in ``/var/log``, typically in
``daemon.log``. When unsure, I run the following command (as root) to
lookup the exact file name::

    # grep neubot /var/log/* | awk -F: '{print $1}' | sort | uniq
    /var/log/daemon.log
    /var/log/syslog

In this example, there are interesting logs in both ``/var/log/daemon.log``
and ``/var/log/syslog``. Once I know the file names, I can grep the logs
out of each file, as follows::

    # grep neubot /var/log/daemon.log | less

3.7. Do I have to periodically rotate log files?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No.  Logs are always saved in the database, but Neubot will periodically
prune old logs.  On UNIX logs are also saved using ``syslog(3)``, which
should automatically rotate them.

3.8. Do I have to periodically rotate the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. Neubot database should grow slowly in space over time. (My
workstation database weighs 2 MBytes after 8 months, and I frequently
run a test every 30 seconds for testing purpose.) To prune the database
run the following command (as root)::

    # neubot database prune

------------------------------------------------------------------------

4. Technical questions
----------------------

4.1. How does Neubot work?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot runs in background. Under Linux, BSD, and other Unices Neubot is
started at boot time, becomes a daemon and drops root privileges. Under
Windows Neubot is started when the user logs in for the first time
(subsequent logins don't start additional instances of Neubot).

Neubot has a minimal impact on system and network load. It spends most
of its time asleep or waiting for its turn to perform a test. During a
test Neubot consumes a lot of system and network resources but the
program tries to guarantee that the test does not take too much
time, as detailed below.

Periodically, Neubot downloads form the *Master Server* information about
the next test it should perform, including the name of the test, the
Test Server to connect to, and possibly other parameters. If there are
updates available, the Master Server response includes update
information too, like the URI to download updates from.

Then, Neubot connects to the Test Server, waits the authorization to
perform the selected test, performs the test, and saves results. It
needs to wait (possibly for quite a long time) because Test Servers do
not handle more than one (or few) test at a time. Overall, the test may
last for a number of seconds but the program tries to guarantee that the
test does not take too much time, as detailed below. At the end of the
test, results are saved in a local database and sent to the project
servers.

Finally, after the test, Neubot sleeps for a long time, before
connecting again to the Master Server.

As of version 0.4.2, Neubot uses the following algorithm to keep the test
duration bounded. The default amount of bytes to transfer is designed to
allow for reasonable testing time with slow ADSL connections. After the
test, Neubot adapts the number of bytes to be transferred for the next test
so that the next test will take about five seconds, regardless of connection
speed. Also, it repeats the test up to seven times if the test
did not take at least three seconds.

*(Future versions of Neubot will implement peer-to-peer tests within instances of Neubot.)*

4.2. What does *speedtest* test measure?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *speedtest* test uses the `HTTP protocol`_ and measures: `round trip
time`_, download and upload goodput_. It was originally inspired to
speedtest.net_ test, hence the name. The test estimates the `round trip
time`_ measuring the time required to connect and the average time to
request and receive a zero-length resource. It also estimates the download
and upload goodput_ dividing the number of bytes transferred by the time
required to transfer them.

4.3. How does Neubot change my Windows registry?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installer writes the following two registry keys::

    HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"
    HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Neubot"

The former makes Windows aware of the uninstaller program, while
the latter starts Neubot when you log in.

Both keys are removed by the uninstall process.

4.4. What is the path of Neubot database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under Linux the database path is ``/var/lib/neubot/database.sqlite3``,
while on other UNIX systems it is ``/var/neubot/database.sqlite3``.

Under Windows, the database path is always
``%APPDATA%\neubot\database.sqlite3``.

For Neubot >= 0.3.7 you can query the location of the database running
the ``neubot database info`` command, for example::

    $ neubot database info
    /home/simone/.neubot/database.sqlite3

    # neubot database info
    /var/lib/neubot/database.sqlite3

Until Neubot 0.4.12, when Neubot was run by an ordinary user, the
database was searched on ``$HOME/.neubot/database.sqlite``, but
this is not supported anymore.

4.5. How can I dump the content of the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can dump the content of the database using the command
``neubot database dump``. The output is a JSON file that contains the
results. (Note that under UNIX, you must be root in order to dump the
content of the system-wide database: If you run this command as an
ordinary user you will dump the user-specific database instead.)

4.6. What does *bittorrent* test measure?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *bittorrent* test emulates the `BitTorrent peer-wire protocol`_ and
measures: `round trip time`_, download and upload goodput_. The test
estimates the `round trip time`_ by measuring the time required to connect.

Since BitTorrent uses small messages, it is not possible to transfer a
huge resource and divide the number of transmitted bytes by the time of
the transfer. So, the test initially makes many back to back requests to
fill the space between the client and the server of many flying
responses. The measurement starts only when the requester thinks there
are enough responses in flight to approximate a continuous transfer.

4.7. What does measuring goodput mean?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot tests *does not* measure the speed of your broadband Internet
connection, but rather the `goodput`_, i.e. *the application-level
achievable speed in the moment of the measurement*. The result will
suffer if, for example:

#. you are downloading a large file;
#. your roommate is downloading a large file;
#. you have a bad wireless connection with high packet loss ratio;
#. there is congestion outside your provider network;
#. you don't live `near our server`_;
#. our server is overloaded.

I.e. you must take Neubot results `with a grain of salt`_.

4.8. Is it possible to compare speedtest and bittorrent results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The bittorrent test was released in 0.4.0. At that time the comparison
was not always possible because the speedtest test used two connections
while the bittorrent one used only one, resulting in worse performance
with high-speed, high-delay and/or more congested networks. Neubot 0.4.2
fixed this issue and modified speedtest to use just one connection.

This is not enough.  Before Neubot 0.5.0 more work must be done to make the
behavior of the two tests much more similar, allowing for a fair comparison
of them.

------------------------------------------------------------------------

5. Privacy questions
--------------------

5.1. What personal data does Neubot collect?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot does not inspect your traffic, does not monitor the sites you
have visited, etc. Neubot use a fraction of your network capacity
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
following command::

    # neubot database regen_uuid

Future versions of Neubot will also monitor and collect information
regarding your computer load (such as the amount of free memory, the
average load, the average network usage). We will monitor the load to
avoid starting tests when you are using your computer heavily. We will
collect load data in order to consider the effect of the load on
results.

5.2. Will you publish my IP address?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
the permission to publish your Internet address is that Measurement Lab (M-Lab_),
the distributed server platform that empowers the Neubot Project, requires
all results to be released as open data.

For more information, please refer to the `privacy policy`_.

------------------------------------------------------------------------

6. Data questions
-----------------

6.1. Where is data published?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data is automatically harvested and published by Measurement Lab, as
explained here:

    http://measurementlab.net/data

The direct link to access Neubot data is:

    https://sandbox.google.com/storage/m-lab/neubot

The Neubot project publishes old data (collected before being accepted
into Measurement Lab) and mirrors recent results collected by Measurement
Lab at:

    http://neubot.org/data

6.2. Is there any license attached to data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot data is available under the terms and provisions of Creative
Commons Zero license:

    http://data.neubot.org/mlab_mirror/LICENSE

6.3. What is data format?
~~~~~~~~~~~~~~~~~~~~~~~~~

Data is published in compressed tarballs, where each tarballs contains
all the results collected during a day by a test server.  Each result
is a text file that contains JSON-encoded dictionary, which is described
here:

    http://data.neubot.org/mlab_mirror/README

Data published before the 27th January 2011 is published in different
format:

    http://data.neubot.org/master.neubot.org/odata/README

------------------------------------------------------------------------

7. Web user interface
---------------------

7.1. What is the web user interface?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The web user interface is a web-based interface that allows the user to
control **neubot** and shows recent results.  By default, when
**neubot** is started, it binds port ``9774`` on ``127.0.0.1``
and waits for web requests.

Users can request raw information, using a ``JSON`` API, or regular
web pages.  If no page or API is specified, **neubot** will return
the content of the *status* page.  In turn, this page will
use ``javascript`` to query the ``JSON`` API and populate the page
itself.  Similarly, other web pages use ``javascript`` and the
``JSON`` API to fill themselves with dynamic data, e.g. settings,
recent results, logs.

7.2. How do I open the web user interface?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On **Windows**, the *Neubot* command on the start menu should open
the web user interface in the default browser.

On **MacOSX**, the *Neubot* application (``/Applications/Neubot.app``)
should open the web user interface in the default browser.

On **Ubuntu and Debian**, if the user has installed the `neubot`
package (and not the `neubot-nox` package), the *Neubot* command
on the applications menu should open the web user interface in
a custom ``Gtk+`` application that embeds ``WebKit`` and uses it
to show the web user interface.

On **UNIX**, if `Gtk+` and `WebKit` bindings for Python are installed,
the following command::

    neubot viewer

opens a custom ``Gtk+`` application that embeds ``WebKit`` and uses
it to show the web user interface.

On **any platform**, of course, the user can open his or her favorite web
browser and point it to the following URI::

    http://127.0.0.1:9774/

7.3. What does the status page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *status* page (which is the default one) shows the status of Neubot,
and the result of the latest transmission test.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-status.png
   :align: center

7.4. What does the speedtest page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *speedtest* page shows the results of recent *speedtest* tests, i.e.
latency, download and upload goodput, both in graphical and in tabular
form.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-speedtest.png
   :align: center

7.5. What does the bittorrent page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *bittorrent* page shows the results of recent *bittorrent* tests, i.e.
latency, download and upload goodput, both in graphical and in tabular
form.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-bittorrent.png
   :align: center

7.6. What does the log page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *log* page shows recent logs.  The color of each log entry reflects
severity.  In particular, the page uses:

* *red* for error messages;
* *yellow* for warning messages;
* *blue* for notice messages;
* *grey* for debug messages.

One can refresh the page by clicking on the `Refresh page` link.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-log.png
   :align: center

7.7. What does the privacy page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *privacy* page shows the privacy policy and allows to set privacy
permissions.  See `5. Privacy questions`_ section for more info.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-privacy.png
   :align: center

7.8. What does the settings page show?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *settings* page shows and allow to change Neubot settings.  One must
click on the `Save` button to make changes effective.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-settings.png
   :align: center

7.9. How do I change the web user interface language?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Change the value of the ``www.lang`` setting, which can be modified
using the *settings* page.  Currently the value can be one of:

**default**
  Uses the browser's default language.

**en**
  Uses english.

**it**
  Uses italian.

------------------------------------------------------------------------

8. Following development
------------------------

8.1. How do I clone Neubot repository?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install git and clone the git repository with the following command::

    git clone git://github.com/neubot/neubot.git

It contains the `master branch`, which holds the code that will be
included in next release.  There may be other branches, but
they are intended for internal development only.  So, they can be
deleted or rebased without notice.

Specific repositories are available for ports on supported operating
systems::

    git clone git://github.com/neubot/neubot_debian.git
    git clone git://github.com/neubot/neubot_macos.git
    git clone git://github.com/neubot/neubot_win32.git

Each contains a `master` branch, which holds the code and patches
that will be included in next release.

8.2. How do I prepare a diff for Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming you already cloned Neubot's git repository, the first step is to
sync your local copy with it::

    git fetch origin
    git checkout master
    git merge origin/master

The second step is to create a branch for your patches.  It is a good idea
to tag your starting point::

    git checkout -b feature_123
    git tag feature_123_start

The third step is to develop your patches.  Make sure that each patch
implements one single change and the rationale of the change is well
documented by the commit message.

When you think your patches are ready, subscribe to the public mailing
list, if needed, and send your patches with `git send-email`::

    git format-patch feature_123_start
    git send-email *.patch

Patches may be rejected or accepted, possibly with the indication of
performing additional changes.  Accepted patches are committed on some
testing branch of Neubot repository.  When we think that they are
stable enough to be included into a release, they are committed on
the master branch.

At this point, they are part of the official history of the project
and you can cleanup your work environment::

    git checkout master
    git branch -D feature_123
    git tag -d feature_123_start

------------------------------------------------------------------------

9. Localhost web API
--------------------

.. TODO:: rewrite to be impersonal

Here is the documentation of Neubot 127.0.0.1:9774
web API.  This wiki describes roughly 3/5 of the API.
I will follow-up with the remainder soon.

The API is quite liberal and in most cases any method,
will do.  When the behavior depends on the method I
have specified that.  Of course, I usually use the GET
method to test the API from command line.

9.1. How do I get a a list of APIs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first API you can access is, indeed, /api/ and
returns just the list of APIs.  I originally planned
to return documentation here, but I never went that
further.  Still, I mention that possibility, because
it may be a nice thing to do in the interest of
discoverability.

Anyway here's the API in action::

 $ curl -o- http://127.0.0.1:9774/api/
 [
   "/api",
   "/api/",
   "/api/results",
   "/api/config",
   "/api/debug",
   "/api/exit",
   "/api/index",
   "/api/log",
   "/api/runner",
   "/api/state",
   "/api/version"
 ]

Needless to say, the response is JSON.

Oh, and of course, /api is just an alias for /api/.

9.2. How do I get test data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. NOTE:: This API will be renamed /api/data
   starting from Neubot 0.4.13

We have a common API, /api/results, for both BitTorrent
and speedtest.

I will describe /api/results taking BitTorrent as an example
but the same apply to speedtest. Both return a list of
dictionaries, what differs is that speedtest dictionaries
have one more (key, value) pair (with key='latency').

Calling /api/results?test=bittorrent without any further
option returns a list of BitTorrent results (just use
test=speedtest for speedtest results), where each result
is a dictionary::

 $ curl -o- http://127.0.0.1:9774/api/results?test=bittorrent
 [{"real_address": "80.182.50.210", "privacy_can_collect": 1, ...}, {...}]

The response is a very long line, here I have edited
it for readability.  (Below there is a pretty-printed
example, with all the dict keys.)

Apart from `test=name`, the other available options are:

since=int
 Returns only results after the specified date,
 which is relative to the EPOCH.

until=int
 Does not return results after the specified date,
 which is relative to the EPOCH.

debug=bool
 Pretty prints the JSON.

One comment: when I wrote the interface I didn't know,
but IIRC here it would be more correct english to use
from..to instead of since..until.

Here's an example with some options::

 $ curl -o- 'http://127.0.0.1:9774/api/results?test=bittorrent&debug=1&since=1332738000'
 [
   {
       "connect_time": 0.034081935882568359,
       "download_speed": 862063.72062096791,
       "internal_address": "192.168.0.33",
       "neubot_version": "0.004010999",
       "platform": "darwin",
       "privacy_can_collect": 1,
       "privacy_can_publish": 1,
       "privacy_informed": 1,
       "real_address": "87.14.214.244",
       "remote_address": "194.116.85.224",
       "timestamp": 1332867719,
       "upload_speed": 49437.521614604324,
       "uuid": "0964312e-f451-4579-9984-3954dcfdeb42"
   },
   {
       "connect_time": 0.035229921340942383,
       "download_speed": 861644.9323690217,
       "internal_address": "192.168.0.33",
       "neubot_version": "0.004010999",
       "platform": "darwin",
       "privacy_can_collect": 1,
       "privacy_can_publish": 1,
       "privacy_informed": 1,
       "real_address": "87.14.214.244",
       "remote_address": "194.116.85.211",
       "timestamp": 1332841328,
       "upload_speed": 48351.377174934867,
       "uuid": "0964312e-f451-4579-9984-3954dcfdeb42"
   },
   {
       "connect_time": 0.03593897819519043,
       "download_speed": 861803.16141179914,
       "internal_address": "192.168.0.33",
       "neubot_version": "0.004010999",
       "platform": "darwin",
       "privacy_can_collect": 1,
       "privacy_can_publish": 1,
       "privacy_informed": 1,
       "real_address": "87.14.214.244",
       "remote_address": "194.116.85.224",
       "timestamp": 1332838263,
       "upload_speed": 46651.459334347594,
       "uuid": "0964312e-f451-4579-9984-3954dcfdeb42"
   },
   {
       "connect_time": 0.036273956298828125,
       "download_speed": 841047.23338805605,
       "internal_address": "192.168.0.33",
       "neubot_version": "0.004010999",
       "platform": "darwin",
       "privacy_can_collect": 1,
       "privacy_can_publish": 1,
       "privacy_informed": 1,
       "real_address": "87.14.214.244",
       "remote_address": "194.116.85.237",
       "timestamp": 1332805450,
       "upload_speed": 44710.82837997895,
       "uuid": "0964312e-f451-4579-9984-3954dcfdeb42"
   }
 ]

The difference between bittorrent and speedtest is
just that the speedtest dictionary has one more (key,
value) pair.  More generally, defines the format of its
own dictionary -- and the javascript on the web api
side is expected to be able to cope with it.

9.3. How do I get/set configuration variables?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get/set configuration variable Neubot uses the
/api/config API.  More specifically:

1. the configuration is a dictionary;

2. GET is used to read and POST to modify it.

GET returns a JSON object, while POST sends an
urlencoded string.

Available options are:

debug=boolean
 Pretty prints the JSON.

labels=boolean
 When True, the API does not return variable
 values but rather their description.

In the following examples I will always use
the debug option, so I don't need to wrap text
at hand anymore :-).

::

 $ curl -o- 'http://127.0.0.1:9774/api/config?debug=1'
 {
   "agent.api": 1,
   "agent.api.address": "127.0.0.1",
   "agent.api.port": 9774,
   "agent.daemonize": 0,
   "agent.interval": 0,
   "agent.master": "master.neubot.org",
   "agent.rendezvous": 1,
   "agent.use_syslog": 1,
   "bittorrent.address": "",
   "bittorrent.bytes.down": 0,
   "bittorrent.bytes.up": 0,
   "bittorrent.daemonize": 0,
   "bittorrent.infohash": "",
   "bittorrent.listen": 0,
   "bittorrent.my_id": "",
   "bittorrent.negotiate": 1,
   "bittorrent.negotiate.port": 80,
   "bittorrent.numpieces": 1048576,
   "bittorrent.piece_len": 131072,
   "bittorrent.port": 6881,
   "bittorrent.watchdog": 300,
   "enabled": 1,
   "http.client.class": "",
   "http.client.method": "GET",
   "http.client.stdout": 0,
   "http.client.uri": "",
   "http.server.address": "0.0.0.0",
   "http.server.class": "",
   "http.server.daemonize": 1,
   "http.server.mime": 1,
   "http.server.ports": "8080,",
   "http.server.rootdir": "",
   "http.server.ssi": 0,
   "negotiate.max_thresh": 64,
   "negotiate.min_thresh": 32,
   "negotiate.parallelism": 7,
   "net.stream.address": "127.0.0.1",
   "net.stream.certfile": "",
   "net.stream.chunk": 262144,
   "net.stream.clients": 1,
   "net.stream.daemonize": 0,
   "net.stream.duration": 10,
   "net.stream.ipv6": 0,
   "net.stream.key": "",
   "net.stream.listen": 0,
   "net.stream.port": 12345,
   "net.stream.proto": "",
   "net.stream.rcvbuf": 0,
   "net.stream.secure": 0,
   "net.stream.server_side": 0,
   "net.stream.sndbuf": 0,
   "notifier_browser.honor_enabled": 0,
   "notifier_browser.min_interval": 86400,
   "privacy.can_collect": 1,
   "privacy.can_publish": 1,
   "privacy.informed": 1,
   "runner.enabled": 1,
   "speedtest.client.latency_tries": 10,
   "speedtest.client.nconn": 1,
   "speedtest.client.uri": "http://master.neubot.org/",
   "uuid": "0964312e-f451-4579-9984-3954dcfdeb42",
   "version": "4.2",
   "www.lang": "default"
 }

 $ curl -o- 'http://127.0.0.1:9774/api/config?debug=1&labels=1'
 {
   "agent.api": "Enable API server",
   "agent.api.address": "Set API server address",
   "agent.api.port": "Set API server port",
   "agent.daemonize": "Enable daemon behavior",
   "agent.interval": "Set rendezvous interval, in seconds (must be >= 1380 or 0 = random value in a given interval)",
   "agent.master": "Set master server address",
   "agent.rendezvous": "Enable rendezvous client",
   "agent.use_syslog": "Force syslog usage in any case",
   "enabled": "Enable Neubot to perform automatic transmission tests",
   "notifier_browser.honor_enabled": "Set to 1 to suppress notifications when Neubot is disabled",
   "notifier_browser.min_interval": "Minimum interval between each browser notification",
   "privacy.can_collect": "You give Neubot the permission to collect your Internet address for research purposes",
   "privacy.can_publish": "You give Neubot the permission to publish on the web your Internet address so that it can be reused for research purposes",
   "privacy.informed": "You assert that you have read and understood the privacy policy",
   "runner.enabled": "When true command line tests are executed in the context of the local daemon, provided that it is running",
   "uuid": "Random unique identifier of this Neubot agent",
   "version": "Version number of the Neubot database schema",
   "www.lang": "Web GUI language (`default' means: use browser default)"
 }

 # Now I change the default language for the
 # web user interface

 $ curl -s -o- 'http://127.0.0.1:9774/api/config?debug=1'|grep 'www\.lang'
   "www.lang": "default"
 $ curl -s -d www.lang=it -o- 'http://127.0.0.1:9774/api/config?debug=1'
 "{}"
 $ curl -s -o- 'http://127.0.0.1:9774/api/config?debug=1'|grep 'www\.lang'
   "www.lang": "it"

9.4. How do I start a test?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This feature is implemented by the /api/runner API,
which accepts the following options:

test=string
 This is the name of the test to start.  If there is no
 name, this operation is basically a no-operation.

streaming=boolean
 When this is True, Neubot will write a copy of the logs
 generated by the test on the network socket, so that one
 can run a test from command line in the context of the
 server and see the logs on console.

Unless streaming is True, this API returns an empty
dictionary to keep jquery happy.

Currently, there is no feedback when there is no test
name, the test name is not known, or the test is known.
This is quite confusing and probably an error should
be returned in the first two cases::

 $ curl -s -o- 'http://127.0.0.1:9774/api/runner'
 {}
 $ curl -s -o- 'http://127.0.0.1:9774/api/runner?test=foo'
 {}
 $ curl -s -o- 'http://127.0.0.1:9774/api/runner?test=speedtest'
 {}

At this point a test is in progress and trying to run
another test will cause an error::

 $ curl -v -o- 'http://127.0.0.1:9774/api/runner?test=speedtest'
 * About to connect() to 127.0.0.1 port 9774 (#0)
 *   Trying 127.0.0.1... connected
 * Connected to 127.0.0.1 (127.0.0.1) port 9774 (#0)
 > GET /api/runner?test=speedtest HTTP/1.1
 > User-Agent: curl/7.19.7 (universal-apple-darwin10.0) libcurl/7.19.7 OpenSSL/0.9.8r zlib/1.2.3
 > Host: 127.0.0.1:9774
 > Accept: */*
 >
 < HTTP/1.1 500 A test is already in progress, try again later
 < Date: Tue, 27 Mar 2012 17:45:23 GMT
 < Content-Length: 46
 < Cache-Control: no-cache
 <
 * Connection #0 to host 127.0.0.1 left intact
 * Closing connection #0
 A test is already in progress, try again later$

Finally, this demonstrates the streaming feature.  Note
that all logs are passed thru, and it's up to the client
to filter out e.g. DEBUG logs::

 $ curl -s -o- 'http://127.0.0.1:9774/api/runner?test=speedtest&streaming=1'
 DEBUG state: test_latency ---
 DEBUG state: test_download ---
 DEBUG state: test_upload ---
 DEBUG state: test_name speedtest
 DEBUG * publish: statechange
 INFO * speedtest with http://neubot.mlab.mlab3.trn01.measurement-lab.org:9773/speedtest
 DEBUG * Connecting to (u'neubot.mlab.mlab3.trn01.measurement-lab.org', 9773) ...
 DEBUG ClientHTTP: latency: 36.5 ms
 DEBUG * Connection made (('192.168.0.33', 50192), ('194.116.85.237', 9773))
 DEBUG state: negotiate {}
 DEBUG * publish: statechange
 INFO * speedtest: negotiate in progress...
 DEBUG > GET /speedtest/negotiate HTTP/1.1
 DEBUG > Content-Length: 0
 DEBUG > Host: neubot.mlab.mlab3.trn01.measurement-lab.org:9773
 DEBUG > Pragma: no-cache
 DEBUG > Cache-Control: no-cache
 DEBUG > Date: Tue, 27 Mar 2012 17:42:56 GMT
 DEBUG > Authorization:
 DEBUG >
 DEBUG < HTTP/1.1 200 Ok
 ...
 DEBUG < HTTP/1.1 200 Ok
 DEBUG < Date: Tue, 27 Mar 2012 17:43:05 GMT
 DEBUG < Connection: close
 DEBUG < Cache-Control: no-cache
 DEBUG <
 INFO * speedtest: collect...done [in 67.6 ms]
 DEBUG * publish: testdone
 DEBUG state: idle {}
 DEBUG * publish: statechange

Neubot stops copying logs when the 'testdone' event is
generated.  This event should be generated at the end
of a test, whatever the result.

Streaming is a nice feature.  I would probably include
it in a specification because it allows for transparency
in the tool.  But I will leave it optional, so a tool
can choose whether to support it or not.  (Or it can be
implemented after some time, when the tool has become
stable).

9.5. How do I get debugging info?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get debugging information use the /api/debug API. Please
note that this is useful only to developers and the consistency
of the format is not guaranteed.

This is an example of a debug request and its output::

 $ curl -o- http://127.0.0.1:9774/api/debug
 {'WWW': '/usr/share/neubot/www',
  'notifier': {'_subscribers': {},
               '_timestamps': {'statechange': 1336727245277393,
                               'testdone': 1336727245277246}},
  'poller': {'readset': {5: listener at ('127.0.0.1', 9774)}, 'writeset': {}},
  'queue_history': [],
  'typestats': {'ABCMeta': 26,
                'BackendNeubot': 1,
                'BackendProxy': 1,
                'CDLL': 1,
                'CFunctionType': 5,
                'ClientRendezvous': 1,
                'CodecInfo': 5,
                'Config': 1,
                'ConfigDict': 1,
                'Context': 3,
                'DatabaseManager': 1,
                'Decimal': 6,
                'EmptyNodeList': 1,
                'Event': 5,
                'FileSystemPOSIX': 1,
                'Formatter': 1,
                'JSONDecoder': 3,
                'JSONEncoder': 3,
                'LazyImporter': 19,
                'LibraryLoader': 2,
                'Listener': 1,
                'Logger': 1,
                'Manager': 1,
                'MemoryError': 1,
                'Message': 3,
                'NegotiateServer': 1,
                'NegotiateServerBitTorrent': 1,
                'NegotiateServerSpeedtest': 1,
                'Notifier': 1,
                'NotifierBrowser': 1,
                'Profiler': 1,
                'PyCFuncPtrType': 8,
                'PyCPointerType': 2,
                'PyCSimpleType': 26,
                'PyDLL': 1,
                'Quitter': 2,
                'Random': 1,
                'RandomBlocks': 1,
                'RootLogger': 1,
                'RunnerCore': 1,
                'RunnerTests': 1,
                'RunnerUpdates': 1,
                'RuntimeError': 1,
                'Scanner': 3,
                'ServerAPI': 1,
                'ServerHTTP': 1,
                'ServerStream': 1,
                'SocketWrapper': 1,
                'SpeedtestServer': 1,
                'SpeedtestWrapper': 1,
                'SplitResult': 5,
                'State': 1,
                'StgDict': 37,
                'Task': 5,
                'TypeInfo': 10,
                'UUID': 4,
                'WeakSet': 78,
                '_Condition': 2,
                '_Event': 1,
                '_FuncPtr': 2,
                '_Helper': 1,
                '_Log10Memoize': 1,
                '_MainThread': 1,
                '_Printer': 3,
                '_RLock': 3,
                '_TemplateMetaclass': 1,
                '_local': 1,
                '_socketobject': 3,
                '_swapped_meta': 1,
                'abstractproperty': 4,
                'builtin_function_or_method': 841,
                'cell': 1,
                'classmethod': 29,
                'classmethod_descriptor': 20,
                'classobj': 103,
                'defaultdict': 5,
                'deque': 19,
                'dict': 984,
                'error': 1,
                'frame': 25,
                'frozenset': 21,
                'function': 3168,
                'generator': 1,
                'getset_descriptor': 382,
                'instance': 17,
                'instancemethod': 75,
                'itemgetter': 42,
                'list': 425,
                'listiterator': 2,
                'member_descriptor': 307,
                'method_descriptor': 697,
                'module': 235,
                'partial': 14,
                'property': 112,
                'set': 184,
                'staticmethod': 29,
                'traceback': 8,
                'tuple': 672,
                'type': 251,
                'weakref': 803,
                'wrapper_descriptor': 1214}}

9.6. Home page redirections
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The API /api/index is used to redirect the user to
/index.html or /privacy.html depending on whether he
has already set privacy permission or not.

This is an example of its usage::

 $ curl -o- http://127.0.0.1:9774/api/index
 <HTML>
  <HEAD>
   <TITLE>Found</TITLE>
  </HEAD>
  <BODY>
   You should go to <A HREF="/index.html">/index.html</A>.
  </BODY>
 </HTML>

Since in this case privacy permission was already set, we
are redirected to /index.html.

9.7. How do I force Neubot to exit?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To exit Neubot, the API /api/neubot can be used. When
Neubot's daemon get this request, it will exit immediately
from the poller's loop, without sending back a message.

Currently this is a cross-platform API, however in the future
we will use it only for Windows systems.

9.8. How do I track Neubot state?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO:: write this section

------------------------------------------------------------------------

..
.. Links
..

.. _`privacy policy`: https://github.com/neubot/neubot/blob/master/PRIVACY
.. _`Measurement Lab`: http://www.measurementlab.net/about
.. _`published on the web`: http://www.neubot.org/data
.. _M-Lab: http://www.measurementlab.net/about

.. _routers: http://en.wikipedia.org/wiki/Router_(computing)
.. _RFC3439: http://tools.ietf.org/html/rfc3439#section-2.1
.. _speedtest.net: http://www.speedtest.net

.. _`round trip time`: http://en.wikipedia.org/wiki/Round-trip_delay_time
.. _goodput: http://en.wikipedia.org/wiki/Goodput
.. _`BitTorrent peer-wire protocol`:
   http://www.bittorrent.org/beps/bep_0003.html

.. _`software application that runs automated tasks over the Internet`:
   http://en.wikipedia.org/wiki/Internet_bot
.. _`Wikipedia's article`: http://en.wikipedia.org/wiki/Network_neutrality

.. _roadmap: https://github.com/neubot/neubot/wiki/roadmap
.. _todo: https://github.com/neubot/neubot/wiki/todo
.. _`github's wiki`: https://github.com/neubot/neubot/wiki

.. _`release early, release often`:
 http://www.catb.org/esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html
.. _`github repository`: https://github.com/neubot/neubot

.. _`Simone Basso`: http://www.neubot.org/people#basso
.. _`Nexa Center for Internet & Society`: http://nexa.polito.it/
.. _`Antonio Servetti`: http://www.neubot.org/people#servetti
.. _`Federico Morando`: http://www.neubot.org/people#morando
.. _`Juan Carlos De Martin`: http://www.neubot.org/people#de_martin

.. _`people page`: http://www.neubot.org/people

.. _`GNU General Public License version 3`: http://www.neubot.org/copying

.. _Python: http://www.python.org/
.. _Ubuntu: http://www.ubuntu.com/
.. _Debian: http://www.debian.org/
.. _MacOSX: http://www.apple.com/macosx/
.. _Windows: http://windows.microsoft.com/
.. _`FreeBSD Ports Collection`: http://www.freshports.org/net/neubot
.. _`FreeBSD documentation`: http://www.freebsd.org/docs.html
.. _`FreeBSD manpages`: http://www.freebsd.org/cgi/man.cgi
.. _`FreeBSD ports mailing list`: http://lists.freebsd.org/mailman/listinfo/freebsd-ports
.. _`send-pr`: http://www.freebsd.org/send-pr.html
.. _FreeBSD: http://www.freebsd.org/
.. _OpenBSD: http://www.openbsd.org/

.. _`download page`: http://www.neubot.org/download

.. _`HTTP protocol`: http://en.wikipedia.org/wiki/HTTP

.. _`Politecnico di Torino (DAUIN)`: http://www.dauin.polito.it/
.. _`free software`: https://github.com/neubot/neubot/blob/master/COPYING

.. _`near our server`: http://en.wikipedia.org/wiki/TCP_tuning#Window_size
.. _`with a grain of salt`: http://en.wikipedia.org/wiki/Grain_of_salt
