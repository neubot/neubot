neubot
^^^^^^

The network neutrality bot
''''''''''''''''''''''''''

..
.. Copyright (c) 2010-2014
..     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
..     and Simone Basso <bassosimone@gmail.com>
..
.. This file is part of Neubot <http://www.neubot.org/>.
..
.. Neubot is free software: you can redistribute it and/or modify
.. it under the terms of the GNU General Public License as published by
.. the Free Software Foundation, either version 3 of the License, or
.. (at your option) any later version.
..
.. Neubot is distributed in the hope that it will be useful,
.. but WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
.. GNU General Public License for more details.
..
.. You should have received a copy of the GNU General Public License
.. along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
..

:Manual section: 1
:Date: 2013-10-14
:Manual group: Neubot manual
:Version: Neubot 0.4.17.0

SYNOPSIS
````````

|   **neubot** **--help**
|   **neubot** **-V**
|   **neubot** *subcommand* ...

DESCRIPTION
```````````

`Neubot`_ is a free-software Internet bot that gathers network performance
data useful to investigate network neutrality. Neubot runs in the
background and periodically performs active network tests with test
servers provided by `Measurement Lab`_ (a distributed server platform
that hosts open network measurement tools). Implemented tests are
described in the `IMPLEMENTED TESTS`_ section.

.. _`Neubot`: http://neubot.org/
.. _`Measurement Lab`: http://measurementlab.net/

Neubot does not perform any network test until you grant it the
permission to collect and publish your IP address for research
purposes. Neubot behaves like this because it is developed in the
European Union; therefore, it must comply with European privacy laws
(which consider IP addresses personal data). See the PRIVACY_
section for more info.

Neubot is a background process. You can control it by using its
subcommands, its web interface or its web API. Neubot
listens for web requests at ``http://127.0.0.1:9774/``. To access
the web interface, use either your favorite browser or the ``viewer``
subcommand. To change the address and/or port where Neubot listens
for web requests, edit ``/etc/neubot/api`` (see the `FILES`_
section).

Neubot runs with the privileges of the ``_neubot`` user,
or with the ones of the user indicated in the ``/etc/neubot/users``
configuration file (see the `FILES`_ section).

The command line interface allows you to get the usage string
(``neubot --help``), get the version number (``neubot -V``), and
run a Neubot's subcommand (``neubot subcommand...``). Those
are described in the `SUBCOMMANDS`_ section of this manual page.

IMPLEMENTED TESTS
`````````````````

All Neubot tests receive and send random data. Neubot does
not monitor the user's traffic.

Neubot implements four active network tests: ``bittorrent``, ``raw``,
``speedtest`` and ``dashtest``. For each test, there is a Neubot
subcommand that allows one to run the test immediately (see the
`SUBCOMMANDS`_ section). Moreover, Neubot
schedules one test at random every 23 - 27 minutes; the likelyhood
with which tests are selected is not equal for all tests, depending
on the Neubot release certain tests are selected more often.

The ``bittorrent`` test emulates BitTorrent peer-wire protocol and
estimates the round-trip time, the download and the upload goodput
(i.e. the application-level speed measured at the receiver). This test
always uses the closest-available Measurement-Lab server.
It uses the time that connect() takes to complete as an estimator of
the round-trip time. It estimates the goodput by dividing the amount of
transferred bytes by the elapsed time. To avoid consuming too much
user resources, the ``bittorrent`` test adapts the number of bytes to
transfer such that the test runs for about ten seconds.

