import os, glob, re
import pandas as pd
from build_ar_ches import TX, put_table, OUT, N, to_pdf, TITLE, LAB, GROUPS
import content_ches as C
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "..")); RS = os.path.join(B, "results_std3"); PH = os.path.join(B, "results_posthoc")
ROB = [("basic_livelihood_rate", "Basic livelihood"), ("moderate_pa_rate", "Physical activity"), ("public_sports_facilities_per_100k", "Sports facilities"), ("tertiary_educated_share", "Tertiary education")]
f3 = lambda r: f"{r[0]:.3f} ({r[1]:.3f}–{r[2]:.3f})"
def row(d, c):
    x = d[d["cov"].astype(str) == c]
    return f3([float(x.IRR.iloc[0]), float(x.lo.iloc[0]), float(x.hi.iloc[0])]) if len(x) else "–"
EN = C.EN
ROM = {"강원도태백시": "Taebaek", "강원도삼척시": "Samcheok", "강원도정선군": "Jeongseon", "강원도영월군": "Yeongwol", "경상북도문경시": "Mungyeong", "충청남도보령시": "Boryeong", "전라남도화순군": "Hwasun",
       "경상남도남해군": "Namhae", "대전시동구": "Dong-gu, Daejeon", "충청북도옥천군": "Okcheon", "경상북도영천시": "Yeongcheon", "강원도홍천군": "Hongcheon", "전라남도강진군": "Gangjin",
       "전라남도무안군": "Muan", "전라남도목포시": "Mokpo", "강원도고성군": "Goseong, Gangwon"}
def s1():
    rows = [["Outcome", "Examinees flagged as suspected other chest disease on the chest radiograph of the general health examination (KOSIS DT_35007_N103, category 'other chest disease'), separate from suspected pulmonary tuberculosis"],
            ["Denominator", "Examinees with a recorded judgement (DT_35007_N098 total), by sex"],
            ["Districts", f"{N['n_districts']} districts harmonised to 2024 boundaries; general districts within cities aggregated; Sejong linked from the province-level rows by sex (single-tier)"],
            ["Period", f"2011–2024, {N['n_rows']:,} district-years, no missing outcome; district sums equal national totals in every year"],
            ["National rates", "Flagged and examinees by sex and 15 age groups (19 years or younger, 5-year groups 20–24 to 80–84, 85 years or older), DT_35007_N104 and N099, 2011–2024"],
            ["Examinee age structure", "Resident population by sex and 5-year age group × national uptake by sex and age, rescaled to observed examinees of each sex (scaling factor 0.70–1.75)"],
            ["Expected numbers", "Indirect standardisation; expected numbers rescaled so that their annual sum equals the observed national number flagged"],
            ["Sensitivity denominators", "Population-based expected numbers (resident population × national flagged per resident, by sex and age); age-only standardisation"],
            ["Analytic copy", "District statistics were read from a fixed analytic copy of the national statistics (read-only); 3,186 overlapping outcome cells agreed exactly with the source tables, and 20 cells missing in the copy (Sejong 2012–2024 and seven city-years) were taken from the source tables"]]
    return ("Supplementary Table S1. Outcome, Denominator and Standardisation", ["Item", "Description"], rows, "KOSIS, Korean Statistical Information Service.")
DEF = {"ext__tb_history_share": ("Examinees reporting current or past treatment for pulmonary tuberculosis in the screening questionnaire, % of examinees", "NHIS screening statistics (DT_35007_N105)"),
       "current_smoking_rate": ("Current smokers, age-standardised, %", "Community Health Survey"),
       "factory_land_share": ("Land registered as factory sites in the cadastre, % of district area", "Cadastral statistics, Ministry of Land, Infrastructure and Transport via KOSIS"),
       "coal_plant_host": ("District hosting at least one coal-fired steam generator in operation in 2011\u20132024 (0/1)", "Korea Power Exchange generator capacity via KOSIS (TX_38803_A004)"),
       "basic_livelihood_rate": ("Basic livelihood security recipients per 100 residents; 2021–2023 values below 20% or above 5 times the 2020/2024 mean set to missing and interpolated", "Ministry of Health and Welfare via KOSIS"),
       "tertiary_educated_share": ("Adults with tertiary education, % (census, interpolated)", "Population and Housing Census"),
       "ext__screening_uptake_ches": ("General health examination examinees / eligible people, %", "NHIS screening statistics (DT_35007_N001)"),
       "ext__clinics_per100k": ("Clinics per 100,000 residents", "NHIS care institution statistics"),
       "walking_practice_rate": ("Adults walking ≥30 min on ≥5 days a week, age-standardised, %", "Community Health Survey"),
       "moderate_pa_rate": ("Adults meeting moderate-or-vigorous activity criteria, age-standardised, %", "Community Health Survey"),
       "public_sports_facilities_per_100k": ("Public sports facilities per 100,000 residents", "National public sports facility register"),
       "urban_population_share": ("Residents in urban zones, % of population", "Ministry of Land via KOSIS"), "physicians_per_1000": ("Physicians working in medical institutions per 1,000 residents", "KOSIS e‑local indicators"),
       "sex_ratio": ("Men per 100 women", "Resident registration"), "fiscal_independence": ("Fiscal autonomy ratio of the local government, %", "Ministry of the Interior and Safety via KOSIS"),
       "pop80_share": ("Residents aged 80 years or older, % of population", "Resident registration")}
