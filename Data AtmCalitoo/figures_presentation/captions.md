# Didascalie e note per la presentazione intermedia (Calitoo, set–ott 2026)

Figure in `figures_presentation/` (PNG 300 dpi + PDF). Lingua nelle figure: `LANG = "en"`.

## 01_campaign_map

**Titolo slide:** Three sites across the Alps, one next to AERONET

**Messaggio:** Tre siti su entrambi i lati delle Alpi; Davos coincide con la stazione AERONET.

- 4 giornate: Zurigo 30/9 e 6/10 (n = 13), Davos 7/10 (n = 26), Lugano 10/10 (n = 20); 59 misure valide su 65.
- Davos: misure a 54 m dal fotometro AERONET del PMOD/WRC → confronto diretto possibile.
- Quote GPS: Zurigo ~455 m, Davos ~1596 m, Lugano ~438 m (non 270 m: verificato anche con la pressione).

*Caveat:* Contorno della Svizzera approssimato, solo indicativo.

## 02_data_quality

**Titolo slide:** Manual pointing is repeatable to 1–8 %

**Messaggio:** Le misure sono ripetibili; le 6 scartate sono riconoscibili dal segnale grezzo.

- CV dell'AOD 540 nm per sessione: 1–8 % (std/media, solo misure valide).
- Scartate 4 misure con fit di Ångström R² < 0.8 (colonna 16 del file) e 2 outlier (Zurigo 30/9 13:19, Davos 7/10 08:09): segnale −7 %/−22 %, AOD molto più alta.
- Il segnale grezzo cresce con l'elevazione solare come atteso; nessuna deriva evidente.

*Caveat:* Ripetibilità ≠ accuratezza: un errore di calibrazione non si vede qui (→ slide AERONET).

## 03_aot_overview

**Titolo slide:** AOD is low everywhere: 0.03–0.08 at 540 nm

**Messaggio:** Aria molto pulita in tutti i siti; differenze tra siti piccole rispetto all'incertezza.

- AOD 540 nm medio: Zurich 30 Sep 0.078, Zurich 6 Oct 0.055, Davos 7 Oct 0.053, Lugano 10 Oct 0.035.
- Differenza massima 0.043 (Zurigo 30/9 vs Lugano): è l'unica che supera ±0.03; le altre sono coerenti entro l'incertezza.
- Nessun effetto quota visibile: Davos (1600 m) ≈ Zurigo 6/10; Lugano (sud delle Alpi) il più basso.

*Caveat:* Un solo giorno per Davos e Lugano: differenze tra siti = anche differenze tra giorni/meteo.

## 04_aot_timeseries

**Titolo slide:** Stable within sessions – Zurich rose +41 % on 6 Oct afternoon

**Messaggio:** Dentro ogni sessione l'AOD è stabile; l'unica variazione forte è a Zurigo il 6/10.

- Zurigo 6/10: AOD 540 nm da 0.046 (10:57 UTC) a 0.065 (13:28 UTC), +41 %, α simile → più aerosol fine nel pomeriggio.
- Davos e Lugano: nessuna tendenza durante la sessione (variazioni entro il rumore).
- Le crocette sono le misure scartate (nuvola/puntamento): ben separate dal resto.

