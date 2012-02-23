1. General questions
--------------------

1.1. What is neubot?
~~~~~~~~~~~~~~~~~~~~

Neubot is a research project on network neutrality of the `NEXA Center
for Internet & Society <http://nexa.polito.it>`_ at `Politecnico
di Torino <http://www.dauin.polito.it>`_. The project is based on a
lightweight `open-source <http://www.neubot.org/copying>`_ program
that interested users can download and install on their computers. The
program runs in the background and periodically performs transmission
tests with some test servers and/or with other instances of the
program itself. These transmission tests probe the Internet using
various application level protocols. The program saves tests results
locally and uploads them on the project servers. The collected dataset
contains samples from various Providers and allows the Neubot project
to monitor network neutrality.

1.2. What is network neutrality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Network neutrality is the principle that the Internet should be neutral
with respect to kinds of applications, senders and destinations. In
other words, a network is neutral when routers_ forward packets using
a *first come, first served* strategy. And is not neutral when certain
packets receive a preferential treatment.

.. _routers: http://en.wikipedia.org/wiki/Router_(computing)

The ancient Internet was strictly neutral, because it was designed
to minimize the interaction between applications and the network
(see RFC3439_). This design choice allowed very fast packet switching
and enabled strong openness towards unforeseen uses of the Internet
Protocol. The result has been an extraordinary outburst of innovation,
and a level-playing field for citizens, associations and companies
worldwide.

.. _RFC3439: http://tools.ietf.org/html/rfc3439#section-2.1

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
the related debate and the various positions, refer to Wikipedia's
`article <http://en.wikipedia.org/wiki/Network_neutrality>`_.

1.3. Why *"the network neutrality bot"*?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The program is called *network neutrality bot* because it is a
`"software application that runs automated tasks over the
Internet" <http://en.wikipedia.org/wiki/Internet_bot>`_ in order to
quantify *network neutrality*.

1.4. Why is crucial to monitor network neutrality?
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

1.5. Why might I want to install Neubot?
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
local results with the aggregated results published on the Neubot site
and/or with results obtained using other tests, in order to achieve a
more in-depth understanding of the behavior of your home network and of
the behavior of your Provider.

If you are interested, don't hesitate to install it, because the success
of this research effort depends heavily on how much people installs the
Neubot.

1.6. What tests are implemented by the latest version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest version of Neubot implements the following transmission
tests:

-  **speedtest** This transmission test is inspired to the test of
   `Speedtest.net <http://www.speedtest.net>`_. It is a client-server
   test using HTTP that measures `round-trip time
   latency <http://en.wikipedia.org/wiki/Round-trip_delay_time>`_,
   upload, and download
   `goodput <http://en.wikipedia.org/wiki/Goodput>`_.

-  **bittorrent** This transmission test performs `round-trip time
   latency <http://en.wikipedia.org/wiki/Round-trip_delay_time>`_,
   download and upload `goodput <http://en.wikipedia.org/wiki/Goodput>`_
   client-server measurements emulating the `BitTorrent peer-wire
   protocol <http://www.bittorrent.org/beps/bep_0003.html>`_.

If you're interested, you can get more details on transmission tests in
the `technical
section <http://www.neubot.org/faq#technical-questions>`_.

1.7. What is the roadmap to Neubot/1.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot/1.0 will be able to perform client-server and peer-to-peer
transmission tests using various application level protocols. Very
briefly, we have divided the path to get to Neubot/1.0 into four steps:

#. implement a simple HTTP-based client-server transmission test;
#. implement a simple BitTorrent client-server transmission test;
#. amend the BitTorrent test to work in peer-to-peer mode;
#. implement more peer-to-peer tests for more protocols;

You can read more on our `roadmap </roadmap>`_ page.

1.8. When is the next release of Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The release process strives to `"release early, release
often" <http://www.catb.org/esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html>`_
to maximize feedback. The rule of thumb is that we update the `public
git repository </download#git>`_ very frequently and we try to deploy a
new release every month.

There are two type of releases: *patch releases* and *milestone
releases*. Patch releases include bug fixes for existing features and
add new experimental features. Typically, it takes a certain amount of
patch releases to stabilize experimental features. Milestone releases
are deployed when a set of features becomes stable. Please, refer to
`the roadmap </roadmap>`_ for the milestone plan.

1.9. What is your versioning policy?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Milestone releases increment the major (or minor) version number and set
to zero the least important version numbers. Patch releases increment
the patch version number. Therefore, 1.0.0 and 0.4.0 are milestone
releases, while 0.3.1 is a patch release.

1.10. What is the best version of Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best version of Neubot will always be the one with the highest
version number, e.g. 0.3.1 is better than 0.3.0. Patch releases might
include experimental features, but these features will not be enabled by
default until they graduate and become stable.

1.11. How long should I keep Neubot installed?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As long as possible. Neubot is not a limited-scope project but rather an
ongoing effort.

