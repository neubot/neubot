/* neubot/www/lang/it.js */
/*-
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita' degli Studi di Milano
 * Copyright (c) 2011 Claudio Artusio <claudioartusio@gmail.com>,
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

    /* neubot/www/header.html */

    'i18n_header_subtitle': "L'interfaccia web per controllare Neubot",
    'i18n_header_title': '<a href="index.html">Interfaccia Web di Neubot</a>',

    /*
     * i18n for javascripts
     * Map the string on the left to the string on the right via
     * the i18n.get() function.
     */

    'Latest test results': "Risultati ultimo test",
    'Current test results': "Risultati test corrente",
    'enabled': "attivo",
    'disabled': "disattivato",
    'Enable': "Attiva",
    'Disable': "Disattiva",
    'Test running': "Test in corso",

    'Your download and upload speed': "Risultati recenti",

    /*
     * i18n for HTML pages
     * To be translated a tag must belong to the i18n class
     * and an i18n_FOO class that idenfies the translation, i.e.
     * below on the left there is the i18n_FOO class and on
     * the right the corresponding translation.
     */

    'i18n_text_direction': "ltr",
    'i18n_settings': "Impostazioni",
    'i18n_status': "Stato",
    'i18n_speedtest': "Speedtest",
    'i18n_log': "Log",
    'i18n_privacy': "Privacy",
    'i18n_website': "Sito web di Neubot",
    'i18n_updavailable': "Aggiornamenti disponibili",
    'i18n_infonav': "N/A",
    'i18n_neubotis': "Neubot è",
    'i18n_resultof': "Risultati di",
    'i18n_latency': "Latenza",
    'i18n_dlspeed': "Velocità download",
    'i18n_ulspeed': "Velocità upload",
    'i18n_about': "Informazioni",
    'i18n_state': "Stato",
    'i18n_description': "Descrizione",
    'i18n_testnow': "Posso far partire un test <em>adesso</em>?",

    'i18n_testnow_text': "L'avvio manuale di un test non è ancora supportato dall'interfaccia web, ma è nella lista delle cose da fare. Al momento, l'unico modo per avviare un test è digitare il comando <b><em>neubot speedtest</em></b> nel terminale.",

    'i18n_idle_status_text': "L'Agent sta dormendo. Il prossimo rendezvous inizierà tra <em><span id='next_rendezvous'>(n/a)</span></em>.",

    'i18n_rendezvous_status_text': "L'Agent si sta connettendo al server di Neubot per reperire informazioni su test e aggiornamenti.",

    'i18n_negotiate_status_text': "L'Agent attende il turno per il test di trasmissione. L'ultima posizione nota in coda è <em><span id='queuePos'>(n/a)</span></em>.",

    'i18n_test_status_text': "Il test <em><span id='testName'>(n/a)</span></em> è in corso.",

    'i18n_collect_status_text': "L'Agent sta esegendo l'upload dei risultati sul server di Neubot.",

    'i18n_about_text': "Questa è l'interfaccia web di Neubot v0.4.2. Neubot è un programma <a href='http://www.neubot.org/copying'>open-source</a> leggero che viene eseguito in background ed esegue periodicamente test di trasmissione dati per testare la tua connessione a Internet utilizzando diversi protocolli applicativi. <a href='http://www.neubot.org/faq'>Leggi le FAQ</a>",

    'i18n_footer_text': "Neubot è un progetto di ricerca sulla neutralità della rete realizzato dal<br /><a href='http://nexa.polito.it/'>Centro NEXA su Internet &amp; Società</a> del <a href='http://www.dauin.polito.it/'>Politecnico di Torino</a>.",

    'i18n_welcome_text': "Grazie per aver installato Neubot! Ora avrai le idee più chiare sulla tua connessione a Internet e potrai aiutare la comunità a capire cosa accade nella rete. Questa sezione fornisce un prospetto generale dell'agent Neubot. Clicca sui vari tab per visualizzare le informazioni relative ai vari test.",

    'i18n_current_status': "Stato di Neubot",

    'i18n_status_text': "Questo è il pannello di controllo dell'Agent di Neubot, in esecuzione con PID <em><span id='pid'>(n/a)</span></em> da <em><span id='since'>(n/a)</span></em>. La tabella sottostante fornisce dettagli aggiuntivi sullo stato dell'Agent. La riga evidenziata rappresenta lo stato corrente.",

    // neubot/www/settings.html

    "i18n_settings_title": "Impostazioni",

    "i18n_settings_par1": "Questa pagina mostra tutte le opzioni di\
                           configurazione che possono essere modificate,\
                           inclusi i settaggi più oscuri e pericolosi.\
                           Perfavore, assicurati di sapere ciò che stai\
                           facendo prima di fare modifiche.  Non riceverai\
                           alcun tipo di aiuto se Neubot smette di funzionare\
                           per colpa di modifiche inopportune.",

    'i18n_settings_par2':
 'Alcune impostazioni, come ad esempio <code>agent.api.address</code>\
  e <code>agent.api.port</code>, hanno effetto solo al successivo\
  restart di Neubot.',

    // neubot/www/bittorrent.html

    "i18n_bittorrent_explanation": "Questo test fa il download e l'upload\
        di un certo numero di bytes da un server remoto, utilizzando il\
        protocollo BitTorrent.  Il test stima la velocità media di download\
        e upload così come il tempo richiesto per connettersi al server\
        remoto, che approssima il round-trip time.",

    "i18n_bittorrent_explanation_2": "Nota che questo test è abbastanza\
        differente dal test <em>Speedtest</em>, quindi ci sono casi in cui\
        i due non sono comparabili.  Stiamo lavorando a un test HTTP\
        che sia più simile a quest'ultimo, così che sia sempre possibile\
        compararli.",

    "i18n_bittorrent_see_last": "Guarda l'ultimo",
    "i18n_bittorrent_see_last_days": "giorno",
    "i18n_bittorrent_see_last_hours": "ora",

    // neubot/www/speedtest.html

    "i18n_speedtest_title": "Risultati dello speedtest",

    "i18n_speedtest_explanation_1": "Speedtest &egrave; un test che getta un po' di luce sulla qualit&agrave; della tua connessione a Internet, facendo download e upload di dati casuali a/da un server remoto, e riportando le velocit&agrave; medie. Il test stima anche (per eccesso) il round-trip time tra te e il server remoto.  Per maggiori informazioni, vedi le <a href='http://www.neubot.org/faq#what-does-speedtest-test-measures'>FAQ</a>.",

    "i18n_speedtest_explanation_2": "Per contestualizzare i risultati di questo test rispetto alla velocit&agrave; media disponibile nel tuo paese puoi far riferimento alle statistiche disponibili sul <a href='http://www.oecd.org/sti/ict/broadband'>Portale Banda larga OECD</a>.   In particolare, potrebbe essere interessante leggere <a href='http://www.oecd.org/dataoecd/10/53/39575086.xls'>'Average advertised download speeds, by country'</a> (in formato XLS).",

    "i18n_speedtest_see_last": "Guarda l'ultimo",
    "i18n_speedtest_see_last_days": "giorno",
    "i18n_speedtest_see_last_hours": "ora",

    // neubot/www/privacy.html

    'i18n_privacy_not_ok':
