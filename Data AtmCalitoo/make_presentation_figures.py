#!/usr/bin/env python3
"""Presentation figures for the Calitoo campaign (Sep–Oct 2026).

Reads the processed tables in output/ (run plot_calitoo.py, compare_aeronet.py and
compare_modis.py first) and writes slide-ready figures (PNG 300 dpi + PDF) and
captions.md to figures_presentation/.
"""
LANG = "en"            # "en" or "it": language of the text inside the figures
CN0_SCENARIO = False   # True: also draw 08b (CN0 correction) even if the 1/m test is not conclusive

import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon, Rectangle

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
FIG = BASE / "figures_presentation"

WL = np.array([465, 540, 619])
BANDS = [f"aot_{w}" for w in WL]
BAND_COLORS = {465: "#1f5fbf", 540: "#2e9a3a", 619: "#d23a2a"}
SITE_COLORS = {"Zurich": "#7c5cd6", "Davos": "#14a3a3", "Lugano": "#c98500"}
DAY_MARKERS = {"2026-09-30": "o", "2026-10-06": "s", "2026-10-07": "^", "2026-10-10": "D"}
AER_COLOR, MODIS_COLOR, REJ_COLOR, CAPTION_COLOR = "#111111", "#8a8a8a", "#9a9a9a", "#555555"
CAL_UNC, AER_UNC = 0.03, 0.01
EE = lambda x: 0.05 + 0.15 * x
WIDE, NARROW = (10, 5.6), (6, 5.6)
MONTHS = {"en": {9: "Sep", 10: "Oct"}, "it": {9: "set", 10: "ott"}}
AERONET_LATLON = (46.81281, 9.84369)

# approximate Swiss border (hand-digitised, ~±5 km), (lon, lat)
CH_BORDER = [
    (7.59, 47.59), (7.70, 47.54), (7.91, 47.55), (8.10, 47.56), (8.23, 47.62), (8.42, 47.58),
    (8.40, 47.67), (8.48, 47.78), (8.62, 47.80), (8.72, 47.72), (8.80, 47.74), (8.87, 47.66),
    (9.03, 47.67), (9.18, 47.66), (9.38, 47.56), (9.56, 47.54), (9.67, 47.38), (9.53, 47.27),
    (9.48, 47.10), (9.61, 47.06), (9.88, 47.02), (10.10, 46.85), (10.39, 46.98), (10.49, 46.92),
    (10.45, 46.75), (10.49, 46.60), (10.30, 46.55), (10.20, 46.63), (10.05, 46.54), (10.16, 46.39),
    (10.10, 46.23), (9.95, 46.38), (9.70, 46.30), (9.47, 46.48), (9.28, 46.50), (9.25, 46.25),
    (9.02, 46.05), (9.08, 45.88), (8.95, 45.83), (8.85, 45.98), (8.72, 46.10), (8.60, 46.12),
    (8.45, 46.23), (8.42, 46.46), (8.10, 46.26), (7.98, 46.00), (7.86, 45.92), (7.55, 45.98),
    (7.04, 45.92), (6.86, 46.13), (6.79, 46.39), (6.52, 46.45), (6.24, 46.30), (6.12, 46.15),
    (5.96, 46.13), (6.11, 46.25), (6.07, 46.41), (6.14, 46.55), (6.43, 46.76), (6.46, 46.95),
    (6.70, 47.04), (6.98, 47.27), (6.95, 47.42), (7.13, 47.50), (7.43, 47.44), (7.53, 47.48)]


def f3(v):
    """3-decimal format, rounding half up (0.0365 -> 0.037) for consistency with the console reports."""
    return f"{np.floor(v * 1000 + 0.5 + 1e-9) / 1000:.3f}"


def L(en, it):
    return en if LANG == "en" else it


def setup_style():
    plt.rcParams.update({
        "font.size": 13, "axes.titlesize": 18, "axes.labelsize": 15,
        "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12,
        "figure.titlesize": 18, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "legend.frameon": False, "savefig.dpi": 300, "pdf.fonttype": 42, "figure.dpi": 100,
    })


def day_label(site, date, short=False):
    d = pd.Timestamp(date)
    s = f"{d.day} {MONTHS[LANG][d.month]}"
    return s if short else f"{site} {s}"


def finish(fig, name, title, caption, rect_bottom=0.1, layout=True, wrap=120):
    """Slide title (= message), small caption at the bottom, PNG + PDF at exact 16:9 / 6×5.6."""
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold")
    if layout:
        fig.tight_layout(rect=(0, rect_bottom, 1, 1))
    fig.text(0.01, 0.012, "\n".join(textwrap.wrap(caption, wrap)), fontsize=10.5,
             color=CAPTION_COLOR, ha="left", va="bottom")
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}")
    plt.close(fig)
    print(f"  saved {name}.png/.pdf")


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
def load():
    cal = pd.read_csv(OUT / "calitoo_all.csv", parse_dates=["datetime_utc"])
    cal["date"] = cal["datetime_utc"].dt.strftime("%Y-%m-%d")
    cal["key"] = cal["site"] + " " + cal["date"]
    order = cal.groupby("key")["datetime_utc"].min().sort_values().index.tolist()
    summ = pd.read_csv(OUT / "summary.csv")
    am = pd.read_csv(OUT / "calitoo_vs_aeronet.csv")
    aer = pd.read_csv(OUT / "aeronet_davos_screened.csv", parse_dates=["datetime_utc"])
    cvm = pd.read_csv(OUT / "calitoo_vs_modis.csv")
    avm = pd.read_csv(OUT / "aeronet_vs_modis.csv") if (OUT / "aeronet_vs_modis.csv").exists() else None
    boxes = pd.read_csv(OUT / "modis_bboxes.csv")
    return dict(cal=cal, ok=cal[cal["qc_ok"]], order=order, summ=summ,
                am=am[am["window_min"] == 15].reset_index(drop=True), aer=aer, cvm=cvm,
                avm=avm, boxes=boxes)


def day_stats(ok):
    rows = []
    for key, g in ok.groupby("key", sort=False):
        mean = g[BANDS].mean().values
        p = np.polyfit(np.log(WL / 1000), np.log(mean), 1)
        fit = np.exp(np.polyval(p, np.log(WL / 1000)))
        rows.append(dict(key=key, site=g["site"].iat[0], date=g["date"].iat[0], n=len(g),
                         aot540=g["aot_540"].mean(), aot540_std=g["aot_540"].std(),
                         alpha_col15=g["angstrom"].mean(), alpha_fit=-p[0], beta=np.exp(p[1]),
                         **{f"mean_{w}": m for w, m in zip(WL, mean)},
                         **{f"res_{w}": 100 * (m / f - 1) for w, m, f in zip(WL, mean, fit)}))
    return pd.DataFrame(rows).set_index("key")


def solar_elevation(t, lat, lon):
    """Low-precision solar elevation (Astronomical Almanac), degrees; t = UTC timestamps."""
    n = (pd.DatetimeIndex(t).to_julian_date() - 2451545.0).values
    Lm = np.radians((280.460 + 0.9856474 * n) % 360)
    g = np.radians((357.528 + 0.9856003 * n) % 360)
    lam = Lm + np.radians(1.915 * np.sin(g) + 0.020 * np.sin(2 * g))
    eps = np.radians(23.439 - 4e-7 * n)
    ra = np.arctan2(np.cos(eps) * np.sin(lam), np.cos(lam))
    dec = np.arcsin(np.sin(eps) * np.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    ha = np.radians((gmst + np.asarray(lon) / 15) * 15) - ra
    la = np.radians(np.asarray(lat))
    return np.degrees(np.arcsin(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)))