1.12. How much do you test Neubot before release?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We test milestone releases for one-two weeks before release. When patch
releases include experimental features, these will not be enabled by
default. They will be enabled by default after a couple of weeks of
testing.

1.13. Who develops Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot project lead is Simone Basso, a research fellow of the NEXA
Center for Internet & Society. He develops Neubot in collaboration with
and under the supervision of prof. Antonio Servetti, prof. Federico
Morando, and prof. Juan Carlos De Martin, of Politecnico di Torino.

See our `people </people>`_ page for more information.

1.14. Under what license is Neubot available?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We release Neubot under `GNU General Public License version
3 </copying>`_.

1.15. How much does Neubot cost?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Zero. Neubot is available for free.

2. Installing Neubot
--------------------

2.1. On what systems does neubot run?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot is written in `Python <http://www.python.org/>`_ and therefore
should run on all the systems supported by Python. However, you might
want to check our `ports </ports>`_ page to be sure that there are not
"porting" issues.

2.2. How do I install neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to `download page </download>`_ and follow instructions for your
operating system. We provide binary packages for `MacOS
X <http://www.apple.com/macosx/>`_,
`Windows <http://www.microsoft.com/windows/>`_,
`Debian <http://www.debian.org/>`_, and distributions based on Debian
(such as `Ubuntu <http://www.ubuntu.com/>`_). If there is not a binary
package for your system, you can still install Neubot from sources.

3. Using Neubot
---------------

3.1. Neubot installed. What should I do now?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Twice a month, you should check for updates (unless you installed the
Debian package, which automatically configures auto-updates). To check
for updates, you just need to open the `web
interface </documentation#web-ui>`_. If an update is available, you will
see a message like the one in the following screenshot. Click on the
link, follow instructions, and you're done.

|neubot update notification|
You might also want to compare the outcome of Neubot with the one of
`Speedtest.net <http://www.speedtest.net/>`_, and, possibly, with the
one of other `online speed
tests <http://voip.about.com/od/voipbandwidth/tp/topspeedtests.htm>`_.
We would appreciate it if you would share your results with us,
expecially in cases where Neubot results are different from the others.

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

|resources usage 1|
The second screenshot shows the amount of consumed resources (in
particular memory) when Neubot is idle.

|resources usage 2|
3.3. How do I report bugs, ask questions, make suggestions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To report bugs and ask questions, please use our mailing list. The
official languages for the mailing list are English and Italian.

Note that you MUST subscribe the mailing list first, because otherwise
your message WOULD NOT be accepted. To subscribe, go to:

::

      http://www.neubot.org/cgi-bin/mailman/listinfo/neubot

We advise you to search the public archive BEFORE posting a message,
because others might have already asked the same question or reported
the same bug. All posts to the mailing list are archived here:

::

      http://www.neubot.org/pipermail/neubot/

Thanks for your cooperation!

3.4. What are the issues if I use mobile broadband, 3G modem, Internet
key?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One possible issue with mobile broadband is the following. If you use
Windows, you installed Neubot, and you are not connected, and Neubot
starts a test, it's possible that Windows asks you to connect. If this
behavior annoys you, stop Neubot from the start menu.

* In future releases we plan to check whether there is an Internet
connection or not, and start a test only if it's available. *

3.5. Do I need to tweak the configuration of my router?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No.

3.6. How do I read Neubot logs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under all operating systems you can read logs via the *Log* tab of the
`web user interface <documentation#web-ui>`_, available since ``0.3.7``.
The following screenshot provides an example:

|neubot log|
When reporting bugs, it's often a good idea to include the logs. To get
logs in plain text format, point your browser to
``http://127.0.0.1:9774/api/log?debug=1`` (this URI works if and only if
Neubot is running on your machine). The following screenshot provides an
example:

|image5|
In addition, under UNIX Neubot saves logs with ``syslog(3)`` and
``LOG_DAEMON`` facility. Logs end up in ``/var/log``, typically in
``daemon.log``. When unsure, I run the following command (as root) to
lookup the exact file name:

::

    # grep neubot /var/log/* | awk -F: '{print $1}' | sort | uniq
    /var/log/daemon.log
    /var/log/syslog

In this example, there are interesting logs in both
``/var/log/daemon.log`` and ``/var/log/syslog``. Once I know the file
names, I can grep the logs out of each file, as follows:

::

    # grep neubot /var/log/daemon.log | less

3.7. Do I have to periodically rotate log files?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No: Under Windows there are no log files, while under UNIX the logging
subsystem should automatically rotate them.

3.8. Do I have to periodically rotate the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. Neubot database should grow slowly in space over time. (My
workstation database weights 2 MBytes after 8 months, and I frequently
run a test every 30 seconds for testing purpose.) To prune the database
run the following command (as root): ``neubot database prune``.

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

