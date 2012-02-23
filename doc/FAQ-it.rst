0. Indice
---------

* `0. Indice`_

* `1. Domande generiche`_

    * `1.1. Che cos'è Neubot?`_

    * `1.2. Che cos'è Measurement Lab?`_

    * `1.3. Che cos'è la neutralità della rete?`_

    * `1.4. Perchè "network neutrality bot"?`_

    * `1.5. Perchè è cruciale monitorare la neutralità della rete?`_

    * `1.6. Perchè potrei voler installare Neubot?`_

    * `1.7. Quali sono i test implementati dall'ultima versione?`_

    * `1.8. Qual'è la roadmap per arrivare a Neubot/1.0?`_

    * `1.9. Quando è prevista la prossima release di Neubot?`_

    * `1.10. Qual'è la vostra politica di versioning?`_

    * `1.11. Qual'è la versione migliore di Neubot?`_

    * `1.12. Per quanto tempo devo tenere installato Neubot?`_

    * `1.13. Quanto testate Neubot prima di ogni release?`_

    * `1.14. Chi sviluppa Neubot?`_

    * `1.15. Con quale licenza viene distribuito Neubot?`_

    * `1.16. Quanto costa Neubot?`_

* `2. Installare Neubot`_

    * `2.1. Su quali sistemi funziona Neubot?`_

    * `2.2. Come installo Neubot?`_

* `3. Usare Neubot`_

    * `3.1. Neubot è installato. Cosa devo fare adesso?`_

    * `3.2. Di quante risorse ha bisogno Neubot?`_

    * `3.3. Come posso riportare bugs, fare domande, dare suggerimenti?`_

    * `3.4. Che problemi ci sono se uso mobile broadband, 3G modem, Internet key?`_

    * `3.5. Devo modificare la configurazione del mio router?`_

    * `3.6. Come leggo i log di Neubot?`_

    * `3.7. Devo ruotare periodicamente i file log?`_

    * `3.8. Devo ruotare periodicamente il database?`_

* `4. Domande tecniche`_

    * `4.1. Come funziona Neubot?`_

    * `4.2. Che cosa misura il test speedtest?`_

    * `4.3. In che modo Neubot modifica il registro di sistema di Windows?`_

    * `4.4. Qual'è il percorso del database di Neubot?`_

    * `4.5. Come posso scaricare i contenuti del database?`_

    * `4.6. Che cosa misura il test bittorrent?`_

    * `4.7. Che significa misurare la banda disponibile?`_

    * `4.8. È possibile paragonare i risultati dei test speedtest e bittorrent?`_

* `5. Domande sulla privacy`_

    * `5.1. Quali dati personali colleziona Neubot?`_

    * `5.2. Pubblicherete il mio indirizzo IP?`_

1. Domande generiche
--------------------

1.1. Che cos'è Neubot?
~~~~~~~~~~~~~~~~~~~~~~

Neubot è un progetto di ricerca sulla neutralità della rete del `Centro
NEXA su Internet & Società`_ del `Politecnico di Torino`_. Il progetto si
basa su un programma leggero e `open source`_ che gli utenti interessati
possono scaricare e installare sul proprio computer. Il programma funziona
in background ed effettua periodicamente prove di trasmissione con alcuni
server di prova, ospitati dalla piattaforma distribuita Measurement Lab,
e (in futuro) con altre istanze del programma stesso.  Queste prove di
trasmissione testano la Rete utilizzando diversi protocolli di livello
applicativo e i risultati dei test sono salvati sia localmente sia sui
test server. Il set di dati raccolti contiene campioni provenienti da
diversi Providers e viene pubblicato sul web, consentendo a chiunque di
analizzare i dati per finalità di ricerca.

1.2. Che cos'è Measurement Lab?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measurement Lab (M-Lab_) è una piattaforma server distribuita che fornisce
connettività e server in giro per il mondo a progetti che si propongono
di misurare la qualità e/o la neutralità delle connession a banada larga a
Internet, verificando il comportamento della Rete con test attivi.

