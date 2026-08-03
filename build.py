#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenera index.html del tablero de Ensifera a partir del xlsx de la hoja
"Conglomerado Gastos Publicitarios 2026" y de meta.json (snapshot de Meta Ads).

Uso:  python build.py <ruta_al_xlsx>
Requiere: openpyxl  (pip install openpyxl)

No necesita Excel. Pensado para correr en un entorno headless (rutina en la nube).
"""
import re, json, sys, os, datetime

try:
    from openpyxl import load_workbook
except ImportError:
    sys.stderr.write("Falta openpyxl. Instala con: pip install openpyxl\n")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
USDCOP = 3600
MONTHNUM = {"JUNIO": 6, "JULIO": 7, "AGOSTO": 8}
SHEETS = ["Junio", "Julio", "Agosto"]

def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def S(x):
    return "" if x is None else str(x).strip()

def cell(row, i):
    if row is None or i < 0 or i >= len(row):
        return None
    return row[i]

def cint(x):
    if x is None: return None
    if is_num(x): return float(x)
    t = str(x)
    if "#" in t: return None
    d = re.sub(r"[^0-9]", "", t)
    return float(d) if d else None

def cusd(x):
    if x is None: return None
    if is_num(x): return float(x)
    t = str(x).strip()
    if "#" in t: return None
    t = re.sub(r"[\$\s ]", "", t)
    if t in ("", "-"): return None
    if re.match(r"^[0-9]+,[0-9]{1,2}$", t): t = t.replace(",", ".")
    else: t = t.replace(",", "")
    try: return float(t)
    except: return None

def cpct(x):
    if x is None: return None
    if is_num(x): return float(x) * 100.0
    t = str(x)
    if "#" in t: return None
    t = re.sub(r"[%\s ]", "", t).replace(",", ".")
    try: return float(t)
    except: return None

def croas(x):
    if x is None: return None
    if is_num(x): return float(x)
    t = str(x)
    if "#" in t: return None
    t = re.sub(r"[\$\s ]", "", t).replace(",", ".")
    if t in ("", "-"): return None
    try: return float(t)
    except: return None

def pdate(x):
    if x is None: return None
    if isinstance(x, datetime.datetime): return x.strftime("%Y-%m-%d")
    if isinstance(x, datetime.date): return x.strftime("%Y-%m-%d")
    if is_num(x):
        n = float(x)
        if 20000 < n < 90000:
            return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=n)).strftime("%Y-%m-%d")
        return None
    t = str(x).strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m: return "%04d-%02d-%02d" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m: return "%04d-%02d-%02d" % (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None

def parse_sheet(ws, sheet_name, days):
    grid = list(ws.iter_rows(values_only=True))
    n = len(grid)
    ncol = max((len(r) for r in grid), default=0)
    markers = []
    for i, row in enumerate(grid):
        m = re.match(r"^GASTOS PUBLICITARIOS\s+(\d+)\s+([A-ZÁÉÍÓÚ]+)", S(cell(row, 0)))
        if m:
            markers.append((i, int(m.group(1)), m.group(2).upper()))
    for mi, (start, mday, mmon) in enumerate(markers):
        end = markers[mi + 1][0] if mi + 1 < len(markers) else n
        campaigns = []
        sedes_conv, agents, products, sales_by_sede = {}, {}, {}, {}
        summ = {}
        date = None
        gasto_usd = gasto_cop = None
        impr = reach = res = 0.0
        r = start
        while r < end:
            row = grid[r]
            c0 = S(cell(row, 0))
            # campaign/ad table (header has "Importe gastado (USD|COP)")
            spend_col = -1; curr = None
            for c in range(ncol):
                h = S(cell(row, c))
                if "Importe gastado" in h:
                    spend_col = c
                    curr = "USD" if "USD" in h else "COP"
                    break
            if spend_col >= 0:
                name_col = impr_col = reach_col = res_col = -1
                for c in range(ncol):
                    h = S(cell(row, c))
                    if h.startswith("Nombre"): name_col = c
                    elif h == "Impresiones": impr_col = c
                    elif h == "Alcance": reach_col = c
                    elif h in ("Resultados", "Mensajes totales", "Contactos de mensajes"): res_col = c
                if name_col < 0: name_col = 0
                j = r + 1
                while j < end:
                    r2 = grid[j]
                    gt = False
                    for c in range(ncol):
                        if S(cell(r2, c)) == "GASTO TOTAL":
                            gt = True
                            if curr == "USD": gasto_usd = cusd(cell(r2, c + 1))
                            else: gasto_cop = cint(cell(r2, c + 1))
                            break
                    if gt: break
                    nm = S(cell(r2, name_col))
                    if nm == "" or nm.startswith("Nombre") or nm.startswith("Inicio"):
                        j += 1; continue
                    sp_raw = cell(r2, spend_col)
                    if curr == "USD":
                        u = cusd(sp_raw); sp = round(u * 3600) if u is not None else None
                    else:
                        sp = cint(sp_raw)
                    im = cint(cell(r2, impr_col)) if impr_col >= 0 else None
                    rc = cint(cell(r2, reach_col)) if reach_col >= 0 else None
                    rs = cint(cell(r2, res_col)) if res_col >= 0 else None
                    campaigns.append({"name": nm, "spendCOP": sp, "impressions": im, "reach": rc, "results": rs})
                    if im: impr += im
                    if rc: reach += rc
                    if rs: res += rs
                    j += 1
                r = j; continue
            # CONVERSACIONES / CONVERSACIONES MERCATELY
            if re.match(r"^CONVERSACIONES", c0):
                a_col = h_row = -1
                for j in range(r + 1, min(r + 4, end)):
                    for c in range(ncol):
                        if S(cell(grid[j], c)) == "Agente":
                            a_col = c; h_row = j; break
                    if a_col >= 0: break
                if a_col >= 0:
                    j = h_row + 1
                    while j < end:
                        a = S(cell(grid[j], a_col))
                        if a == "": break
                        if re.match(r"^(MENSAJES|PRODUCTOS|CONVERSACIONES|Ventas|Valor|NOMBRE)", a): break
                        cnt = cint(cell(grid[j], a_col + 1))
                        if cnt is not None:
                            if re.match(r"(?i)^Ensifera\s", a): sedes_conv[a] = cnt
                            else: agents[a] = cnt
                        j += 1
                r += 1; continue
            # PRODUCTOS
            if c0 == "PRODUCTOS":
                p_col = h_row = -1
                for j in range(r + 1, min(r + 4, end)):
                    for c in range(ncol):
                        if S(cell(grid[j], c)) == "Producto":
                            p_col = c; h_row = j; break
                    if p_col >= 0: break
                if p_col >= 0:
                    j = h_row + 1
                    while j < end:
                        p = S(cell(grid[j], p_col))
                        if p == "": break
                        if re.match(r"^(MENSAJES|CONVERSACIONES|Ventas|Valor|NOMBRE)", p): break
                        cnt = cint(cell(grid[j], p_col + 1))
                        if cnt is not None: products[p] = cnt
                        j += 1
                r += 1; continue
            # Ventas Totales <Sede>
            msede = re.match(r"^Ventas Totales\s+(Palmira|Cali|Medell\S*|Bogot\S*)", c0)
            if msede:
                sede = re.sub(r"^Ventas Totales\s+", "", c0)
                v = cint(cell(row, 1))
                sales_by_sede[sede] = v if v is not None else 0
                r += 1; continue
            # trailing NOMBRE summary
            if c0 == "NOMBRE":
                dd = pdate(cell(row, 1))
                if dd: date = dd
                for j in range(r + 1, min(r + 11, end)):
                    lbl = S(cell(grid[j], 0)); val = cell(grid[j], 1)
                    if re.search(r"Inversi.n USD", lbl): summ["spendUSD"] = cusd(val)
                    elif re.search(r"Inversion PC", lbl): summ["spendCOP"] = cint(val)
                    elif lbl == "Conversaciones": summ["conversations"] = cint(val)
                    elif re.search(r"Costo Conversaci", lbl): summ["costConvCOP"] = cint(val)
                    elif lbl == "Ventas Totales": summ["salesCOP"] = cint(val)
                    elif re.search(r"Inversion Venta", lbl): summ["invSalePct"] = cpct(val)
                    elif lbl == "ROAS": summ["roas"] = croas(val)
                    elif re.search(r"Ticket Conversi", lbl): summ["ticketConvPct"] = cpct(val)
                r += 1; continue
            r += 1
        if not date:
            date = "2026-%02d-%02d" % (MONTHNUM.get(mmon, 0), mday)
        spend_cop = summ.get("spendCOP")
        if spend_cop is None:
            spend_cop = gasto_cop if gasto_cop is not None else (round(gasto_usd * 3600) if gasto_usd is not None else None)
        days[date] = {
            "date": date, "month": sheet_name,
            "spendCOP": spend_cop, "spendUSD": summ.get("spendUSD"),
            "impressions": int(impr), "reach": int(reach), "resultsAds": int(res),
            "conversations": summ.get("conversations"), "costConvCOP": summ.get("costConvCOP"),
            "salesCOP": summ.get("salesCOP"), "roas": summ.get("roas"),
            "invSalePct": summ.get("invSalePct"), "ticketConvPct": summ.get("ticketConvPct"),
            "salesBySede": sales_by_sede, "sedesConv": sedes_conv, "agents": agents,
            "products": products, "campaigns": campaigns,
        }

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Uso: python build.py <ruta_al_xlsx>\n"); sys.exit(1)
    xlsx = sys.argv[1]
    wb = load_workbook(xlsx, data_only=True)
    days = {}
    for name in SHEETS:
        if name in wb.sheetnames:
            parse_sheet(wb[name], name, days)
    days_list = [days[k] for k in sorted(days.keys())]

    with open(os.path.join(HERE, "meta.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)

    combined = {"usdCop": USDCOP, "days": days_list,
                "meta": {"account": meta.get("account"), "accountId": meta.get("accountId"),
                         "currency": meta.get("currency"), "period": meta.get("period"),
                         "campaignTotals": meta.get("campaignTotals", []), "daily": meta.get("daily", [])}}

    with open(os.path.join(HERE, "template.html"), "r", encoding="utf-8") as f:
        tpl = f.read()
    data_json = json.dumps(combined, ensure_ascii=False, separators=(",", ":"))
    out = tpl.replace("/*__DATA__*/ {}", data_json)
    if "/*__DATA__*/" in out:
        sys.stderr.write("ERROR: no se pudo inyectar el placeholder en template.html\n"); sys.exit(3)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)

    tot_spend = sum(d["spendCOP"] or 0 for d in days_list)
    tot_sales = sum(d["salesCOP"] or 0 for d in days_list)
    sys.stderr.write("OK: %d dias (%s -> %s)  spendCOP=%d  salesCOP=%d\n" % (
        len(days_list), days_list[0]["date"] if days_list else "-",
        days_list[-1]["date"] if days_list else "-", tot_spend, tot_sales))

if __name__ == "__main__":
    main()
