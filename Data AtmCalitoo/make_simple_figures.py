#!/usr/bin/env python3
"""Four simple figures for the informal mid-term presentation (figures_simple/).

Uses the processed tables in output/ (QC-passed Calitoo measurements only).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
FIG = BASE / "figures_simple"

WL = [465, 540, 619]
COLORS = {465: "#1f5fbf", 540: "#2e9a3a", 619: "#d23a2a"}
MODIS_COLOR = "#8a8a8a"
DAYS = [("Zurich", "2026-09-30", "Zurich 30 Sep"), ("Zurich", "2026-10-06", "Zurich 6 Oct"),
        ("Davos", "2026-10-07", "Davos 7 Oct"), ("Lugano", "2026-10-10", "Lugano 10 Oct"),
        ("Bern", "2026-11-14", "Bern 14 Nov")]   # Bern = only the acquisition after 14:00 local

plt.rcParams.update({
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14, "xtick.labelsize": 12,
    "ytick.labelsize": 12, "legend.fontsize": 12, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e5e5e5", "axes.axisbelow": True,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})


def save(fig, name, pdf=False):
    fig.savefig(FIG / name)
    if pdf:
        fig.savefig((FIG / name).with_suffix(".pdf"))
    plt.close(fig)
    print(f"  saved {name}" + (" (+ pdf)" if pdf else ""))


def load():
    cal = pd.read_csv(OUT / "calitoo_all.csv", parse_dates=["datetime_utc"])
    cal = cal[cal["qc_ok"]].copy()
    cal["date"] = cal["datetime_utc"].dt.strftime("%Y-%m-%d")
    aer = pd.read_csv(OUT / "aeronet_davos_screened.csv", parse_dates=["datetime_utc"])
    modis = pd.read_csv(OUT / "calitoo_vs_modis.csv")
    return cal, aer, modis


def _plot_sessions(ax, g, legend_labels=False):
    """Lines only between measurements of the same session (gap < 10 min)."""
    for w in WL:
        for i, (_, s) in enumerate(g.groupby("session")):
            ax.plot(s["datetime_utc"], s[f"aot_{w}"], "-o", color=COLORS[w], ms=4, lw=1.8,
                    label=f"{w} nm" if legend_labels and i == 0 else None)


def _time_axis(ax, g, max_ticks=3.5, pad_min=0.0):
    span = (g["datetime_utc"].max() - g["datetime_utc"].min()).total_seconds() / 60
    step = next(s for s in (1, 2, 5, 10, 15, 30, 60) if span / s <= max_ticks)
    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, step)) if step < 60
                               else mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax.tick_params(axis="x", rotation=30)
    if pad_min:
        ax.set_xlim(g["datetime_utc"].min() - pd.Timedelta(minutes=pad_min),
                    g["datetime_utc"].max() + pd.Timedelta(minutes=pad_min))


# panels with a broken x axis (one sub-panel per session) and the tag shown on each sub-panel
BROKEN_AXIS = {"Zurich 6 Oct": ("morning", "afternoon"), "Lugano 10 Oct": ("", ""),
               "Bern 14 Nov": ("", "")}


def fig1(cal):
    fig = plt.figure(figsize=(3.5 * len(DAYS), 4.8))
    gs = fig.add_gridspec(1, len(DAYS), wspace=0.12)
    axes = []
    legend_ax = None
    for k, (site, date, label) in enumerate(DAYS):
        g = cal[(cal["site"] == site) & (cal["date"] == date)]
        last = k == len(DAYS) - 1
        if g["session"].nunique() == 2 and label in BROKEN_AXIS:
            # broken x axis: one narrow sub-panel per session
            sub = gs[k].subgridspec(1, 2, wspace=0.08)
            bg = fig.add_subplot(gs[k])            # carries the common title and x label
            bg.set_frame_on(False)
            bg.set_xticks([])
            bg.set_yticks([])
            bg.grid(False)
            bg.set_title(label)
            bg.set_xlabel("Time (UTC)", labelpad=39)
            pair = []
            for j, ((_, s), tag) in enumerate(zip(g.groupby("session"), BROKEN_AXIS[label])):
                ax = fig.add_subplot(sub[j], sharey=axes[0])
                _plot_sessions(ax, s, legend_labels=(last and j == 1))
                _time_axis(ax, s, max_ticks=2, pad_min=0.3)
                ax.text(0.5, 0.97, tag, transform=ax.transAxes, ha="center", va="top",
                        fontsize=11, color="#555555")
                ax.tick_params(axis="y", labelleft=False)
                pair.append(ax)
            left, right = pair
            right.spines["left"].set_visible(False)
            right.tick_params(axis="y", length=0)
            mk = dict(marker=[(-1, -1), (1, 1)], markersize=10, linestyle="none", color="k",
                      mec="k", mew=1.2, clip_on=False)
            left.plot([1], [0], transform=left.transAxes, **mk)
            right.plot([0], [0], transform=right.transAxes, **mk)
            axes.append(left)
            if last:
                legend_ax = right
            continue
        ax = fig.add_subplot(gs[k], sharey=axes[0] if axes else None)
        _plot_sessions(ax, g, legend_labels=last)
        _time_axis(ax, g)
        ax.set_title(label)
        ax.set_xlabel("Time (UTC)")
        if k:
            ax.tick_params(axis="y", labelleft=False)
        axes.append(ax)
    axes[0].set_ylabel("AOD")
    axes[0].set_ylim(0, 0.12)
    (legend_ax or axes[-1]).legend(loc="upper right")
    fig.subplots_adjust(left=0.05, right=0.99, top=0.9, bottom=0.2)
    save(fig, "1_aot_timeseries.png", pdf=True)


def fig2(cal):
    fig, ax = plt.subplots(figsize=(9.5, 5))
    sel = [cal[(cal.site == s) & (cal.date == d)]["aot_540"] for s, d, _ in DAYS]
    means = [x.mean() for x in sel]
    stds = [x.std() for x in sel]
    ax.bar(range(len(DAYS)), means, yerr=stds, color=COLORS[540], width=0.6, capsize=6)
    ax.set_xticks(range(len(DAYS)))
    ax.set_xticklabels([lab.replace(" ", "\n", 1) for _, _, lab in DAYS])
    ax.set_ylabel("Mean AOD at 540 nm")
    ax.set_ylim(0, 0.1)
    ax.set_title("Mean AOD at 540 nm (± std)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "2_aot_by_site.png", pdf=True)
    return {lab: (len(x), m, s) for (_, _, lab), x, m, s in zip(DAYS, sel, means, stds)}


def fig3(cal, aer):
    d = cal[(cal.site == "Davos") & (cal.date == "2026-10-07")]
    a = aer[(aer["datetime_utc"].dt.strftime("%Y-%m-%d") == "2026-10-07") & aer["screened_ok"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    for w in WL:
        ax.plot(a["datetime_utc"], a[f"aod_{w}"], "-", color=COLORS[w], lw=2.2, label=f"AERONET {w} nm")
    for w in WL:
        ax.plot(d["datetime_utc"], d[f"aot_{w}"], "o", color=COLORS[w], ms=6, mec="black", mew=0.6,
                label=f"Calitoo {w} nm")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("AOD")
    ax.set_ylim(0.02, 0.1)
    ax.set_title("Davos, 7 Oct: Calitoo vs AERONET")
    ax.set_xlim(d["datetime_utc"].min() - pd.Timedelta(minutes=15), d["datetime_utc"].max() + pd.Timedelta(minutes=10))
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    fig.tight_layout()
    save(fig, "3_calitoo_vs_aeronet_davos.png")


NOV14_SITES = [("Near Bern", "o", "until 14:00 CET"), ("Bern", "s", "from 14:00 CET")]
NOV14_SPLIT_UTC = "2026-11-14 13:00"    # 14:00 local (CET = UTC+1)


def _fig_nov14_vs_aeronet(cal, station, tag, ymax, title, aer_note, show_matches, fname):
    """14 Nov: Calitoo near Bern / in Bern vs one AERONET station (tables from compare_aeronet.py).
    Same layout as fig3. Filled = AERONET within ±15 min, open = no AERONET match (no value assigned).
    Cloud screen as fig7 (single-point sessions escape the pipeline QC)."""
    p, pm = OUT / f"aeronet_{tag}.csv", OUT / f"calitoo_nov14_vs_aeronet_{station.lower()}.csv"
    if not (p.exists() and pm.exists()):
        print(f"  ({station} 14 Nov tables missing: run compare_aeronet.py; {fname} skipped)")
        return
    aer = pd.read_csv(p, parse_dates=["datetime_utc"])
    a = aer[aer["screened_ok"]]
    st = aer.iloc[0]
    pairs = pd.read_csv(pm)
    pairs = pairs[pairs["window_min"] == 15]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for w in WL:
        ax.plot(a["datetime_utc"], a[f"aod_{w}"], "-", color=COLORS[w], lw=2.2,
                label=f"AERONET {station} {w} nm")
    loc_lines = [f"AERONET: {station} {st['station_lat']:.2f}N {st['station_lon']:.2f}E, "
                 f"{st['station_elev_m']:.0f} m" + aer_note.format(t0=a["datetime_utc"].min(), t1=a["datetime_utc"].max())]
    any_unmatched = False
    for site, mk, when in NOV14_SITES:
        d = cal[(cal["site"] == site) & (cal["date"] == "2026-11-14")]
        cloud = d["aot_540"] > LANGLEY_CLOUD_FACTOR * d["aot_540"].median()
        ok, bad = d[~cloud], d[cloud]
        ps = pairs[pairs["calitoo_site"] == site]
        matched = ok["datetime_utc"].dt.strftime("%H:%M:%S").isin(ps.loc[ps["n_aeronet"] > 0, "time_utc"])
        any_unmatched |= bool((~matched).any())
        for w in WL:
            ax.plot(ok.loc[matched, "datetime_utc"], ok.loc[matched, f"aot_{w}"], mk, color=COLORS[w],
                    ms=6, mec="black", mew=0.6, label=f"Calitoo {site} {w} nm")
            ax.plot(ok.loc[~matched, "datetime_utc"], ok.loc[~matched, f"aot_{w}"], mk, mfc="white",
                    mec=COLORS[w], mew=1.5, ms=6)
        for _, r in bad.iterrows():
            ax.plot(r["datetime_utc"], ymax * 0.97, "x", color="#555555", ms=9, mew=2, clip_on=False)
            ax.annotate(f"{site} {r['datetime_utc']:%H:%M} UTC: cloud\n(AOD 540 = {r['aot_540']:.2f}, "
                        "off scale), excluded", (r["datetime_utc"], ymax * 0.97), xytext=(8, 0),
                        textcoords="offset points", ha="left", va="top", fontsize=10, color="#555555")
        loc_lines.append(f"Calitoo {site} ({when}): {ok['lat'].mean():.2f}N {ok['lon'].mean():.2f}E, "
                         f"{ok['alt_m'].median():.0f} m – {ps['distance_km'].iat[0]:.0f} km from "
                         + (f"{station}; {matched.sum()}/{len(ok)} with AERONET within ±15 min"
                            if show_matches else "AERONET"))
    split = pd.Timestamp(NOV14_SPLIT_UTC, tz="UTC")
    ax.axvline(split, color="#555555", ls="--", lw=1.2)
    for txt, ha, dx in (("Near Bern", "right", -6), ("Bern", "left", 6)):
        ax.annotate(txt, (split, ymax * 0.82), xytext=(dx, 0), textcoords="offset points",
                    ha=ha, va="top", fontsize=11, color="#555555")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("AOD")
    ax.set_ylim(0, ymax)
    d = cal[(cal["date"] == "2026-11-14") & cal["site"].isin([s for s, _, _ in NOV14_SITES])]
    ax.set_xlim(d["datetime_utc"].min() - pd.Timedelta(minutes=30),
                d["datetime_utc"].max() + pd.Timedelta(minutes=20))
    ax.set_title(title, fontsize=15)
    h, _ = ax.get_legend_handles_labels()       # 3 AERONET, 3 Near Bern, 3 Bern (column-wise)
    if any_unmatched:
        blank = Line2D([], [], ls="", label=" ")
        unmatched = Line2D([], [], marker="o", mfc="white", mec="gray", mew=1.5, ls="", ms=6,
                           label="Calitoo, no AERONET within ±15 min")
        h = h[0:3] + [blank] + h[3:6] + [unmatched] + h[6:9] + [blank]
    ax.legend(handles=h, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18), fontsize=11)
    fig.text(0.01, -0.02, "\n".join(loc_lines), fontsize=10.5, color="#444444", va="top")
    fig.tight_layout()
    save(fig, fname)


def fig3b(cal):
    """14 Nov vs AERONET Davos (Level 1.0, own screening): different locations, ~185 km apart."""
    _fig_nov14_vs_aeronet(
        cal, "Davos", "davos_nov14_screened", ymax=0.14,
        title="14 Nov: Calitoo (Near Bern / Bern) vs AERONET Davos\n"
              "different locations, ~185 km apart – not a same-site validation",
        aer_note="", show_matches=False, fname="3b_calitoo_bern_vs_aeronet_davos_nov14.png")


def fig3c(cal):
    """14 Nov vs AERONET Payerne (Level 1.5): regional comparison, 37–42 km apart."""
    _fig_nov14_vs_aeronet(
        cal, "Payerne", "payerne_nov14", ymax=0.16,
        title="14 Nov: regional comparison – Calitoo (Near Bern / Bern) vs AERONET Payerne\n"
              "stations 37–42 km apart – not a same-site validation",
        aer_note=", Level 1.5 (cloud-screened by AERONET), "
                 "{t0:%H:%M}–{t1:%H:%M} UTC",
        show_matches=True, fname="3c_calitoo_bern_vs_aeronet_payerne_nov14.png")


def _fig_nov14_restyled(cal, station, tag, fname):
    """Restyled 3b/3c: same look as fig3 (Davos 7 Oct). Data, cloud screen and ±15 min matching as in
    _fig_nov14_vs_aeronet; circles = Near Bern, squares = Bern; open = no AERONET within ±15 min.
    Method and distances are documented in notes.md, not in the figure."""
    p, pm = OUT / f"aeronet_{tag}.csv", OUT / f"calitoo_nov14_vs_aeronet_{station.lower()}.csv"
    if not (p.exists() and pm.exists()):
        print(f"  ({station} 14 Nov tables missing: run compare_aeronet.py; {fname} skipped)")
        return
    a = pd.read_csv(p, parse_dates=["datetime_utc"])
    a = a[a["screened_ok"]]
    pairs = pd.read_csv(pm)
    pairs = pairs[pairs["window_min"] == 15]
    fig, ax = plt.subplots(figsize=(10, 5))
    for w in WL:
        ax.plot(a["datetime_utc"], a[f"aod_{w}"], "-", color=COLORS[w], lw=2.2)
    shown, bad_all, any_unmatched = [], [], False
    for site, mk, _ in NOV14_SITES:
        d = cal[(cal["site"] == site) & (cal["date"] == "2026-11-14")]
        cloud = d["aot_540"] > LANGLEY_CLOUD_FACTOR * d["aot_540"].median()
        ok = d[~cloud]
        bad_all.append(d[cloud])
        ps = pairs[pairs["calitoo_site"] == site]
        matched = ok["datetime_utc"].dt.strftime("%H:%M:%S").isin(ps.loc[ps["n_aeronet"] > 0, "time_utc"])
        any_unmatched |= bool((~matched).any())
        for w in WL:
            ax.plot(ok.loc[matched, "datetime_utc"], ok.loc[matched, f"aot_{w}"], mk, color=COLORS[w],
                    ms=6, mec="black", mew=0.6)
            ax.plot(ok.loc[~matched, "datetime_utc"], ok.loc[~matched, f"aot_{w}"], mk, mfc="white",
                    mec=COLORS[w], mew=1.2, ms=6)
        shown.append(ok)
    shown = pd.concat(shown)
    # axis ranges from the plotted data (AERONET during the Calitoo period + valid Calitoo points)
    t0 = shown["datetime_utc"].min() - pd.Timedelta(minutes=15)
    t1 = shown["datetime_utc"].max() + pd.Timedelta(minutes=10)
    aw = a[(a["datetime_utc"] >= t0) & (a["datetime_utc"] <= t1)]
    vals = np.concatenate([aw[[f"aod_{w}" for w in WL]].values.ravel(),
                           shown[[f"aot_{w}" for w in WL]].values.ravel()])
    lo = max(0.0, np.floor((np.nanmin(vals) - 0.005) * 100) / 100)
    has_cloud = any(len(b) for b in bad_all)
    hi = np.ceil((np.nanmax(vals) + (0.012 if has_cloud else 0.005)) * 100) / 100
    for b in bad_all:                       # excluded cloud point: off scale, marked near the top
        for _, r in b.iterrows():
            y = hi - 0.004
            ax.plot(r["datetime_utc"], y, "x", color="#555555", ms=8, mew=1.8)
            ax.annotate(f"cloud, excluded (AOD 540 = {r['aot_540']:.2f})", (r["datetime_utc"], y),
                        xytext=(7, 0), textcoords="offset points", ha="left", va="center",
                        fontsize=10, color="#555555")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("AOD")
    ax.set_ylim(lo, hi)
    ax.set_xlim(t0, t1)
    ax.set_title(f"Near Bern / Bern, 14 Nov: Calitoo vs AERONET {station}")
    h = [Line2D([], [], color=COLORS[w], lw=2.2, label=f"AERONET {station} {w} nm") for w in WL]
    h += [Line2D([], [], color=COLORS[w], marker="o", ls="", ms=6, mec="black", mew=0.6,
                 label=f"Calitoo {w} nm") for w in WL]
    h += [Line2D([], [], color="#888888", marker="o", ls="", ms=6, mec="black", mew=0.6,
                 label="Calitoo Near Bern"),
          Line2D([], [], color="#888888", marker="s", ls="", ms=6, mec="black", mew=0.6,
                 label="Calitoo Bern")]
    if any_unmatched:
        h.append(Line2D([], [], marker="o", ls="", ms=6, mfc="white", mec="#888888", mew=1.2,
                        label="no AERONET within ±15 min"))
    ax.legend(handles=h, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    fig.tight_layout()
    save(fig, fname)


def fig4(modis):
    m = modis.set_index(["site", "date"])
    # (site, date, tick label, text when MODIS has no value)
    # "Bern area — 14 Nov" = only the measurements in the assumed Aqua window (10:45–13:45 UTC); they
    # are all from the Near Bern spot. The afternoon measurements in Bern (13:47–14:49 UTC) are
    # outside the window and are NOT pooled in (see notes.md).
    groups = [("Zurich", "2026-10-06", "Zurich\n6 Oct", ""),
              ("Davos", "2026-10-07", "Davos\n7 Oct", "MODIS:\nno data\n(clouds)"),
              ("Lugano", "2026-10-10", "Lugano\n10 Oct", ""),
              ("Near Bern", "2026-11-14", "Bern area — 14 Nov", "MODIS:\nno data")]
    AQUA_ONLY = {("Near Bern", "2026-11-14")}   # never fall back to the day mean for these
    fig, ax = plt.subplots(figsize=(11, 5))
    w = 0.36
    for i, (s, d, _, nodata) in enumerate(groups):
        r = m.loc[(s, d)]
        if (s, d) in AQUA_ONLY and not r["n_aqua_window"] > 0:
            raise ValueError(f"{s} {d}: no Calitoo measurement in the Aqua window")
        cal = r["aot550_aqua_mean"] if r["n_aqua_window"] > 0 else r["aot550_all_mean"]
        ax.bar(i - w / 2, cal, w, color=COLORS[540], label="Calitoo" if i == 0 else None)
        if np.isfinite(r["modis_aod550"]):
            ax.bar(i + w / 2, r["modis_aod550"], w, color=MODIS_COLOR, label="MODIS-Aqua" if i == 0 else None)
        else:
            ax.text(i + w / 2, 0.004, nodata, ha="center", va="bottom", fontsize=11, color="#555555")
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[2] for g in groups])
    ax.set_ylabel("AOD at 550 nm")
    ax.set_ylim(0, 0.1)
    ax.set_title("Calitoo vs MODIS (550 nm)")
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "4_calitoo_vs_modis.png")


CAL_UNC = 0.03


def fig5():
    m = pd.read_csv(OUT / "calitoo_vs_aeronet.csv")
    m = m[m["window_min"] == 15]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhspan(-CAL_UNC, CAL_UNC, color="#e6e6e6", lw=0, zorder=0, label="±0.03 (typical Calitoo uncertainty)")
    ax.axhline(0, color="black", lw=1.2)
    for w in WL:
        d = m[f"diff_{w}"]
        rel = 100 * (d / m[f"aer_aod_{w}"]).mean()
        ax.errorbar(w, d.mean(), yerr=d.std(), fmt="o", color=COLORS[w], ms=10, capsize=6, lw=2)
        ax.annotate(f"{rel:+.0f} %".replace("-0 %", "0 %").replace("+0 %", "0 %"), (w, d.mean()),
                    xytext=(14, 0), textcoords="offset points", va="center", fontsize=13, color=COLORS[w])
    ax.set_xticks(WL)
    ax.set_xticklabels([f"{w} nm" for w in WL])
    ax.set_xlim(440, 650)
    ax.set_ylim(-0.04, 0.04)
    ax.set_xlabel("Wavelength")
    ax.set_ylabel("Calitoo − AERONET (AOD)")
    ax.set_title("Davos, 7 Oct: mean difference Calitoo − AERONET")
    ax.legend(loc="upper right")
    fig.tight_layout()
    save(fig, "5_bias_vs_wavelength.png")
    return {w: (m[f"diff_{w}"].mean(), m[f"diff_{w}"].std(),
                100 * (m[f"diff_{w}"] / m[f"aer_aod_{w}"]).mean()) for w in WL}


def kasten_young(elev_deg):
    return 1.0 / (np.sin(np.radians(elev_deg)) + 0.50572 * (elev_deg + 6.07995) ** -1.6364)


def fig6(cal):
    d = cal[(cal["site"] == "Davos") & (cal["date"] == "2026-10-07")].copy()
    d["m"] = kasten_young(d["sun_elev_deg"])
    doy = d["datetime_utc"].dt.dayofyear.iat[0]
    r_au = 1 - 0.01672 * np.cos(2 * np.pi * (doy - 4) / 365.256)   # Earth–Sun distance (AU)
    res = {}
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_axes([0.09, 0.3, 0.62, 0.6])
    mx = np.linspace(0, 2.7, 50)
    ax.axvspan(d["m"].min(), d["m"].max(), color="#e6e6e6", lw=0, zorder=0, label="m range of the data")
    for w in WL:
        y = np.log(d[f"raw_{w}"])
        p, cov = np.polyfit(d["m"], y, 1, cov=True)
        sb = np.sqrt(cov[1, 1])
        v0 = np.exp(p[1]) * r_au ** 2          # normalised to 1 AU
        res[w] = dict(v0=v0, v0_lo=v0 * np.exp(-sb), v0_hi=v0 * np.exp(sb), tau=-p[0],
                      tau_err=np.sqrt(cov[0, 0]), lnv0=p[1], lnv0_err=sb)
        ax.plot(d["m"], y, "o", color=COLORS[w], ms=6, label=f"{w} nm")
        ax.plot(mx, np.polyval(p, mx), "--", color=COLORS[w], lw=1.5)
    ax.set_xlim(0, 2.7)
    ax.set_xlabel("Air mass m (Kasten–Young)")
    ax.set_ylabel("ln(raw signal)")
    ax.set_title("Davos, 7 Oct: Langley attempt")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    lines = [f"{w} nm:  V0 = {r['v0']:.0f} ± {r['v0'] * r['lnv0_err']:.0f}  (± {100 * r['lnv0_err']:.0f} %, 1σ of the fit)"
             for w, r in res.items()]
    lines.append("CN0 instrument: to be asked (not in the data files)")
    lines.append(f"V0 normalised to 1 AU (Earth–Sun distance {r_au:.4f} AU, correction {100 * (r_au ** 2 - 1):+.2f} %)")
    fig.text(0.09, 0.03, "\n".join(lines), fontsize=11, color="#444444", va="bottom")
    save(fig, "6_langley_attempt_davos.png")
    return res, d["m"].min(), d["m"].max(), r_au


LANGLEY_CLOUD_FACTOR = 2.0   # Langley screen: drop points with AOD 540 > 2 × median of the acquisition


def fig7(cal_all):
    """Near Bern, 14 Nov: same Langley method as fig6 (ln raw vs Kasten–Young m, linear fit),
    with ln(raw) normalised to 1 AU. Pipeline QC + an extra cloud screen, because an isolated
    single-point session escapes the pipeline's session-outlier test."""
    d = cal_all[(cal_all["site"] == "Near Bern") & (cal_all["date"] == "2026-11-14")].copy()
    d["m"] = kasten_young(d["sun_elev_deg"])
    doy = d["datetime_utc"].dt.dayofyear.iat[0]
    r_au = 1 - 0.01672 * np.cos(2 * np.pi * (doy - 4) / 365.256)   # Earth–Sun distance (AU)
    cloud = d["aot_540"] > LANGLEY_CLOUD_FACTOR * d["aot_540"].median()
    use = d["qc_ok"] & ~cloud
    f = d[use]
    m_lo, m_hi = f["m"].min(), f["m"].max()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axvspan(m_lo, m_hi, color="#e6e6e6", lw=0, zorder=0,
               label=f"fit range m = {m_lo:.2f}–{m_hi:.2f}")
    res = {}
    for w in WL:
        y = np.log(d[f"raw_{w}"] * r_au ** 2)       # signal normalised to 1 AU
        p, cov = np.polyfit(f["m"], y[use], 1, cov=True)
        res[w] = dict(lnv0=p[1], lnv0_err=np.sqrt(cov[1, 1]), v0=np.exp(p[1]),
                      tau=-p[0], tau_err=np.sqrt(cov[0, 0]))
        ax.plot(f["m"], y[use], "o", color=COLORS[w], ms=6, label=f"{w} nm")
        ax.plot(d.loc[~use, "m"], y[~use], "x", color=COLORS[w], ms=9, mew=2)
        ax.plot([0, m_lo], np.polyval(p, [0, m_lo]), "--", color=COLORS[w], lw=1.3)
        ax.plot([m_lo, m_hi], np.polyval(p, [m_lo, m_hi]), "-", color=COLORS[w], lw=1.8)
    excl = d[~use]
    if len(excl):
        ax.plot([], [], "x", color="#555555", ms=9, mew=2,
                label="excluded: " + ", ".join(excl["datetime_utc"].dt.strftime("%H:%M UTC")))
    ax.set_xlim(0, m_hi + 0.3)
    ax.set_xlabel("Air mass m (Kasten–Young)")
    ax.set_ylabel("ln(raw signal × r²)   [r = Earth–Sun distance, AU]")
    ax.set_title("Near Bern, 14 Nov — Preliminary Langley fit")
    ax.legend(loc="lower left")
    fig.tight_layout()
    save(fig, "7_langley_near_bern_nov14.png", pdf=True)
    return res, d, use, cloud, r_au