A partire dalla versione 0.4.6, Neubot è stato incluso nella piattaforma
Measurement Lab, e, dalla versione 0.4.8, la maggior parte dei test insiste
sui server di Measurement Lab.  I vecchi client utilizzano ancora il server
centrale del progetto Neubot, ma la percentuale di questi test è molto
piccola.

1.3. Che cos'è la neutralità della rete?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La neutralità della rete è il principio secondo cui Internet non
dovrebbe fornire un servizio migliore ad alcuni tipi di applicazioni,
ad alcuni mittenti o destinatari. In altre parole, una rete è neutrale
quando i router_ instradano i pacchetti usando una strategia *first
come, first served*. E non è neutrale quando certi pacchetti ricevono
un trattamento privilegiato.

.. _router: http://it.wikipedia.org/wiki/Router

La Internet delle origini era strettamente neutrale, essendo stata
progettata per minimizzare le interazioni tra le applicazioni e la rete
(vedi RFC3439_). Questa scelta progettuale rese possibile l'instradamento
dei pacchetti ad alta velocita\` e rese Internet una piattaforma aperta
dove chiunque poteva innovare senza chiedere il permesso. Di conseguenza
Internet è diventato il volano per l'innovazione che tutti conosciamo. E
il luogo dove cittadini, associazioni e imprese di tutto il mondo si
possono confrontare a parità di condizioni.

.. _RFC3439: http://tools.ietf.org/html/rfc3439#section-2.1

Oggigiorno, Internet non è sempre neutrale per via di tecnologie che
permettono di discriminare in modo fine i flussi di traffico. Quando i
pacchetti entrano nella rete di un Internet Service Provider, vengono
classificati, cioè assegnati ad una classe di traffico come *web*,
*video* o *file-sharing*. Tipicamente, gli algoritmi di classificazione
ispezionano gli header e la porzione iniziale del contenuto dei pacchetti
Internet per cercare di "indovinare" la classe. Ma i pacchetti che
appartengono ad un flusso possono anche ereditare la classificazione
dai pacchetti precedenti, se questi sono gia' stati classificati. Una
volta che un pacchetto e' stato classificato, riceve dai router che
si trovano all'interno della rete il servizio associato alla classe di
traffico assegnata.

Il dibatto di policy riguardo la neutralità della rete si chiede se sia
preferibile (dal punto di vista tecnico, giuridico e per quanto concerne
l'innovazione) continuare a lasciar fare gli operatori o se la
neutralità della rete debba essere garantita per legge. Per saperne di
piu' ti consigliamo di fare riferimento alla pagina Wikipedia sulla
`neutralità della rete`_.

.. _`neutralità della rete`:
   http://it.wikipedia.org/wiki/Neutralità_della_Rete

1.4. Perchè "network neutrality bot"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il programma si chiama *network neutrality bot* perché è un `"software
che esegue operazioni automatiche su
Internet" <http://en.wikipedia.org/wiki/Internet_bot>`_, al fine di
quantificare la *neutralità della rete*.

1.5. Perchè è cruciale monitorare la neutralità della rete?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitorare la neutralità della rete è cruciale perchè permette una più
profonda comprensione del comportamento degli operatori. Questo è
fondamentale *ex-ante*, specie nel momento in cui si apre un ampio
dibattito sulle modifiche nelle politiche di neutralità della rete. La
disponibilità di serie di dati quantitativi raccolti da ricercatori
indipendenti dovrebbe riequilibrare, almeno in parte, la profonda
asimmetria informativa tra Internet Service Providers e altri soggetti
interessati (regolatori e cittadini compresi), e dovrebbe fornire una
base più affidabile per discutere le politiche sul tema.

Monitorare la neutralità della rete sarebbe cruciale anche in uno
scenario *ex-post*. Infatti, consentirebbe di verificare il
comportamento degli operatori, alla luce delle decisioni normative in
materia di neutralità.

