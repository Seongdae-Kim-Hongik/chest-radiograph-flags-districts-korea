#!/usr/bin/env python3
#  기준: 분석용 복사본 GPT버전 SQLite region_year(mode=ro) + 같은 검진 원표 장형 패널(02_패널/NHIS검진_시군구_연도_long.csv).
#  검진 비율 3개는 원표에서 직접 계산한다 — 기준 SQLite chk__ 비율이 세종 2012-24 빈칸이라(99C2와 같은 세종 시도 행 결합 규칙).
#   screening_uptake_ches  = 일반검진 1차 수검인원 ÷ 대상인원 × 100 (DT_35007_N001 2011-17·N001_1 2018-24 합계; SQLite chk__수검률과 같은 정의) — 검진 선택
#   tb_history_share       = 일반검진 유질환자 '폐결핵' ÷ 판정 수검자(N098 계) × 100 (DT_35007_N105) — 결핵 과거력(문진 기반, 판독과 독립)
#   tb_suspect_share       = 일반검진 질환의심 '일반_폐결핵' ÷ 판정 수검자 × 100 (DT_35007_N103) — 같은 판독 체계의 다른 판정(민감도 전용, 판독 관행 대리)
#   clinics_per100k        = 요양기관 의원 수(SQLite chk__요양기관_의원) ÷ 인구(SQLite population) × 10만 — 의원급 검진·판독 비중 대리
#  산출: 02_패널/EXT_canonical_pool_CHES_261116.csv
import os, sqlite3, importlib.util, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널"); AN = os.path.join(ROOT, "04_분석")
DB = os.path.join(os.environ.get("ST_GPT_DATASET", os.path.expanduser("~/Research/연구데이터셋_5종_분석용복사본_GPT버전")), "02_체육건강_시공간_GPT버전", "02_체육건강_시공간_GPT버전.sqlite")
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m50 = _load("m50", "50_build_master_panel.py")
YEARS = list(range(2011, 2025))
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
RY = pd.read_sql('select year, key, fbd_region, population, "chk__요양기관_의원" as clin, "chk__수검률" as sq_upt, "chk__유질환자_폐결핵_수검자대비비율" as sq_tbh, "chk__질환의심_폐결핵_수검자대비비율" as sq_tbs from region_year where year between 2011 and 2024', con)
RY["fbd_region"] = RY.fbd_region.map(NFC); RY["key"] = RY.key.map(NFC); assert len(RY) == 3206
PKEYS = set(RY.key)
L = pd.read_csv(os.path.join(PAN, "NHIS검진_시군구_연도_long.csv"), usecols=["year", "sido", "sigungu", "level", "sex", "category", "measure", "value", "tbl_id"], engine="pyarrow")
SEL = {("DT_35007_N001_1", "1차검진", "대상인원"): "elig", ("DT_35007_N001_1", "1차검진", "수검인원"): "upt", ("DT_35007_N001", "1차검진", "대상인원"): "elig", ("DT_35007_N001", "1차검진", "수검인원"): "upt",
       ("DT_35007_N098", "계", None): "exam", ("DT_35007_N105", "폐결핵", None): "tbh", ("DT_35007_N103", "일반_폐결핵", None): "tbs"}