def fit_lin(x, y):
    p, cov = np.polyfit(x, y, 1, cov=True)
    a0 = (x @ y) / (x @ x)
    se0 = np.sqrt(((y - a0 * x) ** 2).sum() / (len(y) - 1) / (x @ x))
    return dict(a=p[0], b=p[1], sa=np.sqrt(cov[0, 0]), sb=np.sqrt(cov[1, 1]), a0=a0, sa0=se0,
                rms_full=np.sqrt(((y - np.polyval(p, x)) ** 2).mean()),
                rms_a0=np.sqrt(((y - a0 * x) ** 2).mean()),
                rms_b=np.sqrt(((y - y.mean()) ** 2).mean()), mean=y.mean())


def swiss(ax, **kw):
    ax.add_patch(Polygon(CH_BORDER, closed=True, facecolor=kw.get("fc", "#f3f3f0"),
                         edgecolor=kw.get("ec", "#9a9a9a"), lw=kw.get("lw", 1.2), zorder=0))


# ---------------------------------------------------------------------------
# FIGURES
# ---------------------------------------------------------------------------
CAPS = {}


def fig01_map(D, S):
    fig, ax = plt.subplots(figsize=WIDE)
    swiss(ax)
    for name, (lo, la) in {L("FRANCE", "FRANCIA"): (6.25, 47.05), L("GERMANY", "GERMANIA"): (8.2, 47.85),
                           L("ITALY", "ITALIA"): (7.7, 45.85), "AUSTRIA": (10.25, 47.3)}.items():
        ax.text(lo, la, name, fontsize=12, color="#b5b5b5", ha="center", va="center")
    place = {"Zurich": ((-20, 16), "right", "bottom"), "Davos": ((22, -6), "left", "top"),
             "Lugano": ((22, -4), "left", "top")}
    for site, g in D["ok"].groupby("site"):
        lat, lon = g["lat"].mean(), g["lon"].mean()
        ax.plot(lon, lat, "o", color=SITE_COLORS[site], ms=15, mec="black", mew=1.2, zorder=4)
        dates = ", ".join(day_label(site, d, short=True) for d in sorted(g["date"].unique()))
        alt_all = D["cal"].loc[D["cal"]["site"] == site, "alt_m"].median()
        txt = f"{site} · {alt_all:.0f} m\n{dates} · n = {len(g)}"
        if site == "Davos":
            txt += "\n" + L("★ AERONET station (54 m away)", "★ stazione AERONET (a 54 m)")
        off, ha, va = place[site]
        ax.annotate(txt, (lon, lat), xytext=off, textcoords="offset points", ha=ha, va=va,
                    fontsize=13, fontweight="bold", color="#222222",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=SITE_COLORS[site], lw=1.5))
    ax.plot(AERONET_LATLON[1], AERONET_LATLON[0], "*", color=AER_COLOR, ms=13, zorder=5)
    ax.set_xlim(5.8, 10.75)
    ax.set_ylim(45.75, 47.95)
    ax.set_aspect(1 / np.cos(np.radians(46.8)))
    ax.set_xlabel(L("Longitude (°E)", "Longitudine (°E)"))
    ax.set_ylabel(L("Latitude (°N)", "Latitudine (°N)"))
    title = L("Three sites across the Alps, one next to AERONET", "Tre siti attraverso le Alpi, uno accanto ad AERONET")
    finish(fig, "01_campaign_map", title,
           L("n = QC-passed measurements; altitude = median GPS. Border approximate (hand-digitised). "
             "All times in the campaign are UTC.",
             "n = misure che passano il QC; quota = mediana GPS. Confine approssimato (digitalizzato a mano). "
             "Tutti gli orari sono UTC."), rect_bottom=0.06)
    ok = D["ok"]
    CAPS["01_campaign_map"] = dict(
        title=title, msg="Tre siti su entrambi i lati delle Alpi; Davos coincide con la stazione AERONET.",
        bullets=[f"4 giornate: Zurigo 30/9 e 6/10 (n = {(ok.site == 'Zurich').sum()}), Davos 7/10 "
                 f"(n = {(ok.site == 'Davos').sum()}), Lugano 10/10 (n = {(ok.site == 'Lugano').sum()}); "
                 f"{len(ok)} misure valide su {len(D['cal'])}.",
                 "Davos: misure a 54 m dal fotometro AERONET del PMOD/WRC → confronto diretto possibile.",
                 f"Quote GPS: Zurigo ~455 m, Davos ~1596 m, Lugano ~{S['lugano_gps']:.0f} m (non 270 m: "
                 "verificato anche con la pressione)."],
        caveat="Contorno della Svizzera approssimato, solo indicativo.")


def fig02_quality(D, S):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=WIDE, gridspec_kw=dict(width_ratios=[1, 1.15]))
    sm = D["summ"].copy()
    sm["cv"] = 100 * sm["aot_540_std"] / sm["aot_540_mean"]
    sm = sm.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(sm))
    a1.barh(y, sm["cv"], color=[SITE_COLORS[s] for s in sm["site"]], height=0.65)
    for i, r in sm.iterrows():
        a1.text(r["cv"] + 0.2, i, f"{r['cv']:.0f}%", va="center", fontsize=12)
    a1.set_yticks(y)
    a1.set_yticklabels([f"{day_label(r.site, r.date)} {r.start_utc[:5]}" for r in sm.itertuples()],
                       fontsize=12)
    a1.set_xlabel(L("CV of AOT 540 nm per session (%)", "CV dell'AOT 540 nm per sessione (%)"))
    a1.set_xlim(0, max(10, sm["cv"].max() * 1.3))
    a1.grid(axis="y", visible=False)
    a1.set_title(L("(a) repeatability", "(a) ripetibilità"), fontsize=15)

    cal = D["cal"]
    for site, g in cal[cal["qc_ok"]].groupby("site"):
        a2.scatter(g["sun_elev_deg"], g["raw_540"], color=SITE_COLORS[site], s=40,
                   edgecolor="white", lw=0.6, label=site, zorder=3)
    r2 = cal[cal["qc_low_r2"]]
    out = cal[cal["qc_outlier"] & ~cal["qc_low_r2"]]
    a2.scatter(r2["sun_elev_deg"], r2["raw_540"], marker="x", color=REJ_COLOR, s=90, lw=2.5, zorder=4,
               label=L(f"rejected: fit R² < 0.8 ({len(r2)})", f"scartata: R² fit < 0.8 ({len(r2)})"))
    a2.scatter(out["sun_elev_deg"], out["raw_540"], marker="P", color=REJ_COLOR, s=110, zorder=4,
               edgecolor="black", lw=0.6,
               label=L(f"rejected: outlier ({len(out)})", f"scartata: outlier ({len(out)})"))
    a2.set_xlabel(L("Solar elevation (°)", "Elevazione solare (°)"))
    a2.set_ylabel(L("Raw signal 540 nm (counts)", "Segnale grezzo 540 nm (conteggi)"))
    a2.set_title(L("(b) raw signal, rejected", "(b) segnale grezzo, scartate"), fontsize=15)
    a2.legend(loc="upper left", bbox_to_anchor=(-0.12, -0.17), ncol=2, fontsize=11, columnspacing=0.8,
              handletextpad=0.3)
    title = L("Manual pointing is repeatable to 1–8 %", "Il puntamento manuale è ripetibile all'1–8 %")
    finish(fig, "02_data_quality", title,
           L(f"{len(D['ok'])}/{len(cal)} measurements pass QC. Rejected points have a lower raw signal "
             "(thin cloud or mispointing). Session times UTC.",
             f"{len(D['ok'])}/{len(cal)} misure passano il QC. Le scartate hanno segnale grezzo più basso "
             "(nuvola sottile o puntamento). Orari UTC."), rect_bottom=0.07)
    CAPS["02_data_quality"] = dict(
        title=title, msg="Le misure sono ripetibili; le 6 scartate sono riconoscibili dal segnale grezzo.",
        bullets=[f"CV dell'AOT 540 nm per sessione: {sm['cv'].min():.0f}–{sm['cv'].max():.0f} % "
                 "(std/media, solo misure valide).",
                 f"Scartate {len(r2)} misure con fit di Ångström R² < 0.8 (colonna 16 del file) e "
                 f"{len(out)} outlier (Zurigo 30/9 13:19, Davos 7/10 08:09): segnale −7 %/−22 %, AOT molto più alta.",
                 "Il segnale grezzo cresce con l'elevazione solare come atteso; nessuna deriva evidente."],
        caveat="Ripetibilità ≠ accuratezza: un errore di calibrazione non si vede qui (→ slide AERONET).")