1.6. Perchè potrei voler installare Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Potresti voler installare Neubot se tieni alla neutralità della rete,
se desideri sostenere questo lavoro di ricerca, e se sei disponibile a
donare a questo progetto una frazione della tua capacità di rete per
eseguire test periodici di qualità e neutralità. Potrai contribuire
a costruire un set di dati quantitativi sulla neutralità della rete,
e la disponibilità di questo set di dati indipendenti condurrà
probabilmente a un processo decisionale più democratico di Internet,
una delle infrastrutture chiave delle nostre società.

Un'altra ragione per cui potresti voler installare Neubot è che i
risultati dei test forniscono un breve quadro del funzionamento della tua
connessione Internet, in ore diverse ed utilizzando protocolli diversi.
Puoi confrontare questi risultati locali con i risultati ottenuti con
altri test, al fine di ottenere una comprensione più approfondita
del comportamento della tua rete domestica e del comportamento del
tuo provider.

Se sei interessato, non esitare a installarlo, perché il successo di
questo progetto di ricerca dipende in larga misura da quanti utenti
installano Neubot.

1.7. Quali sono i test implementati dall'ultima versione?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'ultima versione di Neubot implementa i seguenti test di trasmissione:

**Speedtest**
  Questo test di trasmissione, originariamente ispirato al test di
  speedtest.net_, è un test client-server HTTP che misura il `round
  trip time`_ e il goodput_ in upload e download.

**BitTorrent**
  Questo test di trasmissione effettua misurazioni client-server del
  `round trip time`_ e del `goodput`_ in upload e download, emulando
  il `protocollo BitTorrent`_.

Se sei interessato, puoi trovare maggiori dettagli sui test di
trasmissione nella sezione `4. Domande tecniche`_.

1.8. Qual'è la roadmap per arrivare a Neubot/1.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot/1.0 sarà in grado di eseguire test di trasmissione client-server
e peer-to-peer, utilizzando vari protocolli di livello applicativo.
Inizialmente, avevamo suddiviso il percorso per arrivare a Neubot/1.0 in
quattro fasi:

#. implementare un semplice test di trasmissione client-server basato su
   HTTP;
#. implementare un semplice test di trasmissione client-server basato su
   BitTorrent;
#. modificare il test BitTorrent affinche\` funzioni in modalità
   peer-to-peer;
#. implementare ulteriori test peer-to-peer per ulteriori protocolli;

In seguito la roadmap e' stata aggiornata ed estesa per tenere conto
di difficolta` e opportunita` incontrate durante il processo di sviluppo
e, adesso, e' possibile leggere la roadmap_ e la TODO_ list, aggiornate
e gestite utilizzando il `wiki di github`_.

1.9. Quando è prevista la prossima release di Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il processo di rilascio si propone di `rilasciare presto, rilasciare
spesso`_ per massimizzare il feedback. Il `repository git pubblico`_
viene aggiornato frequentemente e si cerca di distribuire una nuova
versione del software ogni mese.

In generale, la maggior parte delle release sono *patch release*,
che aggiungono nuove funzionalita` e/o corregono bachi.  Tipicamente,
dopo un certo numero di patch release, si raggiunge una massa critica
di funzionalita` e viene rilasciata una *milestone release*.

La politica di versioning riflette direttamente la distinazione tra
patch e milestone release, come spiega la FAQ successiva.

1.10. Qual'è la vostra politica di versioning?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot segue la ben-nota convenzione che prevede di utilizzare tre
numeri di versione: *major*, *minor* e *patch*.  Ad esempio, Neubot
0.4.8 ha numero major 0, numero minor 4 e numero patch 8.

Una milestone release ha numero patch 0 e numero major e minor che
corrisponde a una milestone nella `roadmap`_.  Le release patch,
invece, hanno numero patch diverso da zero.  Di conseguenza, 1.0.0
e 0.4.0 sono milestone release, mentre 0.3.1 e' una patch release.