'Neubot è DISABILITATO perché non hai ancora impostato i\
 permessi relativi alla privacy. Puoi settarli qua sotto.',

    "i18n_privacy_explanation": "In questa pagina spieghiamo i dettagli della nostra <a href='#policy'>politica sulla privacy</a>, necessaria per essere conformi alla normativa europea in materia. Forniamo inoltre un semplice <a href='#dashboard'>quadro privacy</a> per gestire le autorizzazioni che deciderai di fornirci rispetto al trattamento del tuo indirizzo Internet, che è considerato dato personale nell'Unione Europea.",

    "i18n_privacy_title_1": "Politica sulla privacy",

    "i18n_privacy_policy": "$Versione: 1.5$\n\n\
Lo scopo di Neubot è quello di misurare la qualità e la neutralità della connessione a Internet e di condividere i risultati con la comunità di Internet, al fine di riequilibrare l'asimmetria informativa tra normali utenti e i Service Providers.\n\n\
Neubot non controlla o analizza il traffico Internet. Utilizza appena una piccola frazione della capacità di connessione per eseguire test di trasmissione in background, inviando e/o ricevendo dati casuali. Il risultato contiene misure di prestazioni come la velocità di download, la latenza o il carico percentuale del tuo computer. Inoltre, il risultato contiene il tuo indirizzo Internet. Dopo il test, il risultato viene caricato sui server di Neubot.\n\n\
Il progetto Neubot ha bisogno di raccogliere il tuo indirizzo Internet, perché ciò permette di inferire il tuo Internet Service Provider e di avere un'idea della tua posizione geografica. Questo è coerente per l'obbiettivo di Neubot di monitorare la qualità e la neutralità di Internet, per provider e area geografica.\n\n\
Tuttavia, in Europa gli indirizzi Internet sono dati personali. Pertanto, Neubot non può memorizzare, elaborare, o condividere il tuo indirizzo Internet senza il tuo *consenso informato* preventivo, in base alle disposizioni del 'Codice in Materia di Protezione dei Dati personali' `(Decreto 196/03) <http://www.garanteprivacy.it/garante/doc.jsp?ID=1311248>`_. In accordo con quanto previsto dalla legge, titolare del trattamento è il Centro NEXA di Internet &amp; Società, rappresentato dal suo co-direttore Juan Carlos De Martin.\n\n\
Neubot ti chiede di affermare esplicitamente di avete letto questa politica sulla privacy e di dare il consenso a raccogliere e condividere il tuo indirizzo IP. E si rifiuta di eseguire test finché non affermi di avere letto questo politica sulla privacy e non fornisci il permesso di raccogliere il tuo indirizzio IP. Il progetto ha bisogno almeno del consenso a raccogliere il tuo indirizzo Internet, perché altrimenti non può elaborare i tuoi risultati e pubblicare i dati aggregati. Se non dai a neubot il consenso di condividere, il tuo indirizzo Internet non verrà ovviamente condiviso con gli altri e verrà trattato unicamente dai ricercatori autorizzati dal titolare del trattamento. Ti preghiamo di notare che vi è un grande vantaggio nel condividere il tuo Indirizzo Internet, perché consente ad altri ricercatori di studiare e criticare la metodologia e i set di dati di Neubot. Ciò permetterà alla comunità dei ricercatori di comprendere meglio il funzionamento della rete.\n\n\
Il titolare del trattamento garantisce i diritti di cui all'articolo 7 del suddetto decreto. In sostanza, tu hai il controllo totale sui tuoi dati personali, puoi, ad esempio, intimare a Neubot di rimuovere il tuo indirizzo Internet dal proprio set di dati. Per esercitare i tuoi diritti, scrivi al Dipartimento di Automatica e Infomatica (DAUIN) - Politecnico di Torino - Corso Duca degli Abruzzi, 24 - 10129 Torino, ITALIA.",

    "i18n_privacy_title_2": "Quadro privacy",

    "i18n_privacy_settings_1": "Questo è lo status corrente delle tue impostazioni sulla privacy:",
    
    "i18n_privacy_settings_2_informed":"<b>Informato</b> Affermi di aver letto e compreso la politica sulla privacy di cui sopra",

    "i18n_privacy_settings_2_can_collect": "<b>Può collezionare</b> Consenti a Neubot di collezionare il tuo indirizzo Internet",

    "i18n_privacy_settings_2_can_share": "<b>Può condividere</b> Consenti a Neubot di condividere il tuo indirizzo Internet con la comunità di internet",

    "i18n_privacy_warning": "<b>ATTENZIONE! Neubot non eseguirà alcun test finché non confermi di aver letto la privacy policy e non gli fornisci il permesso di collezionare il tuo indirizzo Internet</b>."

};