def s2():
    rows = []
    for g, vs in GROUPS:
        for v in vs: rows.append([LAB[v][0], g, DEF[v][0], DEF[v][1], {"ext__clinics_per100k": "±"}.get(v, "+" if v in ("ext__tb_history_share", "current_smoking_rate", "factory_land_share", "coal_plant_host", "basic_livelihood_rate") else ("−" if g != "Forced controls" else "–"))])
    for a, b, c in (("Suspected tuberculosis share", "Sensitivity only", "Examinees flagged as suspected pulmonary tuberculosis, % (same radiograph reading)"), ("Detached-house households", "Sensitivity only", "Households in detached houses, %"),
                    ("Internal medicine specialists", "Sensitivity only", "Internal medicine specialists per 100,000"), ("Hit-and-run accidents", "Negative control", "Hit-and-run accidents per 100 traffic accidents"),
                    ("Fires", "Negative control", "Fires per 10,000 residents"), ("Household waste recycling", "Negative control", "Recycled share of household waste, %")):
        rows.append([a, b, c, "KOSIS / NHIS", "none" if b == "Negative control" else "–"])
    return ("Supplementary Table S2. District Characteristics: Definitions, Sources and Expected Direction", ["Characteristic", "Group", "Definition", "Source", "Expected"], rows,
            "Survey indicators were filled within districts for years without data by linear interpolation; all characteristics were standardised to 1 SD of district-years. KOSIS, Korean Statistical Information Service; NHIS, National Health Insurance Service.")
def s3():
    V = pd.read_csv(os.path.join(B, "panel_META_CHES_std3.csv"))
    rows = [[r.variable, f"{r.coverage:.3f}", str(int(r.n_imputed_interp)), str(int(r.n_imputed_sgg_mean)), str(int(r.n_imputed_year_mean)), f"{r.vif_final:.2f}" if pd.notna(r.vif_final) else "–"] for r in V.itertuples()]
    return ("Supplementary Table S3. Covariate Coverage, Filled Values and Variance Inflation Factors", ["Variable", "Coverage", "Interpolated", "District mean", "Year mean", "VIF"], rows,
            "Coverage is the share of district-years observed before filling. VIF, variance inflation factor in the principal model.")
def s4():
    m = pd.read_csv(os.path.join(RS, "S6_moran_year.csv"))
    rows = [[str(int(r.year)), f"{r.moran_I:.3f}", f"{r.p_perm:.3f}", f"{r.crude_rate_per100k:,.0f}"] for r in m.itertuples()]
    rows += [["__H__", "Hot and cold spots by province (whole period)"]]
    for k in sorted(set(N["hot_by_sido"]) | set(N["cold_by_sido"]), key=lambda x: -(N["hot_by_sido"].get(x, 0) + N["cold_by_sido"].get(x, 0))):
        rows.append([EN.get(k, k), f"hot {N['hot_by_sido'].get(k, 0)}", f"cold {N['cold_by_sido'].get(k, 0)}", ""])
    rows += [["__H__", "Highest and lowest residual rate ratios"]] + [[ROM.get(a, a), f"{b:.2f}", "highest", ""] for a, b in N["rr_top"]] + [[ROM.get(a, a), f"{b:.2f}", "lowest", ""] for a, b in N["rr_bottom"]]
    return ("Supplementary Table S4. Spatial Autocorrelation by Year and Distribution of Hot and Cold Spots", ["Year or province", "Moran's I or count", "Permutation P", "Flagged per 100,000"], rows,
            f"Moran's I of log standardised ratios with 999 permutations (593-edge contact graph). Kendall's W of district ranks 2011–2024 {N['kendall_W']:.2f}; provinces accounted for {100*N['desc']['share_var_between_sido']:.0f}% of district variance in log standardised ratios.")
def s5():
    W = pd.read_csv(os.path.join(RS, "S4_window_IRR.csv")); rows = []
    for g, vs in GROUPS:
        for v in vs: rows.append([LAB[v][0]] + [row(W[W.window == w], v) for w in ("W1_2011-15", "W2_2016-19", "W3_2020-24")])
    return ("Supplementary Table S5. Principal Model by Calendar Period: Rate Ratios per 1 SD (95% CrI)", ["Characteristic", "2011–2015", "2016–2019", "2020–2024"], rows, "")