1.11. Qual'è la versione migliore di Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La versione migliore di Neubot sarà sempre quella con il numero di
versione più alto, ad esempio, 0.3.1 è meglio di 0.3.0. Le patch
releases potrebbero includere caratteristiche sperimentali, ma queste
caratteristiche non saranno abilitate di default fino a quando non
matureranno e diventeranno stabili.

1.12. Per quanto tempo devo tenere installato Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Più a lungo possibile. Neubot non è un progetto di portata limitata, ma
piuttosto un impegno continuo.

1.13. Quanto testate Neubot prima di ogni release?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tipicamente una nuova funzionalita` sperimentale viene inclusa in
una patch release e non viene abilitata di default finche` non
matura e diventa stabile.  Quando viene rilasciata una milestone
release, la maggior parte delle feature sono state testate per
almeno un ciclo di release, cioe` da due a quattro settimane.

1.14. Chi sviluppa Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Capoprogetto del progetto Neubot è `Simone Basso`_, ricercatore del
`Centro NEXA su Internet & Società`_. Simone sviluppa Neubot in
collaborazione con e sotto la supervisione dei prof. `Antonio
Servetti`_, prof. `Federico Morando`_ e prof. `Juan Carlos De
Martin`_ del `Politecnico di Torino`_.

Visita la nostra `pagina people`_ per ulteriori informazioni.

1.15. Con quale licenza viene distribuito Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot è rilasciato con licenza `GNU General Public License versione
3`_.

1.16. Quanto costa Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Zero. Neubot è disponibile gratuitamente.

2. Installare Neubot
--------------------

2.1. Su quali sistemi funziona Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot è scritto in Python_ e dovrebbe pertanto funzionare su tutti
i sistemi supportati da Python_.

Il team di sviluppo fornisce pacchetti per Ubuntu_ >= 10.04 (e
Debian_), MacOSX_ >= 10.6, Windows_ >= XP SP3.  Neubot e' incluso
nella `FreeBSD Ports Collection`_ e funziona senza problemi su
OpenBSD_ 5.1 current.

2.2. Come installo Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Vai alla pagina `pagina download`_ e segui le instruzioni per il
tuo sistema operativo. Il team di sviluppo fornisce pacchetti binari
per MacOSX_, Windows_, Debian_, e distribuzioni basate su Debian_
(come Ubuntu_). Se non c'è un pacchetto binario per il tuo sistema,
puoi comunque installare Neubot dai sorgenti.

3. Usare Neubot
---------------

3.1. Neubot è installato. Cosa devo fare adesso?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot scarica e installa automaticamente gli aggiornamenti su tutte
le piattaforme tranne Microsoft Windows (e ovviamente non ci sono
autoaggiornamenti se hai installato Neubot partendo dai sorgenti).

Se non stai usando Windows, dovresti periodicamente controllare che
si sia automaticamente aggiornato all'ultima versione.  A spanne,
se sono passate piu` di due settimane dall'ultima release e non si
e' autoaggiornato, allora c'e` qualche bug.

Se stai usando Windows, l'`interfaccia web`_ verra` aperta
automaticamente nel browser quando c'e` un aggiornamento disponibile.
Comparirà un messaggio come quello contenuto nell'immagine seguente.
Clicca sul link, segui le istruzioni, ed è fatta.

.. image:: http://www.neubot.org/neubotfiles/neubot-update-notification.png
   :align: center

Potresti anche voler confrontare i risultati ottenuti con Neubot
con quelli di altri test e tool disponibili online.  In tal caso,
sarebbe cosa gradita se tu condividessi i risultati di altri test
e tool con il team di sviluppo di Neubot, specie se vengono fuori
risultati che non sono consistenti con quelli di Neubot.

3.2. Di quante risorse ha bisogno Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot ha un impatto minimo sul carico del sistema e della rete. Passa
la maggior parte del suo tempo a riposo o aspettando il suo turno per
eseguire un test. Durante il test Neubot consuma molte risorse di
sistema e di rete, tuttavia il programma cerca di assicurare che ogni
upload/download duri meno di sette secondi.

