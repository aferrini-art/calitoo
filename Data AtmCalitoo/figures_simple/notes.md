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

## 3b_calitoo_bern_vs_aeronet_davos_nov14.png
*Versione grafica `3b_calitoo_bern_vs_aeronet_davos_nov14_restyled.png`:* stessi dati, screening e confronto ±15 min, nello stile della figura 3 (cerchi = Near Bern, quadrati = Berna); i dettagli su metodo e distanze sono solo qui.
**Attenzione: confronto tra località diverse, non una validazione.** Le misure Calitoo del 14 novembre sono state fatte vicino a Berna (prova di calibrazione, prima delle 14:00 ora locale) e a Berna (dopo le 14:00); AERONET è a Davos, a circa 185 km (189 km da Near Bern, 182 km da Berna) e circa 1000 m più in alto (1589 m contro 518/573 m GPS). Il 14 novembre l'ora locale è CET = UTC + 1 h, quindi la separazione è alle 13:00 UTC (linea tratteggiata).
Dati: AERONET Davos, Version 3, Level 1.0, 14/11/2026 (`aeronet_data/20261114_20261114_Davos.csv`, da aeronet.gsfc.nasa.gov); screening nuvole fatto da noi come per il 7 ottobre (112 misure su 113), interpolazione alle lunghezze d'onda Calitoo e confronto ±15 min come per il 7 ottobre. Risultati in `output/calitoo_nov14_vs_aeronet_davos.csv`, separati dalle statistiche di validazione di Davos 7/10 (figura 5).
A Davos l'aria era pulitissima tutto il giorno (AOD 0.013–0.019 alle tre lunghezze d'onda). Calitoo misura valori molto più alti: vicino a Berna AOD 540 nm 0.056–0.100 (variabile, massima verso le 10:50 UTC e più bassa verso mezzogiorno), a Berna 0.041–0.045. Con lo stesso metodo del 7 ottobre (±15 min) la differenza Calitoo − AERONET a 540 nm è in media +0.067 vicino a Berna e +0.029 a Berna: è soprattutto la differenza tra i due siti (Altopiano contro alta quota), non un errore di calibrazione.
Misura esclusa: Near Bern 09:53 UTC (AOD 540 nm = 0.53, α = 0.08, segnale −65 %) è una nuvola; passa il controllo qualità della pipeline perché è da sola nella sua sessione, ed è esclusa qui con lo stesso criterio della figura 7 (AOD 540 > 2 × mediana). Da guardare con cautela: Near Bern 12:13 UTC (più alta delle altre due della stessa sessione) e Berna 14:46–14:50 UTC (sole a circa 9° di elevazione).

