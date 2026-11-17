#!/usr/bin/env python3
"""Validate Calitoo (Davos, 7 Oct 2026) against AERONET Davos (Version 3 direct-sun AOD).

Reuses output/calitoo_all.csv (run plot_calitoo.py first). Writes
output/calitoo_vs_aeronet.csv, output/aeronet_davos_screened.csv and the plots.
The AERONET loader (load_aeronet / aeronet_daily_550) is also used by compare_modis.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import plot_calitoo as pc   # shared style, band colors, haversine

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "output"
AERONET_FILE = BASE / "aeronet_data" / "20261005_20261010_Davos.csv"
CALITOO_SITE = "Davos"
DAY = pd.Timestamp("2026-10-07").date()
MATCH_WINDOWS_MIN = [15, 30]   # ± minutes; the first one is the main result
AQUA_WINDOW_UTC = ("11:30", "13:00")
CALITOO_UNC = 0.03             # typical Calitoo AOT uncertainty
LEVEL_NAMES = {"lev10": "Level 1.0", "lev15": "Level 1.5", "lev20": "Level 2.0"}
CAL_WL = pc.WL                 # 465, 540, 619 nm
# AERONET channel pairs used for log-log interpolation to each target wavelength
INTERP_PAIRS = {465: (440, 500), 540: (500, 675), 550: (500, 675), 619: (500, 675)}
AER_MARKER, CAL_MARKER = "o", "D"


# ---------------------------------------------------------------------------
# READING + SCREENING
# ---------------------------------------------------------------------------
def load_aeronet(path=AERONET_FILE):
    """Return (DataFrame, meta). Adds interpolated AOD at 465/540/550/619 and a cloud flag."""
    head = path.read_text().splitlines()[:7]
    hdr_row = next(i for i, l in enumerate(head) if l.startswith("Date(dd:mm:yyyy)"))
    df = pd.read_csv(path, skiprows=hdr_row, na_values=[-999, -999.0])
    df["datetime_utc"] = pd.to_datetime(df["Date(dd:mm:yyyy)"] + " " + df["Time(hh:mm:ss)"],
                                        format="%d:%m:%Y %H:%M:%S", utc=True)
    df["date"] = df["datetime_utc"].dt.date
    channels = sorted(int(c[4:-2]) for c in df.columns
                      if c.startswith("AOD_") and c.endswith("nm") and df[c].notna().any())
    exact = {w: df[f"Exact_Wavelengths_of_AOD(um)_{w}nm"].iloc[0] * 1000 for w in channels}
    for target, (w1, w2) in INTERP_PAIRS.items():
        a1, a2 = df[f"AOD_{w1}nm"], df[f"AOD_{w2}nm"]
        l1, l2 = np.log(exact[w1]), np.log(exact[w2])
        with np.errstate(invalid="ignore", divide="ignore"):
            slope = (np.log(a2) - np.log(a1)) / (l2 - l1)
            df[f"aod_{target}"] = np.exp(np.log(a1) + slope * (np.log(target) - l1))
    # α over the Calitoo range, from the interpolated values (same method as Calitoo col. 15)
    x = np.log(CAL_WL)
    y = np.log(df[[f"aod_{int(w)}" for w in CAL_WL]].values)
    xm = x - x.mean()
    df["alpha_465_619"] = -(y - y.mean(axis=1, keepdims=True)) @ xm / (xm @ xm)

    # approximate Level-1.5-like cloud screening (NOT the official AERONET algorithm)
    tv = lambda w: df[f"Triplet_Variability_{w}"]
    thr = lambda w: np.maximum(0.01, 0.015 * df[f"AOD_{w}nm"])
    df["cloud_triplet"] = (tv(870) > thr(870)) | (tv(1020) > thr(1020))
    df["cloud_gross"] = (df["440-870_Angstrom_Exponent"] < 0.4) & (df["AOD_500nm"] > 0.15)
    df["screened_ok"] = ~(df["cloud_triplet"] | df["cloud_gross"]) & df["AOD_500nm"].notna()

    lvl = df["Data_Quality_Level"].iloc[0]
    meta = dict(level=LEVEL_NAMES.get(lvl, lvl), level_code=lvl, title=head[2].strip(),
                site=df["AERONET_Site_Name"].iloc[0],
                lat=df["Site_Latitude(Degrees)"].iloc[0], lon=df["Site_Longitude(Degrees)"].iloc[0],
                elev=df["Site_Elevation(m)"].iloc[0],
                instrument=int(df["AERONET_Instrument_Number"].iloc[0]),
                channels=channels, exact=exact)
    return df, meta


def aeronet_daily_550(df=None):
    """Daily AERONET AOD 550 (screened): all-day and Aqua-window mean/std/n."""
    if df is None:
        df, _ = load_aeronet()
    ok = df[df["screened_ok"]].copy()
    t = ok["datetime_utc"].dt.strftime("%H:%M")
    ok["in_aqua"] = (t >= AQUA_WINDOW_UTC[0]) & (t <= AQUA_WINDOW_UTC[1])
    rows = []
    for d, g in df.groupby("date"):
        o = ok[ok["date"] == d]
        a = o[o["in_aqua"]]
        rows.append(dict(date=d, n_total=len(g), n_screened=len(o),
                         aer550_day_mean=o["aod_550"].mean(), aer550_day_std=o["aod_550"].std(),
                         n_aqua=len(a), aer550_aqua_mean=a["aod_550"].mean(),
                         aer550_aqua_std=a["aod_550"].std()))
    return pd.DataFrame(rows)


def load_calitoo_day():
    cal = pd.read_csv(OUT_DIR / "calitoo_all.csv", parse_dates=["datetime_utc"])
    cal = cal[(cal["site"] == CALITOO_SITE) & cal["qc_ok"]].copy()
    cal = cal[cal["datetime_utc"].dt.date == DAY]
    cal["aot_550"] = cal["aot_540"] * (550 / 540) ** (-cal["angstrom"])
    return cal


# ---------------------------------------------------------------------------
# MATCHING
# ---------------------------------------------------------------------------
AER_COLS = ["aod_465", "aod_540", "aod_619", "aod_550", "440-870_Angstrom_Exponent",
            "440-675_Angstrom_Exponent", "alpha_465_619"]


def match(cal, aer, win_min):
    ok = aer[aer["screened_ok"]]
    rows = []
    for _, c in cal.iterrows():
        w = ok[(ok["datetime_utc"] - c["datetime_utc"]).abs() <= pd.Timedelta(minutes=win_min)]
        r = {"time_utc": c["datetime_utc"].strftime("%H:%M:%S"), "datetime_utc": c["datetime_utc"],
             "window_min": win_min, "n_aeronet": len(w),
             "cal_aot_465": c["aot_465"], "cal_aot_540": c["aot_540"], "cal_aot_619": c["aot_619"],
             "cal_aot_550": c["aot_550"], "cal_angstrom": c["angstrom"]}
        for col in AER_COLS:
            key = "aer_" + col.replace("-", "_").replace("_Angstrom_Exponent", "_alpha").lower()
            r[key] = w[col].mean() if len(w) else np.nan
            r[key + "_std"] = w[col].std() if len(w) > 1 else np.nan
        for wl in (465, 540, 619, 550):
            r[f"diff_{wl}"] = r[f"cal_aot_{wl}"] - r[f"aer_aod_{wl}"]
            r[f"rel_diff_{wl}_pct"] = 100 * r[f"diff_{wl}"] / r[f"aer_aod_{wl}"]
        r["diff_alpha_vs_465_619"] = r["cal_angstrom"] - r["aer_alpha_465_619"]
        rows.append(r)
    return pd.DataFrame(rows)


def stats(m, wl):
    p = m.dropna(subset=[f"aer_aod_{wl}"])
    d = p[f"diff_{wl}"]
    n = len(p)
    r = np.corrcoef(p[f"cal_aot_{wl}"], p[f"aer_aod_{wl}"])[0, 1] if n >= 5 else np.nan
    return dict(n=n, bias=d.mean(), rmse=np.sqrt((d ** 2).mean()), r=r,
                rel_bias=100 * (d / p[f"aer_aod_{wl}"]).mean(),
                frac_within_unc=(d.abs() <= CALITOO_UNC).mean())


# ---------------------------------------------------------------------------
# PLOTS
# ---------------------------------------------------------------------------
def save(fig, name):
    fig.savefig(OUT_DIR / name)
    plt.close(fig)
    print(f"  saved {name}")


def fig_timeseries(aer, cal, meta):
    a = aer[aer["date"] == DAY]
    ok, bad = a[a["screened_ok"]], a[~a["screened_ok"]]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 8.5), sharex=True,
                                  gridspec_kw=dict(height_ratios=[2.2, 1]))
    for wl in CAL_WL.astype(int):
        col = pc.BAND_COLORS[wl]
        ax.plot(ok["datetime_utc"], ok[f"aod_{wl}"], "-", color=col, lw=2)
        ax.plot(bad["datetime_utc"], bad[f"aod_{wl}"], "x", color=col, ms=7, mew=1.5, alpha=0.6)
        ax.plot(cal["datetime_utc"], cal[f"aot_{wl}"], CAL_MARKER, color=col, ms=8,
                mec="black", mew=0.8, zorder=4)
    ymax = 0.13
    off = bad[bad["aod_465"] > ymax]
    if len(off):
        ax.annotate(f"cloud: AOD up to {off['aod_465'].max():.2f}\n(off scale)",
                    (off["datetime_utc"].min(), ymax * 0.97), ha="left", va="top",
                    fontsize=10, color="#666666")
    ax.set_ylim(0, ymax)
    ax.set_ylabel("AOD")
    ax.set_title(f"Davos – 7 Oct 2026: AERONET {meta['level']} (unscreened source, "
                 f"own cloud screening) vs Calitoo")
    h = [Line2D([], [], color=pc.BAND_COLORS[w], lw=2, label=f"AERONET → {w} nm")
         for w in CAL_WL.astype(int)]
    h += [Line2D([], [], color=pc.BAND_COLORS[w], marker=CAL_MARKER, mec="black", ls="", ms=8,
                 label=f"Calitoo {w} nm") for w in CAL_WL.astype(int)]
    h.append(Line2D([], [], color="gray", marker="x", ls="", ms=7, mew=1.5,
                    label="AERONET flagged as cloud"))
    h.append(Patch(color="#f2f2f2", label="Calitoo measurement period"))
    ax.legend(handles=h, ncol=3, fontsize=10, frameon=False, loc="upper left")

    ax2.plot(ok["datetime_utc"], ok["440-870_Angstrom_Exponent"], "-", color="#444444", lw=2,
             label="AERONET α 440–870")
    ax2.plot(ok["datetime_utc"], ok["alpha_465_619"], "--", color="#888888", lw=2,
             label="AERONET α 465–619 (interpolated)")
    ax2.plot(cal["datetime_utc"], cal["angstrom"], CAL_MARKER, color="#7c5cd6", ms=7,
             mec="black", mew=0.8, label="Calitoo α (col. 15, 465–619)")
    ax2.set_ylim(0, 2.3)
    ax2.set_ylabel("Ångström α")
    ax2.legend(ncol=3, fontsize=10, frameon=False, loc="lower left")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax2.set_xlabel("Time (UTC)")
    lo = a["datetime_utc"].min() - pd.Timedelta(minutes=10)
    ax2.set_xlim(lo, a["datetime_utc"].max() + pd.Timedelta(minutes=10))
    for axx in (ax, ax2):
        axx.axvspan(cal["datetime_utc"].min(), cal["datetime_utc"].max(), color="#f2f2f2",
                    zorder=0, lw=0)
    fig.tight_layout()
    save(fig, "aeronet_davos_timeseries.png")


def fig_scatter(m, meta):
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    lo, hi = 0.02, 0.10
    x = np.linspace(lo, hi, 10)
    ax.fill_between(x, x - CALITOO_UNC, x + CALITOO_UNC, color="#f0f0f0", lw=0, zorder=0)
    ax.plot(x, x, color="black", lw=1.5)
    h = [Line2D([], [], color="black", lw=1.5, label="1:1"),
         Patch(color="#f0f0f0", label=f"±{CALITOO_UNC} (typical Calitoo uncertainty)")]
    for wl in CAL_WL.astype(int):
        col = pc.BAND_COLORS[wl]
        p = m.dropna(subset=[f"aer_aod_{wl}"])
        ax.errorbar(p[f"aer_aod_{wl}"], p[f"cal_aot_{wl}"], xerr=p[f"aer_aod_{wl}_std"],
                    fmt="o", color=col, ms=7, mec="white", lw=1, capsize=0, alpha=0.9)
        s = stats(m, wl)
        rtxt = f", R={s['r']:.2f}" if np.isfinite(s["r"]) else ""
        h.append(Line2D([], [], color=col, marker="o", ls="", ms=8,
                        label=f"{wl} nm: n={s['n']}, bias={s['bias']:+.4f}, "
                              f"RMSE={s['rmse']:.4f}{rtxt}"))
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.set_xlabel(f"AERONET AOD (interpolated, mean ±{MATCH_WINDOWS_MIN[0]} min)")
    ax.set_ylabel("Calitoo AOT")
    ax.set_title(f"Calitoo vs AERONET {meta['level']} – Davos, 7 Oct 2026")
    ax.legend(handles=h, loc="upper left", frameon=False, fontsize=10.5)
    ax.text(0.98, 0.02, "bias = Calitoo − AERONET\nx error bar = std AERONET in window",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=10, color="#666666")
    save(fig, "calitoo_vs_aeronet_scatter.png")


def fig_spectrum(aer, cal, meta):
    t0, t1 = cal["datetime_utc"].min(), cal["datetime_utc"].max()
    a = aer[(aer["date"] == DAY) & aer["screened_ok"] & (aer["datetime_utc"] >= t0)
            & (aer["datetime_utc"] <= t1)]
    wl = np.array(meta["channels"], float)
    ex = np.array([meta["exact"][int(w)] for w in wl])
    mean = a[[f"AOD_{int(w)}nm" for w in wl]].mean().values
    std = a[[f"AOD_{int(w)}nm" for w in wl]].std().values
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.errorbar(ex, mean, yerr=std, fmt=AER_MARKER + "-", color="#444444", ms=8, lw=1.5,
                capsize=4, mec="white", label=f"AERONET {meta['level']} (all channels, n={len(a)})")
    for wl_c in CAL_WL.astype(int):
        v = cal[f"aot_{wl_c}"]
        ax.errorbar(wl_c, v.mean(), yerr=v.std(), fmt=CAL_MARKER, color=pc.BAND_COLORS[wl_c],
                    ms=11, mec="black", mew=0.8, capsize=5, lw=2, zorder=4)
        ax.plot(wl_c, a[f"aod_{wl_c}"].mean(), "s", mfc="none", mec=pc.BAND_COLORS[wl_c],
                mew=2, ms=13, zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ticks = [340, 440, 500, 675, 870, 1020, 1640]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    yt = [0.01, 0.02, 0.03, 0.05, 0.07, 0.1]
    ax.set_yticks(yt)
    ax.set_yticklabels([f"{v:g}" for v in yt])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylim(0.008, 0.12)
    ax.grid(True, which="both", color="#e5e5e5")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("AOD")
    ax.set_title(f"Davos 7 Oct 2026, {t0:%H:%M}–{t1:%H:%M} UTC – AERONET vs Calitoo spectrum")
    h, _ = ax.get_legend_handles_labels()
    h += [Line2D([], [], marker=CAL_MARKER, color="gray", mec="black", ls="", ms=10,
                 label=f"Calitoo mean ± std (n={len(cal)})"),
          Line2D([], [], marker="s", mfc="none", mec="gray", mew=2, ls="", ms=12,
                 label="AERONET interpolated to Calitoo λ")]
    ax.legend(handles=h, frameon=False, loc="upper right")
    save(fig, "calitoo_vs_aeronet_spectrum.png")


# ---------------------------------------------------------------------------
# REPORT (Italian, as requested)
# ---------------------------------------------------------------------------
def report(aer, meta, cal, matches):
    dist = pc.haversine_km(meta["lat"], meta["lon"], cal["lat"].mean(), cal["lon"].mean())
    a = aer[aer["date"] == DAY]
    print("\n================ AERONET ================")
    print(f"File: {AERONET_FILE.name}  –  {meta['title']}  –  {meta['level']} (codice {meta['level_code']})")
    print(f"Stazione {meta['site']} #{meta['instrument']}: {meta['lat']:.5f}N {meta['lon']:.5f}E, "
          f"{meta['elev']:.0f} m")
    print(f"Calitoo Davos: {cal['lat'].mean():.5f}N {cal['lon'].mean():.5f}E, "
          f"{cal['alt_m'].median():.0f} m GPS  ->  distanza {dist * 1000:.0f} m, "
          f"dislivello {cal['alt_m'].median() - meta['elev']:+.0f} m")
    print(f"Canali AERONET disponibili: {meta['channels']}")
    print(f"7 ott: {len(a)} misure AERONET, {a['screened_ok'].sum()} dopo lo screening nuvole "
          f"({(~a['screened_ok']).sum()} scartate, ultime ok alle "
          f"{a[a['screened_ok']]['datetime_utc'].max():%H:%M} UTC)")
    print("\n================ COPPIE ================")
    for w, m in matches.items():
        print(f"  ±{w} min: {m['n_aeronet'].gt(0).sum()}/{len(m)} misure Calitoo con AERONET "
              f"(media {m['n_aeronet'].mean():.1f} punti AERONET per finestra)")
    m = matches[MATCH_WINDOWS_MIN[0]]
    print(f"\n================ STATISTICHE (±{MATCH_WINDOWS_MIN[0]} min) ================")
    for wl in (465, 540, 619, 550):
        s = stats(m, wl)
        print(f"  {wl} nm: n={s['n']}, bias={s['bias']:+.4f} ({s['rel_bias']:+.0f}%), "
              f"RMSE={s['rmse']:.4f}, R={s['r']:.2f}, entro ±{CALITOO_UNC}: "
              f"{100 * s['frac_within_unc']:.0f}%")
    print(f"  α Calitoo = {m['cal_angstrom'].mean():.2f}±{m['cal_angstrom'].std():.2f}; "
          f"AERONET α 465–619 = {m['aer_alpha_465_619'].mean():.2f}, "
          f"440–675 = {m['aer_440_675_alpha'].mean():.2f}, 440–870 = {m['aer_440_870_alpha'].mean():.2f}")
    m30 = matches[MATCH_WINDOWS_MIN[1]]
    print(f"  (±{MATCH_WINDOWS_MIN[1]} min: bias 540 nm = {stats(m30, 540)['bias']:+.4f}, "
          f"RMSE = {stats(m30, 540)['rmse']:.4f})")


# ---------------------------------------------------------------------------
def main():
    aer, meta = load_aeronet()
    cal = load_calitoo_day()
    matches = {w: match(cal, aer, w) for w in MATCH_WINDOWS_MIN}
    out = pd.concat(matches.values(), ignore_index=True).drop(columns="datetime_utc")
    out.to_csv(OUT_DIR / "calitoo_vs_aeronet.csv", index=False, float_format="%.5g")
    keep = ["datetime_utc", "AOD_340nm", "AOD_380nm", "AOD_440nm", "AOD_500nm", "AOD_675nm",
            "AOD_870nm", "AOD_1020nm", "AOD_1640nm", "aod_465", "aod_540", "aod_550", "aod_619",
            "440-870_Angstrom_Exponent", "440-675_Angstrom_Exponent", "alpha_465_619",
            "Triplet_Variability_870", "Triplet_Variability_1020", "cloud_triplet",
            "cloud_gross", "screened_ok"]
    aer[keep].to_csv(OUT_DIR / "aeronet_davos_screened.csv", index=False, float_format="%.5g")
    print("  saved calitoo_vs_aeronet.csv, aeronet_davos_screened.csv")
    fig_timeseries(aer, cal, meta)
    fig_scatter(matches[MATCH_WINDOWS_MIN[0]], meta)
    fig_spectrum(aer, cal, meta)
    report(aer, meta, cal, matches)


if __name__ == "__main__":
    main()