Qui ci sono un paio di immagini prese da un portatile che fa girare
Ubuntu 9.10 attaccato ad una connessione del Politecnico di Torino.
Nella prima immagine puoi vedere l'utilizzo delle risorse durante un
test on-demand invocato dalla riga di comando. La fase di init del test
è quella in cui Neubot genera i dati casuali da inviare durante la fase
di upload. (L'utilizzo delle risorse è molto più basso se lanci il test
da casa, dato che la connessione del Politecnico è 5x/10x più veloce
della maggior parte delle connsessioni ADSL).

.. image:: http://www.neubot.org/neubotfiles/resources1.png
   :align: center

La seconda immagine mostra quante risorse (soprattutto memoria) vengono
consumate quando Neubot è inattivo.

.. image:: http://www.neubot.org/neubotfiles/resources2.png
   :align: center

3.3. Come posso riportare bugs, fare domande, dare suggerimenti?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ti preghiamo di usare la nostra mailing list per riportare bugs e fare
domande. Le lingue ufficiali della mailing list sono l'inglese e
l'italiano.

Nota che **devi** essere iscritto alla mailing list, altrimenti il tuo
messaggio **non verra`** accettato. Per iscriverti:

      http://www.neubot.org/cgi-bin/mailman/listinfo/neubot

La pagina di iscrizione alla mailing list non ha un certificato SSL
valido e il tuo browser probabilmente si lamentera` di questo.  Non
farti spaventare dal messaggio di warning, in fondo si tratta solo
della pagina per registrarti alla mailing list di Neubot e non del
sito della tua banca.

**Prima** di inviare un messaggio ti consigliamo di consultare l'archivio
pubblico, visto che è possibile che qualcun'altro abbia già fatto la
stessa domanda o riportato lo stesso bug. Tutti i messaggi inviati alla
mailing list sono archiviati qui:

      http://www.neubot.org/pipermail/neubot/

Grazie per la collaborazione!

3.4. Che problemi ci sono se uso mobile broadband, 3G modem, Internet key?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Un possibile problema con mobile broadband può essere il seguente. Se
usi Windows, hai installato Neubot, non sei connesso, e Neubot inizia un
test, è possibile che Windows ti chieda di connetterti. Se questo
comportamento ti disturba, arresta Neubot dal menu start.

*Nelle future versioni progettiamo di verificare se ci sia una
connessione Internet o meno, e iniziare un test solo se questa sia
disponibile.*

3.5. Devo modificare la configurazione del mio router?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No.

3.6. Come leggo i log di Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In tutti i sistemi operativi puoi leggere i log attraverso la
*Tabella log* dell'`interfaccia web`_, disponibile a partire dalla
versione ``0.3.7``. L'immagine seguente fornisce un esempio:

.. image:: http://www.neubot.org/neubotfiles/neubot-log.png
   :align: center

Inoltre, in UNIX Neubot salva i log con ``syslog(3)`` e ``LOG_DAEMON``
*facility*. I log finiscono in ``/var/log``, tipicamente in
``daemon.log``. Per capire quale sia il file in cui davvero finiscano
i log, quando sono in un sistema nuovo, lancio il seguente comando
(da root)::

    # grep neubot /var/log/* | awk -F: '{print $1}' | sort | uniq
    /var/log/daemon.log
    /var/log/syslog

In questo esempio, ci sono log interessanti sia in ``/var/log/daemon.log``
sia in ``/var/log/syslog``. Una volta che conosco i nomi dei file,
posso estrarre i log da ogni file, come di seguito::

    # grep neubot /var/log/daemon.log | less

3.7. Devo ruotare periodicamente i file log?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No.  Su qualsiasi piattaforma, i log vengono salvati nel database,
ma periodicamente Neubot cancella i log vecchi.  Nei sistemi UNIX,
i log vengono anche salvati utilizzando ``syslog(3)``, che dovrebbe
automaticamente occuparsi di ruotare i file di log.