## 3c_calitoo_bern_vs_aeronet_payerne_nov14.png
*Versione grafica `3c_calitoo_bern_vs_aeronet_payerne_nov14_restyled.png`:* stessi dati, screening e confronto ±15 min, nello stile della figura 3 (cerchi = Near Bern, quadrati = Berna, simboli vuoti = nessun dato AERONET entro ±15 min); i dettagli su metodo e distanze sono solo qui.
**Confronto regionale, non una validazione nello stesso punto** (a differenza di Davos 7/10, dove Calitoo era a 54 m dal fotometro). Le misure Calitoo del 14 novembre sono state fatte vicino a Berna (prova di calibrazione, prima delle 14:00 ora locale) e a Berna (dopo le 14:00); la stazione AERONET più vicina con dati è Payerne (MeteoSwiss, 491 m, sull'Altopiano come Berna): 37 km da Near Bern (518 m GPS) e 42 km da Berna (573 m GPS). Il 14 novembre l'ora locale è CET = UTC + 1 h, quindi la separazione è alle 13:00 UTC (linea tratteggiata). Risultati in `output/calitoo_nov14_vs_aeronet_payerne.csv`, tenuti separati dalle statistiche di validazione di Davos 7/10 (figura 5).
Dati: AERONET Payerne, Version 3, **Level 1.5**, 14/11/2026 (`aeronet_data/20261114_20261114_Payerne.csv`, da aeronet.gsfc.nasa.gov; nuvole già filtrate da AERONET, quindi qui non si applica il nostro screening: 80 misure dalle 09:35 alle 14:55 UTC). Metodo: interpolazione log–log alle lunghezze d'onda Calitoo come per Davos (465 nm da 440/500 nm; 540 e 619 nm da 500/675 nm); ogni misura Calitoo è confrontata con la media AERONET entro ±15 min. Punti pieni = con AERONET entro ±15 min; punti vuoti = senza AERONET: le 5 misure Near Bern delle 08:25–09:01 UTC, prima dell'inizio dei dati Level 1.5 (nessun valore AERONET assegnato). Con AERONET: Near Bern 12 su 17, Berna 7 su 7.
Payerne e Calitoo hanno lo stesso andamento (AOD più alta in mattinata, più bassa nel pomeriggio). Differenza media Calitoo − Payerne a 540 nm: −0.010 vicino a Berna (da −0.023 a +0.008) e −0.017 a Berna (da −0.022 a −0.014); a 465 nm −0.009 e −0.024. Le differenze sono dentro ±0.03, ma a 37–42 km di distanza possono essere vere differenze tra i due luoghi (nebbia, inversione, inquinamento locale in novembre): non vanno lette come errore di calibrazione.
Misura esclusa: Near Bern 09:53 UTC (AOD 540 nm = 0.53, α = 0.08, segnale −65 %) è una nuvola; passa il controllo qualità della pipeline perché è da sola nella sua sessione, ed è esclusa qui con lo stesso criterio della figura 7 (AOD 540 > 2 × mediana). Da guardare con cautela: Near Bern 12:13 UTC (più alta delle altre due della stessa sessione) e Berna 14:46–14:50 UTC (sole a circa 9° di elevazione).

## 4_calitoo_vs_modis.png
Dove ci sono entrambi i dati (Zurigo 6/10, Lugano 10/10) Calitoo e MODIS danno valori simili, con differenze di circa 0.003–0.010.
Per Calitoo si usa la media delle misure nella finestra di confronto **assunta** per Aqua, 10:45–13:45 UTC (12:15 ± 1.5 h, cioè 11:45–14:45 ora locale il 14 novembre): l'orario effettivo del passaggio di Aqua non è stato verificato (l'orbita di Aqua si sta spostando verso orari più tardi). Per Davos 7/10 non c'è nessuna misura Calitoo nella finestra (misure 08:05–08:53 UTC) e la barra è la media di tutto il giorno (nella figura non è segnato).

**Barra "Bern area — 14 Nov".** Contiene solo le **9 misure** Calitoo che cadono nella finestra assunta: 10:49–12:13 UTC (11:49–13:13 ora locale), tutte fatte nel punto della prova di calibrazione circa 6.8 km a ovest del centro di Berna (46.966 N, 7.373 E, ~518 m GPS). AOD 550 nm = **0.074** ± 0.014 (deviazione standard delle 9 misure; 540 nm convertito a 550 nm con l'esponente di Ångström di ciascuna misura). Le misure fatte a Berna nel pomeriggio (13:47–14:49 UTC, 46.951 N, 7.460 E, AOD 550 nm 0.042) sono fuori dalla finestra e **non sono incluse**: mattina e pomeriggio non sono stati mediati insieme, perché l'AOD è calata durante la giornata (anche a Payerne) e la media avrebbe mescolato orari e luoghi diversi. Entrambi i punti sono comunque nella stessa cella MODIS da 1° e nella stessa area GIOVANNI.

MODIS non ha dati per Davos il 7 ottobre (nuvole) né per il 14 novembre: nel file GIOVANNI `Bern14.11.csv` (MYD08_D3 v6.1, area 6–9° E, 46–48° N) il 14 novembre ha il valore mancante −9999, quindi "MODIS: no data". In quel file c'è un valore solo il 7 novembre (0.062); dall'8 al 15 novembre mancano tutti. La causa non è nota: può essere nuvolosità nell'area (anche nebbia o nubi basse sull'Altopiano), neve sulle Alpi o il sole basso di novembre.

*Incertezza legata alle nuvole (14 novembre).* Dai dati: la misura delle 09:53 UTC è chiaramente una nuvola (AOD 540 nm = 0.53) ed è esclusa, ma è comunque fuori dalla finestra; la misura delle 12:13:31 UTC, dentro la finestra, è più alta delle altre due della stessa sessione e potrebbe essere disturbata da nuvole sottili (senza di essa la media resta 0.074). L'AOD vicino a Berna varia molto durante la mattinata (540 nm 0.056–0.100), quindi la presenza di nuvole sottili non si può escludere del tutto.

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