def fig03_overview(D, S):
    fig, ax = plt.subplots(figsize=WIDE)
    ok, cal = D["ok"], D["cal"]
    keys = D["order"]
    rng = np.random.default_rng(1)
    meds = []
    for i, k in enumerate(keys):
        g = ok[ok["key"] == k]
        site, date = g["site"].iat[0], g["date"].iat[0]
        med = g["aot_540"].median()
        meds.append(med)
        ax.fill_between([i - 0.38, i + 0.38], med - CAL_UNC, med + CAL_UNC, color="#d9d9d9",
                        alpha=0.6, lw=0, zorder=0)
        ax.boxplot(g["aot_540"], positions=[i], widths=0.45, showfliers=False,
                   medianprops=dict(color="black", lw=2), boxprops=dict(color="#555555"),
                   whiskerprops=dict(color="#555555"), capprops=dict(color="#555555"))
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(g)), g["aot_540"], color=SITE_COLORS[site],
                   marker=DAY_MARKERS[date], s=45, edgecolor="white", lw=0.6, zorder=3)
        b = cal[(cal["key"] == k) & ~cal["qc_ok"]]
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(b)), b["aot_540"], marker="x", color=REJ_COLOR,
                   s=70, lw=2, zorder=3)
        ax.text(i, 0.168, f"{g['aot_540'].mean():.3f}", ha="center", fontsize=13, fontweight="bold",
                color=SITE_COLORS[site])
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([day_label(k.split()[0], k.split()[1]).replace(" ", "\n", 1) for k in keys])
    ax.set_ylabel("AOT 540 nm")
    ax.set_ylim(0, 0.18)
    ax.set_yticks(np.arange(0, 0.161, 0.04))
    ax.set_xlim(-0.6, len(keys) - 0.4)
    h = [Patch(color="#d9d9d9", label=L("±0.03 Calitoo uncertainty around median",
                                        "±0.03 incertezza Calitoo attorno alla mediana")),
         Line2D([], [], marker="x", color=REJ_COLOR, ls="", ms=9, mew=2, label=L("rejected (QC)", "scartate (QC)"))]
    ax.legend(handles=h, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=12)
    spread = max(meds) - min(meds)
    title = L("AOT is low everywhere: 0.03–0.08 at 540 nm", "AOT bassa ovunque: 0.03–0.08 a 540 nm")
    finish(fig, "03_aot_overview", title,
           L(f"Numbers on top = mean AOT 540 nm. Most site/day differences are within ±0.03; the largest "
             f"(Zurich 30 Sep vs Lugano, {spread:.3f}) slightly exceeds it. A calibration error would shift "
             "all sites alike, so relative differences are more robust than absolute values.",
             f"Numeri = AOT media 540 nm. Quasi tutte le differenze sono entro ±0.03; la maggiore "
             f"(Zurigo 30/9 vs Lugano, {spread:.3f}) lo supera di poco. Un errore di calibrazione sposta "
             "tutti i siti allo stesso modo: le differenze relative sono più robuste dei valori assoluti."),
           rect_bottom=0.13)
    st = S["days"]
    CAPS["03_aot_overview"] = dict(
        title=title, msg="Aria molto pulita in tutti i siti; differenze tra siti piccole rispetto all'incertezza.",
        bullets=["AOT 540 nm medio: " + ", ".join(f"{day_label(r.site, r.date)} {r.aot540:.3f}"
                                                  for r in st.itertuples()) + ".",
                 f"Differenza massima {spread:.3f} (Zurigo 30/9 vs Lugano): è l'unica che supera ±0.03; "
                 "le altre sono coerenti entro l'incertezza.",
                 "Nessun effetto quota visibile: Davos (1600 m) ≈ Zurigo 6/10; Lugano (sud delle Alpi) il più basso."],
        caveat="Un solo giorno per Davos e Lugano: differenze tra siti = anche differenze tra giorni/meteo.")


def fig04_timeseries(D, S):
    keys = D["order"]
    ok, cal = D["ok"], D["cal"]
    fig, axes = plt.subplots(1, len(keys), figsize=WIDE, sharey=True)
    for ax, k in zip(axes, keys):
        g, b = ok[ok["key"] == k], cal[(cal["key"] == k) & ~cal["qc_ok"]]
        for w in WL:
            for _, s in g.groupby("session"):
                ax.plot(s["datetime_utc"], s[f"aot_{w}"], "-o", color=BAND_COLORS[w], lw=1.8, ms=4)
            ax.plot(b["datetime_utc"], b[f"aot_{w}"], "x", color=REJ_COLOR, ms=7, mew=1.8)
        span = (g["datetime_utc"].max() - g["datetime_utc"].min()).total_seconds() / 60
        step = next(s for s in (2, 10, 15, 30, 60, 120) if span / s <= 3.5)
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, step)) if step < 60
                                   else mdates.HourLocator(interval=step // 60))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
        ax.tick_params(axis="x", labelsize=11, rotation=35)
        ax.set_title(day_label(g["site"].iat[0], g["date"].iat[0]), fontsize=14, color=SITE_COLORS[g["site"].iat[0]])
    axes[0].set_ylabel("AOT")
    axes[0].set_ylim(0, 0.14)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.83, bottom=0.31, wspace=0.12)
    fig.supxlabel(L("Time (UTC)", "Ora (UTC)"), fontsize=15, y=0.13)
    h = [Line2D([], [], color=BAND_COLORS[w], marker="o", lw=2, ms=5, label=f"{w} nm") for w in WL]
    h.append(Line2D([], [], marker="x", color=REJ_COLOR, ls="", ms=8, mew=2, label=L("rejected (QC)", "scartate (QC)")))
    fig.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, 0.055), ncol=4)
    zs = D["summ"][(D["summ"]["site"] == "Zurich") & (D["summ"]["date"] == "2026-10-06")]
    rise = 100 * (zs["aot_540_mean"].iat[1] / zs["aot_540_mean"].iat[0] - 1)
    title = L(f"Stable within sessions – Zurich rose {rise:+.0f} % on 6 Oct afternoon",
              f"Stabile nelle sessioni – Zurigo {rise:+.0f} % il 6/10 pomeriggio")
    finish(fig, "04_aot_timeseries", title,
           L("Same y scale for all days; lines connect measurements of the same session. Local time = UTC + 2 h.",
             "Stessa scala y per tutti i giorni; le linee uniscono misure della stessa sessione. Ora locale = UTC + 2 h."),
           layout=False)
    CAPS["04_aot_timeseries"] = dict(
        title=title, msg="Dentro ogni sessione l'AOT è stabile; l'unica variazione forte è a Zurigo il 6/10.",
        bullets=[f"Zurigo 6/10: AOT 540 nm da {zs['aot_540_mean'].iat[0]:.3f} (10:57 UTC) a "
                 f"{zs['aot_540_mean'].iat[1]:.3f} (13:28 UTC), {rise:+.0f} %, α simile → più aerosol fine nel pomeriggio.",
                 "Davos e Lugano: nessuna tendenza durante la sessione (variazioni entro il rumore).",
                 "Le crocette sono le misure scartate (nuvola/puntamento): ben separate dal resto."],
        caveat="Orari in UTC (verificato con l'elevazione solare calcolata); ora locale CEST = UTC+2.")


