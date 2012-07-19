0. Index
--------

* `0. Index`_

* `1. General questions`_

   * `1.1. What is Neubot?`_
   * `1.2. What is Measurement Lab?`_
   * `1.3. What is network neutrality?`_
   * `1.4. Why "the network neutrality bot"?`_
   * `1.5. Why is crucial to monitor network neutrality?`_
   * `1.6. Why might I want to install Neubot?`_
   * `1.7. What tests are implemented by the latest version?`_
   * `1.8. What is the roadmap to Neubot/1.0?`_
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
   * `3.2. How much resources does Neubot need?`_
   * `3.3. How do I report bugs, ask questions, make suggestions?`_
   * `3.4. What are the issues if I use mobile broadband, 3G modem, Internet key?`_
   * `3.5. Do I need to tweak the configuration of my router?`_
   * `3.6. How do I read Neubot logs?`_
   * `3.7. Do I have to periodically rotate log files?`_
   * `3.8. Do I have to periodically rotate the database?`_

* `4. Technical questions`_

   * `4.1. How does Neubot work?`_
   * `4.2. What does speedtest test measures?`_
   * `4.3. How does Neubot change my Windows registry?`_
   * `4.4. What is the path of Neubot database?`_
   * `4.5. How can I dump the content of the database?`_
   * `4.6. What does bittorrent test measures?`_
   * `4.7. What does measuring goodput mean?`_
   * `4.8. Is it possible to compare speedtest and bittorrent results?`_

* `5. Privacy questions`_

   * `5.1. What personal data does Neubot collect?`_
   * `5.2. Will you publish my IP address?`_

* `6. Data questions`_

   * `6.1. Where are data published?`_
   * `6.2. Is there any license attached to data?`_
   * `6.3. What is data format?`_

* `7. Web user interface`_

   * `7.1. What is the web user interface?`_
   * `7.2. How do I open the web user interface?`_
   * `7.3. What does the status page shows?`_
   * `7.4. What does the speedtest page shows?`_
   * `7.5. What does the bittorrent page shows?`_
   * `7.6. What does the log page shows?`_
   * `7.7. What does the privacy page shows?`_
   * `7.8. What does the settings page shows?`_
   * `7.9. How do I change the web user interface language?`_

------------------------------------------------------------------------

1. General questions
--------------------

1.1. What is Neubot?
~~~~~~~~~~~~~~~~~~~~

Neubot is a research project on network neutrality of the `NEXA Center for
Internet & Society`_ at `Politecnico di Torino`_. The project is based on
a lightweight `open source`_ program that interested users can download
and install on their computers. The program runs in the background and
periodically performs transmission tests with test servers, hosted by
the distributed `Measurement Lab`_ platform, and (in future) with other
instances of the program itself.  Transmission tests probe the Internet
using various application level protocols and test results are saved both
locally and on the test servers.  The results dataset contains samples
from various Providers and is `published on the web`_, allowing anyone to
analyze the data for research purposes.

1.2. What is Measurement Lab?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measurement Lab (M-Lab_) is a distributed server platform that provides
connectivity and servers around the world for projects that aim to
measure the quality and/or neutrality of broadband Internet connections
by probing the network with active tests.

Starting from version 0.4.6, Neubot has become one of the projects hosted
at Measurement Lab, and, since version 0.4.8, most tests are carried
out by Measurement Lab servers.  Old clients are still served by Neubot
master server, but the percentage is fading.

1.3. What is network neutrality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Network neutrality is the principle that the Internet should be neutral
with respect to kinds of applications, senders and destinations. In
other words, a network is neutral when routers_ forward packets using
a *first come, first served* strategy. And is not neutral when certain
packets receive a preferential treatment.

The ancient Internet was strictly neutral, because it was designed
to minimize the interaction between applications and the network
(see RFC3439_). This design choice allowed very fast packet switching
and enabled strong openness towards unforeseen uses of the Internet
Protocol. The result has been an extraordinary outburst of innovation,
and a level-playing field for citizens, associations and companies
worldwide.

The modern Internet is not always neutral due to technologies that
allow for fine-grained discrimination of traffic. When they enter into
the network of an Internet Service Provider, packets may be classified,
i.e.  assigned to a class like *web*, *video*, or *file-sharing*. The
most commonly exploited characteristics in traffic classification
are the content of packets headers and the payload. But a packet can
also inherit the class from the flow it belongs to, if the flow is
already classified. Once a packet has been classified at the border,
it receives the service associated with its traffic class from routers
inside the network.

The policy debate regarding network neutrality is on whether it is
preferable to continue with *laissez-faire* or whether Internet
neutrality should be safeguarded by the law. The topic can be tackled
using a variety of disciplinary perspectives, such as the ones of
competition law and innovation processes. To know more about neutrality,
the related debate and the various positions, refer to `Wikipedia's
article`_.

1.4. Why *"the network neutrality bot"*?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The program is called *network neutrality bot* because it is a
`software application that runs automated tasks over the Internet`_
in order to quantify *network neutrality*.

