#!/usr/bin/env python3
import os, numpy as np, pandas as pd
B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "04_분석", "CHES"); P = pd.read_csv(os.path.join(B, "panel_CHES_std3.csv"))
s = P.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False).rename("SIR").to_frame()
s["tbs"] = P.groupby("fbd_region").ext__tb_suspect_share_raw.mean(); s["tbh"] = P.groupby("fbd_region").ext__tb_history_share_raw.mean()
s["sido"] = s.index.str.extract(r"^(\S+?(?:도|시))", expand=False).values
ls = np.log(s.SIR); grand = ls.mean(); between = s.assign(l=ls).groupby("sido").l.transform("mean")
r = dict(n=len(s), sir_p10=s.SIR.quantile(.1), sir_p90=s.SIR.quantile(.9), sir_min=s.SIR.min(), sir_max=s.SIR.max(),
         share_var_between_sido=float(((between - grand) ** 2).sum() / ((ls - grand) ** 2).sum()),
         rho_sir_tbsuspect=float(s.SIR.corr(s.tbs, method="spearman")), rho_sir_tbhistory=float(s.SIR.corr(s.tbh, method="spearman")))
Y = P.assign(sir=P.cases / P.E).pivot(index="fbd_region", columns="year", values="sir")
r["rho_year_adjacent_median"] = float(np.median([Y[y].corr(Y[y + 1], method="spearman") for y in range(2011, 2024)]))
r["rho_2011_2024"] = float(Y[2011].corr(Y[2024], method="spearman"))
pd.Series(r).to_csv(os.path.join(B, "results_posthoc", "PH_reading_desc.csv"), header=["value"], encoding="utf-8-sig"); print(pd.Series(r).round(3).to_string())
