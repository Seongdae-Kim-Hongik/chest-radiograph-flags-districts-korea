#  기억·손입력 금지, assert로 정합 확인. 사용: from numbers_anem import load; N = load()
import os, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널"); SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
WIN = [("W1_2011-15", 2011, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-24", 2020, 2024)]
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
BL, PA, FAC, UPT = "basic_livelihood_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "ext__screening_uptake_ches"
ROB = [BL, PA, FAC]
SHP = os.environ.get("ST_SHP", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "data", "boundary", "final.shp"))
HYP = ["ext__tb_history_share", "current_smoking_rate", "factory_land_share", "coal_plant_host", BL, "tertiary_educated_share", UPT, "ext__clinics_per100k",
       "walking_practice_rate", PA, FAC]
FORCED = ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"]
LOG1P = set()   # sets transform log1p: 패널 _raw는 변환 척도 → 표 1은 원척도(expm1)
BANDS = ["0-19"] + [f"{lo}-{lo+4}" for lo in range(20, 85, 5)] + ["85+"]

def _band(a):
    a = str(a).replace(" ", "")
    if a == "19세이하": return "0-19"
    if a == "85세이상": return "85+"
    if a.endswith("세") and "~" in a:
        lo, hi = a[:-1].split("~"); return f"{lo}-{hi}"
    return None

def national():   # 전국 성×연령 의심률(분모 N099 '계', 분자 N104 00303) — 99C2와 같은 원표
    A = pd.read_csv(os.path.join(SRC, "DT_35007_N099_national_long.csv"), encoding="utf-8-sig"); A = A[(A.grp == "계") & A.year.between(2011, 2024)]
    Bn = pd.read_csv(os.path.join(SRC, "DT_35007_N104_national_long.csv"), encoding="utf-8-sig", dtype={"grp_code": str}); Bn = Bn[(Bn.grp_code == "00303") & Bn.year.between(2011, 2024)]
    for X in (A, Bn): X["band"] = X.age.map(_band)
    ex = A[A.band.notna() & A.sex.isin(["남자", "여자"])].groupby(["year", "sex", "band"]).value.sum()
    nu = Bn[Bn.band.notna() & Bn.sex.isin(["남자", "여자"])].groupby(["year", "sex", "band"]).value.sum()
    D = pd.concat({"exam": ex, "cases": nu}, axis=1).fillna(0).reset_index(); D["rate"] = 100 * D.cases / D.exam
    return D

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_CHES_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    E = pd.read_csv(os.path.join(PAN, "CHES_Estd3.csv"))
    assert int(E.cases.sum()) == int(P.cases.sum()) and abs(E.examinees.sum() - P.offset.sum()) < 1
    N["cases_total"] = int(P.cases.sum()); N["exam_total"] = float(E.examinees.sum())
    y = E.groupby("year")[["examinees", "cases"]].sum(); N["pos_y"] = (100 * y.cases / y.examinees).to_dict(); N["exam_y"] = y.examinees.to_dict()
    NA = national(); N["nat"] = NA
    ny = NA.groupby("year")[["exam", "cases"]].sum(); N["nat_pos_y"] = (100 * ny.cases / ny.exam).to_dict()
    nsx = NA.groupby(["year", "sex"])[["exam", "cases"]].sum(); N["nat_pos_sex"] = (100 * nsx.cases / nsx.exam).to_dict()
    r = NA.set_index(["year", "sex", "band"]).rate; N["rate"] = r.to_dict()
    N["estd_ecrude"] = (float((E.E_std / E.E_crude).min()), float((E.E_std / E.E_crude).max()))
    N["rho_std_pop"] = float(E[["SIR_std", "SIR_pop"]].corr(method="spearman").iloc[0, 1])
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; e = E[(E.year >= a) & (E.year <= b)]
        sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), exam=float(e.examinees.sum()), pos=100 * q.cases.sum() / e.examinees.sum(),
                      sir_p10=sir.quantile(.1), sir_p90=sir.quantile(.9), sir_med=sir.median(),
                      cov={v: ((lambda x: (x.mean(), x.std()))(np.expm1(q[f"{v}_raw"]) if v in LOG1P else q[f"{v}_raw"])) for v in HYP + FORCED})
    N["T1"] = T1
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); s6o = s6[s6["class"] != "unobserved"]; assert len(s6o) == 229
    N["rr_min"], N["rr_max"] = s6o.RR.min(), s6o.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    gu = s6.fbd_region.str.endswith("구"); N["cold_gu"] = int(((s6["class"] == "coldspot") & gu).sum()); N["hot_gun"] = int(((s6["class"] == "hotspot") & s6.fbd_region.str.endswith("군")).sum())
    N["n_gun"] = int(s6.fbd_region.str.endswith("군").sum())
    wm = rd("S4b_window_spatialRR.csv"); N["win_hot"] = wm[wm["class"] == "hotspot"].groupby("window").size().to_dict(); N["win_cold"] = wm[wm["class"] == "coldspot"].groupby("window").size().to_dict()
    hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    cs = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*cs.values()))
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    N["ehsa"] = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict()
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en", "P_gt1"]].to_dict("index")
    assert set(m3.index) == set(HYP + FORCED)
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index")
    N["n_robust"] = int(s7.robust.sum()); assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    hb = open(os.path.join(B, "HM_best_CHES_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0])
    N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    lk = rd("S1_likelihood.csv"); lk = lk[lk.set == "REF_forced_only"].set_index("family").WAIC; N["waic_pois"], N["waic_nb"] = float(lk["poisson"]), float(lk["nbinomial"])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, r.cred) for r in wi.itertuples()}
    it = rd("S4_interaction.csv"); N["win_int"] = {r.cov: (r.IRR_ratio, r.lo, r.hi, bool(r.cred)) for r in it.itertuples()}; N["n_win_int"] = int(it.cred.sum()); N["win_int_cov"] = it[it.cred]["cov"].tolist()
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    N["retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index"); N["rubin"] = rd("S41_noise_rubin.csv").set_index("cov").to_dict("index")
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict()
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict(); N["varpart"] = rd("S42_variance_partition.csv").set_index("component").to_dict("index")
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in rd("S41_nco_detail.csv").itertuples()}
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, r.cred) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["drop_prov_min"] = int(S41[S41.analysis.str.startswith("F1_")].groupby("analysis").robust_kept.first().min())
    N["drop_year_min"] = int(S41[S41.analysis.str.startswith("F2_")].groupby("analysis").robust_kept.first().min())
    N["lag"] = {a: int(S41[S41.analysis == a].robust_kept.iloc[0]) for a in ("E1_lag1", "E2_lag2")}
    so = rd("S10_offset_sensitivity_IRR.csv"); N["epop"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in so.itertuples()}
    N["sens_main"] = {}
    for v in ["s577", "s2", "s8"]:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    N["s50_moran"] = rd("S50_resid_moran_by_spec.csv").set_index("spec").to_dict("index")
    cv = rd("S5_covid.csv"); N["covid_nint"] = int(cv[(cv.term == "var_x_post") & cv.cred].shape[0])
    return None

