.. _overview:

====================
Descrizione Generale
====================

.. _constraints_overview:

Vincoli generali
~~~~~~~~~~~~~~~~

.. _usability:

Usabilità
---------

Il target di riferimento (vedi :ref:`use_case`) non necessariamente possiede
nozioni tecniche informatiche specifiche; risulta quindi un vincolo importante
quello di presentare un'interfaccia:

    * semplice
    * intuitiva
    * ricca di indicazioni

Laddove non strettamente necessario si cercherà inoltre di ridurre le
interazioni con l'utente automatizzando quanto più possibile le scelte o,
perlomeno, fornendo sempre una scelta di default che possa adattarsi alle
esigenze della maggior parte degli utenti.

.. _repairability:

Riparabilità
------------

È chiaro che nonostante lo svolgimento di test, che siano essi manuali o
automatici, la possibilità che il software riscontri dei malfunzionamenti è una
realtà dei fatti, ma è importante minimizzare l'impatto che questi hanno sul
sistema e sul business dei clienti che lo utilizzano. Per questo motivo si
predisporrà la produzione costante di file di log e l'uso di strumenti
diagnostici per l'individuazione e la correzione tempestiva di problemi alla
base di malfunzionamenti e/o fallimenti del sistema.

Sarà previsto inoltre l'utilizzo di un sistema di controllo delle versioni che
tenga traccia delle modifiche apportate nel tempo e ne permetta il ripristino
in caso di malfunzionamenti.

.. _confidentiality:

Riservatezza
------------

Per assicurare la riservatezza dei dati inseriti dagli utenti durante la fase
di registrazione (con speciale riguardo per *password* e *dati di pagamento*)
sarà previsto l'utilizzo di moderne tecniche di crittografia.

Inoltre in nessun modo i dati degli utenti verranno ceduti a terze parti per
fini commerciali o altri scopi.

.. _security:

Protezione
----------

La protezione del software e dei dati utente che essa gestisce e mantiene deve
essere un requisito fondamentale per garantire la sicurezza degli utenti da
attacchi accidentali o deliberati. Per questo motivo si intende garantire una
politica quanto più possibile stringente di test e revisione del codice.

Inoltre si prevede che l'amministrazione dell'applicazione venga svolta solo da
dispositivi abilitati e sia inaccessibile al resto del mondo, così da diminuire
la superficie d'attacco al minimo indispensabile.

.. _system_functionalities_overview:

Funzionalità generali del sistema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _access_management:

Gestione accesso
----------------

Possibilità per gli utenti interessati di registrarsi al servizio. La
registrazione verrà differenziata a seconda del tipo di utente che può essere:

    privato
        un utente singolo che voglia utilizzare il servizio per scopi personali

    azienda
        un utente o gruppi di utenti afferenti alla stessa organizzazione che
        vogliano utilizzare il servizio per scopi commerciali

Gli utenti ospiti possono comunque accedere ai file audio resi pubblici dagli
utenti privati per fare le loro ricerche e testare il servizio anche in
valutazione di una possibile registrazione.

.. _payments_management:

Gestione pagamenti
------------------

Possibilità per gli utenti registrati di acquistare crediti per utilizzare il
servizio. L'acquisto richiederà all'utente di avere a disposizione un account
presso `PayPal <https://www.paypal.com/>`_.

A seconda che l'utente sia un privato o un'azienda avrà a disposizione diverse
opzioni di acquisto, quindi diversi prezzi; in particolare:

    privato
        potrà acquistare i crediti necessari a processare un singolo file audio
        per volta e dovrà utilizzare le impostazioni di default riguardo la
        precisione del risultato e altri parametri

    azienda
        potrà acquistare i crediti necessari con formula abbonamento annuale
        personalizzabile secondo le proprie necessità specificando alcuni
        parametri. Sarà anche possibile acquistare singolarmente delle
        estensioni per ottenere più crediti nel caso quelli avuti
        dall'abbonamento fossero esauriti prima della scadenza.

.. _contents_upload_management:

Gestione upload contenuti
-------------------------

Gli utenti, sia essi privati o aziende, che avessero correttamente eseguito
l'accesso al servizio e l'acquisto dei crediti necessari, avranno la
possibilità di fare l'upload di contenuti multimediali in diversi formati, sia
essi **audio** che **video** e in diverse codifiche.

L'utente privato avrà inoltre la possibilità di associare al servizio il
proprio account `Dropbox <https://www.dropbox.com/>`_ e scegliere da questo i
file di cui fare l'upload.

.. _requests_management:

Gestione richieste
------------------

Possibilità per gli utenti che hanno fatto l'upload di file multimediali, di
vederne lo stato di avanzamento del processamento prima di poter effettuare
delle ricerche.

Richieste precedenti rimangono salvate sul sistema e restano utilizzabili in
qualsiasi momento, anche in assenza di crediti. Le richieste precedenti possono
inoltre essere cancellate, modificate, utilizzate per fare ricerche e possono
essere rese pubbliche per l'utilizzo da parte di utenti non registrati, anche
tramite le API pubbliche esposte dal servizio.

.. todo::
    Aggiungi riferimento al documento sulle API

