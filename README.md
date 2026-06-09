Specifica Tecnica: Architettura della Pipeline Joivy Analytics


1. Introduzione e Finalità del Sistema

Nel competitivo mercato del co-living, l'asimmetria informativa rappresenta il principale ostacolo a una strategia di pricing dinamica. Il progetto Joivy Analytics è stato concepito per eliminare questa barriera, automatizzando la raccolta di dati immobiliari e trasformandoli in un asset informativo pronto per l'analisi statistica. L'architettura non si limita al semplice recupero di informazioni, ma implementa un workflow di trasformazione che converte dati web non strutturati in metriche azionabili per la Business Intelligence.

Per garantire scalabilità e resilienza, il sistema è stato ingegnerizzato seguendo una filosofia modulare, articolata in quattro componenti core:

* citynames: L'orchestratore iniziale che mappa i punti di ingresso.
* cityrooms: Il motore di estrazione asincrona ad alta efficienza.
* wrangling: Il layer di validazione semantica e normalizzazione.
* to_dataframe: Il modulo di strutturazione e persistenza dei dati.

Questa separazione delle responsabilità assicura che l'integrità del dato sia preservata lungo l'intero ciclo di vita, dal rendering nel browser alla persistenza nel database analitico.


2. Architettura dell'Estrazione: Scraping Multi-Livello e Asincrono

L'efficienza dell'acquisizione dati poggia su un modello a due stadi che bilancia determinismo operativo e performance di rete.

Identificazione e Navigazione Dinamica

La pipeline inizia con il modulo citynames, che utilizza Playwright in modalità sincrona per mappare gli URL delle città (es. /it/affitto-stanza-milano). Questo approccio garantisce un input deterministico per i successivi lavoratori asincroni.

Per gestire i contenuti dinamici, il sistema implementa una logica di navigazione avanzata:

* Paginazione Ricorsiva: Un ciclo while True monitora il caricamento delle liste stanze, confrontando l'URL corrente con quello richiesto per identificare il termine naturale della paginazione.
* Interazione Automata: All'interno di ogni stanza, il sistema esegue un bottone.click() sull'elemento "Mostra di più" per forzare il rendering dei dettagli nascosti (come i costi accessori), essenziale per la completezza del dataset.

Motore Asincrono e Gestione Risorse

Il modulo cityrooms eleva la velocità di estrazione tramite async_playwright. Per prevenire il sovraccarico dei sistemi e mitigare il rischio di ban IP, è stato implementato un Semaforo (SEMAPHORE_LIMIT = 10), limitando la concorrenza a 10 istanze simultanee.

La stabilità è garantita da parametri di runtime rigorosi:

* Wait State: Utilizzo di domcontentloaded per minimizzare i tempi di attesa.
* Timeout di Sicurezza: Un limite di 20,000ms per evitare processi zombie in caso di latenza del server.
* Resource Interception: La funzione block intercetta e abortisce il caricamento di immagini, fogli di stile (CSS), font e media, ottimizzando drasticamente il consumo di banda e la velocità di parsing del DOM.

Race Condition Prevention

Data la natura concorrente del processo, l'integrità del dizionario globale RECORDS_DATA è protetta da un asyncio.Lock (data_lock). Questo meccanismo di mutua esclusione assicura che la scrittura dei dati estratti avvenga in modo atomico, prevenendo corruzioni durante l'accesso simultaneo da parte dei worker.


3. Logica di Data Wrangling e Pulizia Semantica

Il valore strategico della pipeline risiede nel suo layer di Data Quality (DQ) Gate. Ogni record grezzo deve superare una serie di controlli di conformità prima di essere integrato nel dataset finale.

Requisiti di Validazione e Riduzione Dimensionale

Il sistema verifica che il DOM risponda a una firma strutturale precisa. Se la struttura del sito web cambia, il sistema attiva un "circuito di sicurezza" incrementando il contatore delle stanze_eliminate.

