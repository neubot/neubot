/* neubot/www/lang/it.js */
/*-
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita' degli Studi di Milano
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
    'i18n_infonav': "(informazione non disponibile)",
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

    'i18n_about_text': "Questa è l'interfaccia web di Neubot v0.3.7. Neubot è un programma <a href='http://www.neubot.org/copying'>open-source</a> leggero che viene eseguito in background ed esegue periodicamente test di trasmissione dati per testare la tua connessione a Internet utilizzando diversi protocolli applicativi. <a href='http://www.neubot.org/faq'>Leggi le FAQ</a>",

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

    "i18n_settings_par2": "Le modifiche alla configurazione non vengono\
                           inviate al demone Neubot finché non premi il tasto\
                           Save in fondo alla pagina.",

    // neubot/www/speedtest.html

    "i18n_speedtest_title": "Risultati dello speedtest",

    "i18n_speedtest_explanation_1": "Speedtest &egrave; un test che getta un po' di luce sulla qualit&agrave; della tua connessione a Internet, facendo download e upload di dati casuali a/da un server remoto, e riportando le velocit&agrave; medie. Il test stima anche (per eccesso) il round-trip time tra te e il server remoto.  Per maggiori informazioni, vedi le <a href='http://www.neubot.org/faq#what-does-speedtest-test-measures'>FAQ</a>.",

    "i18n_speedtest_explanation_2": "Per contestualizzare i risultati di questo test rispetto alla velocit&agrave; media disponibile nel tuo paese puoi far riferimento alle statistiche disponibili sul <a href='http://www.oecd.org/sti/ict/broadband'>Portale Banda larga OECD</a>.   In particolare, potrebbe essere interessante leggere <a href='http://www.oecd.org/dataoecd/10/53/39575086.xls'>'Average advertised download speeds, by country'</a> (in formato XLS).",

    "i18n_speedtest_see_last": "Guarda l'ultimo",
    "i18n_speedtest_see_last_days": "giorno",
    "i18n_speedtest_see_last_hours": "ora"

};
