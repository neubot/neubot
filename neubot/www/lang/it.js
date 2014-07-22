/* neubot/www/lang/it.js */
/*-
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita` degli Studi di Milano
 * Copyright (c) 2011 Claudio Artusio <claudioartusio@gmail.com>,
 *  NEXA Center for Internet & Society at Politecnico di Torino
 * Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
 *  NEXA Center for Internet & Society at Politecnico di Torino
 *
 * This file is part of Neubot <http://www.neubot.org/>.
 *
 * Neubot is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Neubot is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
 */

LANG = {

    /*
     * i18n for javascripts
     * Map the string on the left to the string on the right via
     * the i18n.get() function.
     */

    'Latest test results': "Risultati ultimo test",
    'Current test results': "Risultati test corrente",
    'enabled': "attivi",
    'disabled': "disattivati",
    'Enable': "Attiva",
    'Disable': "Disattiva",
    'Test running': "Test in corso",

    'Your bittorrent connect time': 'Tempo per connettersi del test bittorrent',
    'Your bittorrent download and upload speed': 'Velocità di download e upload del test bittorrent',

    'Your speedtest connect time and latency': 'Tempo per connettersi e latenza del test speedtest',
    'Your speedtest download and upload speed': 'Velocità di download e upload del test speedtest',

    /*
     * i18n for HTML pages
     * To be translated a tag must belong to the i18n class
     * and an i18n_FOO class that idenfies the translation, i.e.
     * below on the left there is the i18n_FOO class and on
     * the right the corresponding translation.
     */

    'i18n_header_subtitle': "L'interfaccia web per controllare Neubot",
    'i18n_header_title': '<a href="index.html">Interfaccia Web di Neubot</a>',

    'i18n_text_direction': "ltr",
    'i18n_settings': "Impostazioni",
    'i18n_status': "Stato",
    'i18n_speedtest': "Speedtest",
    'i18n_log': "Log",
    'i18n_privacy': "Privacy",
    'i18n_website': "Sito web di Neubot",
    'i18n_updavailable': "Aggiornamenti disponibili",
    'i18n_infonav': "N/A",
    'i18n_auto_tests': 'Test automatici',
    'i18n_auto_tests_detail': 'Test automatici',
    'i18n_resultof': "Risultati di",
    'i18n_latency': "Latenza",
    'i18n_dlspeed': "Velocità download",
    'i18n_ulspeed': "Velocità upload",
    'i18n_about': "Informazioni",
    'i18n_state': "Stato",
    'i18n_description': "Descrizione",

    'i18n_idle_status_text': "Neubot sta dormendo. Il prossimo \
rendezvous inizierà tra <em><span id='next_rendezvous'>(n/a)</span></em>.",

    'i18n_rendezvous_status_text': "Neubot si sta connettendo al \
server di Neubot per reperire informazioni su test e aggiornamenti.",

    'i18n_negotiate_status_text': "Neubot attende il turno per il \
test di trasmissione. L'ultima posizione nota in coda è \
<em><span id='queuePos'>(n/a)</span></em>.",

    'i18n_test_status_text': "Il test <em><span id='testName'>(n/a)</span>\
</em> è in corso.",

    'i18n_collect_status_text': "Neubot sta eseguendo l'upload dei \
risultati sul server di Neubot.",

    'i18n_about_text': "Questa è l'interfaccia web di Neubot. \
Neubot è un programma <a href='http://www.neubot.org/copying'>free software</a> \
leggero che viene eseguito in background ed esegue periodicamente test \
di trasmissione dati per testare la tua connessione a Internet utilizzando \
diversi protocolli applicativi. <a href='http://www.neubot.org/faq'>Leggi \
le FAQ</a>",

    'i18n_startnow': 'Fai partire un test adesso',

    'i18n_startnowtest': 'Test',

    'i18n_footer_text': "Neubot è un progetto di ricerca sulla neutralità \
della rete realizzato dal <a href='http://nexa.polito.it/'>Centro \
NEXA su Internet &amp; Società</a> del \
<a href='http://www.dauin.polito.it/'>Politecnico di Torino</a>.<br/>\
I server di Neubot sono installati sulla piattaforma distribuita \
<a href='http://www.measurementlab.net'>Measurement Lab</a>.",

    'i18n_welcome_text': "Grazie per aver installato Neubot! Ora avrai \
le idee più chiare sulla tua connessione a Internet e potrai aiutare \
la comunità a capire cosa accade nella rete. Questa sezione fornisce un \
prospetto generale del demone Neubot. Clicca sui vari tab per visualizzare \
le informazioni relative ai vari test.",

    'i18n_current_status': "Stato di Neubot",

    'i18n_status_text': "Questo è il pannello di controllo del demone \
Neubot, in esecuzione con PID <em><span id='pid'>(n/a)</span></em> da \
<em><span id='since'>(n/a)</span></em>. La tabella sottostante fornisce \
dettagli aggiuntivi sullo stato del demone. La riga evidenziata rappresenta \
lo stato corrente.",

    // neubot/www/settings.html

    "i18n_settings_title": "Impostazioni",

    "i18n_settings_par1": "Questa pagina mostra tutte le opzioni di\
                           configurazione che possono essere modificate,\
                           inclusi i settaggi più oscuri e pericolosi.\
                           Perfavore, assicurati di sapere ciò che stai\
                           facendo prima di fare modifiche.  Non riceverai\
                           alcun tipo di aiuto se Neubot smette di funzionare\
                           per colpa di modifiche inopportune.",

    // neubot/www/descr/bittorrent.html

    "i18n_results_bittorrent_explanation": "Questo test fa il download e \
        l'upload\
        di un certo numero di bytes da un server remoto, utilizzando il\
        protocollo BitTorrent.  Il test stima la velocità media di download\
        e upload così come il tempo richiesto per connettersi al server\
        remoto, che approssima il round-trip time.",

    "i18n_results_bittorrent_explanation_2": "Nota che questo test è abbastanza\
        differente dal test <em>Speedtest</em>, quindi ci sono casi in cui\
        i due non sono comparabili.  Stiamo lavorando a un test HTTP\
        che sia più simile a quest'ultimo, così che sia sempre possibile\
        compararli.",

    "i18n_bittorrent_see_last": "Guarda l'ultimo",
    "i18n_bittorrent_see_last_days": "giorno",
    "i18n_bittorrent_see_last_hours": "ora",

    'i18n_bittorrent_title': 'Risultati del test bittorrent',

    // neubot/www/descr/speedtest.html

    "i18n_speedtest_title": "Risultati dello speedtest",

    "i18n_results_speedtest_explanation_1": "Speedtest é un test che \
getta un po' di luce sulla qualità della tua connessione a \
Internet, facendo download e upload di dati casuali a/da un server \
remoto, e riportando le velocità medie. Il test stima anche (per \
eccesso) il round-trip time tra te e il server remoto.  Per maggiori \
informazioni, vedi le \
<a href='http://www.neubot.org/faq#what-does-measuring-goodput-mean'>FAQ</a>.",

    "i18n_results_speedtest_explanation_2": "I risultati di Neubot sono \
correlati \
alla qualità della tua connessione broadband (e anche ad altri fattori \
di confusione, come spiegato nelle \
<a href='http://www.neubot.org/faq#what-does-measuring-goodput-mean'>FAQ</a>).\
 Di conseguenza, per contestualizzare i risultati \
di questo test rispetto alla velocità media disponibile nel \
tuo paese puoi far riferimento alle statistiche disponibili sul \
<a href='http://www.oecd.org/sti/ict/broadband'>Portale Banda larga \
OECD</a>.   In particolare, potrebbe essere interessante leggere \
<a href='http://www.oecd.org/dataoecd/10/53/39575086.xls'>'Average \
advertised download speeds, by country'</a> (in formato XLS).",

    "i18n_speedtest_see_last": "Guarda l'ultimo",
    "i18n_speedtest_see_last_days": "giorno",
    "i18n_speedtest_see_last_hours": "ora",

    // neubot/www/log.html

    'i18n_log_intro':
'Questa pagina presenta i log di Neubot \
 in formato HTML. La <a href="/api/log%3Fdebug%3D1%26verbosity%3D2" onclick="window.open(unescape(this.href)); return false;" target="_blank">rappresentazione \
 testuale</a> dei log è disponibile, per quando hai bisogno di\
 <a href="http://www.neubot.org/mailing-lists">segnalare un\
 bug</a>.',

    // neubot/www/privacy.html

    'i18n_privacy_not_ok':
'Neubot è DISABILITATO: a partire dalla versione 0.4.6, i server di Neubot\
 sono installati sulla piattaforma server distribuita\
 <a href="http://www.measurementlab.net/">Measurement Lab</a>.\
 Per essere conforme alla policy di Measurement Lab e poter così eseguire\
 le proprie misure, Neubot ha bisogno di chiederti il permesso di poter\
 salvare e pubblicare il tuo indirizzo Internet.  Puoi fornire entrambi\
 i permessi qua sotto, ma prima leggi la privacy policy di Neubot.',

    "i18n_privacy_explanation": "In questa pagina spieghiamo i dettagli \
della nostra <a href='#policy'>politica sulla privacy</a>, necessaria \
per essere conformi alla normativa europea in materia. Forniamo inoltre \
un semplice <a href='#dashboard'>quadro privacy</a> per gestire le \
autorizzazioni che deciderai di fornirci rispetto al trattamento del \
tuo indirizzo Internet, che è considerato dato personale nell'Unione Europea.",

    'i18n_privacy': 'Privacy',

    "i18n_privacy_title_1": "Politica sulla privacy",

    'i18n_privacy_policy':
'\r\n\
.. :Versione: 2.0.3$\r\n\
\r\n\
Il progetto Neubot è un progetto di ricerca che si propone di studiare\r\n\
la qualità e la neutralità delle connessioni ad Internet\r\n\
degli utenti comuni, per ribilanciare l\'asimmetria informativa tra utenti\r\n\
comuni e Service Providers.  Il software Neubot (i) *misura* la qualità\r\n\
e la neutralità della tua connessione a Internet.  I risultati\r\n\
grezzi delle misure sono (ii) *salvati* sul server di misura per scopi di\r\n\
ricerca e (iii) *pubblicati*, per permettere ad altri individui e\r\n\
istituzioni di riutilizzarli per finalità di ricerca.\r\n\
\r\n\
Per *misurare* la qualità e la neutralità della tua\r\n\
connessione a Internet, il software Neubot non controlla né analizza\r\n\
il tuo traffico Internet. Si limita a utilizzare una frazione della\r\n\
capacità della tua connessione per effettuare dei test di\r\n\
trasmissione in background, inviando e/o ricevendo dati casuali. I\r\n\
risultati contengono le metriche misurate, come la velocità di\r\n\
download o la latenza, il carico del tuo computer, in percentuale, e il\r\n\
tuo *indirizzo Internet*.\r\n\
\r\n\
L\'indirizzo Internet è fondamentale perché permette di\r\n\
*dedurre il tuo Internet Service Provider* e di avere un\'idea della tua\r\n\
*posizione geografica*, permettendo di contestualizzare la misura.  Il\r\n\
progetto Neubot ha bisogno di *salvarlo* per poter studiare i dati e\r\n\
desidera *pubblicarlo* per permettere ad altri individui e istituzioni di\r\n\
eseguire analisi alternative e/o analizzare criticamente la metodologia\r\n\
utilizzata dal progetto stesso.  Ciò è coerente con la\r\n\
policy della piattaforma server distribuita cui si appoggia il progetto\r\n\
Neubot, Measurement Lab (M-Lab), che richiede che tutti i risultati\r\n\
siano rilasciati come dati aperti [1].\r\n\
\r\n\
Stai leggendo questa privacy policy perché Neubot viene sviluppato\r\n\
nell\'Unione Europea, dove gli indirizzi IP sono ritenuti *dati personali*.\r\n\
Questo significa che il progetto Neubot non può salvare, processare o\r\n\
pubblicare il tuo indirizzo senza ottenere il tuo *consenso informato*,\r\n\
secondo le previsioni del "Codice in materia di protezione dei dati\r\n\
personali" (Decreto 196/03) [2].  Conformemente alla legge, il\r\n\
titolare del trattamento è il Centro NEXA su Internet e Società [3],\r\n\
rappresentato dal suo co-diretore Juan Carlos De Martin.\r\n\
\r\n\
Tramite la sua interfaccia web [4], il software Neubot ti chiede (a) di\r\n\
dichiarare esplicitamente di essere *informato*, ossia di avere letto la\r\n\
privacy policy, (b) di fornirgli il permesso di *salvare* e (c) *pubblicare*\r\n\
il tuo indirizzo IP.  Se non dichiari (a) e non fornisci i permessi (b) e \r\n\
(c), Neubot non può eseguire alcun test perché, se lo facesse,\r\n\
violerebbe la normativa sui dati personali e/o la policy di Measurement Lab.\r\n\
\r\n\
Il responsabile del trattamento ti garantisce i diritti specificati nello\r\n\
Articolo 7 del sopra-menzionato Decreto 196/03.  Fondamentalmente, hai il\r\n\
totale controllo sui tuoi dati personali e puoi, per esempio, chiedere a\r\n\
Neubot di rimuovere il tuo indirizzo Internet dalla sua banca dati.  Per\r\n\
esercitare i tuoi diritti, scrivi a <privacy@neubot.org>\r\n\
oppure a "Centro NEXA su Internet & Società c/o Dipartimento di\r\n\
Automatica e Infomatica, Politecnico di Torino, Corso Duca degli\r\n\
Abruzzi 24, 10129 Torino, ITALIA".\r\n\
\r\n\
[1] http://www.measurementlab.net/about\r\n\
[2] http://www.garanteprivacy.it/garante/doc.jsp?ID=1311248\r\n\
[3] http://nexa.polito.it/\r\n\
[4] http://127.0.0.1:9774/privacy.html\r\n\
        ',

    "i18n_privacy_title_2": "Quadro privacy",

    "i18n_privacy_settings_1": "Questo è lo status corrente delle tue \
impostazioni sulla privacy:",
    
    "i18n_privacy_settings_2_informed":"<b>Informato</b> Affermi di \
aver letto e compreso la politica sulla privacy di cui sopra",

    "i18n_privacy_settings_2_can_collect": "<b>Può salvare</b> Consenti \
a Neubot di salvare il tuo indirizzo Internet per scopi di ricerca",

    "i18n_privacy_settings_2_can_publish": "<b>Può pubblicare</b> Consenti \
a Neubot di pubblicare sul Web il tuo indirizzo Internet affinché possa essere riutilizzato per scopi di ricerca",

    "i18n_privacy_warning": "<b>ATTENZIONE! Neubot non eseguirà alcun \
test finché non confermi di aver letto la privacy policy e non gli \
fornisci il permesso di salvare e pubblicare il tuo indirizzo Internet</b>."

};
