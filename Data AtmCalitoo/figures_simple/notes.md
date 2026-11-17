# Note per la presentazione intermedia – campagna Calitoo (set–ott 2026)

Solo misure che passano il controllo qualità (59 su 65). Orari in UTC (ora locale = UTC + 2 h).

## 1_aot_timeseries.png
L'AOT è bassa in tutti i giorni (circa 0.03–0.11) e il blu (465 nm) è sempre più alto del verde e del rosso, come atteso per aerosol fine.
Dentro ogni sessione i valori sono stabili; l'unica variazione evidente è a Zurigo il 6 ottobre, dove l'AOT sale tra mezzogiorno e il pomeriggio.

## 2_aot_by_site.png
L'AOT media a 540 nm va da 0.035 (Lugano) a 0.078 (Zurigo 30 settembre), con Zurigo 6 ottobre e Davos simili (circa 0.055).
Le differenze tra siti sono piccole e, con un solo giorno per sito, non si possono ancora separare dalle differenze tra giorni.

## 3_calitoo_vs_aeronet_davos.png
A Davos Calitoo e la stazione AERONET (a 54 m di distanza) seguono lo stesso andamento, e nel blu i valori coincidono.
Nel verde e nel rosso Calitoo è un po' più basso di AERONET (circa 0.006–0.008), quindi la calibrazione di questi due canali va verificata.

## 4_calitoo_vs_modis.png
Dove ci sono entrambi i dati (Zurigo 6/10, Lugano 10/10) Calitoo e MODIS danno valori simili, con differenze di circa 0.003–0.010.
A Davos il 7 ottobre MODIS non ha dati per le nuvole; Calitoo è la media nella finestra di passaggio del satellite (a Davos, che non ha misure in quella finestra, la media del giorno).

## 5_bias_vs_wavelength.png
A Davos la differenza media Calitoo − AERONET è praticamente zero a 465 nm, ma diventa negativa a 540 nm (−0.006, −11 %) e a 619 nm (−0.008, −16 %).
Tutte le differenze sono ben dentro l'incertezza tipica di Calitoo (±0.03), ma il fatto che crescano con la lunghezza d'onda fa pensare a un effetto strumentale (calibrazione o correzione dell'ozono) più che a rumore.

*Domanda per i docenti:* un bias che cresce con λ è più probabilmente un errore delle costanti di calibrazione dei canali 540/619 nm o della correzione per l'assorbimento dell'ozono? Come possiamo distinguerli?

## 6_langley_attempt_davos.png
Il grafico mostra ln(segnale) contro la massa d'aria con la retta estrapolata fino a m = 0, che darebbe la costante di calibrazione V0 di ogni banda (corretta per la distanza Terra–Sole, effetto di −0.1 %, trascurabile).
**Attenzione: non è un risultato.** Le misure coprono solo m ≈ 2.0–2.5, quindi l'estrapolazione fino a m = 0 è molto lunga: già l'errore statistico è circa ±3 % su V0, più grande dell'errore di calibrazione che vorremmo vedere (circa 1–2 %). Inoltre la Langley vale solo se l'AOT resta costante durante le misure, e a Davos varia leggermente. È un'illustrazione del problema, non una calibrazione.

*Domanda per i docenti:* possiamo avere le costanti CN0 usate dallo strumento (o dal software Calitoo) ed è possibile organizzare una vera Langley (mattina limpida, m da ~2 a ~6) a Davos o in un sito di alta quota?

## Domande e problemi aperti
- Pochi giorni di misura (4, un solo giorno per Davos e Lugano): servono più giornate per ogni sito.
- Calibrazione da verificare: i canali 540 e 619 nm sembrano leggermente bassi rispetto ad AERONET.
- Servono più misure in coincidenza con AERONET (Davos), possibilmente dalla mattina presto a mezzogiorno.
- MODIS (media su celle da 1°) è poco adatto con AOT così bassa: la sua incertezza è più grande del segnale.
- I dati AERONET di ottobre sono ancora Level 1.0 (non definitivi): il confronto va ripetuto con il Level 2.0.