def s6():
    rows = [["__H__", "Alternative specifications summarised in the text (45)"]]
    for f in sorted(glob.glob(os.path.join(RS, "S41_part_*.csv"))):
        a = os.path.basename(f)[9:-4]
        if a.startswith(("H1_nco", "bw_", "G2_noise")): continue
        d = pd.read_csv(f); note = str(d.note.iloc[0]) if "note" in d and pd.notna(d.note.iloc[0]) else a
        lab = a.replace("F1_drop_sido_", "Without province ").replace("F2_drop_year_", "Without year ") if a.startswith(("F1", "F2")) else note
        rows.append([lab] + [row(d, k) for k, _ in ROB])
    rows.append(["__H__", "Space\u2013time interactions, district effects, other denominators and decomposition"])
    for lab, f in (("Knorr-Held type I", "S9_typeI_IRR.csv"), ("Knorr-Held type II", "S43_part_KH_typeII.csv"), ("Knorr-Held type III", "S43_part_KH_typeIII.csv"), ("Knorr-Held type IV", "S43_part_KH_typeIV.csv"),
                   ("ICAR district effect", "S43_part_icar_besag.csv"), ("Independent district effect only", "S43_part_iid_only.csv"), ("No district effect", "S43_part_no_spatial.csv"), ("k-nearest neighbours (k = 5)", "S43_part_knn5.csv")):
        d = pd.read_csv(os.path.join(RS, f)); rows.append([lab] + [row(d, k) for k, _ in ROB])
    for v, lab in (("s577", "Queen contiguity graph (577 pairs)"), ("s2", "Without the aged-80-or-older control"), ("s8", "Age-only standardisation")):
        d = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")); rows.append([lab] + [row(d, k) for k, _ in ROB])
    d = pd.read_csv(os.path.join(RS, "S10_offset_sensitivity_IRR.csv")); rows.append(["Population-based expected numbers"] + [row(d, k) for k, _ in ROB])
    rows.append(["Between-district component"] + [f3(N["bw"][k + "__between"]) if k + "__between" in N["bw"] else row(pd.DataFrame({"cov": [], "IRR": [], "lo": [], "hi": []}), k) for k, _ in ROB])
    rows.append(["Within-district component"] + [f3(N["bw"][k + "__within"]) if k + "__within" in N["bw"] else "–" for k, _ in ROB])
    for o, lab in (("RESP", "Comparison: respiratory deaths"), ("GCA", "Comparison: gastric cancer")):
        rows.append([lab] + [f3(N["nco"][(o, k)]) if (o, k) in N["nco"] else "–" for k, _ in ROB])
    foot = (f"Each row changes one element of the principal model. Posterior predictive 95% intervals covered {100*N['ppc']['coverage95']:.1f}% of observations (probability integral transform Kolmogorov–Smirnov P = {N['ppc']['pit_ks_p']:.3f}); "
            f"2024 conditional check: coverage {100*N['oos']['coverage95']:.1f}%, median absolute percentage error {N['oos']['median_abs_pct_error']:.1f}%. "
            f"E-values (limit): basic livelihood {N['evalue']['basic_livelihood_rate']['E_point']:.2f} ({N['evalue']['basic_livelihood_rate']['E_limit']:.2f}), physical activity {N['evalue']['moderate_pa_rate']['E_point']:.2f} ({N['evalue']['moderate_pa_rate']['E_limit']:.2f}), sports facilities {N['evalue']['public_sports_facilities_per_100k']['E_point']:.2f} ({N['evalue']['public_sports_facilities_per_100k']['E_limit']:.2f}). "
            "Province codes follow the Statistics Korea classification. ICAR, intrinsic conditional autoregressive.")
    return ("Supplementary Table S6. Alternative Specifications: Rate Ratios per 1 SD (95% CrI)", ["Specification"] + [l for _, l in ROB], rows, foot)