*Caveat:* Orari in UTC (verificato con l'elevazione solare calcolata); ora locale CEST = UTC+2.

## 05_spectrum_540_anomaly

**Titolo slide:** 540 nm falls below the Ångström fit on every day

**Messaggio:** Il canale 540 nm è sistematicamente basso rispetto agli altri due: primo indizio strumentale.

- Residuo a 540 nm: Zurich 30 Sep -4.8 %, Zurich 6 Oct -5.1 %, Davos 7 Oct -2.4 %, Lugano 10 Oct -5.3 %.
- Stesso segno in tutti i giorni e siti → non è l'aerosol, è lo strumento (costante CN0 o correzione ozono).
- α fittato: 1.66, 1.73, 1.62, 1.49 – sovrastimato (vedi confronto AERONET).

*Caveat:* Con 3 sole bande il fit è poco vincolato: il residuo è indicativo, AERONET lo conferma.

## 06_aeronet_timeseries_davos

**Titolo slide:** Calitoo matches AERONET in the blue, reads low at 540/619 nm

**Messaggio:** Stesso sito, stessa ora: Calitoo segue AERONET, ma verde e rosso sono sistematicamente bassi.

- AERONET a 54 m dal punto Calitoo; misure ogni ~3 min; Level 1.0 (non ancora Level 2.0 per ottobre 2026).
- Ångström: Calitoo 1.63 contro AERONET 1.02 sullo stesso intervallo (465–619) e 1.22 su 440–870.
- AERONET Level 1.0 non ha screening nuvole: l'ho fatto io (triplet variability, simile al Level 1.5).

*Caveat:* Una sola sessione di 50 min; Level 1.0 può ancora cambiare calibrazione.

## 07_aeronet_scatter

**Titolo slide:** Calitoo agrees with AERONET within ±0.03

**Messaggio:** Tutte le coppie sono entro ±0.03; il bias però cresce con la lunghezza d'onda.

- Bias (Calitoo − AERONET): 465 nm -0.0002, 540 nm -0.0063 (-11 %), 619 nm -0.0083 (-16 %); RMSE < 0.01.
- Nel blu accordo perfetto; nel verde/rosso Calitoo sottostima di ~0.006–0.008.
- Conseguenza: Ångström di Calitoo troppo alto (1.6 vs 1.0).

*Caveat:* Un solo giorno, AOD molto bassa (~0.05): l'errore relativo (11–16 %) è grande anche se quello assoluto è piccolo.

## 08_bias_vs_airmass

**Titolo slide:** Bias vs 1/m: compatible with a CN0 error, not conclusive

**Messaggio:** Il test 1/m non riesce a distinguere errore di calibrazione e offset costante: la massa d'aria varia troppo poco.

- Errore di CN0 ⇒ bias = −ε/m (b ≈ 0); offset tipo ozono ⇒ bias costante (a ≈ 0).
- Fit completo: a ≈ -0.067, b ≈ +0.024 a 540 nm, ma la stessa pendenza c'è a 465 nm (-0.051) dove il bias medio è zero → è una deriva comune nel tempo, non la calibrazione.
- Test relativo (bias 540 − bias 465): b = +0.001 ± 0.004 (≈ 0, come atteso per CN0), a = -0.016 ± 0.009 (1.8σ). Se fosse CN0: ε ≈ 1.4 % (540) e 1.8 % (619).

*Caveat:* Per decidere servono misure con m tra ~1.2 e 5 (mattina presto → mezzogiorno) in coincidenza con AERONET, o una calibrazione Langley.

## 09_modis_comparison

**Titolo slide:** MODIS agrees within its error – but its error > signal

**Messaggio:** MODIS è compatibile con terra in tutti i casi, ma a AOD ~0.04 il confronto non è un vero test.

- Zurigo 6/10: Calitoo 0.054 vs MODIS 0.043; Lugano 10/10: 0.033 vs 0.037; Davos 9/10: AERONET 0.021 vs MODIS 0.029.
- Incertezza MODIS ~±0.055 a questi valori: più grande dell'AOD stessa.
- I box sono grandi e non centrati (Lugano include la Pianura Padana, Zurigo la Germania meridionale).

*Caveat:* Solo 3 coppie; Davos 7/10 senza MODIS (nuvole). Servono MYD04_3K (3 km), MODIS-Terra, box centrati.

## 10_summary_table

**Titolo slide:** Campaign summary

**Messaggio:** Tabella riassuntiva per la slide finale.

- Una riga per giorno: n, AOD 540 nm, α, confronti disponibili.

*Caveat:* α da leggere alla luce del bias spettrale.
