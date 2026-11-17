#!/usr/bin/env python3
"""Analysis of Calitoo sun photometer data (AOT at 465/540/619 nm).

Reads every file listed in FILE_SITES, merges them into one DataFrame,
writes output/calitoo_all.csv and output/summary.csv and creates the plots
in output/.

To add a new file: add a line to FILE_SITES (and, for a new site, an entry
in SITES). Colors/markers per site-day are assigned automatically.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# file -> site  (add new files here)
# A file with two acquisitions at different sites can be split by LOCAL time:
# a list of (local start "HH:MM", site); each site applies from its start onwards.
FILE_SITES = {
    "calitoo_sep30.txt": "Zurich",
    "calitoo_oct6.txt": "Zurich",
    "calitoo_oct7.txt": "Davos",
    "calitoo_oct10.txt": "Lugano",
    # 14 Nov: calibration attempt outside Bern until 14:00 local (CET), then AOT in Bern
    "calitoo_nov14.txt": [("00:00", "Near Bern"), ("14:00", "Bern")],
}

# nominal site coordinates and altitude (used to check the GPS positions)
SITES = {
    "Zurich": {"lat": 47.37, "lon": 8.54, "alt_nom": 450},
    "Davos": {"lat": 46.80, "lon": 9.83, "alt_nom": 1560},
    "Lugano": {"lat": 46.00, "lon": 8.95, "alt_nom": 270},
    "Bern": {"lat": 46.95, "lon": 7.45, "alt_nom": 540},
    # calibration spot ~6 km W of Bern: no nominal position, GPS mean of 14 Nov used
    "Near Bern": {"lat": 46.966, "lon": 7.373, "alt_nom": 515},
}
MAX_DIST_KM = 5.0          # max allowed distance from the nominal position
SESSION_GAP_MIN = 10       # measurements < 10 min apart = same session
QC_MIN_R2 = 0.80           # quality threshold on the Ångström fit R² (column 16)
OUTLIER_REL = 0.25         # min relative deviation from the session median
LOCAL_TZ = "Europe/Zurich" # file times are UTC (checked vs solar elevation); local =
                           # CEST (UTC+2) until 25 Oct 2026, CET (UTC+1) afterwards

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "output"

WL = np.array([465.0, 540.0, 619.0])           # nm
BANDS = ["aot_465", "aot_540", "aot_619"]
RAWS = ["raw_465", "raw_540", "raw_619"]
BAND_COLORS = {465: "#1f5fbf", 540: "#2e9a3a", 619: "#d23a2a"}  # blue/green/red

# site/day colors: hues away from the blue/green/red used for the bands,
# always paired with a distinct marker (identity never relies on color alone)
SITE_DAY_COLORS = ["#eb6834", "#7c5cd6", "#14a3a3", "#c98500", "#e05a9a", "#555555"]
SITE_DAY_MARKERS = ["o", "s", "^", "D", "v", "P"]

MONTHS = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
          7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

COLUMNS = ["date", "time", "temp_C", "pressure_hPa", "raw_465", "raw_540",
           "raw_619", "alt_m", "lat_raw", "lon_raw", "sun_elev_deg",
           "aot_465", "aot_540", "aot_619", "angstrom", "fit_r2"]

plt.rcParams.update({
    "font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14,
    "legend.fontsize": 11, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 100,
})


# ---------------------------------------------------------------------------
# READING AND CLEANING
# ---------------------------------------------------------------------------
def ddmm_to_deg(s: str) -> float:
    """'4722.59913N' -> 47.3766 ; '00832.77144E' -> 8.5462"""
    s = s.strip()
    hemi = s[-1].upper()
    val = s[:-1]
    dot = val.index(".")
    deg = int(val[: dot - 2])
    minutes = float(val[dot - 2:])
    out = deg + minutes / 60.0
    return -out if hemi in "SW" else out


def parse_alt(s: str) -> float:
    """GPS altitude in m; '0000M' (fix without altitude) -> NaN."""
    s = s.strip()
    return float(s) if s.isdigit() else np.nan


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def label_day(site: str, d: pd.Timestamp) -> str:
    return f"{site} – {d.day} {MONTHS[d.month]} {d.year}"


def load_all() -> pd.DataFrame:
    frames = []
    for fname, site in FILE_SITES.items():
        path = DATA_DIR / fname
        if not path.exists():
            print(f"WARNING: {fname} not found, skipped")
            continue
        df = pd.read_csv(path, sep=";", header=None, dtype=str)
        if df.shape[1] != len(COLUMNS):
            raise ValueError(f"{fname}: {df.shape[1]} columns, expected {len(COLUMNS)}")
        df.columns = COLUMNS
        df["file"] = fname
        if isinstance(site, str):
            df["site"] = site
        else:   # split by local time of day
            t_loc = (pd.to_datetime(df["date"] + " " + df["time"], utc=True)
                     .dt.tz_convert(LOCAL_TZ).dt.strftime("%H:%M:%S"))
            df["site"] = None
            for start, s in sorted(site):
                df.loc[t_loc >= start, "site"] = s
            print(f"  {fname}: " + ", ".join(f"{s} n={n}" for s, n in
                                             df["site"].value_counts(sort=False).items()))
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    df["datetime_utc"] = pd.to_datetime(df["date"] + " " + df["time"], utc=True)
    df["date"] = df["datetime_utc"].dt.date
    for c in ["temp_C", "pressure_hPa", "sun_elev_deg", "angstrom", "fit_r2",
              *RAWS, *BANDS]:
        df[c] = pd.to_numeric(df[c].str.strip())
    df["alt_m"] = df["alt_m"].map(parse_alt)
    df["lat"] = df["lat_raw"].map(ddmm_to_deg)
    df["lon"] = df["lon_raw"].map(ddmm_to_deg)

    # distance from the nominal site position
    nom = df["site"].map(SITES)
    df["dist_site_km"] = haversine_km(df["lat"], df["lon"],
                                      nom.map(lambda s: s["lat"]),
                                      nom.map(lambda s: s["lon"]))

    # AOT at 500 nm extrapolated with each measurement's own Ångström exponent
    df["aot_500"] = df["aot_540"] * (500.0 / 540.0) ** (-df["angstrom"])
    # air mass (Kasten & Young 1989 approximation)
    h = df["sun_elev_deg"]
    df["airmass"] = 1.0 / (np.sin(np.radians(h)) + 0.50572 * (h + 6.07995) ** -1.6364)

    # quality flags
    df["qc_alt_missing"] = df["alt_m"].isna()
    df["qc_far_from_site"] = df["dist_site_km"] > MAX_DIST_KM
    df["qc_low_r2"] = df["fit_r2"] < QC_MIN_R2

    df = df.sort_values(["site", "datetime_utc"]).reset_index(drop=True)

    # site/day identifier and sessions
    df["day_key"] = df["site"] + "_" + df["datetime_utc"].dt.strftime("%Y-%m-%d")
    df["day_label"] = [label_day(s, t) for s, t in zip(df["site"], df["datetime_utc"])]
    sess = []
    for _, g in df.groupby("day_key", sort=False):
        gap = g["datetime_utc"].diff().dt.total_seconds().div(60)
        sess.append((gap.isna() | (gap >= SESSION_GAP_MIN)).cumsum())
    df["session"] = pd.concat(sess).astype(int)
    df["session_id"] = df["day_key"] + "_S" + df["session"].astype(str)
    # robust within-session outlier (thin cloud / pointing): AOT 540 further from
    # the session median than max(3·σ_MAD, OUTLIER_REL·median)
    def _outlier(x):
        if len(x) < 4:
            return pd.Series(False, index=x.index)
        med = x.median()
        sig = 1.4826 * (x - med).abs().median()
        return (x - med).abs() > max(3 * sig, OUTLIER_REL * med)
    df["qc_outlier"] = df.groupby("session_id", group_keys=False)["aot_540"].apply(_outlier)
    df["qc_ok"] = ~(df["qc_low_r2"] | df["qc_far_from_site"] | df["qc_outlier"])

    df["time_local"] = df["datetime_utc"].dt.tz_convert(LOCAL_TZ).dt.strftime("%H:%M:%S")

    # chronological order of site/days
    order = (df.groupby("day_key")["datetime_utc"].min().sort_values().index.tolist())
    df["day_key"] = pd.Categorical(df["day_key"], categories=order, ordered=True)
    df = df.sort_values(["day_key", "datetime_utc"]).reset_index(drop=True)
    return df


def day_styles(df):
    keys = list(df["day_key"].cat.categories)
    labels = df.drop_duplicates("day_key").set_index("day_key")["day_label"]
    return {k: {"color": SITE_DAY_COLORS[i % len(SITE_DAY_COLORS)],
                "marker": SITE_DAY_MARKERS[i % len(SITE_DAY_MARKERS)],
                "label": labels[k],
                "short": labels[k].replace(" 2026", "")}
            for i, k in enumerate(keys)}


def angstrom_fit(aot):
    """Fit AOT = β·λ^(-α), λ in µm. Returns (α, β, R²)."""
    x, y = np.log(WL / 1000.0), np.log(np.asarray(aot, float))
    slope, intercept = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    return -slope, np.exp(intercept), r * r


# ---------------------------------------------------------------------------
# TABLES
# ---------------------------------------------------------------------------
def make_summary(df):
    rows = []
    for sid, g in df.groupby("session_id", sort=False):
        ok = g[g["qc_ok"]]
        row = {
            "site": g["site"].iat[0], "date": g["date"].iat[0],
            "session": int(g["session"].iat[0]), "session_id": sid,
            "n": len(g), "n_qc_ok": len(ok),
            "start_utc": g["datetime_utc"].min().strftime("%H:%M:%S"),
            "end_utc": g["datetime_utc"].max().strftime("%H:%M:%S"),
            "lat_mean": g["lat"].mean(), "lon_mean": g["lon"].mean(),
            "dist_site_km": g["dist_site_km"].mean(),
            "alt_m_median": g["alt_m"].median(),
            "pressure_hPa_mean": g["pressure_hPa"].mean(),
            "temp_C_mean": g["temp_C"].mean(),
            "sun_elev_mean": g["sun_elev_deg"].mean(),
            "airmass_mean": g["airmass"].mean(),
        }
        for c in [*BANDS, "aot_500", "angstrom"]:
            row[f"{c}_mean"] = ok[c].mean()
            row[f"{c}_std"] = ok[c].std()
            row[f"{c}_min"] = ok[c].min()
            row[f"{c}_max"] = ok[c].max()
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# PLOTS
# ---------------------------------------------------------------------------
def save(fig, name):
    fig.savefig(OUT_DIR / name)
    plt.close(fig)
    print(f"  saved {name}")


def plot_bands_timeseries(ax, g, ylim=None, legend=True):
    """AOT of the 3 bands vs time; lines broken between sessions; QC-flagged = x."""
    for wl, c in zip(WL.astype(int), BANDS):
        col = BAND_COLORS[wl]
        for _, s in g.groupby("session"):
            sok = s[s["qc_ok"]]
            ax.plot(sok["datetime_utc"], sok[c], "-o", color=col, lw=2, ms=6,
                    mec="white", mew=1)
        bad = g[~g["qc_ok"]]
        ax.plot(bad["datetime_utc"], bad[c], "x", color=col, ms=9, mew=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    span_min = (g["datetime_utc"].max() - g["datetime_utc"].min()).total_seconds() / 60
    step = next((s for s in [1, 2, 5, 10, 15, 30, 60, 120] if span_min / s <= 6), 180)
    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, step))
                               if step < 60 else mdates.HourLocator(interval=step // 60))
    ax.set_xlabel("Time (GMT)")
    if ylim:
        ax.set_ylim(*ylim)
    if legend:
        h = [Line2D([], [], color=BAND_COLORS[w], marker="o", lw=2, label=f"{w} nm")
             for w in WL.astype(int)]
        if (~g["qc_ok"]).any():
            h.append(Line2D([], [], color="gray", marker="x", ls="", ms=9, mew=2,
                            label="rejected (QC)"))
        ax.legend(handles=h, loc="best", frameon=False)


def fig_daily(df, st):
    for k, g in df.groupby("day_key", observed=True):
        fig, ax = plt.subplots(figsize=(10, 5.5))
        plot_bands_timeseries(ax, g)
        ax.set_ylabel("AOT")
        ax.set_ylim(bottom=0)
        ax.set_title(st[k]["label"])
        d = g["datetime_utc"].iat[0]
        save(fig, f"aot_timeseries_{g['site'].iat[0]}_{d:%Y-%m-%d}.png")


def fig_timeseries_all(df, st):
    keys = list(df["day_key"].cat.categories)
    ymax = df[BANDS].max().max() * 1.08
    fig, axes = plt.subplots(1, len(keys), figsize=(5 * len(keys), 5.5), sharey=True)
    for i, (ax, k) in enumerate(zip(np.atleast_1d(axes), keys)):
        g = df[df["day_key"] == k]
        plot_bands_timeseries(ax, g, ylim=(0, ymax), legend=(i == 0))
        ax.set_title(st[k]["label"], fontsize=14)
        ax.tick_params(axis="x", rotation=30)
    np.atleast_1d(axes)[0].set_ylabel("AOT")
    fig.suptitle("AOT at 465/540/619 nm – all days (same scale)", y=1.02)
    fig.tight_layout()
    save(fig, "aot_timeseries_all.png")


def day_spectra(df):
    """Mean of the session means (QC-passed only) for each site/day."""
    ok = df[df["qc_ok"]]
    sess = ok.groupby(["day_key", "session"], observed=True)[BANDS + ["angstrom"]].mean()
    out = {}
    for k, s in sess.groupby(level=0, observed=True):
        mean = s[BANDS].mean().values
        std = ok[ok["day_key"] == k][BANDS].std().values
        a, b, r2 = angstrom_fit(mean)
        out[k] = dict(mean=mean, std=std, alpha=a, beta=b, r2=r2,
                      alpha_col15=ok[ok["day_key"] == k]["angstrom"].mean(),
                      alpha_col15_std=ok[ok["day_key"] == k]["angstrom"].std(),
                      n_sess=len(s))
    return out


def fig_spectrum(df, st, spec):
    fig, ax = plt.subplots(figsize=(10, 8.5))
    lam_fine = np.linspace(440, 650, 50)
    for k, v in spec.items():
        s = st[k]
        ax.errorbar(WL, v["mean"], yerr=v["std"], fmt=s["marker"], color=s["color"],
                    ms=9, mec="white", capsize=4, lw=1.5)
        ax.plot(lam_fine, v["beta"] * (lam_fine / 1000) ** (-v["alpha"]), "-",
                color=s["color"], lw=2,
                label=(f"{s['short']}:  α={v['alpha']:.2f}  β={v['beta']:.3f}"
                       f"   (col.15: {v['alpha_col15']:.2f}±{v['alpha_col15_std']:.2f})"))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(WL)
    ax.set_xticklabels([f"{int(w)}" for w in WL])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("AOT")
    ax.set_title("AOT spectrum per site/day – fit AOT = β·λ$^{-α}$ (λ in µm)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False, fontsize=12,
              title="mean of sessions (bars = std of measurements); in brackets: mean of col. 15",
              title_fontsize=11)
    ax.grid(True, which="both", color="#e5e5e5")
    save(fig, "aot_spectrum.png")


def fig_box_with_points(ax, df, st, col, flagged_too=True):
    keys = list(df["day_key"].cat.categories)
    data = [df[(df["day_key"] == k) & df["qc_ok"]][col].values for k in keys]
    ax.boxplot(data, positions=range(len(keys)), widths=0.5, showfliers=False,
               medianprops=dict(color="black", lw=2),
               boxprops=dict(color="#666666"), whiskerprops=dict(color="#666666"),
               capprops=dict(color="#666666"))
    rng = np.random.default_rng(0)
    for i, k in enumerate(keys):
        g = df[df["day_key"] == k]
        x = i + rng.uniform(-0.15, 0.15, len(g))
        ok = g["qc_ok"].values
        ax.scatter(x[ok], g[col].values[ok], color=st[k]["color"], marker=st[k]["marker"],
                   s=55, edgecolor="white", lw=1, zorder=3)
        if flagged_too and (~ok).any():
            ax.scatter(x[~ok], g[col].values[~ok], color=st[k]["color"], marker="x",
                       s=70, lw=2, zorder=3)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([st[k]["short"].replace(" – ", "\n") for k in keys])


def fig_angstrom(df, st):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig_box_with_points(ax, df, st, "angstrom")
    ax.set_ylabel("Ångström exponent α (col. 15)")
    ax.set_title("Ångström exponent per site/day")
    ax.legend(handles=[Line2D([], [], color="gray", marker="x", ls="", ms=9, mew=2,
                              label="rejected (QC: R² < 0.8 or outlier), excluded from box")],
              loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False)
    save(fig, "angstrom_by_site.png")


def fig_aot_box(df, st):
    keys = list(df["day_key"].cat.categories)
    fig, ax = plt.subplots(figsize=(12, 6))
    w = 0.25
    for j, (wl, c) in enumerate(zip(WL.astype(int), BANDS)):
        data = [df[(df["day_key"] == k) & df["qc_ok"]][c].values for k in keys]
        pos = np.arange(len(keys)) + (j - 1) * w
        bp = ax.boxplot(data, positions=pos, widths=w * 0.85, patch_artist=True,
                        showfliers=True, flierprops=dict(marker="o", ms=5,
                                                         mfc=BAND_COLORS[wl], mec="none"),
                        medianprops=dict(color="black", lw=1.5))
        for b in bp["boxes"]:
            b.set(facecolor=BAND_COLORS[wl], alpha=0.75, edgecolor="white")
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([st[k]["short"].replace(" – ", "\n") for k in keys])
    ax.set_ylabel("AOT")
    ax.set_ylim(bottom=0)
    ax.set_title("AOT distribution per site/day (QC-passed only)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BAND_COLORS[w], alpha=0.75,
                                     label=f"{w} nm") for w in WL.astype(int)],
              frameon=False, loc="upper right")
    save(fig, "aot_boxplot_by_site.png")


def fig_aot_altitude(df, st):
    ok = df[df["qc_ok"]]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    site_alt = df.groupby("site")["alt_m"].median()
    offsets = {}
    for k, g in ok.groupby("day_key", observed=True):
        site = g["site"].iat[0]
        n_same = offsets.get(site, 0)
        offsets[site] = n_same + 1
        alt = site_alt[site] + n_same * 30   # small offset for Zurich (2 days)
        s = st[k]
        ax.errorbar(alt, g["aot_500"].mean(), yerr=g["aot_500"].std(), fmt=s["marker"],
                    color=s["color"], ms=11, mec="white", capsize=5, lw=2,
                    label=f"{s['short']}  (n={len(g)})")
        ax.errorbar(alt, g["aot_540"].mean(), yerr=g["aot_540"].std(), fmt=s["marker"],
                    mfc="white", mec=s["color"], color=s["color"], ms=9, capsize=3,
                    lw=1, alpha=0.9)
    # labels next to the points (Lugano and Zurich have almost the same GPS altitude)
    place = {"Zurich": ((40, 0), "left", "center"), "Lugano": ((0, -38), "center", "top"),
             "Davos": ((-40, 0), "right", "center")}
    for site, a in site_alt.items():
        y = ok[ok["site"] == site]["aot_500"].mean()
        off, ha, va = place.get(site, ((40, 0), "left", "center"))
        ax.annotate(f"{site}\nGPS {a:.0f} m (nom. {SITES[site]['alt_nom']} m)", (a, y),
                    xytext=off, textcoords="offset points", ha=ha, va=va, fontsize=12,
                    color="#333333")
    ax.set_xlabel("Site altitude (m, GPS median)")
    ax.set_ylabel("AOT")
    ax.set_ylim(0, None)
    ax.set_xlim(site_alt.min() - 250, site_alt.max() + 250)
    h = [Line2D([], [], marker=st[k]["marker"], color=st[k]["color"], ls="", ms=10,
                label=f"{st[k]['short']}  (n={(ok['day_key'] == k).sum()})")
         for k in df["day_key"].cat.categories]
    h += [Line2D([], [], marker="o", color="gray", ls="", ms=10, label="AOT 500 nm (filled)"),
          Line2D([], [], marker="o", mfc="white", mec="gray", ls="", ms=9,
                 label="AOT 540 nm (open)")]
    ax.legend(handles=h, frameon=False, loc="upper center", ncol=2, fontsize=11)
    ax.set_title("Mean AOT vs altitude (bars = std of measurements)")
    save(fig, "aot_vs_altitude.png")


def fig_zurich(df, st, spec):
    z = df[df["site"] == "Zurich"]
    keys = [k for k in df["day_key"].cat.categories if k in set(z["day_key"].astype(str))]
    if len(keys) < 2:
        print("  (fewer than 2 days in Zurich: zurich_comparison skipped)")
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6),
                                 gridspec_kw=dict(width_ratios=[1.4, 1]))
    for k in keys:
        g = z[z["day_key"] == k]
        s = st[k]
        tod = (g["datetime_utc"] - g["datetime_utc"].dt.normalize()).dt.total_seconds() / 3600
        okm = g["qc_ok"].values
        for sess in g["session"].unique():
            m = (g["session"].values == sess) & okm
            a1.plot(tod[m], g["aot_540"][m], "-", marker=s["marker"], color=s["color"],
                    ms=8, mec="white", lw=2)
        a1.plot(tod[~okm], g["aot_540"][~okm], "x", color=s["color"], ms=10, mew=2)
        a1.plot([], [], "-", marker=s["marker"], color=s["color"], ms=8, label=s["short"])
        v = spec[k]
        a2.errorbar(WL, v["mean"], yerr=v["std"], fmt=s["marker"], color=s["color"],
                    ms=9, mec="white", capsize=4,
                    label=f"{s['short']}: α={v['alpha']:.2f}, β={v['beta']:.3f}")
        lf = np.linspace(450, 630, 30)
        a2.plot(lf, v["beta"] * (lf / 1000) ** (-v["alpha"]), color=s["color"], lw=2)
    a1.plot([], [], "x", color="gray", ms=10, mew=2, label="rejected (QC)")
    a1.set_xlabel("Time (GMT, h)")
    a1.set_ylabel("AOT 540 nm")
    a1.set_ylim(bottom=0)
    a1.set_title("AOT 540 nm vs time")
    a1.legend(frameon=False)
    a2.set_xlabel("Wavelength (nm)")
    a2.set_ylabel("AOT")
    a2.set_ylim(bottom=0)
    a2.set_title("Mean spectrum + Ångström fit")
    a2.legend(frameon=False, fontsize=11)
    fig.suptitle("Zurich – 30 Sep vs 6 Oct 2026", y=1.01)
    fig.tight_layout()
    save(fig, "zurich_comparison.png")


def legend_days(ax, st, keys, **kw):
    ax.legend(handles=[Line2D([], [], color=st[k]["color"], marker=st[k]["marker"], ls="",
                              ms=9, label=st[k]["short"]) for k in keys]
              + [Line2D([], [], color="gray", marker="x", ls="", ms=9, mew=2,
                        label="rejected (QC)")], frameon=False, **kw)


def scatter_days(ax, df, st, ycol, xcol="sun_elev_deg"):
    for k, g in df.groupby("day_key", observed=True):
        s = st[k]
        ok = g["qc_ok"]
        ax.scatter(g.loc[ok, xcol], g.loc[ok, ycol], color=s["color"], marker=s["marker"],
                   s=60, edgecolor="white", lw=1, zorder=3)
        ax.scatter(g.loc[~ok, xcol], g.loc[~ok, ycol], color=s["color"], marker="x",
                   s=70, lw=2, zorder=3)


def fig_elevation(df, st):
    keys = list(df["day_key"].cat.categories)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6))
    scatter_days(a1, df, st, "aot_540")
    a1.set_ylabel("AOT 540 nm")
    a1.set_ylim(bottom=0)
    a1.set_title("AOT 540 nm vs solar elevation")
    scatter_days(a2, df, st, "angstrom")
    a2.set_ylabel("Ångström exponent α")
    a2.set_title("Ångström vs solar elevation")
    for a in (a1, a2):
        a.set_xlabel("Solar elevation (°)")
    legend_days(a1, st, keys, loc="lower right", fontsize=10)
    fig.tight_layout()
    save(fig, "aot_vs_elevation.png")


def fig_raw(df, st):
    keys = list(df["day_key"].cat.categories)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), sharex=True)
    for ax, wl, c in zip(axes, WL.astype(int), RAWS):
        scatter_days(ax, df, st, c)
        ax.set_title(f"Raw signal {wl} nm", color=BAND_COLORS[wl])
        ax.set_xlabel("Solar elevation (°)")
    axes[0].set_ylabel("Signal (counts)")
    legend_days(axes[0], st, keys, loc="upper left", fontsize=10)
    fig.suptitle("Raw signals vs solar elevation", y=1.02)
    fig.tight_layout()
    save(fig, "raw_signals.png")


def fig_session_var(df, st, summary):
    fig, ax = plt.subplots(figsize=(14, 6.5))
    n = len(summary)
    x = np.arange(n)
    for j, (wl, c) in enumerate(zip(WL.astype(int), BANDS)):
        ax.errorbar(x + (j - 1) * 0.18, summary[f"{c}_mean"], yerr=summary[f"{c}_std"],
                    fmt="o", color=BAND_COLORS[wl], ms=8, mec="white", capsize=4, lw=2,
                    label=f"{wl} nm")
    labels = []
    for _, r in summary.iterrows():
        d = pd.Timestamp(r["date"])
        cv = 100 * r["aot_540_std"] / r["aot_540_mean"]
        labels.append(f"{r['site']} {d.day} {MONTHS[d.month]}\n{r['start_utc'][:5]}–"
                      f"{r['end_utc'][:5]}\nn={r['n_qc_ok']}  CV={cv:.0f}%")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("AOT (mean ± std)")
    ax.set_ylim(bottom=0)
    ax.set_title("Repeatability per session (CV = std/mean at 540 nm; times GMT)")
    ax.legend(frameon=False, ncol=3, loc="upper right")
    save(fig, "session_variability.png")


def fig_map(df, st):
    # no cartopy/geopandas: lat/lon scatter in an equirectangular projection
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ref = {"Basel": (47.56, 7.59), "Bern": (46.95, 7.45), "Geneva": (46.20, 6.14),
           "Chur": (46.85, 9.53), "Sion": (46.23, 7.36)}
    for name, (la, lo) in ref.items():
        ax.plot(lo, la, "o", color="#bbbbbb", ms=6)
        ax.annotate(name, (lo, la), xytext=(5, 4), textcoords="offset points",
                    fontsize=11, color="#888888")
    for site, s in SITES.items():
        ax.plot(s["lon"], s["lat"], "+", color="black", ms=16, mew=1.5)
    for k, g in df.groupby("day_key", observed=True):
        s = st[k]
        ax.scatter(g["lon"], g["lat"], color=s["color"], marker=s["marker"], s=90,
                   edgecolor="white", lw=1, zorder=3, label=s["short"])
    for site, g in df.groupby("site"):
        ax.annotate(f"{site}\n{g['lat'].mean():.3f}N {g['lon'].mean():.3f}E\n"
                    f"{g['alt_m'].median():.0f} m",
                    (g["lon"].mean(), g["lat"].mean()), xytext=(12, -10),
                    textcoords="offset points", fontsize=12, fontweight="bold")
    ax.set_xlim(5.9, 11.0)
    ax.set_ylim(45.75, 47.9)
    ax.set_aspect(1 / np.cos(np.radians(46.8)))
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Calitoo measurement locations (+ = nominal site position)")
    ax.legend(frameon=False, loc="lower left", fontsize=11)
    save(fig, "map_locations.png")


# ---------------------------------------------------------------------------
# TEXT REPORT
# ---------------------------------------------------------------------------
def print_report(df, summary, spec, st):
    ok = df[df["qc_ok"]]
    print("\n================ CHECKS ================")
    print(f"Total measurements: {len(df)}  –  QC ok: {len(ok)}  –  rejected: {len(df) - len(ok)}")
    for site, g in df.groupby("site"):
        print(f"  {site:7s}: lat {g['lat'].mean():.4f}N lon {g['lon'].mean():.4f}E, "
              f"distance from nominal {g['dist_site_km'].mean():.1f} km "
              f"(max {g['dist_site_km'].max():.1f}), median GPS alt {g['alt_m'].median():.0f} m "
              f"(nominal {SITES[site]['alt_nom']} m), mean p {g['pressure_hPa'].mean():.0f} hPa")
    far = df[df["qc_far_from_site"]]
    print(f"Measurements > {MAX_DIST_KM} km from site: {len(far)}")
    print(f"Missing altitude ('0000M'): {df['qc_alt_missing'].sum()} measurements")
    print(f"Rejected (R² < {QC_MIN_R2} or session outlier):")
    for _, r in df[~df["qc_ok"]].iterrows():
        why = "R²" if r["qc_low_r2"] else "outlier"
        print(f"   [{why}] {r['day_label']} {r['time']}  AOT={r['aot_465']:.3f}/{r['aot_540']:.3f}/"
              f"{r['aot_619']:.3f}  α={r['angstrom']:.2f}  R²={r['fit_r2']:.2f}")

    print("\n================ AOT AND ÅNGSTRÖM PER SITE/DAY (QC ok) ================")
    for k, g in ok.groupby("day_key", observed=True):
        v = spec[k]
        print(f"  {st[k]['label']:22s} n={len(g):2d}  AOT500={g['aot_500'].mean():.3f}±"
              f"{g['aot_500'].std():.3f}  AOT540={g['aot_540'].mean():.3f}±{g['aot_540'].std():.3f}"
              f"  α col15={g['angstrom'].mean():.2f}±{g['angstrom'].std():.2f}"
              f"  α fit of mean spectrum={v['alpha']:.2f} (β={v['beta']:.3f})")
    print("\n================ SESSIONS ================")
    cols = ["site", "date", "session", "start_utc", "end_utc", "n", "n_qc_ok",
            "sun_elev_mean", "aot_540_mean", "aot_540_std", "angstrom_mean"]
    print(summary[cols].round(3).to_string(index=False))


# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(exist_ok=True)
    df = load_all()
    st = day_styles(df)

    out_cols = ["site", "file", "date", "time", "time_local", "datetime_utc", "session",
                "session_id", "temp_C", "pressure_hPa", "alt_m", "lat", "lon",
                "dist_site_km", "sun_elev_deg", "airmass", *RAWS, *BANDS, "aot_500",
                "angstrom", "fit_r2", "qc_ok", "qc_low_r2", "qc_outlier", "qc_alt_missing",
                "qc_far_from_site", "lat_raw", "lon_raw"]
    df[out_cols].to_csv(OUT_DIR / "calitoo_all.csv", index=False, float_format="%.6g")
    summary = make_summary(df)
    summary.to_csv(OUT_DIR / "summary.csv", index=False, float_format="%.5g")
    print("  saved calitoo_all.csv, summary.csv")

    spec = day_spectra(df)
    fig_daily(df, st)
    fig_timeseries_all(df, st)
    fig_spectrum(df, st, spec)
    fig_angstrom(df, st)
    fig_aot_box(df, st)
    fig_aot_altitude(df, st)
    fig_zurich(df, st, spec)
    fig_elevation(df, st)
    fig_raw(df, st)
    fig_session_var(df, st, summary)
    fig_map(df, st)
    print_report(df, summary, spec, st)


if __name__ == "__main__":
    main()
