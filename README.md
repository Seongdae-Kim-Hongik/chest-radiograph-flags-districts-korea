# Chest radiographs flagged as other chest disease at national health screening across districts of South Korea, 2011-2024

Analysis code for the manuscript

> Kim S. *Where is a screening chest radiograph called abnormal? District variation in other chest disease flags over 14 years of Korean national health screening.*

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24294259 (v1.0.0).

This code is released under the MIT licence.

## Contents

This repository contains code only. The processed district-year data (analytic panel, expected counts, result tables and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/CHES/` | Model settings fixed before covariate models were fitted (`sets_CHES_*.json`, `config_CHES_std3.json`), the full model chain (`run_std3_chain.sh`) and the district adjacency graph (`graph_593.graph`). Sensitivity versions: queen contiguity graph `s577`, without the share aged 80 or older `s2`, age-only standardisation `s8` |
| `04_분석/CHES/MS/build/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supplementary material (`numbers_ches.py`, `figs_ches.py`, `content_ches.py`, `build_ar_ches.py`, `esm_ches.py`) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Examinees with a judgement and examinees flagged as suspected other chest disease or suspected pulmonary tuberculosis on the chest radiograph, and examinees reporting pulmonary tuberculosis treatment, by district and sex: National Health Insurance Service health screening statistics, KOSIS tables DT_35007_N098, N103 and N105, 2011-2024; screening uptake, DT_35007_N001 and N001_1.
- National numbers by sex and age group: KOSIS DT_35007_N099 and N104.
- Population by sex and 5-year age group: Ministry of the Interior and Safety, resident registration statistics.
- District covariates: Community Health Survey (smoking, walking, moderate-or-vigorous physical activity), public sports facility register, cadastral statistics (factory sites), Korea Power Exchange generator capacity (coal-fired plants), basic livelihood security statistics, census (tertiary education), care institution statistics (clinics) and KOSIS local indicators (forced controls and negative controls).

## Pipeline

Set `ST_DATA_ROOT` and `ST_GPT_DATASET` to the local copies of the public source files and the read-only district database, and `ST_FBDZIP` to the resident population tables, then run from the repository root.

| Step | Script | Output |
|---|---|---|
| 1 | `99C2_build_Estd3_ches.py` (uses `38_build_Estd_all.py`, `40_region_crosswalk.py`, `50_build_master_panel.py`) | District numbers flagged and examinees (code-based linkage) and expected numbers by indirect standardisation in 2 sexes x 15 age groups |
| 2 | `99c_extra_canonical_pool_ches.py` | Covariate pool (model settings in `04_분석/CHES/sets_CHES_*.json`) |
| 3 | `80_build_disease_panel_v.py CHES` (`ST_VER=std3`) and `99C4_ches_sqlite_compare.py` | Analytic panel and comparison with the read-only district database |
| 4 | `81_fit_inla.R CHES` (see `04_분석/CHES/run_std3_chain.sh`, which wraps R jobs in `rslot.sh`) | Principal model, 200-subset multiverse, period models, sensitivity versions |
| 5 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `87_window_grid.py` | Maps and yearly smoothed ratios |
| 6 | `88g_sens_prep.py CHES std3 RESP,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R` (nb, struct, kh, review) with `kh_constraints.R`, `89g_sens_combine.py` | Alternative specifications, comparison outcomes, Knorr-Held models, decomposition |
| 7 | `88X_ches_posthoc.R`, `88Y_ches_reading_desc.py` | Post hoc analyses |
| 8 | `04_분석/CHES/MS/build/` | Manuscript numbers, tables, figures and supplementary material |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.

## Licence

MIT (see `LICENSE`).