The *speedtest* test uses the `HTTP
protocol <http://en.wikipedia.org/wiki/HTTP>`_ and measures: `round-trip
latency <http://en.wikipedia.org/wiki/Round-trip_delay_time>`_, download
and upload `goodput <http://en.wikipedia.org/wiki/Goodput>`_. It is
inspired to `Speedtest.net <http://www.speedtest.net/>`_ test, hence the
name. The test estimates the round-trip latency measuring the time
required to connect and the average time to request and receive a
zero-length resource. It also estimates the download and upload goodput
dividing the number of bytes transferred by the time required to
transfer them.

4.3. How does Neubot change my Windows registry?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installer writes the following registry key, so that Windows is
aware of the uninstaller:

::

    HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"

The key is removed during the uninstall process.

4.4. What is the path of Neubot database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under UNIX, if you run Neubot as root the database path is
``/var/neubot/database.sqlite3``. Otherwise, if you run Neubot as an
ordinary user, the database path is ``$HOME/.neubot/database.sqlite3``.

Under Windows, the database path is always
``%APPDATA%\neubot\database.sqlite3``.

For Neubot >= 0.3.7 you can query the location of the database running
the following command: ``neubot database``, for example:

::

    $ neubot database info
    /home/simone/.neubot/database.sqlite3

    $ sudo neubot database info
    [sudo] password for simone: 
    /var/neubot/database.sqlite3

4.5. How can I dump the content of the database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can dump the content of the database using the command
``neubot database dump``. The output is a JSON file that contains the
results. (Note that under UNIX, you must be root in order to dump the
content of the system-wide database: If you run this command as an
ordinary user you will dump the user-specific database instead.)

4.6. What does *bittorrent* test measures?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *bittorrent* test emulates the `BitTorrent peer-wire
protocol <http://www.bittorrent.org/beps/bep_0003.html>`_ and measures:
`round-trip
latency <http://en.wikipedia.org/wiki/Round-trip_delay_time>`_, download
and upload `goodput <http://en.wikipedia.org/wiki/Goodput>`_. The test
estimates the round-trip latency measuring the time required to connect.
It also estimates the download and upload goodput.

Since BitTorrent uses small messages, it is not possible to transfer a
huge resource and divide the number of transmitted bytes by the time of
the transfer. So, the test initially makes many back to back requests to
fill the space between the client and the server of many flying
responses. The measurement starts only when the requester thinks there
are enough responses in flight to approximate a continuous transfer.

4.7. What does measuring goodput mean?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot tests DOES NOT measure the speed of your broadband Internet
connection, but rather the goodput, i.e. *the application-level
achievable speed in the moment of the measurement*. The result will
suffer if, for example:

#. you are downloading a large file;
#. your roommate is downloading a large file;
#. you have a bad wireless connection with high packet loss ratio;
#. there is congestion outside your provider network;
#. you don't live
   `near <http://en.wikipedia.org/wiki/TCP_tuning#Window_size>`_ our
   server;
#. our server is overloaded.

I.e. you must take Neubot results `cum grano
salis <http://en.wikipedia.org/wiki/Grain_of_salt>`_.

4.8. Is it possible to compare speedtest and bittorrent results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The bittorrent test was released in 0.4.0. At that time the comparison
was not always possible because the speedtest test used two connections
while the bittorrent one used only one, resulting in worst performances
with high-speed, high-delay and/or more congested network. Neubot 0.4.2
fixed this issue and modified speedtest to use just one connection.

This may not be enough: therefore, the speedtest will be further
modified to use small messages like the bittorrent one does. So we will
be more confident that they stress the network in a similar way, i.e.
with similarly sized packets in both directions. This improvement is to
be implemented before Neubot 0.5.0.

5. Privacy questions
--------------------

5.1. What personal data does Neubot collect?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot does not inspect your traffic, does not monitor the sites you
have visited, etc. Neubot use a tiny fraction of your network capacity
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
following command: ``neubot database regen_uuid``.

Future versions of Neubot will also monitor and collect information
regarding your computer load (such as the amount of free memory, the
average load, the average network usage). We will monitor the load to
avoid starting tests when you are using your computer heavily. We will
collect load data in order to consider the effect of the load on
results.

5.2. Will you publish my IP address?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It depends. By default we don't share your Internet address. But we
would like to do that, in order to share our results with other
researchers, to empower the research community at large. To do that we
need your explicit permission, to be compliant with European Union
privacy law. It's easy: just open the web interface, click on the
*Privacy* tab, `read the policy </privacy>`_, and give us the
permissions!

.. |image0| image:: /neubotfiles/flag-of-italy.png
.. |neubot update
notification| image:: http://www.neubot.org/neubotfiles/neubot-update-notification.png
.. |resources usage 1| image:: /neubotfiles/resources1.png
.. |resources usage 2| image:: /neubotfiles/resources2.png
.. |neubot log| image:: /neubotfiles/neubot-log.png
.. |image5| image:: /neubotfiles/neubot-log-text.png