Requisito di Validazione	Motivazione Tecnica
len(info) == 8	Integrità strutturale della risposta del crawler.
Presenza "€" e "m²"	Conferma la corretta estrazione di prezzo e superficie.
Keyword "stanz", "inq", "lett"	Validazione della tipologia e della capienza.
Keyword "tot", "cond"	Conferma la presenza del dettaglio spese e configurazione locali.

In questa fase avviene una Dimensionality Reduction: il set iniziale di 8 elementi estratti viene ridotto a 5 attributi core tramite operazioni di pop() sugli indici 1 e 3. Questo processo elimina le etichette testuali ridondanti, isolando solo i valori necessari all'analisi.

Tipizzazione e Casting

Per consentire operazioni matematiche, i dati vengono convertiti nei seguenti tipi primitivi:

* price (int): Sanitizzazione del simbolo "€" e casting intero.
* max_tenants (int): Estratto dai primi due caratteri della stringa dedicata.
* baths (int): Derivato dall'indice info[2] dopo la pulizia.
* mq (float): Conversione della superficie previa rimozione dell'unità di misura.
* has_large_bed (bool): Mapping logico (False per "Singolo", True per altri formati).


4. Strategia di Persistenza e Strutturazione dei Dati

La trasformazione finale converte il dizionario nidificato in un DataFrame bidimensionale. Durante questa fase di Flattening, l'identificativo univoco id_room viene generato tramite string slicing (link[-13:-1]) dall'URL della pagina, garantendo la tracciabilità di ogni unità.

Schema dei Dati Finale

- city: string          (Localizzazione geografica)
- id_room: string       (Hash/ID derivato dall'URL)
- price: int            (Canone mensile normalizzato)
- max_tenants: int      (Capacità abitativa massima)
- mq: float             (Superficie calpestabile)
- has_large_bed: bool   (Presenza dotazioni premium)
- baths: int            (Numero di servizi igienici)


Il sistema predilige il formato Parquet con motore pyarrow. Rispetto al CSV tradizionale, Parquet offre una compressione colonnare superiore e tempi di caricamento ridotti del 70-80% nella dashboard Streamlit, ottimizzando l'esperienza dell'utente finale.


5. Visualizzazione Analitica: Dashboard Streamlit e Plotly

L'interfaccia di visualizzazione trasforma i dati grezzi in insight competitivi attraverso un'interfaccia reattiva e statisticamente rigorosa.

Ottimizzazione e Coerenza Visiva

* Caching Intelligente: L'implementazione di @st.cache_data evita il ricaricamento ridondante del file Parquet, mantenendo il DataFrame in memoria per tutte le interazioni della sessione.
* Branding Geografico: La funzione get_country_color_map impone una coerenza cromatica su 15 città in 4 nazioni:
  * Italia (IT): Toni del verde e marrone (es. Milano #2E7D32, Roma #4E342E).
  * Francia (FR): Scala di blu e rosa (es. Parigi #0D47A1, Lione #1976D2).
  * Spagna (ES): Arancione saturo per Madrid (#FF6D00).
  * Portogallo (PT): Rosso vivido per Lisbona (#D50000).
  * Fallback: Grigio neutro (#757575) per entità non mappate.

Analisi Statistica e Robustezza

La dashboard utilizza Plotly per la generazione di grafici di dispersione (Mq vs Prezzo, Inquilini vs Prezzo) integrando marginal box plots (marginal_x="box"). Questa scelta architettonica è fondamentale nel mercato immobiliare per visualizzare istantaneamente la distribuzione dei prezzi e identificare gli outlier (valori fuori mercato).

Infine, il sistema privilegia la Mediana come indicatore centrale nelle tabelle statistiche, garantendo una rappresentazione del mercato più veritiera e meno influenzata da inserzioni di lusso o anomalie nei dati estratti, consolidando la pipeline come uno strumento di decision-making di alto livello.