1.5. Why is crucial to monitor network neutrality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitoring network neutrality is crucial because it enables a deeper
understanding of operators behavior. This is paramount *ex-ante*, i.e.
at a time when there is a broad discussion regarding changes in network
neutrality policies. The availability of quantitative datasets collected
by independent researchers should rebalance, at least in part, the deep
information asymmetry between Internet Service Providers and other
interested stakeholders (including regulators and citizens) and should
provide a more reliable basis for discussing policies.

Monitoring network neutrality is crucial in an *ex-post* scenario as
well. Indeed, it enables to verify operators behavior in light of
regulatory decisions regarding neutrality.

1.6. Why might I want to install Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You might want to install Neubot if you care about network neutrality,
you wish to support this research effort and are willing to donate
this project a fraction of your network capacity to run periodic
transmission tests. You will contribute to build a quantitative dataset
on network neutrality, and the availability of this independent dataset
will be arguably conducive to a more democratic decisional process
about the Internet, one of the key infrastructures of our societies.

Another reason why you might want to install Neubot is that test results
provide a brief picture of how your Internet connection is working, at
different hours and using different protocols. You can compare these
local results
with results obtained using other tests, in order to achieve a
more in-depth understanding of the behavior of your home network and of
the behavior of your Provider.

If you are interested, don't hesitate to install it, because the success
of this research effort depends heavily on how much people installs the
Neubot.

1.7. What tests are implemented by the latest version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest version of Neubot implements the following transmission
tests:

**Speedtest**
  This transmission test was originally inspired to the test of
  speedtest.net_, hence the name. It is an HTTP client-server test
  and measures `round trip time`_, download and upload goodput_.

**BitTorrent**
  This transmission test is a `BitTorrent peer-wire protocol`_
  client-server test and measures `round trip time`_, download and
  upload goodput_.

If you're interested, you can get more details on transmission tests in
the `4. Technical questions`_ section.

1.8. What is the roadmap to Neubot/1.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot/1.0 will be able to perform client-server and peer-to-peer
transmission tests using various application level protocols. At
the outset, we had divided the path to get to Neubot/1.0 into four
steps:

#. implement a simple HTTP-based client-server transmission test;
#. implement a simple BitTorrent client-server transmission test;
#. amend the BitTorrent test to work in peer-to-peer mode;
#. implement more peer-to-peer tests for more protocols.

Roadmap_ and TODO_ list are now updated and maintained using
`github's wiki`_.

1.9. When is the next release of Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The release process strives to `release early, release often`_ to
maximize feedback.  The `github repository`_ is updated very frequently
and there is a commitment to deploy a new release every month.

In general, most releases are *patch releases*, add new features and/or
correct bugs.  Typically, after a numer of patch releases, there is a
critical mass of new features, and a *milestone release* is issued.

The version numbering directly reflects the distinction between patch
and milestone releases, as explained by the next FAQ.

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
sources, you will not receive automatic updates).

If you are not using Windows, you should periodically make sure that
it automatically updated to the latest version.  As a rule of thumb, if
more than two weeks have passed since the last release and it has not
updated, then it's a bug.

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

3.2. How much resources does Neubot need?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot has a minimal impact on system and network load. It spends most
of its time asleep or waiting for its turn to perform a test. During a
test Neubot consumes a lot of system and network resources but the
program tries to guarantee that the test does not take not too much
time.

Here are a couple of screenshots captured from a netbook running Ubuntu
9.10 and attached to Politecnico di Torino network. In the first
screenshot you can see the resources usage during an on-demand test
invoked from the command line. The *init* phase of the test is the one
where Neubot generates the random data to send during the upload phase.
(The resources usage is much lower if you run the test at home, given
that Politecnico network is 5x/10x faster than most ADSLs.)

.. image:: http://www.neubot.org/neubotfiles/resources1.png
   :align: center

The second screenshot shows the amount of consumed resources (in
particular memory) when Neubot is idle.

.. image:: http://www.neubot.org/neubotfiles/resources2.png
   :align: center

3.3. How do I report bugs, ask questions, make suggestions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To report bugs and ask questions, please use our mailing list. The
official languages for the mailing list are English and Italian.

Note that you **must** subscribe the mailing list first, because otherwise
your message **would not** be accepted. To subscribe, go to:

      http://www.neubot.org/cgi-bin/mailman/listinfo/neubot

The mailing list subscription page does not have a valid SSL certificate
and your browser is likely to complain.  Don't be scared by that, it
is the page to register to Neubot mailing list, not your bank account.

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
prune old logs.  Under UNIX logs are also saved using ``syslog(3)``, which
should automatically rotate them.