def main():
    FIG.mkdir(exist_ok=True)
    cal, aer, modis = load()
    cal_all = pd.read_csv(OUT / "calitoo_all.csv", parse_dates=["datetime_utc"])
    cal_all["date"] = cal_all["datetime_utc"].dt.strftime("%Y-%m-%d")
    fig1(cal)
    bars = fig2(cal)
    fig3(cal, aer)
    fig3b(cal)
    fig3c(cal)
    _fig_nov14_restyled(cal, "Davos", "davos_nov14_screened",
                        "3b_calitoo_bern_vs_aeronet_davos_nov14_restyled.png")
    _fig_nov14_restyled(cal, "Payerne", "payerne_nov14",
                        "3c_calitoo_bern_vs_aeronet_payerne_nov14_restyled.png")
    fig4(modis)
    b = fig5()
    lg, m0, m1, r_au = fig6(cal)
    lb, nb, use, cloud, r_au_nb = fig7(cal_all)
    print("\nMean AOD 540 nm (QC ok):")
    for lab, (n, mu, sd) in bars.items():
        print(f"  {lab:14s} n={n:2d}  {mu:.4f} ± {sd:.4f}")
    print(f"\nLangley Near Bern 14/11: {len(nb)} measurements, {use.sum()} in the fit, "
          f"m = {nb.loc[use, 'm'].min():.2f}–{nb.loc[use, 'm'].max():.2f}, r = {r_au_nb:.4f} AU")
    for _, r in nb[~use].iterrows():
        print(f"  excluded {r['datetime_utc']:%H:%M:%S} UTC: qc_ok={r['qc_ok']}, cloud screen={cloud[_]}, "
              f"raw={r['raw_465']:.0f}/{r['raw_540']:.0f}/{r['raw_619']:.0f}, AOD540={r['aot_540']:.3f}, "
              f"α={r['angstrom']:.2f}, R²={r['fit_r2']:.2f}")
    for w, r in lb.items():
        print(f"  {w} nm: ln V0 = {r['lnv0']:.3f} ± {r['lnv0_err']:.3f} → V0 = {r['v0']:.0f} "
              f"(±{100 * r['lnv0_err']:.0f} %), slope τ_tot = {r['tau']:.3f} ± {r['tau_err']:.3f}")
    print("\nBias Calitoo − AERONET (Davos 7/10):")
    for w, (mean, sd, rel) in b.items():
        print(f"  {w} nm: {mean:+.4f} ± {sd:.4f} ({rel:+.0f} %)")
    print(f"\nLangley Davos 7/10: m = {m0:.2f}–{m1:.2f}, Earth–Sun distance {r_au:.4f} AU")
    for w, r in lg.items():
        print(f"  {w} nm: ln V0 = {r['lnv0']:.3f} ± {r['lnv0_err']:.3f} → V0 = {r['v0']:.0f} "
              f"(±{100 * r['lnv0_err']:.0f} %), slope τ_tot = {r['tau']:.3f} ± {r['tau_err']:.3f}")


if __name__ == "__main__":
    main()