def fig05_spectrum(D, S):
    st = S["days"]
    fig = plt.figure(figsize=WIDE)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.1, 1], hspace=0.08)
    ax, ar = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    lf = np.linspace(455, 630, 40)
    for i, r in enumerate(st.itertuples()):
        col, mk = SITE_COLORS[r.site], DAY_MARKERS[r.date]
        mean = [getattr(r, f"mean_{w}") for w in WL]
        ax.plot(WL, mean, mk, color=col, ms=10, mec="white", zorder=3)
        ax.plot(lf, r.beta * (lf / 1000) ** (-r.alpha_fit), "-", color=col, lw=1.8)
        ax.plot([], [], "-", marker=mk, color=col, ms=9, mec="white", lw=1.8,
                label=f"{day_label(r.site, r.date)}  α = {r.alpha_fit:.2f}")
        off = (i - 1.5) * 4
        ar.plot(WL + off, [getattr(r, f"res_{w}") for w in WL], mk, color=col, ms=9, mec="white")
    for a in (ax, ar):
        a.set_xscale("log")
        a.set_xticks(WL)
        a.set_xticklabels([str(w) for w in WL])
        a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        a.set_xlim(445, 645)
    ax.set_yscale("log")
    yt = [0.03, 0.04, 0.05, 0.06, 0.08, 0.1]
    ax.set_yticks(yt)
    ax.set_yticklabels([f"{v:g}" for v in yt])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.tick_params(labelbottom=False)
    ax.set_ylabel("AOT")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), title="fit AOT = β·λ$^{-α}$")
    ar.axhline(0, color="black", lw=1)
    ar.axvspan(525, 555, color="#2e9a3a", alpha=0.12, lw=0)
    ar.set_ylabel(L("residual (%)", "residuo (%)"))
    ar.set_xlabel(L("Wavelength (nm)", "Lunghezza d'onda (nm)"))
    lim = np.ceil(np.abs(st[[f"res_{w}" for w in WL]].values).max() + 1)
    ar.set_ylim(-lim, lim)
    n_neg = int((st["res_540"] < 0).sum())
    title = (L("540 nm falls below the Ångström fit on every day", "540 nm cade sotto il fit di Ångström in ogni giorno")
             if n_neg == len(st) else
             L(f"540 nm falls below the fit on {n_neg}/{len(st)} days", f"540 nm sotto il fit in {n_neg}/{len(st)} giorni"))
    fig.subplots_adjust(left=0.1, right=0.72, top=0.86, bottom=0.2)
    finish(fig, "05_spectrum_540_anomaly", title,
           L("Daily mean of QC-passed measurements; residual = AOT / fit − 1 (with 3 bands, a low 540 nm pushes "
             "465/619 above the fit). The same bend on every day and site points to the instrument, not the aerosol.",
             "Media giornaliera delle misure valide; residuo = AOT / fit − 1 (con 3 bande, 540 basso spinge 465/619 "
             "sopra il fit). La stessa piega in ogni giorno e sito indica lo strumento, non l'aerosol."), layout=False)
    CAPS["05_spectrum_540_anomaly"] = dict(
        title=title, msg="Il canale 540 nm è sistematicamente basso rispetto agli altri due: primo indizio strumentale.",
        bullets=["Residuo a 540 nm: " + ", ".join(f"{day_label(r.site, r.date)} {r.res_540:+.1f} %" for r in st.itertuples()) + ".",
                 "Stesso segno in tutti i giorni e siti → non è l'aerosol, è lo strumento (costante CN0 o correzione ozono).",
                 "α fittato: " + ", ".join(f"{r.alpha_fit:.2f}" for r in st.itertuples())
                 + " – sovrastimato (vedi confronto AERONET)."],
        caveat="Con 3 sole bande il fit è poco vincolato: il residuo è indicativo, AERONET lo conferma.")


