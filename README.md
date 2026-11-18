# Calitoo – aerosol optical depth campaign (Sep–Nov 2026)

Analysis of measurements taken with a **Calitoo** handheld sun photometer
(AOD at 465, 540 and 619 nm) in Zurich, Davos, Lugano and Bern. The Calitoo
measurements are compared with the **AERONET** station in Davos and with
**MODIS-Aqua** satellite data (downloaded from NASA GIOVANNI).

## Project structure

```
Data AtmCalitoo/
├── calitoo_*.txt               raw Calitoo exports, one file per day (see below)
├── aeronet_data/               AERONET Version 3 direct-sun AOD: Davos Level 1.0, 5–10 Oct 2026;
│                               Davos Level 1.0, 14 Nov 2026 (figure 3b, different location);
│                               Payerne Level 1.5, 14 Nov 2026 (figure 3c, regional comparison)
├── giovanni_data/              MODIS-Aqua MYD08_D3 v6.1 AOD 550 nm, area-averaged (GIOVANNI CSV + PNG)
│
├── plot_calitoo.py             1. read + merge Calitoo files, QC, per-session statistics, overview plots
├── compare_aeronet.py          2. Calitoo vs AERONET (Davos, 7 Oct)
├── compare_modis.py            3. Calitoo (and AERONET) vs MODIS-Aqua
├── make_presentation_figures.py 4. slide-ready figures + captions.md
├── make_simple_figures.py      5. simple figures + preliminary Langley fits
│
├── output/                     generated tables (CSV) and diagnostic plots
├── figures_presentation/       generated slide figures (PNG 300 dpi + PDF) and captions.md
└── figures_simple/             generated simple figures and notes.md (presentation notes)
```

### Measurement days

| File | Site(s) | Date |
|---|---|---|
| `calitoo_sep30.txt` | Zurich | 30 Sep 2026 |
| `calitoo_oct6.txt` | Zurich | 6 Oct 2026 |
| `calitoo_oct7.txt` | Davos (next to the AERONET station) | 7 Oct 2026 |
| `calitoo_oct10.txt` | Lugano | 10 Oct 2026 |
| `calitoo_nov14.txt` | Near Bern (calibration attempt, before 14:00 local) and Bern (after 14:00 local) | 14 Nov 2026 |

### Calitoo export format

Semicolon-separated, no header, one measurement per line, times in **UTC**:

`date; time; temperature (°C); pressure (hPa); raw counts 465; raw 540; raw 619; GPS altitude (m);
latitude (ddmm.mmmmm N); longitude (dddmm.mmmmm E); solar elevation (°); AOD 465; AOD 540; AOD 619;
Ångström exponent; R² of the Ångström fit`

The AOD values are taken **as computed by the instrument**; the scripts do not
recompute them from the raw counts. The instrument's calibration constants
(CN0) are not included in the export.

### 14 November 2026 update

- Added Aiyana's Calitoo measurements from `calitoo_nov14.txt`, kept as two locations:
  Near Bern (before 14:00 local) and Bern (after 14:00 local).
- Figure 3b compares them with AERONET Davos (Level 1.0, ~185 km away) and figure 3c with
  AERONET Payerne (Level 1.5, 37–42 km away). Neither station is collocated, so these
  comparisons are kept separate from the collocated Davos validation of 7 October.
- Figure 4 has one "Bern area — 14 Nov" bar from the nine measurements in the assumed Aqua
  comparison window (10:45–13:45 UTC). MODIS-Aqua data were downloaded for 6–9° E, 46–48° N
  (`giovanni_data/Bern14.11.csv`), but the 14 November value is missing, so the figure shows
  "MODIS: no data".

Details: [`figures_simple/notes.md`](Data%20AtmCalitoo/figures_simple/notes.md).

## Requirements

Python 3 (tested with 3.11) with `numpy`, `pandas` and `matplotlib`:

```
pip install numpy pandas matplotlib
```

## How to run

Run the scripts from inside `Data AtmCalitoo/`, in this order (each step reads
the tables written by the previous ones into `output/`):

```
cd "Data AtmCalitoo"
python3 plot_calitoo.py                # -> output/calitoo_all.csv, output/summary.csv, plots
python3 compare_aeronet.py             # -> output/calitoo_vs_aeronet.csv, ...
python3 compare_modis.py               # -> output/calitoo_vs_modis.csv, ...
python3 make_presentation_figures.py   # -> figures_presentation/
python3 make_simple_figures.py         # -> figures_simple/
```

To add a new measurement day, add the file to `FILE_SITES` in
`plot_calitoo.py` (and the site to `SITES` if it is new). A file containing two
acquisitions at different places can be split by local time, as done for
14 Nov.

## Quality control (summary)

A measurement is rejected if the instrument's Ångström-fit R² is below 0.80,
if it is a within-session outlier at 540 nm, or if it was taken more than 5 km
from the nominal site. See `plot_calitoo.py` for the details.

## Data sources

- AERONET: NASA Goddard Space Flight Center, <https://aeronet.gsfc.nasa.gov>
  (Davos site, PI listed in the file header). October 2026 data are Level 1.0
  (not final).
- MODIS-Aqua MYD08_D3 v6.1 via NASA GIOVANNI, <https://giovanni.gsfc.nasa.gov>