3.8. Devo ruotare periodicamente il database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si. Il database di Neubot dovrebbe crescere lentamente per dimensione
rispetto al tempo di utilizzo. (Il database della mia workstation pesa 2
MBytes dopo 8 mesi, e io lancio di frequente un test ogni 30 secondi per
esigenze di monitoraggio.) Per eliminare i risultati vecchi lancia il
seguente comando (da root)::

    # neubot database prune

4. Domande tecniche
-------------------

4.1. Come funziona Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot viene eseguito in background. In Linux, BSD e altri sistemi Unix
Neubot viene avviato al momento del boot, diventa un demone, e abbandona
i privilegi di root. In Windows Neubot viene avviato quando l'utente
accede per la prima volta (gli accessi successivi non avviano ulteriori
istanze di Neubot).

Neubot ha un impatto minimo sul carico della rete e del sistema. Passa
la maggior parte del suo tempo dormendo o aspettando il suo turno per
eseguire un test. Durante un test Neubot consuma molte risorse di
sistema e di rete, ma il programma cerca di garantire che ogni test non
richieda troppo tempo.

Periodicamente, Neubot scarica dal *server centrale* le informazioni sul
prossimo test da eseguire, incluso il nome del test, il server cui
connettersi e eventualmente altri parametri. Se ci sono aggiornamenti
disponibili, la risposta del server centrale include anche le
informazioni per eseguire l'aggiornamento, come l'URI da cui scaricare
gli aggiornamenti.

In seguito, Neubot si connette al server specificato, attende
l'autorizzazione per eseguire il test selezionato, effettua il test, e
salva i risultati. Neubot può attendere anche per un tempo abbastanza
lungo perché i server non gestiscono più di uno (o pochi) test
contemporaneamente. Nel complesso, il test può durare alcuni secondi, ma
Neubot cerca di garantire che il test non richieda troppo tempo. Alla
fine del test, i risultati vengono salvati in un database locale e
inviati ai server del progetto.

Infine, dopo il test, Neubot rimane in sleep per un lungo periodo di
tempo, prima di connettersi nuovamente al server centrale.

A partire dalla versione 0.4.2, Neubot utilizza il seguente algoritmo
per contenere la durata del test. La quantità predefinita di bytes da
trasferire è tale da ottenere una durata ragionevole del test con
connessioni ADSL lente. Dopo il test, Neubot adatta il numero di bytes
da trasferire in modo che il test seguente richieda circa cinque
secondi, nelle attuali condizioni. Inoltre, ripete il test fino a sette
volte se questo non ha richiesto almeno tre secondi.

*(Le versioni future di Neubot utilizzeranno anche una modalità di test
peer-to-peer, ossia eseguiranno i test anche tra istanze di Neubot.)*

4.2. Che cosa misura il test speedtest?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il test *speedtest* utilizza il `protocollo HTTP`_ e misura: il
`round trip time`_ e il goodput_ in download e upload. È ispirato
al test speedtest.net_, da cui il nome. Il test stima il `round
trip time`_ misurando il tempo medio richiesto per connettersi e
il tempo medio necessario per richiedere e scaricare una risorsa
di lunghezza zero. Stima inoltre il goodput_ in download e upload
dividendo il numero di bytes trasferiti per il tempo richiesto a
trasferirli.

4.3. In che modo Neubot modifica il registro di sistema di Windows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il programma di installazione scrive la seguente chiave di registro, in
modo che Windows sia a conoscenza del programma di disinstallazione::

    HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\neubot"

La chiave viene rimossa durante la procedura di disinstallazione.

4.4. Qual'è il percorso del database di Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In UNIX, se esegui Neubot come utente root il percorso del database
è ``/var/neubot/database.sqlite3``. Invece, se esegui Neubot come
utente non privilegiato, il percorso del database è
``$HOME/.neubot/database.sqlite3``.

