#!/usr/bin/env python3
#  region_year 원열 vs 80 패널(결과·분모·인구·원척도 공변량 *_raw). SQLite 결측 칸(보간·평균 대체 칸)은 비교에서 빠진다.
import os, sqlite3, unicodedata, numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
DB = os.path.join(os.environ.get("ST_GPT_DATASET", os.path.expanduser("~/Research/연구데이터셋_5종_분석용복사본_GPT버전")), "02_체육건강_시공간_GPT버전", "02_체육건강_시공간_GPT버전.sqlite")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "04_분석", "CHES", "sqlite_대조"); os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
P = pd.read_csv(os.path.join(ROOT, "04_분석/CHES/panel_CHES_std3.csv"), encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC)
MAP = {"cases": ("chk__질환의심_기타흉부질환", None), "population": ("population", None),
 "physicians_per_1000_raw": ("eloc__DT_1YL20981__인구천명당의료기관종사의사수＜br＞(A÷B×1000)", None),
 "sex_ratio_raw": ("eloc__DT_1YL20701__남녀성비＜br＞(A÷B×100)", None), "fiscal_independence_raw": ("eloc__DT_1YL20891__재정자주도(세입과목개편전)", None),
 "urban_population_share_raw": ("eloc__DT_1YL20421E__1인당도시지역면적현황__도시지역인구", "share"),
 "ext__screening_uptake_ches_raw": ("chk__수검률", None), "ext__tb_history_share_raw": ("chk__유질환자_폐결핵_수검자대비비율", None),
 "ext__tb_suspect_share_raw": ("chk__질환의심_폐결핵_수검자대비비율", None), "ext__clinics_per100k_raw": ("chk__요양기관_의원", "per100k"),
 "current_smoking_rate_raw": ("kchs__DT_H_SM__SR", None), "walking_practice_rate_raw": ("kchs__DT_H_EX_WALK__SR", None), "moderate_pa_rate_raw": ("kchs__DT_H_EX_PHY__SR", None),
 "public_sports_facilities_per_100k_raw": ("fac__total", "per100k"),
 "hit_and_run_rate_raw": ("eloc__DT_1YL13901__뺑소니교통사고율＜br＞(A÷B×100)", None), "fires_per_10000_raw": ("eloc__DT_1YL21081__주민만명당화재발생건수＜br＞(A÷B×10000)", None),
 "waste_recycling_rate_raw": ("eloc__DT_1YL21311__생활계폐기물재활용률＜br＞(A÷B×100)", None)}
cols = sorted({v[0] for v in MAP.values()})
R = pd.read_sql(f'select year, fbd_region, {", ".join(chr(34)+c+chr(34) for c in cols)} from region_year where year between 2011 and 2024', con); R["fbd_region"] = R.fbd_region.map(NFC)
M = P.merge(R, on=["year", "fbd_region"], how="left", suffixes=("", "__sq")); assert len(M) == len(P)
rows = []
for ours, (src, tr) in MAP.items():
    ref = M[src + "__sq" if src in P.columns else src].astype(float)
    if tr == "share": ref = ref / M.population.astype(float) * 100
    if tr == "per100k": ref = ref / M.population.astype(float) * 1e5
    v = M[ours].astype(float); ok = ref.notna()
    d = (v - ref).abs(); rel = d / ref.abs().replace(0, np.nan); bad = ok & (d > 1e-6) & ~(rel < 1e-9)
    rows.append(dict(variable=ours, sqlite_column=src, n_compared=int(ok.sum()), n_sqlite_missing=int((~ok).sum()), n_diff=int(bad.sum()), max_abs_diff=float(d[ok].max()) if ok.any() else np.nan))
A = pd.DataFrame(rows); A.to_csv(os.path.join(OUT, "A_region_year_대조.csv"), index=False, encoding="utf-8-sig"); print(A.to_string())
