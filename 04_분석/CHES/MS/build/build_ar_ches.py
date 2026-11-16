#  규정(MS/00_AcadRadiol_규정요약_261117.md): ≤5,000단어·참고 ≤50·표 ≤5·그림 ≤10, Take-Home Messages 1–2(≤50단어), 구조화 초록 250(Rationale and Objectives / Materials and Methods / Results / Conclusion),
#   이중 익명 → 제목면(짧은 제목 ≤6단어·키워드 3–5·이해충돌·연구비·AI 선언)·익명 원고·사사 파일 별도, 표는 참고문헌 뒤 + 별도 Word 파일, 그림 개별 파일 ≥300 dpi·범례는 참고문헌 뒤,
#   AI 선언 절은 참고문헌 앞, 참고문헌 AMA형(Boyko A, ... Title. Acad Radiol. 2024;31(5):1727-1734. doi: ...), 약어 목록, 12pt 이중 간격 쪽 번호.
import os, re, json, subprocess
from docx.shared import Pt
from jkms_engine import JKMS
import content_ches as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_ches.json"), encoding="utf-8"))
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
_pf = os.path.join(OUT, "phone.txt"); PHONE = (open(_pf).read().strip() + ". ") if os.path.exists(_pf) else ""
_gf = os.path.join(OUT, "github_url.txt"); GITHUB = open(_gf).read().strip() if os.path.exists(_gf) else "[GITHUB URL]"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
FUNDING = "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."
CREDIT = "Seongdae Kim: Conceptualization, Data curation, Formal analysis, Investigation, Methodology, Software, Visualization, Writing – original draft, Writing – review and editing."
COI = "The author declares that there are no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper."
AI_HEAD = "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"
AI_STATEMENT = "During the preparation of this work the author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. After using these tools, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article."
DATA_ANON = "All source data are publicly available aggregate statistics cited in the Materials and Methods. The analysis code is openly available in a public repository under the MIT License (link on the title page, withheld for blinded review). The processed district-year data are available on reasonable request."
AI_ANON = "During the preparation of this work, Claude (Anthropic) and ChatGPT (OpenAI) were used only for translation and English-language editing of the manuscript. After using these tools, the content was reviewed and edited as needed, and full responsibility is taken for the content of the published article."
def data_full(): return f"All source data are publicly available aggregate statistics cited in the Materials and Methods. The analysis code and the scripts that generate every number, table and figure are openly available on Zenodo (https://doi.org/{ZENODO}) and GitHub ({GITHUB}) under the MIT License; they contain code only. The processed district-year data are available from the author on reasonable request."
ETHICS_FULL = "The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 (7002340-202611-HR-040) and waived informed consent because only published aggregate statistics were used."
ABBR_ALL = [("AI", "artificial intelligence"), ("BYM2", "Besag–York–Mollié 2"), ("CrI", "credible interval"), ("CT", "computed tomography"), ("RR", "rate ratio"), ("SD", "standard deviation"), ("STROBE", "Strengthening the Reporting of Observational Studies in Epidemiology"), ("WAIC", "widely applicable information criterion")]
def _abbr():
    import content_ches as _C
    body = " ".join(_C.INTRO + [t for _, t in _C.METHODS] + [t for _, t in _C.RESULTS] + _C.DISCUSSION)
    return [(a, b) for a, b in ABBR_ALL if len(re.findall(rf"(?<![A-Za-z]){re.escape(a)}(?![A-Za-z])", body)) >= 3]
ABBR = _abbr()

def cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: " {{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def all_keys():
    src = open(os.path.join(HERE, "content_ches.py"), encoding="utf-8").read(); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys(); _miss = [k for k in KEYS if k not in REFS]; assert not _miss, _miss
def full_pages(p):
    m = re.fullmatch(r"([A-Za-z]*)(\d+)-([A-Za-z]*)(\d+)", p or "")
    if not m: return p
    pre, a, _, b = m.groups()
    if len(b) < len(a): b = a[:len(a) - len(b)] + b
    return f"{pre}{a}-{pre}{b}" if pre else f"{a}-{b}"
def ama(k):   # Academic Radiology(AMA): 저자 ≤6 전부, 7명 이상 3명 + et al. Title. J Abbr. Year;Vol(Issue):pages. doi: ...
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title']}. Available at: {r['url']}. Accessed {r['accessed']}."
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    t = r["title"].rstrip("."); t = t + ("" if t.endswith(("?", "!")) else ".")
    if r.get("lang"): t = t[:-1] + f" [in {r['lang']}]."
    s = f"{a}. {t} {r['journal'].replace('.', '')}. {r['year']}"
    if r.get("vol"): s += f";{r['vol']}" + (f"({r['issue']})" if r.get("issue") else "") + (f":{full_pages(r['pages'])}" if r.get("pages") else "")
    return s + "." + (f" doi: {r['doi']}." if r.get("doi") else "")

