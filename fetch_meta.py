#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga datos diarios de Meta Ads para Ensifera y genera meta_daily.json.
Corre como paso previo en el workflow de GitHub Actions.

Requisitos: pip install requests
Env:        META_ADS_TOKEN  (user token con permisos ads_read + pages_read_engagement)
"""
import os, json, datetime, sys, re

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

ACCOUNT_ID = "act_1580457616921076"
API_VERSION = "v21.0"
TOKEN = os.environ.get("META_ADS_TOKEN", "").strip()

if not TOKEN:
    sys.exit("ERROR: META_ADS_TOKEN no definido. Agregar como GitHub Secret.")

HERE = os.path.dirname(os.path.abspath(__file__))

# Rango: últimos 35 días (cubre mes actual completo)
today = datetime.date.today()
since = today - datetime.timedelta(days=35)

def parse_cop(s):
    """Convierte '$\xa087.771\xa0COP' o '87771' a int COP."""
    clean = re.sub(r"[^\d]", "", str(s))
    return int(clean) if clean else 0

def fetch_page(url, params):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Llamada a Insights API nivel campaign, time_increment=1 (sin reach — lo rompe)
url = f"https://graph.facebook.com/{API_VERSION}/{ACCOUNT_ID}/insights"
params = {
    "access_token": TOKEN,
    "fields": "spend,impressions,campaign_id,campaign_name,results",
    "level": "campaign",
    "time_increment": "1",
    "time_range": json.dumps({"since": str(since), "until": str(today)}),
    "limit": 500,
}

all_records = []
data = fetch_page(url, params)
all_records.extend(data.get("data", []))
# Paginación
while data.get("paging", {}).get("next"):
    data = fetch_page(data["paging"]["next"], {})
    all_records.extend(data.get("data", []))

# Agregar por fecha
by_date = {}
for rec in all_records:
    d = rec["date_start"]
    spend = parse_cop(rec.get("spend", "0"))
    impr = int(rec.get("impressions", 0) or 0)
    results_raw = rec.get("results", [])
    results = sum(int(r.get("value", 0)) for r in results_raw) if isinstance(results_raw, list) else 0
    camp_name = rec.get("campaign_name", "")
    camp_id = rec.get("campaign_id", "")
    if d not in by_date:
        by_date[d] = {"date": d, "spendCOP": 0, "impressions": 0, "resultsAds": 0, "campaigns": []}
    by_date[d]["spendCOP"] += spend
    by_date[d]["impressions"] += impr
    by_date[d]["resultsAds"] += results
    by_date[d]["campaigns"].append({"name": camp_name, "id": camp_id, "spendCOP": spend, "impressions": impr, "results": results})

days = sorted(by_date.values(), key=lambda x: x["date"])
out = {"generated": str(today), "days": days}

out_path = os.path.join(HERE, "meta_daily.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

t_spend = sum(d["spendCOP"] for d in days)
sys.stderr.write(f"OK: {len(days)} dias  inversion={t_spend:,} COP  ({since} → {today})\n")
