# -*- coding: utf-8 -*-
#  시리즈 규칙: 컬러, 패널 문자 대문자·같은 크기(28pt), 방위표 3배, 0-50-100 km 축척, 그림 안 설명문 없음, 한글 없음, 결합은 시군구 코드로만.
#  Fig 1 (A) 전국 의심률 추이 (B) 성·연령별 2011·2024 · Fig 2 (A) 잔차 RR 지도 + 핫·콜드 윤곽 (B) 3창 핫·콜드 횟수 · Fig 3 모형별 RR
import os, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch, Rectangle, Polygon
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_ches import load, SHP, RS, BANDS
N = load()
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 166 * MM; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 7.5, "legend.title_fontsize": 8, "axes.linewidth": 1.0, "xtick.major.width": 1.0, "ytick.major.width": 1.0, "lines.linewidth": 1.0, "pdf.fonttype": 42})
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido"); XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
def letter(ax, ch, dx=0.0, dy=1.03, fs=28): ax.text(dx, dy, ch.upper(), transform=ax.transAxes, fontsize=fs, fontweight="bold", va="bottom", ha="left", clip_on=False)
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=1.0); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0; bx, by = x0 + 0.62 * W_, y0 + 0.04 * H_; hh = 0.012 * H_
    ax.add_patch(Rectangle((bx, by), 50000, hh, facecolor="black", edgecolor="black", linewidth=1.0)); ax.add_patch(Rectangle((bx + 50000, by), 50000, hh, facecolor="white", edgecolor="black", linewidth=1.0))
    for xx, lab in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + xx, by + hh + 0.008 * H_, lab, ha="center", va="bottom", fontsize=7)
    ax.text(bx + 108000, by + 0.5 * hh, "km", ha="left", va="center", fontsize=7)
    nx, ny = x0 + 0.90 * W_, y0 + 0.70 * H_
    ax.add_patch(Polygon([[nx - 0.036 * W_, ny], [nx + 0.036 * W_, ny], [nx, ny + 0.21 * H_]], closed=True, facecolor="black", edgecolor="none")); ax.text(nx, ny + 0.225 * H_, "N", ha="center", va="bottom", fontsize=24)