In Windows, il percorso del database è sempre
``%APPDATA%\neubot\database.sqlite3``.

Con Neubot >= 0.3.7 puoi richiedere la posizione del database usando
il comando ``neubot database info``, ad esempio::

    $ neubot database info
    /home/simone/.neubot/database.sqlite3

    # neubot database info
    /var/neubot/database.sqlite3

4.5. Come posso scaricare i contenuti del database?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Puoi scaricare i contenuti del database utilizzando il comando
``neubot database dump``. L'output sarà un file JSON che contiene i
risultati. (Nota che in UNIX devi essere root per scaricare i contenuti
del system-wide database: se lanci questo comando come utente senza
privilegi scaricherai invece l'user-specific database.)

4.6. Che cosa misura il test bittorrent?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il test *bittorrent* emula il `protocollo
BitTorrent`_ e misura: il
`round trip time`_
e il goodput_ in
download e upload. Il test stima il `round trip time`_ misurando il tempo
necessario a connettersi. Stima inoltre la banda disponibile in download
e upload.

Dato che BitTorrent utilizza messaggi piccoli, non è possibile
trasferire un file di grosse dimensioni e dividere il numero di bytes
trasmessi per il tempo del trasferimento. Pertanto, il test effettua
inizialmente numerose richieste successive per riempire lo spazio tra
client e server di numerose risposte "in volo". La misurazione inizia
solo quando il richiedente ritiene che il numero di risposte "in volo"
sia sufficiente per approssimare un trasferimento continuo.

4.7. Che significa misurare la banda disponibile?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I test di Neubot NON misurano la velocità della tua connessione
Internet, ma piuttosto la banda disponibile, cioè la *banda che si
riesce ad ottenere a livello applicativo nel momento in cui si esegue la
misura*. Il risultato, quindi, potrebbe essere penalizzato dalle
seguenti condizioni:

#. stai scaricando un grosso file;
#. il tuo coinquilino sta scaricando un grosso file;
#. hai una cattiva connessione wireless che perde molti pacchetti;
#. c'è congestione nella rete del tuo provider;
#. non vivi
   `vicino <http://en.wikipedia.org/wiki/TCP_tuning#Window_size>`_ ai
   nostri server;
#. il nostro server è sovraccarico.

In altre parole, i risultati di Neubot vanno presi cum grano salis.

4.8. È possibile paragonare i risultati dei test speedtest e bittorrent?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il test bittorrent è stato rilasciato con la versione 0.4.0. In quel
periodo la comparazione non era sempre possibile perchè il test
speedtest utilizzava due connessioni mentre bittorrent ne utilizzava
solo una, con il risultato che le prestazioni erano peggiori in caso di
traffico ad alta velocità, ad elevato ritardo e/o più congestionato.
Neubot 0.4.2 ha risolto questo problema e modificato speedtest in modo
da usare una sola connessione.

Questo può ancora non essere sufficiente: pertanto, speedtest verrà
ulteriormente modificato in modo da utilizzare piccoli messaggi come fa
bittorrent. In questo modo, potremo essere sicuri che entrambi i test
carichino la rete in modo simile, cioè con pacchetti di dimensioni
simili in entrambe le direzioni. Questo miglioramento sarà implementato
prima di Neubot 0.5.0.

5. Domande sulla privacy
------------------------

5.1. Quali dati personali colleziona Neubot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neubot non ispeziona il tuo traffico, non controlla i siti che hai
visitato, ecc. Neubot utilizza una piccola parte della tua capacità di
rete per eseguire i test di trasmissione periodica e questi test
utilizzano dati casuali o dati provenienti dai nostri server.

Neubot raccoglie l'indirizzo Internet del computer nel quale è in
esecuzione. Dobbiamo raccogliere il tuo indirizzo Internet (che è un
dato personale), perché questo ci indica il tuo Internet Service
Provider e (approssimativamente) la tua posizione. Entrambe le
informazioni sono funzionali al nostro obiettivo di monitorare la
neutralità della rete.

Identifichiamo ogni istanza di Neubot con un identificativo univoco
casuale. Usiamo questo identificativo per eseguire analisi di serie
temporali e per verificare se ci sono tendenze ricorrenti. Crediamo che
questo identificativo non violi la tua privacy: nel peggiore dei casi,
saremmo in grado di dire che una determinata istanza di Neubot ha
cambiato indirizzo Internet (e, quindi Provider e/o posizione).
Tuttavia, se sei veramente preoccupato per questo identificativo univoco
casuale e stai facendo girare Neubot >= 0.3.7, puoi generare un nuovo
identificativo univoco lanciando il seguente comando:
``neubot database regen_uuid``.

Le versioni future di Neubot monitoreranno e raccoglieranno anche
informazioni riguardanti il carico del computer (come la quantità di
memoria libera, il carico medio, l'utilizzo medio della rete).
Monitoreremo il carico per evitare di iniziare test quando stai
utilizzando il computer a pieno carico. Raccoglieremo i dati di carico
al fine di esaminare l'effetto del carico sui risultati.

5.2. Pubblicherete il mio indirizzo IP?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dipende. Per impostazione predefinita non condividiamo il tuo indirizzo
Internet. Però ci piacerebbe farlo, per condividere i nostri risultati
con altri ricercatori e, più in generale, per potenziare la comunità di
ricerca. Tuttavia, per fare questo abbiamo bisogno del tuo permesso
esplicito, in conformità a quanto richiesto dalla normativa europea
sulla privacy. È facile: basta aprire l'interfaccia web, cliccare sulla
tabella *Privacy*, `leggere la policy </privacy>`_, e darci
l'autorizzazione!

..
.. Links
..

.. _`privacy policy`: https://github.com/neubot/neubot/blob/master/PRIVACY
.. _M-Lab: http://www.measurementlab.net/about

.. _speedtest.net: http://www.speedtest.net

.. _`round trip time`: http://en.wikipedia.org/wiki/Round-trip_delay_time
.. _goodput: http://en.wikipedia.org/wiki/Goodput
.. _`protocollo BitTorrent`: http://www.bittorrent.org/beps/bep_0003.html

.. _roadmap: https://github.com/neubot/neubot/wiki/roadmap
.. _todo: https://github.com/neubot/neubot/wiki/todo
.. _`wiki di github`: https://github.com/neubot/neubot/wiki

.. _`rilasciare presto, rilasciare spesso`:
 http://www.catb.org/esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html
.. _`repository git pubblico`: https://github.com/neubot/neubot

.. _`Simone Basso`: http://www.neubot.org/people#basso
.. _`Centro NEXA su Internet & Società`: http://nexa.polito.it/
.. _`Antonio Servetti`: http://www.neubot.org/people#servetti
.. _`Federico Morando`: http://www.neubot.org/people#morando
.. _`Juan Carlos De Martin`: http://www.neubot.org/people#de_martin

.. _`pagina people`: http://www.neubot.org/people

.. _`GNU General Public License versione 3`: http://www.neubot.org/copying

.. _Python: http://www.python.org/
.. _Ubuntu: http://www.ubuntu.com/
.. _Debian: http://www.debian.org/
.. _MacOSX: http://www.apple.com/macosx/
.. _Windows: http://windows.microsoft.com/
.. _`FreeBSD Ports Collection`: http://www.freshports.org/net/neubot
.. _OpenBSD: http://www.openbsd.org/

.. _`pagina download`: http://www.neubot.org/download

.. _`interfaccia web`: http://www.neubot.org/documentation#web-ui

.. _`protocollo HTTP`: http://en.wikipedia.org/wiki/HTTP

.. _`Politecnico di Torino`: http://www.dauin.polito.it/
.. _`open source`: https://github.com/neubot/neubot/blob/master/COPYING