class TX(JKMS):
    raw = False; table_bold = True
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw: text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)

LAB = {"ext__tb_history_share": ("Tuberculosis history among examinees", "% of examinees"), "current_smoking_rate": ("Current smoking", "%"), "factory_land_share": ("Industrial land", "% of area"),
       "coal_plant_host": ("Coal-fired power plant", "% of districts"), "basic_livelihood_rate": ("Basic livelihood security receipt", "%"), "tertiary_educated_share": ("Tertiary education", "% of adults"),
       "ext__screening_uptake_ches": ("Screening uptake", "%"), "ext__clinics_per100k": ("Clinics", "per 100,000"), "walking_practice_rate": ("Walking", "%"),
       "moderate_pa_rate": ("Moderate-or-vigorous physical activity", "%"), "public_sports_facilities_per_100k": ("Public sports facilities", "per 100,000"),
       "urban_population_share": ("Urban population share", "%"), "physicians_per_1000": ("Physicians", "per 1,000"), "sex_ratio": ("Sex ratio", "men per 100 women"),
       "fiscal_independence": ("Fiscal autonomy", "%"), "pop80_share": ("Aged 80 years or older", "%")}
GROUPS = [("Chest exposures", ["ext__tb_history_share", "current_smoking_rate", "factory_land_share", "coal_plant_host"]),
          ("Deprivation", ["basic_livelihood_rate", "tertiary_educated_share"]),
          ("Screening selection and reading", ["ext__screening_uptake_ches", "ext__clinics_per100k"]),
          ("Physical activity", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
EXPECT = {"ext__tb_history_share": "+", "current_smoking_rate": "+", "factory_land_share": "+", "coal_plant_host": "+", "basic_livelihood_rate": "+", "tertiary_educated_share": "\u2212",
          "ext__screening_uptake_ches": "\u2212", "ext__clinics_per100k": "\u00b1", "walking_practice_rate": "\u2212", "moderate_pa_rate": "\u2212", "public_sports_facilities_per_100k": "\u2212"}
assert set(LAB) == set(N["main"]) and sum(len(v) for _, v in GROUPS[:-1]) == N["n_hyp"]
th = lambda x: f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.1f}"
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    rows = [["__H__", "Screening"], ["  District-years, n"] + [f"{T[c]['n']:,}" for c in cols], ["  Examinations, million"] + [f"{T[c]['exam']/1e6:.1f}" for c in cols],
            ["  Flagged as other chest disease, n"] + [f"{T[c]['cases']:,}" for c in cols], ["  Crude positivity, %"] + [f"{T[c]['pos']:.2f}" for c in cols],
            ["  Standardised ratio, median*"] + [f"{T[c]['sir_med']:.2f}" for c in cols], ["  Standardised ratio, P10\u2013P90*"] + [f"{T[c]['sir_p10']:.2f}\u2013{T[c]['sir_p90']:.2f}" for c in cols]]
    for g, vs in GROUPS:
        rows.append(["__H__", f"{g}, mean (SD)"])
        for v in vs:
            lab, unit = LAB[v]; mx = max(abs(T[c]["cov"][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 3 else 1)
            f = (lambda m, s: f"{100*m:.1f}") if v == "coal_plant_host" else (lambda m, s: f"{m:,.{dp}f} ({s:,.{dp}f})")
            rows.append([f"  {lab}, {unit}"] + [f(*T[c]["cov"][v]) for c in cols])
    foot = ("*Observed over expected number flagged, summed over the period by district; expected numbers from national positivity by year, sex and age group applied to the estimated age structure of each district's examinees. "
            "Covariates are shown before standardisation; coal-fired power plant is the percentage of districts hosting a plant. P10\u2013P90, 10th\u201390th percentile; SD, standard deviation.")
    return ("Table 1. Chest Radiographs Flagged as Other Chest Disease and District Characteristics by Period, Korea, 2011\u20132024", ["Characteristic", "2011\u20132015", "2016\u20132019", "2020\u20132024", "2011\u20132024"], rows, foot)
def table2():
    rows = []; f = lambda x: f"{x[0]:.3f} ({x[1]:.3f}\u2013{x[2]:.3f})"
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v)
            rows.append([f"  {LAB[v][0]}", EXPECT.get(v, "\u2013"), f((m["IRR"], m["lo"], m["hi"])), f"{100*mv['cred_frac']:.0f}" if mv else "\u2013",
                         f(C.S43("KH_typeI", v)), f(C.S43("KH_typeII", v)), f(C.S43("KH_typeIV", v))])
    foot = (f"Rate ratios (RRs) per 1 standard deviation with 95% credible intervals (CrIs). Principal model: negative binomial with a Besag\u2013York\u2013Molli\u00e9 2 district effect and random-walk and independent year effects, "
            f"{N['n_hyp']} characteristics and 5 forced controls ({N['n_rows']:,} district-years). \u2013, forced control or not applicable. "
            "*Share of the 200 covariate-subset models containing the characteristic in which the CrI excluded 1. "
            "\u2020Principal model plus Knorr-Held type I (independent district-year), type II (district-specific random walk) or type IV (space\u2013time) interaction; type I had the lowest widely applicable information criterion.")
    return ("Table 2. District Characteristics and Chest Radiographs Flagged as Other Chest Disease, Korea, 2011\u20132024",
            ["Characteristic", "Expected", "Principal model\nRR (95% CrI)", "Subsets\ncredible, %*", "Type I\u2020\nRR (95% CrI)", "Type II\u2020\nRR (95% CrI)", "Type IV\u2020\nRR (95% CrI)"], rows, foot)

FIGCAP = {
 1: ("National positivity for other chest disease at general health screening, Korea, 2011\u20132024",
     "(A) Percentage of examinations flagged as other chest disease on the chest radiograph by year. (B) Percentage flagged by sex and age group in 2011 and 2024."),
 2: ("District pattern of chest radiographs flagged as other chest disease, Korea, 2011\u20132024",
     "(A) Residual district rate ratio from the principal model (Besag\u2013York\u2013Molli\u00e9 2 district effect, exponentiated), with hot spots (posterior probability that the ratio exceeds 1 greater than 0.95; solid outline) and cold spots (less than 0.05; dashed outline). "
     "(B) Number of the three periods (2011\u20132015, 2016\u20132019, 2020\u20132024) in which each district was a hot spot (red) or a cold spot (blue). Map lines delineate study areas and do not necessarily depict accepted national boundaries."),
 3: ("Rate ratios per 1 standard deviation of district characteristics across model specifications",
     "Points and lines show rate ratios and 95% credible intervals from the principal model, models with Knorr-Held type I, II and IV space\u2013time interactions, and the between-district and within-district components of a decomposition model."),
}
def foot_row(J, text, sz=8, ls=12):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=False); foot_row(J, t[3]); J.counting = c

IRB_ANON = "The Institutional Review Board of [blinded] approved the study on 4 November 2025 ([blinded]) and its continuing review on 3 November 2026 ([blinded])"
IRB_FULL = "The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 (7002340-202611-HR-040)"
def build(bw=0, aw=0, deanon=False):
    J = TX(cite="bracket")
    dz = (lambda t: t.replace(IRB_ANON, IRB_FULL)) if deanon else (lambda t: t)
    J.para(f"<b>{TITLE}</b>")
    if deanon:
        J.para("Seongdae Kim, PhD", before=6); J.para(ADDRESS); J.para(f"Corresponding author: Seongdae Kim. Email: kimsd@hongik.ac.kr. ORCID: {ORCID}.")
    J.para("<b>Article type:</b> Original Investigation", before=6)
    J.para(f"<b>Word counts:</b> abstract {aw} words; text {bw:,} words. <b>Tables and figures:</b> 2 tables and 3 figures. <b>References:</b> {len(KEYS)}.", before=6)
    J.page_break(); J.head("Take-Home Messages", 1)
    for t in C.TAKE_HOME: J.para("\u2022 " + t)
    J.head("Abstract", 1)
    for h, t in C.ABSTRACT.items(): J.para(f"<b>{h}:</b> {t}")
    J.para(f"<b>Keywords:</b> {'; '.join(C.KEYWORDS)}", before=6)
    J.head("Abbreviations", 1); J.para("; ".join(f"{a}, {b}" for a, b in ABBR))
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in C.INTRO: J.para(cites(p), indent=True)
    J.head("Materials and Methods", 1)
    for h, p in C.METHODS: J.head(h, 2); J.para(cites(dz(p)), indent=True)
    J.head("Results", 1)
    for h, p in C.RESULTS: J.head(h, 2); J.para(cites(p), indent=True)
    J.head("Discussion", 1)
    disc = C.DISCUSSION; ci_ = disc.index("### Conclusion")
    for p in disc[:ci_]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(cites(p), indent=True)
    J.head("Conclusion", 1)
    for p in disc[ci_ + 1:]: J.para(cites(p), indent=True)
    J.counting = False
    if deanon: J.head("CRediT authorship contribution statement", 1); J.para(CREDIT)
    for h, t in (("Data availability", data_full() if deanon else DATA_ANON), (AI_HEAD, AI_STATEMENT if deanon else AI_ANON)):
        J.head(h, 1); J.para(t)
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for n, k in enumerate(J.cites, 1): s = f"{n}. {ama(k)}"; rl.append(s); J.para(s)
    J.raw = False
    J.page_break(); put_table(J, table1()); J.new_page("landscape"); put_table(J, table2(), fs=8)
    J.new_page("portrait"); J.head("Figure Legends", 1)
    for k in sorted(FIGCAP): t, c = FIGCAP[k]; J.para(f"<b>Figure {k}.</b> {t}. {c}")
    return J, rl

def docx_bw(path):
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    return len(t[t.find("\nIntroduction\n"):t.find("\nData availability\n")].split())
def to_pdf(p): subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_ches_ar", "--convert-to", "pdf", "--outdir", os.path.dirname(p), p], check=True, capture_output=True)

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript_Blinded.docx")
    aw = sum(len(t.split()) for t in C.ABSTRACT.values()); assert aw <= 250, aw
    J, rl = build(); J.save(p); bw = docx_bw(p); assert bw <= 5000, bw
    J, rl = build(bw, aw); J.save(p); assert docx_bw(p) == bw, bw; to_pdf(p)
    D, _ = build(bw, aw, deanon=True); dp = os.path.join(OUT, "Manuscript_Deanonymized.docx"); D.save(dp); to_pdf(dp)
    for i, t in ((1, table1()), (2, table2())):
        T = TX(cite="bracket")
        if i == 2:
            from docx.enum.section import WD_ORIENT
            from docx.shared import Cm
            s0 = T.doc.sections[0]; s0.orientation = WD_ORIENT.LANDSCAPE; s0.page_width, s0.page_height = Cm(29.7), Cm(21.0)
        put_table(T, t, fs=8 if i == 2 else 9); tp = os.path.join(OUT, f"Table_{i}.docx"); T.save(tp)
    K = TX(cite="bracket"); K.para("<b>Declaration of interests</b>"); K.para(f"Manuscript: {TITLE}")
    K.para("\u2612 The author declares that there are no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.")
    K.save(os.path.join(OUT, "Declaration_of_Interests.docx"))
    K = TX(cite="bracket"); K.para("<b>Acknowledgements</b>"); K.para("None."); K.para(f"<b>Funding:</b> {FUNDING}", before=6); K.save(os.path.join(OUT, "Acknowledgements.docx"))
    # 제목면(이중 익명: 저자·소속·교신·짧은 제목·키워드·이해충돌·연구비·AI·윤리·데이터)
    K = TX(cite="bracket"); K.para(f"<b>{TITLE}</b>"); K.para(f"<b>Short title:</b> {C.RUNNING}", before=6)
    K.para("Seongdae Kim, PhD<sup>a</sup>", before=12); K.para(f"<sup>a</sup>{ADDRESS}")
    K.para(f"<b>Corresponding author:</b> Seongdae Kim, {ADDRESS}. {PHONE}Email: kimsd@hongik.ac.kr. ORCID: {ORCID}.", before=6)
    K.para(f"<b>Keywords:</b> {'; '.join(C.KEYWORDS)}", before=6)
    for h, t in (("Disclosures (declaration of competing interest)", COI), ("Funding", FUNDING), ("CRediT authorship contribution statement", CREDIT), ("Ethics", ETHICS_FULL),
                 ("Data availability", data_full()), (AI_HEAD, AI_STATEMENT)):
        K.para(f"<b>{h}:</b> {t}", before=6)
    K.para(f"<b>Word counts:</b> abstract {aw}; text {bw:,}; 2 tables; 3 figures; {len(KEYS)} references.", before=6)
    tpp = os.path.join(OUT, "Title_Page.docx"); K.save(tpp); to_pdf(tpp)
    open(os.path.join(OUT, "wordcount_ar.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=3\ntitle_words={len(TITLE.split())}\nthm_words={[len(t.split()) for t in C.TAKE_HOME]}\n")
    open(os.path.join(OUT, "references.txt"), "w").write("\n".join(rl))
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | title words {len(TITLE.split())}")