The ``raw`` test performs a `raw` 10-second TCP download to estimate
the download goodput. It is called `raw` because it directly uses TCP
and it does not emulate any protocol. This test uses a random
Measurement-Lab server.
During the download, this test also collects statistics about the
TCP sender by using Web100 (see ``http://www.web100.org``), which is
installed on all Measurement Lab servers. In addition, this test
estimates the round-trip time in two ways: (1) by measuring the time
that connect() takes to complete (like ``bittorrent``) and (2) by
measuring the average time elapsed between sending a small request
and receiving a small response.

The ``speedtest`` test emulates HTTP and estimates the round-trip
time, the download and the upload goodput. This test always uses
the closest-available Measurement-Lab server. It estimates the round-trip
time in two ways: (1) by measuring the time that connect() takes
to complete (like ``bittorrent``) and (2) by measuring the average
time elapsed between sending a small request and receiving a small
response (like ``raw``). It estimates the goodput by dividing the
amount of transferred bytes by the elapsed time. To avoid consuming
too much user resources, the ``speedtest`` test adapts the number
of bytes to transfer such that the test runs for about ten seconds.

The ``dashtest`` test emulates the download of a video payload using
the Dynamic Adaptive Streaming over HTTP (DASH) MPEG standard. As
`raw` does, this test uses a random Measurement Lab server. This
test uses the following DASH rate-adaptation logic: at the beginning
of the test, the dashtest client requests the first segment
using the lowest bitrate representation. During the download of the
first segment, the client calculates the estimated available bandwidth
of the downloaded segment by dividing the size of such segment (in kbit)
by the download time (in seconds). Next, the Dashtest requests
the next segment using, in the common case, the representation rate
that is closer to the download speed of the current segment. This process
is, of course, repeated for all subsequent segments, thereby adapting
the requested bitrate representation to the download speed.

As said, the speedtest and the bittorrent tests use the closest-available
Measurement Lab server; the raw and the dashtest tests use, instead,
a random Measurement Lab server. As a consequence, it is normal
that the average speed measured with speedtest and bittorrent is
generally greater than the one measured with the other two tests (since
the measured speed depends on the latency).


SUBCOMMANDS
```````````

This section documents Neubot's subcommands.

**neubot bittorrent [-6fv] [-A address] [-p port]**
  Asks Neubot to run a bittorrent test using the web API and fails
  if Neubot is not running in the background.

  Accepts the following options:

  -6
    Prefer IPv6 to IPv4. This means that, if a server is available both
    via IPv6 and via IPv6, Neubot tries to connect to the IPv6 address first
    and falls back to IPv4 if IPv6 fails. If this option is not specified,
    IPv4 is tried first and IPv6 is used as a fallback.

  -A address
    Address of the remote test server.

  -f
    Force the test. Run the test in the local process context
    (instead of using the web API) and override privacy
    settings if needed. Useful for developers and for debugging.

  -p port
    Port of the remote test server.

  -v
    Makes the command more verbose.

**neubot dash [-6fv] [-A address] [-p port]**
  Asks Neubot to run a dashtest test using the web API and fails
  if Neubot is not running in the background.

  Accepts the following options:

  -6
    Prefer IPv6 to IPv4. This means that, if a server is available both
    via IPv6 and via IPv6, Neubot tries to connect to the IPv6 address first
    and falls back to IPv4 if IPv6 fails. If this option is not specified,
    IPv4 is tried first and IPv6 is used as a fallback.

  -A address
    Address of the remote test server.

  -f
    Force the test. Run the test in the local process context
    (instead of using the web API) and override privacy
    settings if needed. Useful for developers and for debugging.

  -p port
    Port of the remote test server.

  -v
    Makes the command more verbose.

**neubot database [-f database] [action]**
  Performs the specified ``action`` or prints the database's path
  if no action is specified.  We do not recommended to use this
  command to modify the database while Neubot is running, since
  Neubot does not expect the database to change while it is
  running, so it won't pick the changes up. This command requires
  ``root`` privileges to modify the database: if you are not
  ``root``, the database is opened in readonly mode.

  Accepts the following options:

  -f database
    Force file. Forces the command to use *database* instead of the default
    database path.

  Implements the following actions:

  delete_all
    Deletes all the results in the database.

  dump
    Dumps to the standard ouput the content of the database in JSON format.

  prune
    Removes results older than one year.

  regen_uuid
    Generates a new random unique identifier (or UUID) for Neubot. (See
    the `PRIVACY`_ section for more on the UUID).

  show
    Pretty prints to the standard ouput the content of the database
    in JSON format.

**neubot privacy [-Pt] [-D setting=value] [-f database]**
  Manage privacy settings. When invoked without
  options, this command prints the current privacy
  settings values.

  Accepts the following options:

  -D setting=value
    Turn on (nonzero) and off (zero) the specified privacy
    setting.

    This command just modifies the database: you have to
    restart Neubot to make changes effective. To modify privacy
    settings when Neubot is running, we recommend to use the
    web interface.

    Privacy settings:

    informed
      The user has read the privacy policy.

    can_collect
      The user provides the permission to collect his/her IP
      address for research purposes.

    can_publish
      The user provides the permission to publish his/her IP
      address allowing anyone to reuse it for research purposes.

  -f database
    Force file. Forces the command to use database instead of the
    default database path.

  -P
    Prints privacy policy on the standard output.

  -t
    Test.  Exits with success (exit value *0*) if all privacy
    settings all nonzero.  Exits with failure (exit value
    *nonzero*) if at least one setting is zero.

**neubot raw [-6fv] [-A address] [-p port]**
  Asks Neubot to run a raw test using the web API and fails if
  Neubot is not running in the background.

  Accepts the following options:

  -6
    Prefer IPv6 to IPv4. This means that, if a server is available both
    via IPv6 and via IPv6, Neubot tries to connect to the IPv6 address first
    and falls back to IPv4 if IPv6 fails. If this option is not specified,
    IPv4 is tried first and IPv6 is used as a fallback.

  -A address
    Address of the remote test server.

  -f
    Force the test. Run the test in the local process context
    (instead of using the web API) and override privacy
    settings if needed. Useful for developers and for debugging.

  -p port
    Port of the remote test server.

  -v
    Makes the command more verbose.

**neubot speedtest [-6fv] [-A address] [-p port]**
  Asks Neubot to run a speedtest test using the web API and fails
  if Neubot is not running in the background.

  Accepts the following options:

  -6
    Prefer IPv6 to IPv4. This means that, if a server is available both
    via IPv6 and via IPv6, Neubot tries to connect to the IPv6 address first
    and falls back to IPv4 if IPv6 fails. If this option is not specified,
    IPv4 is tried first and IPv6 is used as a fallback.

  -A address
    Address of the remote test server.

  -f
    Force the test. Run the test in the local process context
    (instead of using the web API) and override privacy
    settings if needed. Useful for developers and for debugging.

  -p port
    Port of the remote test server.

  -v
    Makes the command more verbose.

**neubot start**
  On MacOS this command runs launchctl(1), which in turn starts
  Neubot. You must be ``root`` to run this command.  On MacOS, Neubot's
  installer configures the system to launch Neubot at startup; i.e.
  you do not typically need to run this command.

  (On MacOS, Neubot is implemented by two daemons: the usual unprivileged
  daemon and a privileged daemon. The latter controls the former and
  periodically forks an unprivileged child to check for updates.)

  On MacOS, the start command accepts the following options:

  -a
    Auto-updates. When this flag is specified, the privileged
    daemon periodically forks an unprivileged child to check
    for updates.

  -d
    Debug. When this flag is specified, Neubot runs in
    the foreground.

  -v
    Verbose. When this flag is specified, the start command
    is verbose (i.e. it prints on the standard error
    the commands it is about to invoke).

    When both -v and -d are specified, Neubot runs in verbose mode
    in the foreground.

  At boot time, launchctl(1) starts Neubot with the -a and -d
  command line options.

  On other UNIX systems, the start command forks the Neubot daemon,
  which drops ``root`` privileges and runs in the background.  On such
  systems, this command does not accept any command line option.

**neubot status**
  This command asks the status of Neubot using the web API.  It
  returns 0 if connect() succeeds and the response is OK, nonzero
  otherwise.

  On MacOS this command accepts the ``-v`` option, which makes it
  more verbose. On other UNIX systems, it does not accept any
  command line option.

**neubot stop**
  On MacOS, this command runs launchctl(1), which in turn stops
  Neubot. You must be ``root`` to run this command. On MacOS, this
  command accepts the ``-v`` option, which makes it more verbose.

  On other UNIX systems, this command uses the web
  API to request Neubot to exit.

**neubot viewer**
  This command shows the web interface by embedding a web
  rendering engine into a window manager's window. Currently,
  the only implemented ``viewer`` is based on ``python-webkit``
  and ``pygtk``.

FILES
`````

Assuming that Neubot is installed at ``/usr/local``, this is the
list of the files installed.

**/etc/neubot/api**
  Configuration file that indicates the endpoint where Neubot should
  listen for web API requests. Example (which also shows the syntax
  and indicates the default values)::

    #
    # /etc/neubot/api - controls address, port where Neubot listens
    # for incoming web API requests.
    #
    address 127.0.0.1  # Address where the listen
    port 9774          # Port where to listen


**/etc/neubot/users**
  Configuration file that indicates the unprivileged user names
  that Neubot should use. Example (which also shows the syntax
  and indicates the default values)::

    #
    # /etc/neubot/users - controls the unprivileged user names used
    # by Neubot to perform various tasks.
    #
    update_user _neubot_update  # For auto-updates (MacOS-only)
    unpriv_user _neubot         # For network tests

**/usr/local/bin/neubot**
  The Neubot executable script.

**/usr/local/share/neubot/**
  Location where Neubot Python modules are installed.

**/usr/local/share/neubot/www/**
  Location where the web interface files are installed. The web interface
  is described in the `WEB INTERFACE FILES`_ section.

**/var/lib/neubot**
  System-wide directory where results are saved on Linux systems.
  This contains `database.sqlite3` and possibly other files containing the
  results of some tests; as of this writing dashtest uses Python's
  pickle format to save data, while other tests use the sqlite3 database.

**/var/neubot/**
  System-wide results database for other Unix-like systems such as MacOS
  and other BSD systems.
  This contains `database.sqlite3` and possibly other files containing the
  results of some tests; as of this writing dashtest uses Python's
  pickle format to save data, while other tests use the sqlite3 database.

EXAMPLES
````````

In this section, we represent the unprivileged user prompt with ``$``
and the ``root`` user prompt with ``#``.

Run on-demand bittorrent test::

    $ neubot bittorrent

Run on-demand raw test::

    $ neubot raw

Run on-demand speedtest test::

    $ neubot speedtest

Run on-demand dashtest test::

    $ neubot dash

Start Neubot::

    # neubot start

Stop Neubot::

    # neubot stop  # MacOS
    $ neubot stop  # other UNIX

Run Neubot in the foreground with verbose logging::

    # neubot start -dv                       # MacOS
    $ neubot agent -v -D agent.daemonize=no  # other UNIX

Export Neubot results to JSON::

    $ neubot database dump > output.json

Read Neubot's privacy policy::

    $ neubot privacy -P

Run Neubot ``command`` from the sources directory (useful for
developing Neubot)::

    $ ./UNIX/bin/neubot command

WEB INTERFACE FILES
```````````````````

Here we provide a brief description of the core files of the web
interface:

**css/**
  Directory that contains CSS files.

**favicon.ico**
  Neubot's favicon.

**footer.html**
  Common footer for all web pages (Neubot uses server-side includes).

**header.html**
  Common header for all web pages (Neubot uses server-side includes).

**img/**
  Directory that contains images.

**js/**
  Directory that contains javascript files. In addition to jQuery and
  jqPlot, it contains the following scripts:

  **js/contrib.js**
    Helper functions from many authors.

  **js/i18n.js**
    Implementation of web user interface internationalization (aka i18n).

  **js/index.js**
    Contains functions to retrieve and process the state of Neubot.

  **js/log.js**
    Contains code to retrieve and process Neubot logs.

  **js/privacy.js**
    Contains code to query and modify privacy settings.

  **js/results.js**
    Contains code to process Neubot results, as well as code to display
    them as plots and tables.

  **js/settings.js**
    Contains code to retrieve and modify Neubot settings.

  **js/state.js**
    Helper code for retrieving and processing Neubot state.

  **js/update.js**
    Minimal script included by updater.html. It just sets the active
    tab in the web interface.

  **js/utils.js**
    Miscellaneous helper functions.

**lang/**
  Directory that contains one javascript file for each language in which
  the web interface is translated. Each of these javascripts contains
  a dictionary, named ``LANG``, that maps a string (or a key representing
  a string) to its translation.

  In javascript, you mark strings for translation by wrapping them
  with ``i18n.get()`` calls. For example, to indicate that the string
  "Disable automatic tests" should be translated, you should write::

    ...
    i18n.get("Disable automatic tests");

  In HTML code, you mark the content of an HTML tag for translation by adding
  the tag to the ``i18n`` class. Differently from javascript, we don't map
  the content of an HTML tag to its translation; instead, we map a key that
  represents the HTML tag content to its translation. The key is another HTML
  class, which must start with ``i18n_``, as in the following example::

    ...
    <p class="i18n i18n_foobar">Neubot web interface</p>

  To translate the two examples above in, for example, Italian you
  edit the ``www/lang/it.css`` file and add::

    var LANG = {
        ...
        "Disable automatic tests": "Disabilita test automatici",
        "i18n_foobar": "Interfaccia web di Neubot",
        ...
    };

**log.html**
  Shows Neubot logs.

**not_running.html**
  Page displayed when Neubot is not running.

**privacy.html**
  Shows, and allows to modify, privacy settings.

**results.html**
  The results page, dynamically filled by javascript using Neubot web
  API. It allows you to see the results of recent experiments, both
  in form of plots and tables.

**settings.html**
  Shows (and allows to modify) Neubot settings.

**test/**
  Directory that contains a ``foo.html`` and a ``foo.json`` file for
  each test ``foo``. The list of available tests in ``results.html`` is
  automatically generated from the files in this directory.

  **test/foo.html**
    Description of the ``foo`` test. It is included into the
    ``results.html`` page when the test is selected.

  **test/foo.json**
    Description of the plots and tables included into ``results.html``
    when test ``foo`` is selected. The format of the JSON is documented
    into the `WEB API`_ section of this manual page.

  **test/foo.json.local**
    When ``foo.json.local`` exists, Neubot will use it (instead of
    ``foo.json``) to prepare plots and tables in ``results.html``.
    Allows the user to heavily customize the results page for test
    ``foo``.

**update.html**
  Page displayed on Windows when Neubot needs to be manually
  updated. Now that automatic updates are implemented, it
  should never pop up.

WEB API
```````

To access Neubot API, you send HTTP requests to the address and port
where Neubot is listening (which is ``127.0.0.1:9774`` by default, and
which can be changed by editing ``/etc/neubot/api``).

Here is a detailed description of each API.

**/api**
  This API is an alias for ``/api/``.

**/api/**
  This API allows you to get (``GET``) the list of available APIs,
  encoded as a JSON.

  Returned JSON example::

    [
     "/api",
     "/api/",
     "/api/config",
     "/api/data",
     "/api/debug",
     "/api/exit",
     "/api/index",
     "/api/log",
     "/api/results",
     "/api/runner",
     "/api/state",
     "/api/version"
   ]

**/api/config[?options]**
  This API allows to you get (``GET``) and set (``POST``) the variables
  that modify the behavior of Neubot.

  ``GET`` returns a dictionary, encoded using JSON, that maps each variable
  to its value.  ``POST`` sends a url-encoded string, which contains one
  or more ``variable=new_value`` atoms separated by ``&``.

  The API accepts the following query-string options:

  **debug=integer [default: 0]**
    When nonzero, the API returns a pretty-printed JSON. Otherwise, the
    JSON is serialized on a single line.

  **labels=integer [default: 0]**
    When nonzero, returns the description of the variables instead of their
    values.

  Returned JSON example::

    {
     "enabled": 1,
     "negotiate.max_thresh": 64,
     "negotiate.min_thresh": 32,
     "negotiate.parallelism": 7,
     "privacy.can_collect": 1,
     "privacy.can_publish": 1,
     "privacy.can_informed": 1,
     ...
     "uuid": "0964312e-f451-4579-9984-3954dcfdeb42",
     "version": "4.2",
     "www.lang": "default"
    }

  We have not standardized variable names yet. Therefore, we don't provide
  here a list of variable names, types, and default values.

**/api/data?test=string[&options]**
  This API allows you to retrieve (``GET``) the data collected during Neubot
  tests.  As we have a single API for all tests, you must provide the test
  name using the query string.

  This API returns a JSON that serializes a list of dictionaries, in which
  each dictionary is the data collected during a test. There is a section of
  this manual page describing the data format of each implemented test.

  This API accepts the following query-string parameters:

  **debug=integer [default: 0]**
    When nonzero, the API returns a pretty-printed JSON. Otherwise, the
    JSON is serialized on a single line.

  **since=integer [default: 0]**
    Returns only the data collected after the specified time (indicated
    as the number of seconds elapsed since midnight of January,
    1st 1970).

  **test=string**
    This parameter is mandatory and specifies the test whose data you
    want to retrieve.

  **until=integer [default: 0]**
    Returns only the data collected before the specified time (indicated
    as the number of seconds elapsed since midnight of January,
    1st 1970).

**/api/debug**
  This API allows you to get (``GET``) text/plain information about Neubot
  internals, which is typically useful for debugging purposes. As such,
  the consistency of the output format is not guaranteed.

  Returned text example::

    {'WWW': '/usr/share/neubot/www',
     'notifier': {'_subscribers': {},
               '_timestamps': {'statechange': 1336727245277393,
                               'testdone': 1336727245277246}},
     'queue_history': [],
     'typestats': {'ABCMeta': 26,
                   'BackendNeubot': 1,
                   'BackendProxy': 1,
                   ...
                  }}

**/api/exit**
  When this API is invoked, Neubot exits immediately (i.e. without
  sending any response).

  Don't use this API to shut down Neubot on MacOS, use the ``neubot
  stop`` command instead. This API, in fact, has effect on the unprivileged
  Neubot process only, and the privileged process will respawn the
  unprivileged process once it notices it died.

**/api/index**
  This API uses ``302 Found`` and ``Location`` to redirect the
  caller to either ``index.html`` (if privacy settings are OK)
  or on ``privacy.html`` (if privacy settings are not OK).

**/api/log[?options]**
  This API allows you to get (``GET``) Neubot logs, as a list of
  dictionaries. Each dictionary represents a log record and contains
  the following fields:

  **timestamp (integer)**
    Time when this log was generated, expressed as number of seconds
    elapsed since midnight of January, 1st 1970.

  **severity (string)**
    The log message severity; one of: ``DEBUG``, ``INFO``, ``WARNING``,
    and ``ERROR``.

  **message (string)**
    The log message string.

  This API accepts the following query-string options:

  **debug (int) [default: 0]**
    If nonzero, the API formats logs like they are printed on the
    system logger (i.e. as a text/plain sequence of lines). Otherwise,
    the API returns the JSON list of dictionaries described above.

  **reversed (int) [default: 0]**
    If nonzero logs are reversed (i.e. the most recent log record is
    the first element of the list). Otherwise logs are returned in
    natural order (the most recent log record is the last element of
    the list).

  **verbosity (int) [default: 1]**
    When the verbosity is less than 1, only ``ERROR`` and ``WARNING``
    messages are returned. When the verbosity is 1, the API returns
    also ``INFO`` messages. When the verbosity is greater than 1,
    the API returns also ``INFO`` and ``DEBUG`` messages.

  Returned JSON example::

   [
    {
     "message": "raw_negotiate: not reached final state",
     "severity": "WARNING",
     "timestamp": 1366195042
    },
    {
     "message": "raw_negotiate: bad response",
     "severity": "ERROR",
     "timestamp": 1366236483
    },
    {
     "message": "raw_negotiate: not reached final state",
     "severity": "WARNING",
     "timestamp": 1366236484
    }
   ]


**/api/results?test=string[&options]**
  This API allows the web interface to get (``GET``) information on how to
  format results. It returns a dictionary, encoded as JSON, that indicates
  the plots and the tables to be generated in the ``results.html`` page for the
  *selected test* (which is either the test specified via query string or
  the default test, speedtest, if none was specified).

  The dictionary for test ``foo`` is generated using ``www/test/foo.json`` (or
  ``www/test/foo.json.local``) as template and contains the following fields:

  **available_tests (list of strings)**
    List that contains the name of all the available tests.

  **description (string)**
    String that contains a long description of the selected test. This is
    the content of ``www/test/foo.html``.

  **plots (list of dictionaries)**
    List of dictionaries. Each dictionary contains the instructions to
    generate a plot:

    **datasets (list of dictionaries)**
      List of dictionaries. Each dictionary contains the instructions to
      plot one serie of data:

      **label (string)**
        Label to use in the legend.

      **marker (string)**
        Indicates the marker to use, either ``circle`` or ``square``.

      **recipe (list)**
        LISP-like code that describes how to generate one point on the Y
        axis from one row of the selected test's data. We describe this
        lisp-like language in the `DATA PROCESSING LANGUAGE`_ section of
        this manual page.

    **title (string)**
      Title of the plot.

    **xlabel (string)**
      Label for the X axis.

    **ylabel (string)**
      Label for the Y axis.

  **selected_test**
    The selected test name.

  **table (list of dictionaries)**
    List of dictionaries. Each dictionary is one column of the table
    to be added to ``results.html``:

    **label (string)**
      Label of the column header.

    **recipe (list)**
      LISP-like code that describes how to generate the value of the
      current column in the table from one row of the selected test's
      data. We describe this lisp-like language in the `DATA PROCESSING
      LANGUAGE`_ section of this manual page.

  **title (string)**
    The title of the test (e.g. 'BitTorrent test').

  **www_no_description (integer)**
    Whether to include a description of the test in the results page (zero)
    or not (nonzero).

  **www_no_legend (integer)**
    Whether to include a legend in the plots (zero) or not (nonzero).

  **www_no_plot (integer)**
    Whether to generate plots (zero) or not (nonzero).

  **www_no_split_by_ip (integer)**
    Whether to split the selected test's data by IP and plot a different line
    for each IP (zero) or not (nonzero).

  **www_no_table (integer)**
    Whether to generate a table that contains the selected test's data (zero)
    or not (nonzero).

  **www_no_title (integer)**
    Whether to include the title of the test in the results page (zero)
    or not (nonzero).

  The API accepts the following query-string options:

  **debug=integer [default: 0]**
    When nonzero, the API returns a pretty-printed JSON. Otherwise,
    the JSON is serialized on a single line.

  **test=string**
    This parameter is mandatory and specifies the selected test.

  Returned JSON example::

   {
    "available_tests": [
        "raw",
        "speedtest",
        "bittorrent"
    ],
    "description": "...",
    "www_no_split_by_ip": 0,
    "title": "Your recent Speedtest results",
    "www_no_legend": 0,
    "selected_test": "speedtest",
    "www_no_plot": 0,
    "www_no_table": 0,
    "table": [
        {
            "recipe": ["to-datetime",
                        ["select", "timestamp", "result"]],
            "label": "Timestamp"
        },
        {
            "recipe": ["select", "internal_address", "result"],
            "label": "Internal address"
        },
        {
            "recipe": ["select", "real_address", "result"],
            "label": "Real address"
        },
        {
            "recipe": ["select", "remote_address", "result"],
            "label": "Remote address"
        },
        {
            "recipe": ["to-millisecond-string",
                        ["select", "connect_time", "result"]],
            "label": "Connect time"
        },
        {
            "recipe": ["to-millisecond-string",
                        ["select", "latency", "result"]],
            "label": "Appl. latency"
        },
        {
            "recipe": ["to-speed-string",
                        ["select", "download_speed", "result"]],
            "label": "Download speed"
        },
        {
            "recipe": ["to-speed-string",
                        ["select", "upload_speed", "result"]],
            "label": "Upload speed"
        }
    ],
    "www_no_description": 0,
    "plots": [
        {
            "datasets": [
                {
                    "marker": "circle",
                    "recipe": ["to-speed",
                                ["select", "download_speed",
                                 "result"]],
                    "label": "Dload"
                },
                {
                    "marker": "square",
                    "recipe": ["to-speed",
                                ["select", "upload_speed",
                                 "result"]],
                    "label": "Upload"
                }
            ],
            "ylabel": "Goodput (Mbit/s)",
            "xlabel": "Date",
            "title": "Download and upload speed"
        },
        {
            "datasets": [
                {
                    "marker": "circle",
                    "recipe": ["to-millisecond",
                                ["select", "latency", "result"]],
                    "label": "Appl. latency"
                },
                {
                    "marker": "square",
                    "recipe": ["to-millisecond",
                                ["select", "connect_time",
                                 "result"]],
                    "label": "Connect time"
                }
            ],
            "ylabel": "Delay (ms)",
            "xlabel": "Date",
            "title": "Connect time and latency"
        }
    ],
    "www_no_title": 0
   }

**/api/runner?test=string[&options]**
  This API allows the caller to schedule a test for immediate
  execution. If a test is already running the API returns an
  error ``500``, otherwise it returns ``200``.

  The API accepts the following query-string options:

  **test=string**
    This option is mandatory and indicates the name of the test
    that Neubot should schedule for execution.

  **streaming=integer [default: 0]**
    When nonzero, Neubot streams logs generated during the test in the
    response body and closes the connection when the test is complete.
    Otherwise, the response body is an empty dictionary.

    When you invoke tests from the command line (e.g. ``neubot
    bittorrent``), *streaming* is the feature that allows to print logs
    generated by the test on the console.

  Returned JSON example::

   {}

  Returned text example::

   1366299354 [INFO] runner_core: Need to auto-discover first...
   1366299355 [INFO] runner_mlabns: server discovery...
   1366299356 [INFO] runner_mlabns: server discovery... done
   1366299356 [INFO] raw_clnt: connection established with ...
   1366299356 [INFO] raw_clnt: connect_time: 13.6 ms
   1366299357 [INFO] raw_clnt: sending auth to server...
   1366299357 [INFO] raw_clnt: sending auth to server... done
   1366299357 [INFO] raw_clnt: receiving auth from server...
   1366299357 [INFO] raw_clnt: receiving auth from server... done
   1366299357 [INFO] raw_clnt: estimating ALRTT...
   1366299357 [INFO] raw_clnt: alrtt_avg: 14.3 ms
   1366299357 [INFO] raw_clnt: estimating ALRTT... done
   1366299357 [INFO] raw_clnt: raw goodput test...
   1366299367 [INFO] raw_clnt: raw goodput test... done
   1366299367 [INFO] raw_clnt: goodput: 65.5 Mbit/s

**/api/state[?options]**
  This API allows you to get (``GET``) and track (via comet) the state
  of Neubot. The API returns a dictionary with the following fields:

  **current=string**
    The name of the current state; one of: ``idle``, ``rendezvous``,
    ``negotiate``, ``test``, and ``collect``.

  **events=dictionary**
    A dictionary that maps the name of an event (a string) to the most
    recent value related to such event (a string, an integer, a list,
    or a dictionary).

    While running, Neubot generates a limited set of events, which drive
    the web interface. For example, the ``test_download`` event value
    is used to update the download speed in the right
    sidebar of the web interface.

    The list of generated events is not standardized yet, so we don't
    provide it here.

  **t=integer**
    The identifier of the current event.

  The API accepts the following query-string options:

  **debug=integer [default: 0]**
    When nonzero, the API returns a pretty-printed JSON. Otherwise,
    the JSON is serialized on a single line.

  **t=integer**
    When this option is present, Neubot does not return a response until
    the next event after the one identified by ``integer`` is fired (or
    until a timeout expires). This behavior allows to implement the comet
    pattern and to timely update the web interface with low overhead.

**/api/version**
  This API allows you to get (``GET``) the version number of Neubot, in
  ``text/plain`` format.

  Returned text example::

   0.4.15.7

BitTorrent data format
``````````````````````

We represent the data collected by the ``bittorrent`` test with a
dictionary that contains the following fields:

**connect_time (float)**
  RTT estimated by measuring the time that connect() takes
  to complete, measured in seconds.

**download_speed (float)**
  Download speed measured by dividing the number of received bytes by
  the elapsed download time, measured in bytes per second.

**internal_address (string)**
  Neubot's IP address, as seen by Neubot. It is typically either
  an IPv4 or an IPv6 address.

**neubot_version (string)**
  Neubot version number, encoded as a floating point number and
  printed into a string. Given a version number in the format
  ``<major>.<minor>.<patch>.<revision>``, the encoding is as follows::

    <major> + 1e-03 * <minor> + 1e-06 * <patch>
            + 1e-09 * <revision>

  For example, the ``0.4.15.3`` version number
  is encoded as ``0.004015003``.

**platform (string)**
  The operating system platform, e.g. ``linux2``, ``win32``.

**privacy_can_collect (integer)**
  The value of the ``can_collect`` privacy setting.

**privacy_can_publish (integer)**
  The value of the ``can_publish`` privacy setting.

**privacy_informed (integer)**
  The value of the ``informed`` privacy setting.

**real_address (string)**
  Neubot's IP address, as seen by the server. It is typically either
  an IPv4 or an IPv6 address.

**remote_address (string)**
  The server's IP address. It is typically either an IPv4 or an
  IPv6 address.

**timestamp (integer)**
  Time when the test was performed, expressed as number of seconds
  elapsed since midnight of January, 1st 1970.

**upload_speed (float)**
  Upload speed measured by dividing the number of sent bytes by the
  elapsed upload time, measured in bytes per second.

**uuid (string)**
  Random unique identifier of the Neubot instance, useful to perform
  time series analysis.

Example::

   [
    {
     "connect_time": 0.003387928009033203,
     "download_speed": 4242563.145733707,
     "internal_address": "130.192.91.231",
     "neubot_version": "0.004015007",
     "platform": "linux2",
     "privacy_can_collect": 1,
     "privacy_can_publish": 1,
     "privacy_informed": 1,
     "real_address": "130.192.91.231",
     "remote_address": "194.116.85.224",
     "test_version": 1,
     "timestamp": 1366045628,
     "upload_speed": 4231443.875881268,
     "uuid": "7528d674-25f0-4ac4-aff6-46f446034d81"
    },
    ...

Dashtest data format
````````````````````

The dashtest format depends on whether your are looking at its results
from a Neubot instance or whether you are looking at data collected on the
server-side and made available by Measurement Lab.

The basic piece of information saved during the dashtest consists of the
*per_segment* dictionary, which contains the results of the download of a
single segment of data during the test (recall that the test downloads
several segments of data)::

    {
        "connect_time": 0.21549296379089355,
        "delta_sys_time": 0.0,
        "delta_user_time": 0.01999999999998181,
        "elapsed": 1.557049036026001,
        "elapsed_target": 2,
        "internal_address": "130.192.91.215",
        "iteration": 1,
        "platform": "linux2",
        "rate": 2500,
        "real_address": "130.192.91.215",
        "received": 625130,
        "remote_address": "196.24.45.160",
        "request_ticks": 1413299395.564522,
        "timestamp": 1413299397,
        "uuid": "e4cd449a-f703-4c6a-a271-f0cea350d723",
        "version": "0.004016009",
    }

This is the meaning of the above fields:

**connect_time (float)**
  RTT estimated by measuring the time that connect() takes
  to complete, measured in seconds. This piece of data is
  collected before the test, and (yes, this is confusing) is
  repeated in each dictionary.

**delta_user_time (float)**
  The time spent by the current process in userland during
  the download of the current segment.

**delta_sys_time (float)**
  The time spent by the current process in kernel-land during
  the download of the current segment.

**elapsed (float)**
  Time elapsed since the beginning of the download to the end of
  the download of this segment.

**elapsed_target (float)**
  Target elapsed time for the download of the current segment. In the
  current implementation it is a constant set to two seconds.

**internal_address (string)**
  Neubot's IP address, as seen by Neubot. It is typically either
  an IPv4 or an IPv6 address. This is of course constant within the test.

**iteration (int)**
  Index of this segment within the test; currently 15 segments
  are downloaded during the dashtest.

**platform (string)**
  Name of the operating system platform (e.g., `linux`).

**rate (float)**
  This is the bitrate of the segment currently being downloaded. This is
  chosen by the test and adjusted depending on the download speed of
  the previous segment so that the download of this segment should take
  about two seconds (the elapsed_target).

  Note that, if the download of the previous segment took more than two
  seconds, the rate of the next segment is reduced, because it is assumed
  that the download took more than two seconds due to congestion.

**real_address (string)**
  Neubot's IP address, as seen by the server. It is typically either
  an IPv4 or an IPv6 address.

**received (int)**
  Size of the current segment in bytes, also including HTTP metadata (i.e.,
  response line and headers). You can compute the download speed by
  dividing this by elapsed.

**remote_address (string)**
  The server's IP address. It is typically either an IPv4 or an
  IPv6 address.

**request_ticks (float)**
  Time when the request for the current segment
  was sent. This may not be a timestamp relative
  to the Unix epoch. Add elapsed to this to get the time when the response
  was received (again not necessarily a timestamp).

**timestamp (int)**
  Timestamp relative to the Unix epoch of when the response was received.

**uuid (string)**
  Random unique identifier of the Neubot instance, useful to perform
  time series analysis.

**version (string)**
  Neubot version number, encoded as a floating point number and printed
  into a string. Given a version number in the format
  <major>.<minor>.<patch>.<revision>, the encoding is as follows::

    <major> + 1e-03 * <minor> + 1e-06 * <patch>
            + 1e-09 * <revision>

  For example, the `0.4.15.3` version number is encoded as `0.004015003`.

The following example shows the results of a test as collected on
the client side. To help the reader, we only show the fields that are
not present in the above dictionary::

    {
        "clnt_schema_version": 3,

        ... per_segment dictionary fields here (iteration: 1)

        "srvr_data": {
            "timestamp": 1413299382
        },
        "whole_test_timestamp": 1413299397
    }, {
        "clnt_schema_version": 3,

        ... per_segment dictionary fields here (iteration: 2)

        "srvr_data": {
            "timestamp": 1413299382
        },
    },
    ...
    }, {
        "clnt_schema_version": 3,

        ... per_segment dictionary fields here (iteration: 15)

        "srvr_data": {
            "timestamp": 1413299382
        },
    },

So, basically the dashtest adds fiteen entries to the results
each representing the download of a single segment plus some extra
information. In particular, the version of the client-side data schema is
added (currently it is three); server data is added (currently only the
server-side timestamp); the timestamp when the whole test started is added.

It is counterintuitive that a single test adds many dictionaries to
the results, however we are forced to do so due to limitations of the
web interface implementation. A better design would have been to group
the results of a dashtest into a vector instead.

Regarding data saved on the server side (i.e., on Measurement Lab), we have
less restrictions on the data format. In particular, the result of a whole
dashtest looks like this::

    {
        "client": [{
            ... per_segment dictionary fields here (iteration: 1)
          }, {
            ... per_segment dictionary fields here (iteration: 2)
          }
          ...
        ],
        "server": [],
        "srvr_schema_version": 3,
        "srvr_timestamp": 123456789
    }

So, basically, there is a list called client and containing the results
of each iteration of the test. Then there is server-related data, including
the version of the schema and the server-side timestamp. No server-specific
data is currently collected during the test.


Raw test data format
````````````````````

The raw test data format used on the server is different from the
format used on the Neubot side.

On the Neubot side,
we represent the data collected by the ``raw`` test with a
dictionary that contains the following fields:

**connect_time (float)**
  RTT estimated by measuring the time that connect() takes
  to complete, measured in seconds.

**download_speed (float)**
  Download speed measured by dividing the number of received bytes by
  the elapsed download time, measured in bytes per second.

**json_data (string)**
  This string contains the serialization of a JSON object, which
  contains all the data collected during the test, both on the server
  and on the client side. The dictionary that we are describing, in
  fact, contains just a subset of the collected results. We can
  not store the full JSON object directly until Neubot's ``database``
  module and web interface are ready to process it.

**internal_address (string)**
  Neubot's IP address, as seen by Neubot. It is typically either
  an IPv4 or an IPv6 address.

**latency (float)**
  RTT estimated by measuring the average time elapsed between sending
  a small request and receiving a small response, measured in seconds.

**neubot_version (float)**
  Neubot version number, encoded as a floating point number and printed
  into a string. Given a version number in the format
  ``<major>.<minor>.<patch>.<revision>``, the encoding is as follows::

    <major> + 1e-03 * <minor> + 1e-06 * <patch>
            + 1e-09 * <revision>

  For example, the ``0.4.15.3`` version number
  is encoded as ``0.004015003``.

**platform (string)**
  The operating system platform, e.g. ``linux2``, ``win32``.

**real_address (string)**
  Neubot's IP address, as seen by the server. It is typically either
  an IPv4 or an IPv6 address.

**remote_address (string)**
  The server's IP address. It is typically either an IPv4 or an
  IPv6 address.

**timestamp (integer)**
  Time when the test was performed, expressed as number of seconds
  elapsed since midnight of January, 1st 1970.

**uuid (string)**
  Random unique identifier of the Neubot instance, useful to perform
  time series analysis.

Example::

   [
    {
     "connect_time": 0.2981860637664795,
     "download_speed": 3607.120929707688,
     "internal_address": "130.192.91.231",
     "json_data": "...",
     "latency": 0.29875500202178956,
     "neubot_version": "0.004015007",
     "platform": "linux2",
     "real_address": "130.192.91.231",
     "remote_address": "203.178.130.237",
     "timestamp": 1365071100,
     "uuid": "7528d674-25f0-4ac4-aff6-46f446034d81"
    },
    ...

On the server side we save the dictionary corresponding to the JSON
object serialized into the ``json_data`` on the Neubot side. Henceforth
we call 'outer dictionary' the dictionary saved on the Neubot side and
we call 'inner dictionary' the one saved both on the server side on
and the ``json_data`` field.

The inner dictionary contains the following fields:

**client (dictionary)**
  A dictionary that contains data collected on the client side.

**server (dictionary)**
  A dictionary that contains data collected on the server side.

The client dictionary contains the following fields:

**al_capacity (float)**
  Median bottleneck capacity computed at application level (experimental).

**al_mss (float)**
  MSS according to the application level (information gathered
  using setsockopt(2)).

**al_rexmits (list)**
  Likely retransmission events computed at application level (experimental).

**alrtt_avg (float)**
  Same as ``latency`` in the outer dictionary.

**alrtt_list (list of tuples)**
  List of RTT samples estimated by measuring the average time elapsed
  between sending a small request and receiving a small response,
  measured in seconds.

**connect_time (float)**
  Same as ``connect_time`` in the outer dictionary.

**goodput (dictionary)**
  The dictionary contains the following fields:

  **bytesdiff**
    Total number of received bytes.

  **ticks (float)**
    Timestamp when this piece of data was collected, expressed as number of
    seconds elapsed since midnight of January, 1st 1970.

  **timediff (float)**
    Total download time.

**goodput_snap (list of dictionaries)**
  List that contains a dictionary, which is updated roughly every
  second during the download, and which contains the following fields:

  **ticks (float)**
    Time when the current dictionary was saved, expressed as number
    of seconds since midnight of January, 1st 1970.

  **bytesdiff (integer)**
    Number of bytes received since stats were previously saved.

  **timediff (float)**
    Number of seconds elapsed since stats were previously saved.

  **utimediff (float)**
    Difference between current ``tms_utime`` field of the ``tms``
    struct modified by ``times(3)`` and the previous value of
    the same field.

  **stimediff (float)**
    Difference between current ``tms_stime`` field of the ``tms``
    struct modified by ``times(3)`` and the previous value of
    the same field.

**myname (string)**
  Neubot's address (according to the server). This is same as
  ``real_address`` in the outer dictionary.

**peername (string)**
  Servers's address. This is same as ``server_address`` in the outer
  dictionary.

**platform (string)**
  Same as ``platform`` in the outer dictionary.

**uuid (string)**
  Same as ``uuid`` in the outer dictionary.

**version (string)**
  Same as ``neubot_version`` in the outer dictionary.

The server dictionary contains the following fields:

**goodput (dictionary)**
  The dictionary contains the following fields:

  **bytesdiff**
    Total number of sent bytes.

  **ticks (float)**
    Timestamp when this piece of data was collected, expressed as number of
    seconds elapsed since midnight of January, 1st 1970.

  **timediff (float)**
    Total upload time.

**goodput_snap (list of dictionaries)**
  List that contains a dictionary, which is updated roughly every
  second during the upload, and which contains the following fields:

  **ticks (float)**
    Time when the current dictionary was saved, expressed as number
    of seconds since midnight of January, 1st 1970.

  **bytesdiff (integer)**
    Number of bytes sent since stats were previously saved.

  **timediff (float)**
    Number of seconds elapsed since stats were previously saved.

  **utimediff (float)**
    Difference between current ``tms_utime`` field of the ``tms``
    struct modified by ``times(3)`` and the previous value of
    the same field.

  **stimediff (float)**
    Difference between current ``tms_stime`` field of the ``tms``
    struct modified by ``times(3)`` and the previous value of
    the same field.

**myname (string)**
  Servers's address. This is same as ``server_address`` in the outer
  dictionary.

**peername (string)**
  Neubot's address (according to the server). This is same as
  ``real_address`` in the outer dictionary.

**platform (string)**
  Same as ``platform`` in the outer dictionary.

**timestamp (integer)**
  Time when the server dictionary was created, expressed as number of
  seconds elapsed since midnight of January, 1st 1970.

**version (string)**
  Same as ``neubot_version`` in the outer dictionary.

**web100_snap (list)**
  A list that contains dictionaries. Each dictionary is a snapshot
  of the Web100 TCP state. We take one Web100 snapshot every second
  during the upload.

  On the client side, this field is empty. We are working to identify
  the most interesting fields that is interesting to save. The data saved
  on the server side (and that you can download from Measurement Lab)
  instead contains all the data collected using Web100.

Example::

   [
    {
     "client": {
      "al_mss": 1448,
      "uuid": "7528d674-25f0-4ac4-aff6-46f446034d81",
      "goodput": {
       "bytesdiff": 128200,
       "timediff": 35.540810108184814,
       "ticks": 1365071098.203412
      },
      "al_rexmits": [],
      "connect_time": 0.2981860637664795,
      "alrtt_list": [
       0.31011295318603516,
       0.30966901779174805,
       0.29677391052246094,
       0.2957899570465088,
       0.29570794105529785,
       0.2956199645996094,
       0.29558706283569336,
       0.2956211566925049,
       0.2958400249481201,
       0.296828031539917
      ],
      "myname": "130.192.91.231",
      "peername": "203.178.130.237",
      "platform": "linux2",
      "version": "0.004015007",
      "al_capacity": 10982553.692585895,
      "alrtt_avg": 0.29875500202178956,
      "goodput_snap": [
       {
        "bytesdiff": 24616,
        "timediff": 1.0001380443572998,
        "ticks": 1365071063.66274,
        "stimediff": 0.0,
        "utimediff": 0.0
       },
       ...
      ]
     },
     "server": {
      "timestamp": 1365070933,
      "myname": "203.178.130.237",
      "peername": "130.192.91.231",
      "platform": "linux2",
      "version": "0.004015007",
      "goodput": {
       "bytesdiff": 131092,
       "timediff": 34.94503116607666,
       "ticks": 1365070933.95337
      },
      "goodput_snap": [
       {
        "bytesdiff": 31856,
        "timediff": 1.0005459785461426,
        "ticks": 1365070900.008885,
        "stimediff": 0.0,
        "utimediff": 0.0
       },
       ...
      ],
      "web100_snap": []
     }
    }

Speedtest data format
`````````````````````

We represent the data collected by the ``speedtest`` test with a
dictionary that contains the following fields:

**connect_time (float)**
  RTT estimated by measuring the time that connect() takes
  to complete, measured in seconds.

**download_speed (float)**
  Download speed measured by dividing the number of received bytes by
  the elapsed download time, measured in bytes per second.

**internal_address (string)**
  Neubot's IP address, as seen by Neubot. It is typically either
  an IPv4 or an IPv6 address.

**latency (float)**
  RTT estimated by measuring the average time elapsed between sending
  a small request and receiving a small response, measured in seconds.

**neubot_version (string)**
  Neubot version number, encoded as a floating point number and printed
  into a string. Given a version number in the format
  ``<major>.<minor>.<patch>.<revision>``, the encoding is as follows::

    <major> + 1e-03 * <minor> + 1e-06 * <patch>
            + 1e-09 * <revision>

  For example, the ``0.4.15.3`` version number
  is encoded as ``0.004015003``.

**platform (string)**
  The operating system platform, e.g. ``linux2``, ``win32``.

**privacy_can_collect (integer)**
  The value of the ``can_collect`` privacy setting.

**privacy_can_publish (integer)**
  The value of the ``can_publish`` privacy setting.

**privacy_informed (integer)**
  The value of the ``informed`` privacy setting.

**real_address (string)**
  Neubot's IP address, as seen by the server. It is typically either
  an IPv4 or an IPv6 address.

**remote_address (string)**
  The server's IP address. It is typically either an IPv4 or an
  IPv6 address.

**timestamp (integer)**
  Time when the test was performed, expressed as number of seconds
  elapsed since midnight of January, 1st 1970.

**upload_speed (float)**
  Upload speed measured by dividing the number of sent bytes by the
  elapsed upload time, measured in bytes per second.

**uuid (string)**
  Random unique identifier of the Neubot instance, useful to perform
  time series analysis.

Example::

   [
    {
     "connect_time": 0.0017991065979003906,
     "download_speed": 11626941.501993284,
     "internal_address": "130.192.91.231",
     "latency": 0.003973397341641513,
     "neubot_version": "0.004015007",
     "platform": "linux2",
     "privacy_can_collect": 1,
     "privacy_can_publish": 1,
     "privacy_informed": 1,
     "real_address": "130.192.91.231",
     "remote_address": "194.116.85.237",
     "test_version": 1,
     "timestamp": 1365074302,
     "upload_speed": 10974865.674026133,
     "uuid": "7528d674-25f0-4ac4-aff6-46f446034d81"
    },
    ...

DATA PROCESSING LANGUAGE
````````````````````````

The data processing language is a simple LISP-like language. As such,
it describes processes whose goal is to transform pieces of collected data
by using lists.

Differently from traditional LISP syntax, however, the data processing
language is encoded using JSON.

The language implements the following operations:

**["divide", atom-or-list, atom-or-list]**
  Divides the left atom (or list) by the right atom (or list) and
  returns the result.

**["map-select", atom, list]**
  Cycles over the list and, for each element, it selects the
  field indicated by the atom.

**["parse-json", atom-or-list]**
  Parses the value of the atom (or list) into an object.

**["reduce-avg", list]**
  Computes the average value of the list.

**["select", atom, object]**
  Selects the element of object indicated by atom.

**["to-datetime", atom-or-list]**
  Converts atom (or list) to datetime string.

**["to-millisecond", atom-or-list]**
  Converts atom (or list) to millisecond.

**["to-millisecond-string", atom-or-list]**
  Converts atom (or list) to millisecond string.

**["to-speed", atom-or-list]**
  Converts atom (or list) to speed (in bits per second).

**["to-speed-string", atom-or-list]**
  Converts atom (or list) to speed string (in bits per second).

**"result"**
  The current piece of data we are processing.

Example (select the ``json_data`` field of the result, convert it to json,
take the ``client`` field, take and compute the average of the ``alrtt_list``
field, convert the result to millisecond)::

  ["to-millisecond",
    ["reduce-avg",
      ["select", "alrtt_list",
        ["select", "client",
          ["parse-json",
            ["select", "json_data", "result"]]]]]]

PRIVACY
```````

Neubot collects your IP address, which is personal data according to
European privacy laws. For this reason, Neubot needs to obtain your
permission to collect your IP address for research purposes, as well
as to publish it on the web for the same purpose. In addition, it
also needs that you assert that you have read the privacy policy.

Without the assertion that you have read the privacy policy and the
permission to collect and publish your IP address, Neubot can not
perform automatic (or manual) tests.

You can read Neubot's privacy policy by running the ``neubot privacy -P``
command. The privacy policy is also available at::

    http://127.0.0.1:9774/privacy.html

Of course, if you modified the address and/or port where Neubot listens,
you need to update the URI accordingly.

In addition to the above, each Neubot is identified by a random
unique identifier (UUID) that is used to perform time series
analysis. We believe that this identifier does not brach your
privacy: in the worst case, we would be able to say that a given
Neubot has changed Internet address (anche, hence, ISP and/or
location). To regenerate your unique identifier, you can run
the ``neubot database regen_uuid`` command.

AUTHOR
``````

Neubot authors are::

  Simone Basso                  <bassosimone@gmail.com>

The following people have contributed patches to the project::

  Alessio Palmero Aprosio	<alessio@apnetwork.it>
  Antonio Servetti              <antonio.servetti@polito.it>
  Roberto D'Auria		<everlastingfire@autistici.org>
  Marco Scopesi			<marco.scopesi@gmail.com>

The following people have helped with internationalization::

  Claudio Artusio               <claudioartusio@gmail.com>

COPYRIGHT
`````````

Neubot as a collection is::

  Copyright (c) 2010-2013 Nexa Center for Internet & Society,
      Politecnico di Torino (DAUIN)

  Neubot is free software: you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation, either version
  3 of the License, or (at your option) any later version.

SEE ALSO
````````

- http://www.neubot.org/
- http://github.com/neubot/neubot
- http://twitter.com/neubot
