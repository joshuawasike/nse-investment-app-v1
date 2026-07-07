"""
JOBURA WEALTH®
NSE Institutional Wealth Management Platform
Company Research Engine
(Merged Version)
"""

import os
import json
import glob
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_DIR = os.path.join(DATA_DIR, "nse_csv")
COMPANY_FILE = os.path.join(DATA_DIR, "companies.json")

_market_df = None

def load_companies():
    if not os.path.exists(COMPANY_FILE):
        return []
    with open(COMPANY_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def all_companies():
    return load_companies()

def get_company(code):
    for c in load_companies():
        if c["code"].upper()==code.upper():
            return c
    return None

def search_company(keyword):
    k=keyword.lower()
    return [c for c in load_companies() if k in c["name"].lower() or k in c["code"].lower() or k in c["sector"].lower() or k in c["industry"].lower()]

# ---------------- Historical Market Data ---------------- #

def load_market_data():
    df_local=pd.DataFrame()
    for file in glob.glob(os.path.join(CSV_DIR,"*.csv")):
        try:
            t=pd.read_csv(file)
            t.columns=t.columns.astype(str).str.strip().str.upper()
            req=["CODE","DATE","PREVIOUS"]
            if not all(r in t.columns for r in req):
                continue
            df_local=pd.concat([df_local,t[req]],ignore_index=True)
        except Exception:
            continue
    if not df_local.empty:
        df_local["DATE"]=pd.to_datetime(df_local["DATE"],errors="coerce")
        df_local["PREVIOUS"]=pd.to_numeric(df_local["PREVIOUS"],errors="coerce")
        df_local=df_local.dropna(subset=["CODE","DATE","PREVIOUS"]).sort_values(["CODE","DATE"]).reset_index(drop=True)
    return df_local

def get_market_data():
    global _market_df
    if _market_df is None:
        _market_df=load_market_data()
    return _market_df

def companies_by_sector(sector):
    return [c for c in load_companies() if c["sector"].lower()==sector.lower()]

def top_dividend(limit=10):
    return sorted(load_companies(),key=lambda x:x["dividend_yield"],reverse=True)[:limit]

def top_quality(limit=10):
    return sorted(load_companies(),key=lambda x:x["quality_score"],reverse=True)[:limit]

def top_roe(limit=10):
    return sorted(load_companies(),key=lambda x:x["roe"],reverse=True)[:limit]

def largest_companies(limit=10):
    return sorted(load_companies(),key=lambda x:x["market_cap"],reverse=True)[:limit]

def value_companies(limit=10):
    return sorted([c for c in load_companies() if c["pe_ratio"]>0],key=lambda x:x["pe_ratio"])[:limit]

def best_esg():
    return sorted(load_companies(),key=lambda x:x["health_score"],reverse=True)

def statistics():
    c=load_companies()
    if not c: return {}
    return {
      "companies":len(c),
      "market_cap":sum(i["market_cap"] for i in c),
      "average_dividend":round(sum(i["dividend_yield"] for i in c)/len(c),2),
      "average_roe":round(sum(i["roe"] for i in c)/len(c),2),
      "average_pe":round(sum(i["pe_ratio"] for i in c)/len(c),2),
      "average_health":round(sum(i["health_score"] for i in c)/len(c),2)
    }

def dashboard():
    return {
      "statistics":statistics(),
      "top_dividend":top_dividend(5),
      "top_quality":top_quality(5),
      "top_roe":top_roe(5),
      "largest":largest_companies(5),
      "value":value_companies(5)
    }