3.8. Do I have to periodically rotate the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. Neubot database should grow slowly in space over time. (My
workstation database weights 2 MBytes after 8 months, and I frequently
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
program tries to guarantee that the test does not take not too much
time, as detailed below.

Periodically, Neubot downloads form the *Master Server* information on
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

As of version 0.4.2, Neubot uses to following algorithm to keep the test
duration bounded. The default amount of bytes to transfer is designed to
allow for reasonable testing time with slow ADSL connections. After the
test, Neubot adapts the number of bytes to be transferred by next test
so that the next test would take about five seconds, under current
conditions. Also, it repeats the test for up to seven times if the test
did not take at least three seconds.

*(Future versions of Neubot will implement peer-to-peer tests, i.e.
within instances of Neubot.)*

4.2. What does *speedtest* test measures?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *speedtest* test uses the `HTTP protocol`_ and measures: `round trip
time`_, download and upload goodput_. It was originally inspired to
speedtest.net_ test, hence the name. The test estimates the `round trip
time`_ measuring the time required to connect and the average time to
request and receive a zero-length resource. It also estimates the download
and upload goodput_ dividing the number of bytes transferred by the time
required to transfer them.

4.3. How does Neubot change my Windows registry?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installer writes the two following registry keys::

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

4.6. What does *bittorrent* test measures?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

I.e. you must take Neubot results `cum grano salis`_.

4.8. Is it possible to compare speedtest and bittorrent results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The bittorrent test was released in 0.4.0. At that time the comparison
was not always possible because the speedtest test used two connections
while the bittorrent one used only one, resulting in worst performances
with high-speed, high-delay and/or more congested network. Neubot 0.4.2
fixed this issue and modified speedtest to use just one connection.

This is not enough.  Before Neubot 0.5.0 more work is due to make the
behavior of the two tests much more similar, allowing for a fair comparison
of them.

------------------------------------------------------------------------

5. Privacy questions
--------------------

5.1. What personal data does Neubot collect?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot does not inspect your traffic, does not monitor the sites you
have visited, etc. Neubot use a fraction of your network capacity
to run periodic transmission tests and this tests either use random data
or data from our servers.

Neubot collects the Internet address of the computer where it is
running. We have to collect your Internet address (which is personal
data) because it tells us your Internet Service Provider and (roughly)
your location. Both information are functional to our goal of monitoring
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
For this reason, it asks you this permission during the installation,
if applicable, or during operation.  It goes without saying that it
will not start any test until you have read the privacy policy and
provided the permission to publish your Internet address.

One more reason why Neubot cannot run any test until you provide
the permission to publish your Internet address is that this is
also request by the policy of the distributed server platform that
empowers the Neubot Project, Measurement Lab (M-Lab_), which requires
all results to be released as open data.

For more information, please refer to the `privacy policy`_.

------------------------------------------------------------------------

6. Data questions
-----------------

6.1. Where are data published?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data is automatically harvested and published by Measurement Lab, as
explained here:

    http://www.measurementlab.net/data

The direct link to access Neubot data is:

    https://sandbox.google.com/storage/m-lab/neubot

The Neubot project publishes old data (collected before being accepted
into Measurement Lab) and plans to host recent Neubot results collected
by Measurement Lab at:

    http://www.neubot.org/data

6.2. Is there any license attached to data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot data is available under the terms and provisions of Creative
Commons Zero license as explained here:

    https://github.com/neubot/neubot/blob/master/data/LICENSE

6.3. What is data format?
~~~~~~~~~~~~~~~~~~~~~~~~~

Data is published in compressed tarballs, where each tarballs contains
all the results collected during a day by a test server.  Each result
is a text file that contains JSON-encoded dictionary, which is described
here:

    https://github.com/neubot/neubot/blob/master/data/README

Data published before the 27th January 2011 is published in different
format and this is explained better here:

    http://www.neubot.org/data

------------------------------------------------------------------------

7. Web user interface
---------------------

7.1. What is the web user interface?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The web user interface is a web-based interface that allows to
control **neubot** and show recent results.  By default, when
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

On **any platform**, of course, the user can open her favorite web
browser and point it to the following URI::

    http://127.0.0.1:9774/

7.3. What does the status page shows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *status* page (which is the default one) shows the status of Neubot,
and the result of the latest transmission test.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-status.png
   :align: center

7.4. What does the speedtest page shows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *speedtest* page shows the results of recent *speedtest* tests, i.e.
latency, download and upload goodput, both in graphical and in tabular
form.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-speedtest.png
   :align: center

7.5. What does the bittorrent page shows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *bittorrent* page shows the results of recent *bittorrent* tests, i.e.
latency, download and upload goodput, both in graphical and in tabular
form.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-bittorrent.png
   :align: center

7.6. What does the log page shows?
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

7.7. What does the privacy page shows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *privacy* page shows the privacy policy and allows to set privacy
permissions.  See `5. Privacy questions`_ section for more info.

.. image:: http://www.neubot.org/neubotfiles/faq-wui-privacy.png
   :align: center

7.8. What does the settings page shows?
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
.. _`NEXA Center for Internet & Society`: http://nexa.polito.it/
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

.. _`Politecnico di Torino`: http://www.dauin.polito.it/
.. _`open source`: https://github.com/neubot/neubot/blob/master/COPYING

.. _`near our server`: http://en.wikipedia.org/wiki/TCP_tuning#Window_size
.. _`cum grano salis`: http://en.wikipedia.org/wiki/Grain_of_salt