def save(fig, k, dpi):
    p = os.path.join(FIG, f"AR_Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi)); im.save(os.path.join(OUTF, f"Figure_{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw"); return im.size

# Fig 1 — 전국 의심률
fig = plt.figure(figsize=(W, 2.9))
a = fig.add_axes([0.11, 0.20, 0.34, 0.66]); ys = sorted(N["nat_pos_y"])
a.plot(ys, [N["nat_pos_y"][y] for y in ys], color="#B2182B", marker="o", ms=3, lw=1.2); a.set_ylim(0, 5); a.set_xticks([2011, 2014, 2017, 2020, 2024])
a.set_ylabel("Flagged as other chest disease, %"); a.set_xlabel("Year"); a.spines[["top", "right"]].set_visible(False); letter(a, "A", dx=-0.30, dy=1.04)
b = fig.add_axes([0.58, 0.20, 0.40, 0.66]); xs = np.arange(len(BANDS))
for y, ls in ((2011, "--"), (2024, "-")):
    for s, col, lab in (("남자", "#2166AC", "Men"), ("여자", "#B2182B", "Women")):
        b.plot(xs, [N["rate"][(y, s, bd)] for bd in BANDS], color=col, ls=ls, lw=1.1, label=f"{lab}, {y}")
b.set_xticks(xs[::2]); b.set_xticklabels([BANDS[i].replace("0-19", "≤19") for i in range(0, len(BANDS), 2)], rotation=45, ha="right", fontsize=6.8)
b.set_ylabel("Flagged, %"); b.set_xlabel("Age group, years"); b.spines[["top", "right"]].set_visible(False); b.legend(frameon=False, fontsize=6.8, loc="upper left"); letter(b, "B", dx=-0.22, dy=1.04)
s1 = save(fig, 1, 1000)

# Fig 2 — 잔차 RR 지도와 3창 핫·콜드 횟수
s6 = pd.read_csv(os.path.join(RS, "S6_spatial_RR.csv"), dtype={"sigungu_cd": str}); wm = pd.read_csv(os.path.join(RS, "S4b_window_spatialRR.csv"), dtype={"sigungu_cd": str})
gg = G.merge(s6[["sigungu_cd", "RR", "class"]].rename(columns={"sigungu_cd": "cd"}), on="cd", how="left"); assert gg.RR.notna().all() and len(gg) == 229
cnt = wm.assign(h=(wm["class"] == "hotspot").astype(int), c=(wm["class"] == "coldspot").astype(int)).groupby("sigungu_cd")[["h", "c"]].sum().reset_index()
gg = gg.merge(cnt.rename(columns={"sigungu_cd": "cd"}), on="cd", how="left"); assert gg.h.notna().all()
fig = plt.figure(figsize=(W, 4.6))
ax = fig.add_axes([0.0, 0.20, 0.49, 0.76])
BR = [0, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 9]; LB = ["<0.70", "0.70–0.79", "0.80–0.89", "0.90–0.99", "1.00–1.09", "1.10–1.24", "1.25–1.49", "≥1.50"]
PAL = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
gg.plot(ax=ax, column="RR", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(ax)
gg[gg["class"] == "coldspot"].boundary.plot(ax=ax, color="#08306B", linewidth=0.9, linestyle=(0, (2.0, 1.2))); gg[gg["class"] == "hotspot"].boundary.plot(ax=ax, color="black", linewidth=1.0); letter(ax, "A", dy=0.95)
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=0.5, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=1.0, label="Hot spot"), Patch(facecolor="none", edgecolor="#08306B", linewidth=0.9, linestyle="--", label="Cold spot")]
ax.legend(handles=h, title="Residual district rate ratio, 2011–2024", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3, fontsize=6.8)
bx = fig.add_axes([0.51, 0.20, 0.49, 0.76])
gg["k"] = np.where(gg.h > 0, gg.h, -gg.c).astype(int)
KP = {-3: "#08306B", -2: "#4393C3", -1: "#C6DBEF", 0: "#F0F0F0", 1: "#FCBBA1", 2: "#EF3B2C", 3: "#99000D"}
gg.plot(ax=bx, color=gg.k.map(KP), edgecolor="#a0a0a0", linewidth=LW); mapax(bx); letter(bx, "B", dy=0.95)
h2 = [Patch(facecolor=KP[k], edgecolor="#777777", linewidth=0.5, label=l) for k, l in ((3, "Hot spot, 3 periods"), (2, "Hot spot, 2"), (1, "Hot spot, 1"), (0, "Neither"), (-1, "Cold spot, 1"), (-2, "Cold spot, 2"), (-3, "Cold spot, 3 periods"))]
bx.legend(handles=h2, title="Periods as hot or cold spot", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3, fontsize=6.8)
assert int((gg.k == 3).sum()) == N["hot_all_windows"] and int((gg.k == -3).sum()) == N["cold_all_windows"]
s2 = save(fig, 2, 600)

# Fig 3 — 모형별 RR
LABF = {"basic_livelihood_rate": "Basic livelihood\nsecurity receipt", "tertiary_educated_share": "Tertiary\neducation", "moderate_pa_rate": "Moderate-or-vigorous\nphysical activity",
        "public_sports_facilities_per_100k": "Public sports\nfacilities", "current_smoking_rate": "Current\nsmoking", "ext__tb_history_share": "Tuberculosis\nhistory"}
ORD = list(LABF)
def bwv(v, part):
    k = f"{v}__{part}"; return N["bw"][k] if k in N["bw"] else None
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "#000000", "o"),
       ("Knorr-Held type I", lambda v: N["s43"][("KH_typeI", v)], "#1B7837", "s"),
       ("Knorr-Held type II", lambda v: N["s43"][("KH_typeII", v)], "#E08214", "P"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)], "#B2182B", "D"),
       ("Between-district component", lambda v: bwv(v, "between"), "#7f7f7f", "^"),
       ("Within-district component", lambda v: bwv(v, "within"), "#67A9CF", "v")]
fig, ax = plt.subplots(figsize=(W, 4.4)); fig.subplots_adjust(left=0.22, right=0.98, top=0.98, bottom=0.25)
off = np.linspace(-0.32, 0.32, len(MOD)); lo_all, hi_all = 9, 0
for i, v in enumerate(ORD):
    for (lab, f, col, mk), o in zip(MOD, off):
        t = f(v)
        if t is None: continue
        e, lo, hi = t[:3]; lo_all, hi_all = min(lo_all, lo), max(hi_all, hi)
        ax.plot([lo, hi], [i + o] * 2, color=col, lw=1.0); ax.plot(e, i + o, marker=mk, color=col, ms=3.6, mew=0, ls="none")
ax.axvline(1, color="#404040", lw=1.0, ls=":"); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LABF[v] for v in ORD]); ax.invert_yaxis()
xt = [0.88, 0.92, 0.96, 1.00, 1.04, 1.08]; assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 standard deviation (95% credible interval)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=c_, marker=m, lw=1.0, ms=3.6, mew=0, label=l) for l, _, c_, m in MOD], loc="upper center", bbox_to_anchor=(0.38, -0.13), ncol=3, frameon=False)
s3 = save(fig, 3, 1000)
for k, s, d in ((1, s1, 1000), (2, s2, 600), (3, s3, 1000)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/d*25.4:.0f} x {s[1]/d*25.4:.0f} mm @ {d} dpi")