def fig06_aeronet_ts(D, S):
    aer = D["aer"]
    a = aer[aer["datetime_utc"].dt.strftime("%Y-%m-%d") == "2026-10-07"]
    ok_a, bad = a[a["screened_ok"]], a[~a["screened_ok"]]
    cal = D["ok"][D["ok"]["site"] == "Davos"]
    fig = plt.figure(figsize=WIDE)
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.1)
    ax, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    t0 = cal["datetime_utc"].min() - pd.Timedelta(minutes=95)
    t1 = cal["datetime_utc"].max() + pd.Timedelta(minutes=20)
    for w in WL:
        ax.plot(ok_a["datetime_utc"], ok_a[f"aod_{w}"], "-", color=BAND_COLORS[w], lw=2.2)
        ax.plot(cal["datetime_utc"], cal[f"aot_{w}"], "D", color=BAND_COLORS[w], ms=6, mec="black", mew=0.6)
    bb = bad[(bad["datetime_utc"] >= t0) & (bad["datetime_utc"] <= t1) & (bad["aod_465"] < 0.12)]
    ax.plot(bb["datetime_utc"], bb["aod_540"], "x", color=REJ_COLOR, ms=7, mew=1.8)
    ax.set_ylim(0.03, 0.12)
    ax.set_ylabel("AOD / AOT")
    ax.tick_params(labelbottom=False)
    h = [Line2D([], [], color=BAND_COLORS[w], lw=2.2, label=f"AERONET {w} nm") for w in WL]
    h += [Line2D([], [], color="gray", marker="D", mec="black", ls="", ms=7, label="Calitoo (3 bands)" if LANG == "en" else "Calitoo (3 bande)"),
          Line2D([], [], color=REJ_COLOR, marker="x", ls="", ms=8, mew=2, label=L("AERONET cloud", "AERONET nuvola"))]
    ax.legend(handles=h, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax2.plot(ok_a["datetime_utc"], ok_a["alpha_465_619"], "-", color=AER_COLOR, lw=2,
             label=L("AERONET 465–619", "AERONET 465–619"))
    ax2.plot(ok_a["datetime_utc"], ok_a["440-870_Angstrom_Exponent"], "--", color="#777777", lw=1.6,
             label=L("AERONET 440–870", "AERONET 440–870"))
    ax2.plot(cal["datetime_utc"], cal["angstrom"], "D", color="#555555", ms=6, mec="black", mew=0.6,
             label="Calitoo 465–619")
    ax2.set_ylabel("Ångström α")
    ax2.set_ylim(0.5, 2.2)
    ax2.legend(loc="upper left", bbox_to_anchor=(1.01, 1.05), fontsize=11)
    for a_ in (ax, ax2):
        a_.set_xlim(t0, t1)
        a_.axvspan(cal["datetime_utc"].min(), cal["datetime_utc"].max(), color="#f1f1f1", lw=0, zorder=0)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax2.set_xlabel(L("Time (UTC), Davos 7 Oct 2026", "Ora (UTC), Davos 7 ott 2026"))
    ax.text(0.01, 0.95, L("AERONET Level 1.0, cloud-screened ad hoc", "AERONET Level 1.0, screening nuvole ad hoc"),
            transform=ax.transAxes, fontsize=11, color=CAPTION_COLOR, va="top")
    fig.subplots_adjust(left=0.09, right=0.73, top=0.86, bottom=0.19)
    title = L("Calitoo matches AERONET in the blue, reads low at 540/619 nm",
              "Calitoo coincide con AERONET nel blu, è basso a 540/619 nm")
    m = D["am"]
    finish(fig, "06_aeronet_timeseries_davos", title,
           L("AERONET interpolated to Calitoo wavelengths (log–log between adjacent channels). Clouds after 09:00 UTC "
             "(AOD up to 0.7) are off scale. Grey band = Calitoo session.",
             "AERONET interpolata alle λ Calitoo (log–log tra canali adiacenti). Nuvole dopo le 09:00 UTC (AOD fino a 0.7) "
             "fuori scala. Banda grigia = sessione Calitoo."), layout=False)
    CAPS["06_aeronet_timeseries_davos"] = dict(
        title=title, msg="Stesso sito, stessa ora: Calitoo segue AERONET, ma verde e rosso sono sistematicamente bassi.",
        bullets=["AERONET a 54 m dal punto Calitoo; misure ogni ~3 min; Level 1.0 (non ancora Level 2.0 per ottobre 2026).",
                 f"Ångström: Calitoo {m['cal_angstrom'].mean():.2f} contro AERONET {m['aer_alpha_465_619'].mean():.2f} "
                 f"sullo stesso intervallo (465–619) e {m['aer_440_870_alpha'].mean():.2f} su 440–870.",
                 "AERONET Level 1.0 non ha screening nuvole: l'ho fatto io (triplet variability, simile al Level 1.5)."],
        caveat="Una sola sessione di 50 min; Level 1.0 può ancora cambiare calibrazione.")


def fig07_aeronet_scatter(D, S):
    m = D["am"]
    fig = plt.figure(figsize=WIDE)
    ax = fig.add_axes([0.08, 0.17, 0.42, 0.66])
    lo, hi = 0.02, 0.10
    x = np.linspace(lo, hi, 10)
    ax.fill_between(x, x - CAL_UNC, x + CAL_UNC, color="#ececec", lw=0, zorder=0)
    ax.plot(x, x, color="black", lw=1.5)
    rows = []
    for w in WL:
        d = m[f"diff_{w}"]
        ax.scatter(m[f"aer_aod_{w}"], m[f"cal_aot_{w}"], color=BAND_COLORS[w], s=40, edgecolor="white", lw=0.6, zorder=3)
        rows.append([f"{w} nm", f"{len(d)}", f"{d.mean():+.4f}", f"{100 * (d / m[f'aer_aod_{w}']).mean():+.0f} %".replace("-0 %", "0 %").replace("+0 %", "0 %"),
                     f"{np.sqrt((d ** 2).mean()):.4f}"])
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.set_xticks([0.02, 0.04, 0.06, 0.08, 0.10])
    ax.set_yticks([0.02, 0.04, 0.06, 0.08, 0.10])
    ax.set_xlabel(L("AERONET AOD (±15 min mean)", "AOD AERONET (media ±15 min)"))
    ax.set_ylabel("Calitoo AOT")
    ax.text(0.03, 0.97, L("grey: ±0.03", "grigio: ±0.03"), transform=ax.transAxes, va="top", fontsize=12, color=CAPTION_COLOR)
    tax = fig.add_axes([0.55, 0.35, 0.43, 0.4])
    tax.axis("off")
    tb = tax.table(cellText=rows, colLabels=[L("band", "banda"), "n", "bias", L("bias %", "bias %"), "RMSE"],
                   loc="center", cellLoc="center")
    tb.auto_set_font_size(False)
    tb.set_fontsize(14)
    tb.scale(1, 2.1)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#cccccc")
        if r == 0:
            cell.set_text_props(fontweight="bold")
            cell.set_facecolor("#f2f2f2")
        elif c == 0:
            cell.set_text_props(color=BAND_COLORS[int(rows[r - 1][0][:3])], fontweight="bold")
    tax.text(0.5, -0.05, L("bias = Calitoo − AERONET", "bias = Calitoo − AERONET"), ha="center",
             transform=tax.transAxes, fontsize=12, color=CAPTION_COLOR)
    title = L("Calitoo agrees with AERONET within ±0.03", "Calitoo concorda con AERONET entro ±0.03")
    finish(fig, "07_aeronet_scatter", title,
           L("Davos 7 Oct, 26 Calitoo measurements, AERONET Level 1.0 interpolated, cloud-screened ad hoc. "
             "Pairs share overlapping AERONET windows (~10 independent). R is not shown: AOD range too narrow.",
             "Davos 7/10, 26 misure Calitoo, AERONET Level 1.0 interpolata, screening ad hoc. Le coppie condividono "
             "finestre AERONET sovrapposte (~10 indipendenti). R non mostrato: intervallo di AOD troppo stretto."),
           layout=False)
    CAPS["07_aeronet_scatter"] = dict(
        title=title, msg="Tutte le coppie sono entro ±0.03; il bias però cresce con la lunghezza d'onda.",
        bullets=[f"Bias (Calitoo − AERONET): 465 nm {rows[0][2]}, 540 nm {rows[1][2]} ({rows[1][3]}), "
                 f"619 nm {rows[2][2]} ({rows[2][3]}); RMSE < 0.01.",
                 "Nel blu accordo perfetto; nel verde/rosso Calitoo sottostima di ~0.006–0.008.",
                 "Conseguenza: Ångström di Calitoo troppo alto (1.6 vs 1.0)."],
        caveat="Un solo giorno, AOD molto bassa (~0.05): l'errore relativo (11–16 %) è grande anche se quello assoluto è piccolo.")


def fig08_airmass(D, S):
    t = S["test"]
    x = t["x"]
    fig, axes = plt.subplots(1, 3, figsize=WIDE, sharey=True)
    xx = np.linspace(0.39, 0.51, 10)
    for ax, w in zip(axes, WL):
        f = t[w]
        ax.scatter(x, t["y"][w], color=BAND_COLORS[w], s=40, edgecolor="white", lw=0.6, zorder=3)
        ax.plot(xx, f["a"] * xx + f["b"], "-", color="black", lw=1.6)
        ax.plot(xx, f["a0"] * xx, "--", color=BAND_COLORS[w], lw=1.8)
        ax.axhline(0, color="#999999", lw=1)
        ax.set_title(f"{w} nm", color=BAND_COLORS[w], fontsize=15)
        ax.text(0.04, 0.97,
                f"a = {f['a']:+.3f} ± {f['sa']:.3f}\nb = {f['b']:+.3f} ± {f['sb']:.3f}\n"
                + L("b = 0: ε", "b = 0: ε") + f" = {-100 * f['a0']:.1f} ± {100 * f['sa0']:.1f} %",
                transform=ax.transAxes, fontsize=11.5, va="top",
                bbox=dict(fc="white", ec="#cccccc", alpha=0.9))
        ax.set_xlim(0.39, 0.51)
        ax.set_xlabel("1 / m")
        sec = ax.secondary_xaxis("top", functions=(lambda v: 1 / np.maximum(v, 1e-3), lambda v: 1 / np.maximum(v, 1e-3)))
        sec.set_xticks([2.0, 2.2, 2.4])
        sec.tick_params(labelsize=11)
        sec.set_xlabel("m", fontsize=12, labelpad=2)
    axes[0].set_ylabel(L("bias Calitoo − AERONET", "bias Calitoo − AERONET"))
    axes[0].set_ylim(-0.022, 0.032)
    fig.subplots_adjust(left=0.1, right=0.985, top=0.76, bottom=0.3, wspace=0.1)
    h = [Line2D([], [], color="black", lw=1.6, label=L("fit bias = a/m + b", "fit bias = a/m + b")),
         Line2D([], [], color="gray", ls="--", lw=1.8, label=L("CN0-only model (b = 0)", "solo CN0 (b = 0)"))]
    fig.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, 0.12), ncol=2)
    title = (L("Bias vs 1/m: consistent with a CN0 error", "Bias vs 1/m: coerente con un errore di CN0")
             if S["cn0_supported"] else
             L("Bias vs 1/m: compatible with a CN0 error, not conclusive", "Bias vs 1/m: compatibile con errore CN0, non conclusivo"))
    finish(fig, "08_bias_vs_airmass", title,
           L(f"m = Kasten–Young air mass (top axis). 1/m spans only {x.min():.2f}–{x.max():.2f} and is "
             f"{100 * t['corr_time']:.1f} % correlated with time: slope a and offset b are degenerate; the same slope "
             "appears at 465 nm (common drift). n = 26 pairs, ~10 independent. ε = CN0 relative error if b = 0.",
             f"m = massa d'aria Kasten–Young (asse in alto). 1/m varia solo tra {x.min():.2f} e {x.max():.2f} ed è "
             f"correlato al {100 * t['corr_time']:.1f} % col tempo: a e b degeneri; la stessa pendenza c'è a 465 nm "
             "(deriva comune). n = 26 coppie, ~10 indipendenti. ε = errore relativo di CN0 se b = 0."),
           layout=False, wrap=125)
    d540 = t["diff"][540]
    CAPS["08_bias_vs_airmass"] = dict(
        title=title,
        msg="Il test 1/m non riesce a distinguere errore di calibrazione e offset costante: la massa d'aria varia troppo poco.",
        bullets=["Errore di CN0 ⇒ bias = −ε/m (b ≈ 0); offset tipo ozono ⇒ bias costante (a ≈ 0).",
                 f"Fit completo: a ≈ {t[540]['a']:+.3f}, b ≈ {t[540]['b']:+.3f} a 540 nm, ma la stessa pendenza c'è a 465 nm "
                 f"({t[465]['a']:+.3f}) dove il bias medio è zero → è una deriva comune nel tempo, non la calibrazione.",
                 f"Test relativo (bias 540 − bias 465): b = {d540['b']:+.3f} ± {d540['sb']:.3f} (≈ 0, come atteso per CN0), "
                 f"a = {d540['a']:+.3f} ± {d540['sa']:.3f} (1.8σ). Se fosse CN0: ε ≈ {-100 * t[540]['a0']:.1f} % (540) e "
                 f"{-100 * t[619]['a0']:.1f} % (619)."],
        caveat="Per decidere servono misure con m tra ~1.2 e 5 (mattina presto → mezzogiorno) in coincidenza con AERONET, "
               "o una calibrazione Langley.")