L = L[L.year.isin(YEARS) & (L.sex == "합계") & ((L.level == "시군구") | ((L.level == "시도") & (L.sido == "세종")))].copy()
L["v"] = [SEL.get((t, c, m if t.startswith("DT_35007_N001") else None)) for t, c, m in zip(L.tbl_id, L.category, L.measure)]
L = L[L.v.notna()]
pairs = L[["sido", "sigungu"]].drop_duplicates(); mp = {(a, b): m50.map_region(a, b, PKEYS) for a, b in zip(pairs.sido, pairs.sigungu)}
L["key"] = [mp[(a, b)]["key"] for a, b in zip(L.sido, L.sigungu)]; L["role"] = [mp[(a, b)]["role"] for a, b in zip(L.sido, L.sigungu)]
sj = (L.level == "시도") & (L.sido == "세종"); L.loc[sj, "key"] = "세종시|세종시"; L.loc[sj, "role"] = "primary"; L = L[~((L.level == "시군구") & (L.sido == "세종"))]
L = L[L.key.notna()]; L["key"] = L.key.map(NFC)
hp = L[L.role == "primary"].groupby(["key", "year", "v"]).size().index
L = L[~((L.role == "sub") & L.set_index(["key", "year", "v"]).index.isin(hp))]
W = L.pivot_table(index=["year", "key"], columns="v", values="value", aggfunc="sum").reset_index()
P = RY.merge(W, on=["year", "key"], how="left", validate="one_to_one")
P["screening_uptake_ches"] = P.upt / P.elig * 100
P["tb_history_share"] = P.tbh / P.exam * 100
P["tb_suspect_share"] = P.tbs / P.exam * 100
P["clinics_per100k"] = P.clin / P.population * 1e5
for a, b in [("screening_uptake_ches", "sq_upt"), ("tb_history_share", "sq_tbh"), ("tb_suspect_share", "sq_tbs")]:
    both = P[a].notna() & P[b].notna(); d = (P[a] - P[b]).abs()[both]
    print(f"[99c-ches] {a} vs SQLite {b}: 겹침 {int(both.sum())}, 최대차 {d.max():.4f}, 차>0.01 {int((d > 0.01).sum())}; 원표 결측 {int(P[a].isna().sum())} {P.loc[P[a].isna(), ['fbd_region', 'year']].values.tolist()[:8]}; SQLite만 결측 {int((P[a].notna() & P[b].isna()).sum())}")
A = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_ANEM_261111.csv"), encoding="utf-8-sig")[["year", "fbd_region", "basic_livelihood_rate", "tertiary_educated_share", "im_specialists_per100k"]]
C = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_CLRD_261109.csv"), encoding="utf-8-sig")[["year", "fbd_region", "factory_land_share", "coal_host", "detached_hh_share"]]
for X in (A, C): X["fbd_region"] = X.fbd_region.map(NFC)
out = P[["year", "fbd_region", "screening_uptake_ches", "tb_history_share", "tb_suspect_share", "clinics_per100k"]].merge(A, on=["year", "fbd_region"], how="left", validate="one_to_one").merge(C, on=["year", "fbd_region"], how="left", validate="one_to_one")
out = out.sort_values(["fbd_region", "year"]).reset_index(drop=True)
for c in ["screening_uptake_ches", "tb_history_share", "tb_suspect_share", "clinics_per100k"]:
    n0 = int(out[c].isna().sum())
    out[c] = out.groupby("fbd_region")[c].transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
    nb = out.groupby("fbd_region")[c].transform(lambda s: (s.shift(1) + s.shift(-1)) / 2)
    print(f"[99c-ches] {c}: 결측 {n0}칸 지역 안 보간, 남은 결측 {int(out[c].isna().sum())}, 이웃 평균 20% 미만 {int((out[c] < 0.2 * nb).sum())}, 5배 초과 {int((out[c] > 5 * nb).sum())}, 0값 {int((out[c] == 0).sum())}")
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any()
assert out.notna().all().all(), out.isna().sum()
# 수급률 양쪽 규칙 재확인(ANEM 풀이 이미 정정본이어야 함)
r = out.fbd_region.map(out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean())
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * r) | (out.basic_livelihood_rate > 5 * r)); print("[99c-ches] 수급률 규칙 위반 칸(0이어야 함):", int(bad.sum())); assert bad.sum() == 0
fp = os.path.join(PAN, "EXT_canonical_pool_CHES_261116.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
print(f"[99c-ches] 저장 {fp} {out.shape}"); print(out.describe().T[["min", "50%", "max"]].round(3))
print("[99c-ches] 세종:", out[out.fbd_region == NFC("세종시세종시")][["year", "screening_uptake_ches", "tb_history_share", "tb_suspect_share", "clinics_per100k"]].round(3).values.tolist()[:3])
