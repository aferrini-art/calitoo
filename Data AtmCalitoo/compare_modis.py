#!/usr/bin/env python3
"""Compare Calitoo AOT (converted to 550 nm) with MODIS-Aqua MYD08_D3 v6.1 AOD 550 nm.

Reuses output/calitoo_all.csv (run plot_calitoo.py first) and the GIOVANNI
area-averaged time series in MODIS_DIR. Writes output/calitoo_vs_modis.csv,
output/modis_bboxes.csv and the comparison plots.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

import plot_calitoo as pc   # shared style (rcParams), colors, site metadata

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "output"
MODIS_DIR = BASE / "giovanni_data"
# site -> list of GIOVANNI CSV files (add more files here)
MODIS_FILES = {
    "Zurich": ["Zurich6.10.csv"],
    "Davos": ["Davos.csv"],
    "Lugano": ["Lugano10.10.csv"],
}
AQUA_CENTER_UTC = 12.25    # 12:15 UTC, typical Aqua overpass over Switzerland
AQUA_HALF_WIN_H = 1.5      # ±1.5 h window
GRID_RES_DEG = 1.0         # MYD08_D3 grid; GIOVANNI "Data Bounding Box" = cell centres
SITE_ORDER = ["Zurich", "Davos", "Lugano"]
SITE_COLORS = {"Zurich": "#7c5cd6", "Davos": "#14a3a3", "Lugano": "#c98500"}
SITE_MARKERS = {"Zurich": "s", "Davos": "^", "Lugano": "D"}
MODIS_COLOR = "#444444"
EE = lambda aod: 0.05 + 0.15 * aod   # MODIS DT expected error over land
AER_COLOR = "#222222"
AERONET_SITES = ["Davos"]            # sites with an AERONET station (see compare_aeronet.py)


def load_aeronet_daily():
    """{site: daily AERONET AOD 550 table} – empty if the AERONET file/module is missing."""
    try:
        import compare_aeronet as ca
        return {s: ca.aeronet_daily_550() for s in AERONET_SITES}, ca.load_aeronet()[1]["level"]
    except (ImportError, FileNotFoundError) as e:
        print(f"  (AERONET not available: {e})")
        return {}, ""


# ---------------------------------------------------------------------------
# READING
# ---------------------------------------------------------------------------
def read_giovanni(path: Path):
    """Return (metadata dict, DataFrame[date, aod550]) from a GIOVANNI CSV."""
    meta, lines = {}, path.read_text().splitlines()
    i = 0
    while i < len(lines) and lines[i].strip():
        key, _, val = lines[i].partition(":,")
        meta[key.strip()] = val.strip().strip('"').strip()
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    header = [h.strip() for h in lines[i].split(",")]
    rows = [l.split(",") for l in lines[i + 1:] if l.strip()]
    df = pd.DataFrame(rows, columns=header)
    var = header[1]
    fill = float(next(v for k, v in meta.items() if k.startswith("Fill Value")))
    out = pd.DataFrame({"date": pd.to_datetime(df[header[0]]).dt.date,
                        "aod550": pd.to_numeric(df[var])})
    out["missing"] = out["aod550"] == fill
    out.loc[out["missing"], "aod550"] = np.nan
    out["negative"] = out["aod550"] < 0          # kept, flagged as physically questionable
    meta["variable"] = var
    meta["fill_value"] = fill
    return meta, out


def bbox(s):
    w, so, e, n = (float(x) for x in s.split(","))
    return dict(west=w, south=so, east=e, north=n)


def load_modis():
    series, boxes = [], []
    for site, files in MODIS_FILES.items():
        for fname in files:
            meta, df = read_giovanni(MODIS_DIR / fname)
            df["site"], df["file"] = site, fname
            series.append(df)
            data_bb, user_bb = bbox(meta["Data Bounding Box"]), bbox(meta["User Bounding Box"])
            h = GRID_RES_DEG / 2
            boxes.append(dict(
                site=site, file=fname, variable=meta["variable"],
                start=meta["User Start Date"], end=meta["User End Date"],
                **{f"data_{k}": v for k, v in data_bb.items()},
                **{f"user_{k}": v for k, v in user_bb.items()},
                # area actually covered by the 1° cells whose centres span the data bbox
                cov_west=data_bb["west"] - h, cov_east=data_bb["east"] + h,
                cov_south=data_bb["south"] - h, cov_north=data_bb["north"] + h,
                fill_value=meta["fill_value"]))
    return pd.concat(series, ignore_index=True), pd.DataFrame(boxes)


def load_calitoo():
    df = pd.read_csv(OUT_DIR / "calitoo_all.csv", parse_dates=["datetime_utc"])
    df = df[df["qc_ok"]].copy()
    df["date"] = df["datetime_utc"].dt.date
    # 540 -> 550 nm with the Ångström exponent of col. 15 (= 3-band least-squares fit)
    df["aot_550"] = df["aot_540"] * (550.0 / 540.0) ** (-df["angstrom"])
    hours = df["datetime_utc"].dt.hour + df["datetime_utc"].dt.minute / 60 \
        + df["datetime_utc"].dt.second / 3600
    df["in_aqua_window"] = (hours - AQUA_CENTER_UTC).abs() <= AQUA_HALF_WIN_H
    return df


# ---------------------------------------------------------------------------
# COMPARISON TABLE
# ---------------------------------------------------------------------------
def compare(cal, modis, boxes):
    rows = []
    for (site, date), g in cal.groupby(["site", "date"], sort=False):
        w = g[g["in_aqua_window"]]
        m = modis[(modis["site"] == site) & (modis["date"] == date)]
        if m.empty:
            flag, aod = "date_not_in_modis_file", np.nan
        elif m["missing"].all():
            flag, aod = "missing_fill_-9999", np.nan
        else:
            aod = m["aod550"].dropna().iat[0]
            flag = "negative_questionable" if aod < 0 else "ok"
        ref = w["aot_550"].mean() if len(w) else g["aot_550"].mean()
        b = boxes[boxes["site"] == site].iloc[0]
        lat, lon = g["lat"].mean(), g["lon"].mean()
        rows.append(dict(
            site=site, date=date,
            n_all=len(g), aot550_all_mean=g["aot_550"].mean(), aot550_all_std=g["aot_550"].std(),
            time_all=f"{g['datetime_utc'].min():%H:%M}-{g['datetime_utc'].max():%H:%M}",
            n_aqua_window=len(w),
            aot550_aqua_mean=w["aot_550"].mean() if len(w) else np.nan,
            aot550_aqua_std=w["aot_550"].std() if len(w) > 1 else np.nan,
            time_aqua=(f"{w['datetime_utc'].min():%H:%M}-{w['datetime_utc'].max():%H:%M}"
                       if len(w) else ""),
            calitoo_ref="aqua_window" if len(w) else "all",
            modis_aod550=aod, modis_flag=flag,
            diff_modis_minus_calitoo=aod - ref,
            rel_diff_pct=100 * (aod - ref) / ref,
            within_modis_EE=abs(aod - ref) <= EE(ref) if np.isfinite(aod) else np.nan,
            site_lat=lat, site_lon=lon,
            inside_data_bbox=(b.data_south <= lat <= b.data_north) and (b.data_west <= lon <= b.data_east),
            inside_cell_coverage=(b.cov_south <= lat <= b.cov_north) and (b.cov_west <= lon <= b.cov_east),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# PLOTS
# ---------------------------------------------------------------------------
def save(fig, name):
    fig.savefig(OUT_DIR / name)
    plt.close(fig)
    print(f"  saved {name}")


def fmt_date(d):
    return f"{d.day} {pc.MONTHS[d.month]}"


def fig_timeseries(site, modis, comp, aer=None, aer_level=""):
    m = modis[modis["site"] == site].sort_values("date")
    c = comp[comp["site"] == site]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    dates = pd.to_datetime(m["date"])
    # missing days as grey bands
    for d in dates[m["missing"].values]:
        ax.axvspan(d - pd.Timedelta(hours=12), d + pd.Timedelta(hours=12),
                   color="#e6e6e6", lw=0, zorder=0)
    ok = ~m["missing"] & ~m["negative"]
    ax.plot(dates[ok.values], m.loc[ok, "aod550"], "o", color=MODIS_COLOR, ms=9,
            mec="white", zorder=3)
    neg = m["negative"].values
    ax.plot(dates[neg], m.loc[neg, "aod550"], "o", mfc="white", mec="#d23a2a", mew=2,
            ms=9, zorder=3)
    for d, v in zip(dates[neg], m.loc[neg, "aod550"]):
        ax.annotate(f"{v:.3f}\n(< 0)", (d, v), xytext=(0, -30), textcoords="offset points",
                    ha="center", fontsize=10, color="#d23a2a")
    col, mk = SITE_COLORS[site], SITE_MARKERS[site]
    for _, r in c.iterrows():
        d = pd.Timestamp(r["date"])
        ax.errorbar(d - pd.Timedelta(hours=3), r["aot550_all_mean"], yerr=r["aot550_all_std"],
                    fmt=mk, color=col, ms=10, mec="white", capsize=5, lw=2, zorder=4)
        if r["n_aqua_window"]:
            ax.errorbar(d + pd.Timedelta(hours=3), r["aot550_aqua_mean"],
                        yerr=np.nan_to_num(r["aot550_aqua_std"]), fmt=mk, mfc="white",
                        mec=col, color=col, ms=10, mew=2, capsize=5, lw=2, zorder=4)
        if r["modis_flag"] != "ok":
            note = {"missing_fill_-9999": "MODIS: no data / cloud",
                    "date_not_in_modis_file": "MODIS: date not\nin downloaded file"}.get(
                r["modis_flag"], r["modis_flag"])
            ax.annotate(note, (d, r["aot550_all_mean"]), xytext=(22, 0),
                        textcoords="offset points", ha="left", va="center", fontsize=10,
                        color="#666666")
    all_dates = [dates.min(), dates.max(), *pd.to_datetime(c["date"])]
    if aer is not None:
        ad = aer.dropna(subset=["aer550_day_mean"])
        dd = pd.to_datetime(ad["date"])
        ax.errorbar(dd + pd.Timedelta(hours=5), ad["aer550_day_mean"], yerr=ad["aer550_day_std"],
                    fmt="*", mfc="white", mec=AER_COLOR, color=AER_COLOR, ms=15, mew=1.5,
                    capsize=4, lw=1.2, zorder=5)
        aq = ad.dropna(subset=["aer550_aqua_mean"])
        ax.errorbar(pd.to_datetime(aq["date"]) + pd.Timedelta(hours=9), aq["aer550_aqua_mean"],
                    yerr=aq["aer550_aqua_std"], fmt="*", color=AER_COLOR, ms=15, capsize=4,
                    lw=1.2, zorder=5)
        all_dates += list(dd)
    lo = min(all_dates) - pd.Timedelta(days=1)
    hi = max(all_dates) + pd.Timedelta(days=1)
    ax.set_xlim(lo, hi)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1 if (hi - lo).days <= 10 else 2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(axis="x", rotation=30)
    ymin = min(0, np.nanmin(m["aod550"]) - 0.02) if m["negative"].any() else 0
    ax.set_ylim(ymin, None)
    ax.axhline(0, color="#999999", lw=1)
    ax.set_ylabel("AOD / AOT at 550 nm")
    f = m["file"].iat[0]
    ax.set_title(f"{site} – MODIS-Aqua MYD08_D3 (1° area mean) vs Calitoo"
                 + (f" and AERONET {aer_level}" if aer is not None else ""))
    h = [Line2D([], [], marker="o", color=MODIS_COLOR, ls="", ms=9, label="MODIS-Aqua AOD 550")]
    if m["negative"].any():
        h.append(Line2D([], [], marker="o", mfc="white", mec="#d23a2a", mew=2, ls="", ms=9,
                        label="MODIS < 0 (physically questionable)"))
    if m["missing"].any():
        h.append(Patch(color="#e6e6e6", label="MODIS no data / cloud (fill −9999)"))
    h.append(Line2D([], [], marker=mk, color=col, ls="", ms=10,
                    label="Calitoo AOT 550, all (mean ± std)"))
    if c["n_aqua_window"].sum():
        h.append(Line2D([], [], marker=mk, mfc="white", mec=col, mew=2, ls="", ms=10,
                        label=f"Calitoo AOT 550, Aqua window 12:15 ± {AQUA_HALF_WIN_H} h UTC"))
    else:
        h.append(Line2D([], [], ls="", label="(no Calitoo measurement in the Aqua window)"))
    if aer is not None:
        h += [Line2D([], [], marker="*", mfc="white", mec=AER_COLOR, ls="", ms=15,
                     label="AERONET 550, daily mean (cloud-screened)"),
              Line2D([], [], marker="*", color=AER_COLOR, ls="", ms=15,
                     label="AERONET 550, Aqua window 11:30–13:00 UTC")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2,
              frameon=False, fontsize=11)
    save(fig, f"modis_timeseries_{site}.png")


def fig_scatter(comp, aer_pairs=None):
    fig, ax = plt.subplots(figsize=(8, 8))
    lim = 0.15
    x = np.linspace(0, lim, 50)
    ax.fill_between(x, x - EE(x), x + EE(x), color="#eeeeee", lw=0, zorder=0)
    ax.plot(x, x, color="black", lw=1.5)
    ax.plot(x, x + EE(x), "--", color="#888888", lw=1)
    ax.plot(x, x - EE(x), "--", color="#888888", lw=1)
    ok = comp[np.isfinite(comp["modis_aod550"])]
    for _, r in ok.iterrows():
        col, mk = SITE_COLORS[r["site"]], SITE_MARKERS[r["site"]]
        if r["n_aqua_window"]:
            ax.errorbar(r["aot550_aqua_mean"], r["modis_aod550"],
                        xerr=np.nan_to_num(r["aot550_aqua_std"]), fmt=mk, mfc="white",
                        mec=col, mew=2, color=col, ms=17, capsize=5, lw=1.5, zorder=3)
        ax.errorbar(r["aot550_all_mean"], r["modis_aod550"], xerr=r["aot550_all_std"],
                    fmt=mk, color=col, ms=8, mec=col, capsize=5, lw=2, zorder=4)
        left = r["aot550_all_mean"] < 0.045
        ax.annotate(f"{r['site']} {fmt_date(r['date'])}", (r["aot550_all_mean"], r["modis_aod550"]),
                    xytext=(-14, 14) if left else (14, -22), textcoords="offset points",
                    ha="right" if left else "left", fontsize=12)
    if aer_pairs is not None and len(aer_pairs):
        for r in aer_pairs.itertuples():
            ax.errorbar(r.aer, r.modis, xerr=np.nan_to_num(r.aer_std), fmt="*", color=AER_COLOR,
                        ms=15, capsize=4, lw=1.2, zorder=4)
            ax.annotate(f"AERONET {r.site} {fmt_date(r.date)}", (r.aer, r.modis), xytext=(14, -14),
                        textcoords="offset points", fontsize=11, va="top")
    ax.set_xlim(0, lim)
    ax.set_ylim(-0.02, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Ground-based AOD 550 nm (Calitoo / AERONET)")
    ax.set_ylabel("MODIS-Aqua AOD 550 nm (1° area mean)")
    ax.set_title("Ground-based vs MODIS-Aqua")
    h = [Line2D([], [], color="black", lw=1.5, label="1:1"),
         Patch(color="#eeeeee", label="MODIS DT expected error ±(0.05 + 0.15·AOD)")]
    h += [Line2D([], [], marker=SITE_MARKERS[s], color=SITE_COLORS[s], ls="", ms=10,
                 label=f"{s}: all measurements (small, filled)") for s in ok["site"].unique()]
    h += [Line2D([], [], marker="o", mfc="white", mec="gray", mew=2, ls="", ms=14,
                 label="Aqua window only (large, open)")]
    if aer_pairs is not None and len(aer_pairs):
        h.append(Line2D([], [], marker="*", color=AER_COLOR, ls="", ms=14,
                        label="AERONET (Aqua window if available, else daily)"))
    miss = comp[~np.isfinite(comp["modis_aod550"])]
    if len(miss):
        h.append(Line2D([], [], ls="", label="No MODIS: " + ", ".join(
            f"{r.site} {fmt_date(r.date)}" for r in miss.itertuples())))
    ax.legend(handles=h, loc="upper left", frameon=False, fontsize=10)
    n_aer = 0 if aer_pairs is None else len(aer_pairs)
    ax.text(0.98, 0.02, f"n = {len(ok)} Calitoo + {n_aer} AERONET pairs – no regression",
            transform=ax.transAxes, ha="right", fontsize=11, color="#666666")
    save(fig, "calitoo_vs_modis_scatter.png")


def fig_bars(comp, aer_level=""):
    comp = comp.sort_values("date")
    fig, ax = plt.subplots(figsize=(13, 6.5))
    w = 0.2
    has_aer = "aer550_day_mean" in comp
    x = np.arange(len(comp))
    ymax = np.nanmax(comp[["aot550_all_mean", "aot550_aqua_mean", "modis_aod550"]].values) * 1.35
    for i, (_, r) in enumerate(comp.iterrows()):
        col = SITE_COLORS[r["site"]]
        ax.bar(i - 1.5 * w, r["aot550_all_mean"], w * 0.92, yerr=r["aot550_all_std"], color=col,
               capsize=4, edgecolor="white")
        if r["n_aqua_window"]:
            ax.bar(i - 0.5 * w, r["aot550_aqua_mean"], w * 0.92, yerr=np.nan_to_num(r["aot550_aqua_std"]),
                   color=col, alpha=0.45, hatch="//", edgecolor="white", capsize=4)
        else:
            ax.text(i - 0.5 * w, 0.003, "no Calitoo\nin Aqua\nwindow", ha="center", va="bottom",
                    fontsize=9, color="#666666", rotation=90)
        if np.isfinite(r["modis_aod550"]):
            ax.bar(i + 0.5 * w, r["modis_aod550"], w * 0.92, color=MODIS_COLOR, edgecolor="white")
            ax.text(i + 0.5 * w, r["modis_aod550"] + 0.002, f"{r['modis_aod550']:.3f}", ha="center",
                    va="bottom", fontsize=10)
        else:
            why = "no data/\ncloud" if r["modis_flag"].startswith("missing") else "not\ndownloaded"
            ax.bar(i + 0.5 * w, ymax * 0.25, w * 0.92, color="none", edgecolor="#999999", ls="--")
            ax.text(i + 0.5 * w, ymax * 0.125, f"MODIS\n{why}", ha="center", va="center",
                    fontsize=9, color="#666666")
        if has_aer and np.isfinite(r["aer550_day_mean"]):
            ax.bar(i + 1.5 * w, r["aer550_day_mean"], w * 0.92, yerr=r["aer550_day_std"],
                   color="white", edgecolor=AER_COLOR, hatch="..", capsize=4, lw=1.5)
            ax.text(i + 1.5 * w, r["aer550_day_mean"] + r["aer550_day_std"] + 0.002,
                    f"{r['aer550_day_mean']:.3f}", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.site}\n{fmt_date(r.date)}" for r in comp.itertuples()])
    ax.set_ylabel("AOT / AOD at 550 nm")
    ax.set_ylim(0, ymax)
    ax.set_title("Calitoo vs MODIS-Aqua" + (" vs AERONET" if has_aer else "") + " per site/date")
    h = [Patch(color="#999999", label="Calitoo, all measurements (± std)"),
         Patch(facecolor="#999999", alpha=0.45, hatch="//", edgecolor="white",
               label=f"Calitoo, Aqua window 12:15 ± {AQUA_HALF_WIN_H} h UTC"),
         Patch(color=MODIS_COLOR, label="MODIS-Aqua MYD08_D3")]
    if has_aer and comp["aer550_day_mean"].notna().any():
        h.append(Patch(facecolor="white", edgecolor=AER_COLOR, hatch="..",
                       label=f"AERONET {aer_level}, daily mean (± std)"))
    ax.legend(handles=h, loc="upper right", frameon=False, fontsize=11)
    save(fig, "calitoo_vs_modis_bars.png")


def fig_map(boxes, cal, comp):
    fig, ax = plt.subplots(figsize=(11, 8))
    for _, b in boxes.iterrows():
        col = SITE_COLORS[b["site"]]
        ax.add_patch(Rectangle((b.cov_west, b.cov_south), b.cov_east - b.cov_west,
                               b.cov_north - b.cov_south, facecolor=col, alpha=0.10,
                               edgecolor=col, lw=2))
        ax.add_patch(Rectangle((b.data_west, b.data_south), b.data_east - b.data_west,
                               b.data_north - b.data_south, facecolor="none",
                               edgecolor=col, lw=1.5, ls="--"))
        for lo in np.arange(b.data_west, b.data_east + 0.01, GRID_RES_DEG):
            for la in np.arange(b.data_south, b.data_north + 0.01, GRID_RES_DEG):
                ax.plot(lo, la, "+", color=col, ms=7, mew=1, alpha=0.7)
    ref = {"Basel": (47.56, 7.59), "Bern": (46.95, 7.45), "Geneva": (46.20, 6.14),
           "Milan": (45.46, 9.19), "Chur": (46.85, 9.53)}
    for name, (la, lo) in ref.items():
        ax.plot(lo, la, "o", color="#bbbbbb", ms=6)
        ax.annotate(name, (lo, la), xytext=(5, 4), textcoords="offset points",
                    fontsize=10, color="#888888")
    for site, g in cal.groupby("site"):
        col, mk = SITE_COLORS[site], SITE_MARKERS[site]
        ax.scatter(g["lon"], g["lat"], color=col, marker=mk, s=130, edgecolor="black",
                   lw=1, zorder=4)
        ax.annotate(site, (g["lon"].mean(), g["lat"].mean()), xytext=(-12, 0),
                    textcoords="offset points", fontsize=12, fontweight="bold",
                    ha="right", va="center")
    lines = []
    for site in SITE_ORDER:
        r = comp[comp["site"] == site].iloc[0]
        status = ("inside data bbox" if r["inside_data_bbox"] else
                  "OUTSIDE data bbox, inside 1° cells" if r["inside_cell_coverage"]
                  else "OUTSIDE MODIS area")
        lines.append(f"{site} ({r['site_lat']:.2f}N {r['site_lon']:.2f}E): {status}")
    ax.text(0.02, 0.02, "\n".join(lines), transform=ax.transAxes, fontsize=10.5,
            va="bottom", ha="left", bbox=dict(facecolor="white", edgecolor="#bbbbbb"))
    allb = boxes
    ax.set_xlim(allb.cov_west.min() - 0.3, allb.cov_east.max() + 0.3)
    ax.set_ylim(allb.cov_south.min() - 0.3, allb.cov_north.max() + 0.3)
    ax.set_aspect(1 / np.cos(np.radians(47)))
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Calitoo sites and MODIS MYD08_D3 averaging areas")
    h = [Patch(facecolor="gray", alpha=0.2, edgecolor="gray", lw=2,
               label="area covered by the 1° cells (= user bbox)"),
         Line2D([], [], color="gray", ls="--", lw=1.5,
                label="GIOVANNI 'Data Bounding Box' (cell centres, +)")]
    h += [Line2D([], [], marker=SITE_MARKERS[s], color=SITE_COLORS[s], mec="black", ls="",
                 ms=10, label=f"Calitoo {s}") for s in SITE_ORDER]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2,
              frameon=False, fontsize=11)
    save(fig, "map_modis_boxes.png")


# ---------------------------------------------------------------------------
# REPORT (Italian, as requested)
# ---------------------------------------------------------------------------
def report(comp, modis, boxes, aer_pairs=None):
    print("\n================ METADATI MODIS ================")
    print(boxes[["site", "file", "start", "end", "data_west", "data_south", "data_east",
                 "data_north", "cov_west", "cov_south", "cov_east", "cov_north"]].to_string(index=False))
    neg = modis[modis["negative"]]
    for r in neg.itertuples():
        print(f"  ATTENZIONE: {r.site} {r.date} AOD MODIS = {r.aod550:.4f} < 0 (fisicamente dubbio, mantenuto)")
    print("\n================ CALITOO vs MODIS ================")
    cols = ["site", "date", "n_all", "aot550_all_mean", "aot550_all_std", "n_aqua_window",
            "time_aqua", "aot550_aqua_mean", "modis_aod550", "modis_flag",
            "diff_modis_minus_calitoo", "rel_diff_pct", "within_modis_EE",
            "inside_data_bbox", "inside_cell_coverage"]
    print(comp[cols].round(4).to_string(index=False))

    print("\n================ RIASSUNTO ================")
    ok = comp[np.isfinite(comp["modis_aod550"])]
    print(f"Confronto possibile per {len(ok)} giorni su {len(comp)}:")
    for r in ok.itertuples():
        ref = r.aot550_aqua_mean if r.n_aqua_window else r.aot550_all_mean
        print(f"  - {r.site} {r.date}: Calitoo {ref:.3f} ({r.calitoo_ref}, n="
              f"{r.n_aqua_window if r.n_aqua_window else r.n_all}) vs MODIS {r.modis_aod550:.3f} "
              f"-> diff {r.diff_modis_minus_calitoo:+.3f} ({r.rel_diff_pct:+.0f}%), "
              f"{'entro' if r.within_modis_EE else 'FUORI da'} ±(0.05+0.15·AOD) = ±{EE(ref):.3f}")
    for r in comp[~np.isfinite(comp["modis_aod550"])].itertuples():
        why = ("MODIS fill -9999 (nuvole / nessun retrieval)" if r.modis_flag.startswith("missing")
               else "data non presente nel file GIOVANNI scaricato")
        print(f"  - {r.site} {r.date}: nessun confronto – {why}")
    if "aer550_day_mean" in comp:
        for r in comp[comp["aer550_day_mean"].notna()].itertuples():
            print(f"  - {r.site} {r.date}: AERONET 550 media giornaliera {r.aer550_day_mean:.3f} "
                  f"± {r.aer550_day_std:.3f}; Calitoo {r.aot550_all_mean:.3f} "
                  f"(diff {r.aot550_all_mean - r.aer550_day_mean:+.3f}); finestra Aqua AERONET: "
                  + (f"{r.aer550_aqua_mean:.3f}" if np.isfinite(r.aer550_aqua_mean) else "nessun dato"))
    if aer_pairs is not None and len(aer_pairs):
        print("  Coppie AERONET–MODIS (Davos):")
        for r in aer_pairs.itertuples():
            print(f"    {r.date}: AERONET {r.aer:.3f} ({r.aer_window}) vs MODIS {r.modis:.3f} "
                  f"-> diff {r.modis - r.aer:+.3f}")
    print("Nota: le differenze (~0.01) sono molto più piccole dell'incertezza attesa di MODIS "
          "(~0.055 a AOD 0.04): l'accordo è formalmente buono ma non significativo.")


# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(exist_ok=True)
    modis, boxes = load_modis()
    cal = load_calitoo()
    comp = compare(cal, modis, boxes)
    aer_daily, aer_level = load_aeronet_daily()
    aer_pairs = []
    for site, ad in aer_daily.items():
        ad = ad.assign(site=site)
        comp = comp.merge(ad[["site", "date", "aer550_day_mean", "aer550_day_std", "n_aqua",
                              "aer550_aqua_mean", "aer550_aqua_std"]]
                          .rename(columns={"n_aqua": "aer_n_aqua"}), on=["site", "date"], how="left",
                          suffixes=("", "_new"))
        for c in ["aer550_day_mean", "aer550_day_std", "aer_n_aqua", "aer550_aqua_mean", "aer550_aqua_std"]:
            if c + "_new" in comp:
                comp[c] = comp[c].fillna(comp.pop(c + "_new"))
        mm = modis[(modis["site"] == site) & modis["aod550"].notna()].merge(ad, on="date")
        for r in mm.itertuples():
            use_aqua = np.isfinite(r.aer550_aqua_mean)
            aer_pairs.append(dict(site=site, date=r.date, modis=r.aod550,
                                  aer=r.aer550_aqua_mean if use_aqua else r.aer550_day_mean,
                                  aer_std=r.aer550_aqua_std if use_aqua else r.aer550_day_std,
                                  aer_window="aqua" if use_aqua else "day"))
    aer_pairs = pd.DataFrame(aer_pairs)
    if "aer550_day_mean" in comp:
        comp["diff_modis_minus_aeronet"] = comp["modis_aod550"] - comp["aer550_day_mean"]
        comp["diff_calitoo_minus_aeronet"] = comp["aot550_all_mean"] - comp["aer550_day_mean"]
    if len(aer_pairs):
        aer_pairs.to_csv(OUT_DIR / "aeronet_vs_modis.csv", index=False, float_format="%.5g")
    comp.to_csv(OUT_DIR / "calitoo_vs_modis.csv", index=False, float_format="%.5g")
    boxes.to_csv(OUT_DIR / "modis_bboxes.csv", index=False)
    modis.to_csv(OUT_DIR / "modis_aod550_all.csv", index=False)
    print("  saved calitoo_vs_modis.csv, modis_bboxes.csv, modis_aod550_all.csv")
    for site in SITE_ORDER:
        if site in modis["site"].values:
            fig_timeseries(site, modis, comp, aer_daily.get(site), aer_level)
    fig_scatter(comp, aer_pairs)
    fig_bars(comp, aer_level)
    fig_map(boxes, cal, comp)
    report(comp, modis, boxes, aer_pairs)


if __name__ == "__main__":
    main()