def national():   # 전국 성×연령 의심률(분모 N099 '계', 분자 N104 00303) — 99C2와 같은 원표
    A = pd.read_csv(os.path.join(SRC, "DT_35007_N099_national_long.csv"), encoding="utf-8-sig"); A = A[(A.grp == "계") & A.year.between(2011, 2024)]
    Bn = pd.read_csv(os.path.join(SRC, "DT_35007_N104_national_long.csv"), encoding="utf-8-sig", dtype={"grp_code": str}); Bn = Bn[(Bn.grp_code == "00303") & Bn.year.between(2011, 2024)]
    for X in (A, Bn): X["band"] = X.age.map(_band)
    ex = A[A.band.notna() & A.sex.isin(["남자", "여자"])].groupby(["year", "sex", "band"]).value.sum()
    nu = Bn[Bn.band.notna() & Bn.sex.isin(["남자", "여자"])].groupby(["year", "sex", "band"]).value.sum()
    D = pd.concat({"exam": ex, "cases": nu}, axis=1).fillna(0).reset_index(); D["rate"] = 100 * D.cases / D.exam
    return D

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_CHES_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    E = pd.read_csv(os.path.join(PAN, "CHES_Estd3.csv"))
    assert int(E.cases.sum()) == int(P.cases.sum()) and abs(E.examinees.sum() - P.offset.sum()) < 1
    N["cases_total"] = int(P.cases.sum()); N["exam_total"] = float(E.examinees.sum())
    y = E.groupby("year")[["examinees", "cases"]].sum(); N["pos_y"] = (100 * y.cases / y.examinees).to_dict(); N["exam_y"] = y.examinees.to_dict()
    NA = national(); N["nat"] = NA
    ny = NA.groupby("year")[["exam", "cases"]].sum(); N["nat_pos_y"] = (100 * ny.cases / ny.exam).to_dict()
    nsx = NA.groupby(["year", "sex"])[["exam", "cases"]].sum(); N["nat_pos_sex"] = (100 * nsx.cases / nsx.exam).to_dict()
    r = NA.set_index(["year", "sex", "band"]).rate; N["rate"] = r.to_dict()
    N["estd_ecrude"] = (float((E.E_std / E.E_crude).min()), float((E.E_std / E.E_crude).max()))
    N["rho_std_pop"] = float(E[["SIR_std", "SIR_pop"]].corr(method="spearman").iloc[0, 1])
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; e = E[(E.year >= a) & (E.year <= b)]
        sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), exam=float(e.examinees.sum()), pos=100 * q.cases.sum() / e.examinees.sum(),
                      sir_p10=sir.quantile(.1), sir_p90=sir.quantile(.9), sir_med=sir.median(),
                      cov={v: ((lambda x: (x.mean(), x.std()))(np.expm1(q[f"{v}_raw"]) if v in LOG1P else q[f"{v}_raw"])) for v in HYP + FORCED})
    N["T1"] = T1
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); s6o = s6[s6["class"] != "unobserved"]; assert len(s6o) == 229
    N["rr_min"], N["rr_max"] = s6o.RR.min(), s6o.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    gu = s6.fbd_region.str.endswith("구"); N["cold_gu"] = int(((s6["class"] == "coldspot") & gu).sum()); N["hot_gun"] = int(((s6["class"] == "hotspot") & s6.fbd_region.str.endswith("군")).sum())
    N["n_gun"] = int(s6.fbd_region.str.endswith("군").sum())
    wm = rd("S4b_window_spatialRR.csv"); N["win_hot"] = wm[wm["class"] == "hotspot"].groupby("window").size().to_dict(); N["win_cold"] = wm[wm["class"] == "coldspot"].groupby("window").size().to_dict()
    hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    cs = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*cs.values()))
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    N["ehsa"] = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict()
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en", "P_gt1"]].to_dict("index")
    assert set(m3.index) == set(HYP + FORCED)
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index")
    N["n_robust"] = int(s7.robust.sum()); assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    hb = open(os.path.join(B, "HM_best_CHES_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0])
    N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    lk = rd("S1_likelihood.csv"); lk = lk[lk.set == "REF_forced_only"].set_index("family").WAIC; N["waic_pois"], N["waic_nb"] = float(lk["poisson"]), float(lk["nbinomial"])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, r.cred) for r in wi.itertuples()}
    it = rd("S4_interaction.csv"); N["win_int"] = {r.cov: (r.IRR_ratio, r.lo, r.hi, bool(r.cred)) for r in it.itertuples()}; N["n_win_int"] = int(it.cred.sum()); N["win_int_cov"] = it[it.cred]["cov"].tolist()
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    N["retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index"); N["rubin"] = rd("S41_noise_rubin.csv").set_index("cov").to_dict("index")
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict()
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict(); N["varpart"] = rd("S42_variance_partition.csv").set_index("component").to_dict("index")
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in rd("S41_nco_detail.csv").itertuples()}
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, r.cred) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["drop_prov_min"] = int(S41[S41.analysis.str.startswith("F1_")].groupby("analysis").robust_kept.first().min())
    N["drop_year_min"] = int(S41[S41.analysis.str.startswith("F2_")].groupby("analysis").robust_kept.first().min())
    N["lag"] = {a: int(S41[S41.analysis == a].robust_kept.iloc[0]) for a in ("E1_lag1", "E2_lag2")}
    so = rd("S10_offset_sensitivity_IRR.csv"); N["epop"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in so.itertuples()}
    N["sens_main"] = {}
    for v in ["s577", "s2", "s8"]:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    N["s50_moran"] = rd("S50_resid_moran_by_spec.csv").set_index("spec").to_dict("index")
    cv = rd("S5_covid.csv"); N["covid_nint"] = int(cv[(cv.term == "var_x_post") & cv.cred].shape[0])
    PH = os.path.join(B, "results_posthoc")
    X = pd.read_csv(os.path.join(PH, "PH_extra_IRR.csv")); N["ph_extra"] = {(r.spec, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in X.itertuples()}; N["ph_waic"] = X.groupby("spec").WAIC.first().to_dict()
    D = pd.read_csv(os.path.join(PH, "PH_reading_desc.csv"), index_col=0).value.to_dict(); N["desc"] = D
    CM = pd.read_csv(os.path.join(PH, "PH_coalmining_districts.csv"), index_col=0); N["coal_mines"] = CM.to_dict("index")
    N["coal_mines_med"] = float(CM.RR.median()); N["coal_others_med"] = float(s6o[~s6o.fbd_region.isin(CM.index)].RR.median())
    N["rr_top"] = s6o.sort_values("RR", ascending=False).head(5)[["fbd_region", "RR"]].values.tolist(); N["rr_bottom"] = s6o.sort_values("RR").head(5)[["fbd_region", "RR"]].values.tolist()
    N["yeff"] = rd("S3_year_effect.csv").set_index("year").rw1_mean.to_dict()
    vif = pd.read_csv(os.path.join(B, "panel_META_CHES_std3.csv")) if os.path.exists(os.path.join(B, "panel_META_CHES_std3.csv")) else None
    N["vif_max"] = float(vif.vif_final.max()) if vif is not None else None
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame)) and v is not None})
    print("hot_by_sido", N["hot_by_sido"]); print("cold_by_sido", N["cold_by_sido"]); print("ehsa", N["ehsa"]); print("win", N["win_hot"], N["win_cold"])
    print("nat_pos_y", {k: round(v, 2) for k, v in N["nat_pos_y"].items()}); print("KH WAIC", {k: v for k, v in N["s43_waic"].items() if "KH" in k}, "main", N["waic_main"])
    print("bw", N["bw"]); print("lag", N["lag"], "drop prov/year min", N["drop_prov_min"], N["drop_year_min"]); print("desc", N["desc"]); print("rr_top", N["rr_top"]); print("rr_bottom", N["rr_bottom"])
    print("varpart", {k: round(v["share_of_linear_predictor_var"], 3) for k, v in N["varpart"].items()})