def fig08b_corrected(D, S):
    t = S["test"]
    ok = D["ok"].copy()
    for w in WL:
        ok[f"corr_{w}"] = ok[f"aot_{w}"] - t[w]["a0"] / ok["airmass"]
    X = np.log(WL) - np.log(WL).mean()
    Y = np.log(ok[[f"corr_{w}" for w in WL]].values)
    ok["alpha_corr"] = -((Y - Y.mean(axis=1, keepdims=True)) @ X) / (X @ X)
    g = ok.groupby("key", sort=False).agg(a540=("aot_540", "mean"), c540=("corr_540", "mean"),
                                          al=("angstrom", "mean"), alc=("alpha_corr", "mean")).loc[D["order"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=WIDE)
    xi = np.arange(len(g))
    lab = [day_label(k.split()[0], k.split()[1]).replace(" ", "\n", 1) for k in g.index]
    a1.bar(xi - 0.18, g["a540"], 0.34, color="#bbbbbb", label=L("original", "originale"))
    a1.bar(xi + 0.18, g["c540"], 0.34, color=BAND_COLORS[540], label=L("CN0-corrected", "corretto CN0"))
    a2.bar(xi - 0.18, g["al"], 0.34, color="#bbbbbb")
    a2.bar(xi + 0.18, g["alc"], 0.34, color="#555555", label=L("CN0-corrected", "corretto CN0"))
    a2.axhline(D["am"]["aer_alpha_465_619"].mean(), color=AER_COLOR, ls="--", lw=1.5, label="AERONET Davos")
    for a, yl in ((a1, "AOT 540 nm"), (a2, "Ångström α")):
        a.set_xticks(xi)
        a.set_xticklabels(lab, fontsize=12)
        a.set_ylabel(yl)
    a1.legend(loc="upper right")
    a2.legend(loc="upper right")
    title = L("PRELIMINARY: CN0 correction from one day at Davos", "PRELIMINARE: correzione CN0 da un solo giorno a Davos")
    finish(fig, "08b_corrected_vs_original", title,
           L(f"Scenario only: CN0 raised by {-100 * t[540]['a0']:.1f} % (540) and {-100 * t[619]['a0']:.1f} % (619), "
             "AOT corrected as τ − a/m for each measurement. Not validated.",
             f"Solo scenario: CN0 aumentata di {-100 * t[540]['a0']:.1f} % (540) e {-100 * t[619]['a0']:.1f} % (619), "
             "AOT corretta come τ − a/m per ogni misura. Non validata."), rect_bottom=0.1)
    CAPS["08b_corrected_vs_original"] = dict(
        title=title, msg="Scenario: cosa cambierebbe con la correzione CN0 (non validata).",
        bullets=["AOT 540 nm e α prima/dopo per tutti i giorni."], caveat="Basata su un solo giorno a Davos; test 1/m non conclusivo.")


def mini_map(ax, D):
    swiss(ax, fc="#f6f6f3", lw=1)
    for _, b in D["boxes"].iterrows():
        col = SITE_COLORS[b["site"]]
        ax.add_patch(Rectangle((b.cov_west, b.cov_south), b.cov_east - b.cov_west, b.cov_north - b.cov_south,
                               fc=col, alpha=0.12, ec=col, lw=1.8))
    for site, g in D["ok"].groupby("site"):
        ax.plot(g["lon"].mean(), g["lat"].mean(), "o", color=SITE_COLORS[site], mec="black", ms=10, zorder=4)
        ax.annotate(site, (g["lon"].mean(), g["lat"].mean()), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=11, fontweight="bold")
    ax.set_xlim(5.8, 12.2)
    ax.set_ylim(44.8, 49.2)
    ax.set_aspect(1 / np.cos(np.radians(47)))
    ax.set_xticks([6, 8, 10, 12])
    ax.set_yticks([45, 46, 47, 48, 49])
    ax.tick_params(labelsize=10)
    ax.set_title(L("MODIS 1° averaging boxes", "box MODIS da 1°"), fontsize=13, fontweight="normal")


def fig09_modis(D, S):
    c = D["cvm"].set_index(["site", "date"])
    groups = [("Zurich", "2026-10-06"), ("Davos", "2026-10-07"), ("Davos", "2026-10-09"), ("Lugano", "2026-10-10")]
    avm = D["avm"]

    def cal_val(s, d):
        if (s, d) not in c.index:
            return np.nan
        r = c.loc[(s, d)]
        return r["aot550_aqua_mean"] if r["n_aqua_window"] > 0 else r["aot550_all_mean"]

    def aer_val(s, d):
        if s != "Davos":
            return np.nan, "nostation"
        if (s, d) in c.index and np.isfinite(c.loc[(s, d)].get("aer550_day_mean", np.nan)):
            r = c.loc[(s, d)]
            v = r["aer550_aqua_mean"] if np.isfinite(r["aer550_aqua_mean"]) else r["aer550_day_mean"]
            return v, "ok"
        m = avm[(avm["site"] == s) & (avm["date"] == d)] if avm is not None else []
        return (m["aer"].iat[0], "ok") if len(m) else (np.nan, "nodata")

    def modis_val(s, d):
        if (s, d) in c.index:
            r = c.loc[(s, d)]
            return r["modis_aod550"], r["modis_flag"]
        m = avm[(avm["site"] == s) & (avm["date"] == d)] if avm is not None else []
        return (m["modis"].iat[0], "ok") if len(m) else (np.nan, "missing")

    fig = plt.figure(figsize=WIDE)
    ax = fig.add_axes([0.08, 0.31, 0.56, 0.54])
    mx = fig.add_axes([0.68, 0.24, 0.31, 0.62])
    w = 0.26
    for i, (s, d) in enumerate(groups):
        v = cal_val(s, d)
        if np.isfinite(v):
            ax.bar(i - w, v, w * 0.92, yerr=CAL_UNC, color=SITE_COLORS[s], capsize=4, ecolor="#444444")
        else:
            ax.text(i - w, 0.004, L("no Calitoo", "no Calitoo"), rotation=90, ha="center", va="bottom", fontsize=10, color=CAPTION_COLOR)
        v, fl = aer_val(s, d)
        if np.isfinite(v):
            ax.bar(i, v, w * 0.92, yerr=AER_UNC, color="white", edgecolor=AER_COLOR, lw=1.6, hatch="..",
                   capsize=4, ecolor="#444444")
        else:
            ax.text(i, 0.004, L("no AERONET", "no AERONET") if fl == "nostation" else L("no data", "no dati"),
                    rotation=90, ha="center", va="bottom", fontsize=10, color=CAPTION_COLOR)
        v, fl = modis_val(s, d)
        if np.isfinite(v):
            ax.bar(i + w, v, w * 0.92, yerr=EE(v), color=MODIS_COLOR, capsize=4, ecolor="#444444")
        else:
            ax.bar(i + w, 0.035, w * 0.92, color="none", edgecolor=MODIS_COLOR, ls="--", lw=1.4)
            ax.text(i + w, 0.0175, L("no data\n(clouds)", "no dati\n(nuvole)"), rotation=90, ha="center",
                    va="center", fontsize=10, color=CAPTION_COLOR)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([day_label(s, d).replace(" ", "\n", 1) for s, d in groups])
    ax.set_ylabel("AOD 550 nm")
    ax.set_ylim(0, 0.12)
    ax.legend(handles=[Patch(color="#999999", label="Calitoo ±0.03"),
                       Patch(fc="white", ec=AER_COLOR, hatch="..", label="AERONET ±0.01"),
                       Patch(color=MODIS_COLOR, label="MODIS ±(0.05+0.15·AOD)")],
              loc="upper left", bbox_to_anchor=(-0.02, -0.25), ncol=3, fontsize=11)
    mini_map(mx, D)
    title = L("MODIS agrees within its error – but its error > signal",
              "MODIS concorda entro l'errore – ma l'errore > segnale")
    finish(fig, "09_modis_comparison", title,
           L("MODIS-Aqua MYD08_D3 1° area mean (~300×220 km). Calitoo/AERONET: Aqua-window mean when available, "
             "else daily mean. Zurich 30 Sep omitted (MODIS not downloaded).",
             "MODIS-Aqua MYD08_D3, media areale 1° (~300×220 km). Calitoo/AERONET: media nella finestra Aqua se "
             "disponibile, altrimenti giornaliera. Zurigo 30/9 escluso (MODIS non scaricato)."), layout=False)
    CAPS["09_modis_comparison"] = dict(
        title=title, msg="MODIS è compatibile con terra in tutti i casi, ma a AOD ~0.04 il confronto non è un vero test.",
        bullets=[f"Zurigo 6/10: Calitoo {f3(cal_val('Zurich', '2026-10-06'))} vs MODIS {f3(modis_val('Zurich', '2026-10-06')[0])}; "
                 f"Lugano 10/10: {f3(cal_val('Lugano', '2026-10-10'))} vs {f3(modis_val('Lugano', '2026-10-10')[0])}; "
                 f"Davos 9/10: AERONET {f3(aer_val('Davos', '2026-10-09')[0])} vs MODIS {f3(modis_val('Davos', '2026-10-09')[0])}.",
                 "Incertezza MODIS ~±0.055 a questi valori: più grande dell'AOD stessa.",
                 "I box sono grandi e non centrati (Lugano include la Pianura Padana, Zurigo la Germania meridionale)."],
        caveat="Solo 3 coppie; Davos 7/10 senza MODIS (nuvole). Servono MYD04_3K (3 km), MODIS-Terra, box centrati.")


def fig10_table(D, S):
    st = S["days"]
    c = D["cvm"].set_index(["site", "date"])
    rows = []
    for r in st.itertuples():
        tot = (D["cal"]["key"] == r.Index).sum()
        cr = c.loc[(r.site, r.date)] if (r.site, r.date) in c.index else None
        aer = L("yes (Δ540 = −0.006)", "sì (Δ540 = −0.006)") if r.site == "Davos" else "–"
        if cr is None:
            mod = "–"
        elif cr["modis_flag"] == "ok":
            mod = f3(cr["modis_aod550"])
        elif cr["modis_flag"].startswith("missing"):
            mod = L("no data (clouds)", "no dati (nuvole)")
        else:
            mod = L("not downloaded", "non scaricato")
        rows.append([r.site, day_label(r.site, r.date, short=True), f"{r.n}/{tot}",
                     f"{r.aot540:.3f} ± {r.aot540_std:.3f}", f"{r.alpha_col15:.2f}", aer, mod])
    fig, ax = plt.subplots(figsize=WIDE)
    ax.axis("off")
    tb = ax.table(cellText=rows, colLabels=[L("Site", "Sito"), L("Date", "Data"), "n (QC/all)",
                                            "AOT 540 nm", "α", "AERONET", "MODIS AOD 550"],
                  loc="center", cellLoc="center", colWidths=[0.11, 0.09, 0.12, 0.18, 0.07, 0.22, 0.19])
    tb.auto_set_font_size(False)
    tb.set_fontsize(13)
    tb.scale(1, 2.6)
    for (ri, ci), cell in tb.get_celld().items():
        cell.set_edgecolor("#d0d0d0")
        if ri == 0:
            cell.set_facecolor("#efefef")
            cell.set_text_props(fontweight="bold")
        elif ci == 0:
            cell.set_text_props(color=SITE_COLORS[rows[ri - 1][0]], fontweight="bold")
    title = L("Campaign summary", "Riepilogo della campagna")
    finish(fig, "10_summary_table", title,
           L("AOT: mean ± std of QC-passed measurements; α = Calitoo column 15 (likely overestimated, see AERONET).",
             "AOT: media ± std delle misure valide; α = colonna 15 Calitoo (probabilmente sovrastimato, vedi AERONET)."),
           rect_bottom=0.06)
    CAPS["10_summary_table"] = dict(title=title, msg="Tabella riassuntiva per la slide finale.",
                                    bullets=["Una riga per giorno: n, AOT 540 nm, α, confronti disponibili."],
                                    caveat="α da leggere alla luce del bias spettrale.")


# ---------------------------------------------------------------------------
# CHECKS + CAPTIONS
# ---------------------------------------------------------------------------
def checks(D):
    S = {}
    cal, ok = D["cal"], D["ok"]
    S["days"] = day_stats(ok).loc[D["order"]]
    # 1) UTC check: computed solar elevation vs column 11
    el = solar_elevation(cal["datetime_utc"], cal["lat"], cal["lon"])
    dif = cal["sun_elev_deg"] - el
    el2 = solar_elevation(cal["datetime_utc"] - pd.Timedelta(hours=2), cal["lat"], cal["lon"])
    S["utc"] = dict(mean=dif.mean(), maxabs=dif.abs().max(), if_local=(cal["sun_elev_deg"] - el2).abs().mean())
    # 2) Lugano altitude from pressure (standard-atmosphere hypsometric relation)
    qnh = lambda p, h: p * (1 - 0.0065 * h / 288.15) ** -5.2559
    alt = lambda p, q: 288.15 / 0.0065 * (1 - (p / q) ** (1 / 5.2559))
    g = cal.groupby(["site", "date"]).agg(p=("pressure_hPa", "mean"), h=("alt_m", "median")).reset_index()
    g["qnh_gps"] = qnh(g["p"], g["h"])
    ref = g[g["site"] != "Lugano"]
    lug = g[g["site"] == "Lugano"].iloc[0]
    S["lugano_gps"] = lug["h"]
    S["press"] = dict(table=g, lug_p=lug["p"], qnh_ref=ref["qnh_gps"].mean(), qnh_ref_range=(ref["qnh_gps"].min(), ref["qnh_gps"].max()),
                      lug_h_from_p=alt(lug["p"], ref["qnh_gps"].mean()),
                      lug_h_range=(alt(lug["p"], ref["qnh_gps"].max()), alt(lug["p"], ref["qnh_gps"].min())),
                      lug_qnh_438=qnh(lug["p"], lug["h"]), lug_qnh_273=qnh(lug["p"], 273),
                      p_expected_273=ref["qnh_gps"].mean() * (1 - 0.0065 * 273 / 288.15) ** 5.2559,
                      zur_p=g[g["site"] == "Zurich"]["p"].mean())
    # 3) airmass test
    am = D["am"]
    dv = ok[ok["site"] == "Davos"].reset_index(drop=True)
    assert (dv["time"].values == am["time_utc"].values).all(), "pair/time mismatch"
    x = 1 / dv["airmass"].values
    t = dict(x=x, y={}, diff={}, corr_time=np.corrcoef(x, dv["datetime_utc"].astype("int64"))[0, 1])
    for w in WL:
        t["y"][w] = am[f"diff_{w}"].values
        t[w] = fit_lin(x, t["y"][w])
    for w in (540, 619):
        t["diff"][w] = fit_lin(x, t["y"][w] - t["y"][465])
    S["test"] = t
    sig = lambda v, s: abs(v) > 2 * s
    S["cn0_supported"] = all(not sig(t["diff"][w]["b"], t["diff"][w]["sb"]) and sig(t["diff"][w]["a"], t["diff"][w]["sa"])
                             for w in (540, 619)) and not sig(t[465]["a"], t[465]["sa"])
    # 4) consistency with summary.csv
    sm = D["summ"]
    re = ok.groupby("session_id").agg(n_re=("aot_540", "size"), a=("aot_540", "mean"), al=("angstrom", "mean"))
    j = sm.set_index("session_id").join(re)
    S["consistency"] = dict(n_ok=(j["n_re"] == j["n_qc_ok"]).all(),
                            max_aot=(j["a"] - j["aot_540_mean"]).abs().max(),
                            max_alpha=(j["al"] - j["angstrom_mean"]).abs().max())
    return S


def write_captions(S):
    lines = ["# Didascalie e note per la presentazione intermedia (Calitoo, set–ott 2026)", "",
             f"Figure in `figures_presentation/` (PNG 300 dpi + PDF). Lingua nelle figure: `LANG = \"{LANG}\"`.", ""]
    for name in sorted(CAPS):
        c = CAPS[name]
        lines += [f"## {name}", "", f"**Titolo slide:** {c['title']}", "", f"**Messaggio:** {c['msg']}", ""]
        lines += [f"- {b}" for b in c["bullets"]]
        lines += ["", f"*Caveat:* {c['caveat']}", ""]
    (FIG / "captions.md").write_text("\n".join(lines))
    print("  saved captions.md")


def report(S):
    print("\n================ TEST 1/m (bias = a·(1/m) + b) ================")
    t = S["test"]
    print(f"1/m: {t['x'].min():.3f}–{t['x'].max():.3f} (m {1 / t['x'].max():.2f}–{1 / t['x'].min():.2f}); "
          f"corr(1/m, tempo) = {t['corr_time']:.4f}")
    for w in WL:
        f = t[w]
        print(f"  {w} nm: fit completo a = {f['a']:+.4f} ± {f['sa']:.4f}, b = {f['b']:+.4f} ± {f['sb']:.4f} "
              f"(rms {f['rms_full']:.4f}) | solo CN0 (b=0): a = {f['a0']:+.4f} ± {f['sa0']:.4f} → ε = {-100 * f['a0']:.1f} % "
              f"(rms {f['rms_a0']:.4f}) | solo offset (a=0): b = {f['mean']:+.4f} (rms {f['rms_b']:.4f})")
    for w in (540, 619):
        f = t["diff"][w]
        print(f"  bias {w} − bias 465: a = {f['a']:+.4f} ± {f['sa']:.4f}, b = {f['b']:+.4f} ± {f['sb']:.4f}")
    print("  → CN0 supportato in modo significativo:", "SÌ" if S["cn0_supported"] else
          "NO (compatibile ma non conclusivo) → 08b non prodotta" + (" [forzata da CN0_SCENARIO]" if CN0_SCENARIO else ""))
    p = S["press"]
    print("\n================ QUOTA DI LUGANO ================")
    print(p["table"].round(1).to_string(index=False))
    print(f"  QNH di riferimento (Zurigo/Davos, con quota GPS): {p['qnh_ref']:.1f} hPa "
          f"(range {p['qnh_ref_range'][0]:.1f}–{p['qnh_ref_range'][1]:.1f})")
    print(f"  Lugano p = {p['lug_p']:.1f} hPa (Zurigo {p['zur_p']:.1f} hPa) → quota dalla pressione ≈ {p['lug_h_from_p']:.0f} m "
          f"(range {p['lug_h_range'][0]:.0f}–{p['lug_h_range'][1]:.0f} m)")
    print(f"  Se Lugano fosse a 273 m: p attesa ≈ {p['p_expected_273']:.0f} hPa, QNH implicito {p['lug_qnh_273']:.0f} hPa; "
          f"a 438 m (GPS): QNH {p['lug_qnh_438']:.0f} hPa")
    u = S["utc"]
    print("\n================ CONTROLLO UTC ================")
    print(f"  elevazione col. 11 − calcolata (UTC): media {u['mean']:+.2f}°, max |Δ| {u['maxabs']:.2f}°; "
          f"se gli orari fossero locali (UTC+2) |Δ| medio sarebbe {u['if_local']:.1f}°")
    c = S["consistency"]
    print("\n================ COERENZA CON summary.csv ================")
    print(f"  n QC per sessione uguale: {c['n_ok']}; max |Δ AOT540| = {c['max_aot']:.2e}; max |Δ α| = {c['max_alpha']:.2e}")
    print("\n================ NUMERI CAMBIATI RISPETTO AL RIASSUNTO PRECEDENTE ================")
    prev = {"Zurich 2026-09-30": 1.66, "Zurich 2026-10-06": 1.73, "Davos 2026-10-07": 1.57, "Lugano 2026-10-10": 1.49}
    for k, r in S["days"].iterrows():
        print(f"  α fit spettro {k}: {r['alpha_fit']:.2f} (prima {prev[k]:.2f}, prima = media delle medie di sessione, "
              f"ora = media delle misure)")
    print(f"  ε CN0 (b=0): 540 {-100 * t[540]['a0']:.1f} %, 619 {-100 * t[619]['a0']:.1f} % "
          f"(prima stimato come media(bias·m): −1.36 % / −1.81 % in ln, ovvero 1.4 % / 1.8 %)")


def main():
    FIG.mkdir(exist_ok=True)
    setup_style()
    D = load()
    S = checks(D)
    fig01_map(D, S)
    fig02_quality(D, S)
    fig03_overview(D, S)
    fig04_timeseries(D, S)
    fig05_spectrum(D, S)
    fig06_aeronet_ts(D, S)
    fig07_aeronet_scatter(D, S)
    fig08_airmass(D, S)
    if S["cn0_supported"] or CN0_SCENARIO:
        fig08b_corrected(D, S)
    fig09_modis(D, S)
    fig10_table(D, S)
    write_captions(S)
    report(S)


if __name__ == "__main__":
    main()