def s7():
    X = pd.read_csv(os.path.join(PH, "PH_extra_IRR.csv")); rows = []
    for sp, lab in (("tb_suspect", "+ suspected tuberculosis share"), ("detached", "+ detached-house households"), ("im_spec", "+ internal medicine specialists"), ("all3", "+ all three")):
        d = X[X.spec == sp]; extra = {"tb_suspect": ["ext__tb_suspect_share"], "detached": ["detached_house_households"], "im_spec": ["im_specialists_per_100k"], "all3": ["ext__tb_suspect_share", "detached_house_households", "im_specialists_per_100k"]}[sp]
        rows.append([lab, "; ".join(row(d, e) for e in extra), row(d, "basic_livelihood_rate"), row(d, "moderate_pa_rate"), f"{d.WAIC.iloc[0]:,.1f}"])
    rows += [["__H__", "Former coal-mining districts"]]
    for k, v in N["coal_mines"].items(): rows.append([ROM.get(k, k), f"RR {v['RR']:.2f}", v["class"].replace("hotspot", "hot spot").replace("coldspot", "cold spot"), f"percentile {100*v['pct_rank_RR']:.0f}", ""])
    D = N["desc"]
    foot = (f"Upper rows: the principal model with characteristics fixed in advance for sensitivity analysis only; columns give the added characteristic(s), basic livelihood security receipt, moderate-or-vigorous physical activity and WAIC. "
            f"Lower rows: residual district rate ratio of seven districts with former major coal mines (median {N['coal_mines_med']:.2f}, other districts {N['coal_others_med']:.2f}). "
            f"Unadjusted Spearman's ρ of district standardised ratios: {D['rho_sir_tbsuspect']:.2f} with the suspected tuberculosis share and {D['rho_sir_tbhistory']:.2f} with tuberculosis history; median ρ between adjacent years {D['rho_year_adjacent_median']:.2f}; 2011 vs 2024 {D['rho_2011_2024']:.2f}. WAIC, widely applicable information criterion.")
    rows += [["__H__", "Exposure markers by district-effect structure"]]
    EXP = [("ext__tb_history_share", "TB history"), ("current_smoking_rate", "Smoking"), ("factory_land_share", "Industrial land"), ("coal_plant_host", "Coal plant")]
    for lab, f in (("Principal model", "S3_main_IRR.csv"), ("Independent district effect only", "S43_part_iid_only.csv"), ("No district effect", "S43_part_no_spatial.csv"), ("Spatial+", "S41_part_D1_spatial_plus.csv")):
        d = pd.read_csv(os.path.join(RS, f)); rows.append([lab] + ["; ".join(f"{n} {row(d, k)}" for k, n in EXP[:2]), "; ".join(f"{n} {row(d, k)}" for k, n in EXP[2:]), "", ""])
    d = X[X.spec == "drop2123"]; rows += [["__H__", "Without 2021\u20132023"], ["Principal model without 2021\u20132023", "\u2013", row(d, "basic_livelihood_rate"), row(d, "moderate_pa_rate"), f"{d.WAIC.iloc[0]:,.1f}"]]
    return ("Supplementary Table S7. Post Hoc Analyses", ["Analysis or district", "Added characteristic(s)", "Basic livelihood", "Physical activity", "WAIC"], rows, foot)
STROBE = [("Title and abstract", "Ecological panel design stated in the abstract", "Abstract"), ("Background/rationale", "Introduction", "Introduction"), ("Objectives", "Final paragraph of the Introduction", "Introduction"),
          ("Study design", "Ecological panel study", "Materials and Methods"), ("Setting", "Korea, 2011–2024, national general health examination", "Materials and Methods"), ("Participants", "All districts; examinees with a judgement", "Materials and Methods; Table S1"),
          ("Variables", "Outcome, characteristics, forced controls, negative controls", "Materials and Methods; Table S2"), ("Data sources/measurement", "National statistics portal and registers", "Table S2"),
          ("Bias", "Standardisation, negative controls, comparison outcomes, E-values", "Materials and Methods"), ("Study size", f"{N['n_rows']:,} district-years", "Results"),
          ("Quantitative variables", "Standardised to 1 SD", "Materials and Methods"), ("Statistical methods", "Bayesian spatiotemporal models; sensitivity analyses", "Materials and Methods; Table S6"),
          ("Descriptive data", "Table 1", "Results"), ("Outcome data", "Flagged and expected numbers", "Results; Table 1"), ("Main results", "Rate ratios with 95% CrIs", "Table 2; Figure 3"),
          ("Other analyses", "Space–time, window, decomposition and post hoc analyses", "Tables S5–S7"), ("Key results", "First paragraph of the Discussion", "Discussion"),
          ("Limitations", "Strengths and limitations", "Discussion"), ("Interpretation", "Discussion", "Discussion"), ("Generalisability", "Discussion", "Discussion"), ("Funding", "None", "Title page")]
def s8(): return ("Supplementary Table S8. STROBE Checklist", ["Item", "Where addressed", "Section"], [list(x) for x in STROBE], "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.")

if __name__ == "__main__":
    J = TX(cite="bracket"); J.para("<b>Supplementary Material</b>"); J.para(TITLE)
    J.para("Supplementary Appendix S1, Table S1; S2, Table S2; S3, Table S3; S4, Table S4; S5, Table S5; S6, Table S6; S7, Table S7; S8, Table S8.", before=6)
    for t in (s1(), s2(), s3(), s4(), s5(), s6(), s7(), s8()):
        J.page_break(); put_table(J, t, fs=8)
    p = os.path.join(OUT, "Supplementary_Material.docx"); J.save(p); to_pdf(p); print("supplement ok")
