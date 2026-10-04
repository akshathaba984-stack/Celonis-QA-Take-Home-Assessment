#!/usr/bin/env python3
"""OMS <-> Analytics data-diff anomaly explainer.

Design: CODE finds defects and sets a severity floor. The LLM only EXPLAINS them.
  - LLM never decides pass/fail, never removes a finding, can only RAISE severity.
  - LLM output is schema-checked and grounded (numbers must exist in the evidence).
  - Any failure -> deterministic template explanation, finding is still reported.
No API key in code. Configure via environment variables (all optional):
  ANTHROPIC_API_KEY (+ EXPLAINER_MODEL)         -> Anthropic Messages API
  LLM_BASE_URL (+ LLM_API_KEY, EXPLAINER_MODEL) -> any OpenAI-compatible endpoint
                                                   (Ollama local = free, no key)
  none set                                      -> offline template mode
"""
import argparse, json, os, re, sys, urllib.request
from datetime import datetime, timezone
import pandas as pd

RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
NAMES = {v: k for k, v in RANK.items()}
P, C, S, D = "Order Placed", "Order Confirmed", "Order Shipped", "Order Delivered"
EXPECTED = {"Confirmed": [P, C], "Shipped": [P, C, S], "Delivered": [P, C, S, D],
            "Cancelled": [P, C, "Order Cancelled"], "Returned": [P, C, S, "Order Returned"]}
HAPPY = [P, C, S, D]
ts = lambda x: pd.to_datetime(x, utc=True)
norm = lambda s: str(s).strip().lower()


NOTES = []


def detect(oms, ev, now):
    NOTES.clear()
    F = []
    def add(oid, rule, cat, sev, evidence):
        F.append(dict(order=oid, rule=rule, category=cat, base_severity=sev, evidence=evidence))
    omsi = oms.set_index("OrderId")
    for oid in sorted(set(ev.CaseId) - set(oms.OrderId)):
        add(oid, "Orphan case", "Referential integrity", "High",
            {"events": int((ev.CaseId == oid).sum()), "note": "CaseId not in OMS"})
    for _, o in oms.iterrows():
        oid, g = o.OrderId, ev[ev.CaseId == o.OrderId]
        if o.OrderAmount < 0:
            add(oid, "Negative amount", "Value correctness", "Low" if o.Status == "Cart" else "High",
                {"OrderAmount": o.OrderAmount, "Status": o.Status})
        if o.Status == "Cart":
            if len(g): add(oid, "Cart synced", "Completeness", "High", {"events": len(g)})
            continue
        if g.empty:
            add(oid, "Order missing in Analytics", "Completeness", "High",
                {"Status": o.Status, "OrderAmount": o.OrderAmount, "Currency": o.Currency}); continue
        acts = list(g.Activity)
        for a in dict.fromkeys(acts):
            if acts.count(a) > 1:
                add(oid, "Duplicate activity", "Process conformance", "Medium", {"Activity": a, "count": acts.count(a)})
        for a in EXPECTED.get(o.Status, []):
            if a not in acts:
                add(oid, "Missing activity", "Process conformance", "High" if (o.Status == "Delivered" or a == P or a == "Order Returned") else "Medium",
                    {"Status": o.Status, "missing": a, "present": acts})
        for _, e in g.drop_duplicates(["Activity", "Timestamp"]).iterrows():
            if abs(e.Amount - o.OrderAmount) > 0.005:
                add(oid, "Amount mismatch", "Value correctness", "High",
                    {"Activity": e.Activity, "OMS": o.OrderAmount, "Analytics": e.Amount, "diff": round(e.Amount - o.OrderAmount, 2)})
            if e.Currency != o.Currency:
                add(oid, "Currency mismatch", "Value correctness", "High",
                    {"Activity": e.Activity, "OMS": o.Currency, "Analytics": e.Currency})
        if norm(g.CustomerName.iloc[0]) == norm(o.CustomerName) and (g.CustomerName != o.CustomerName).any():
            NOTES.append(f"{oid}: name differs only by case/whitespace ({o.CustomerName!r} vs {g.CustomerName.iloc[0]!r}); passes contract after normalisation, not a defect.")
        elif norm(g.CustomerName.iloc[0]) != norm(o.CustomerName):
            add(oid, "Customer name mismatch", "Value correctness", "Medium",
                {"OMS": o.CustomerName, "Analytics": g.CustomerName.iloc[0]})
        for _, e in g.iterrows():
            if ts(e.Timestamp) > now:
                add(oid, "Future timestamp", "Temporal", "High", {"Activity": e.Activity, "Timestamp": e.Timestamp})
        seq = [(a, ts(t)) for a, t in zip(g.Activity, g.Timestamp) if a in HAPPY]
        seq.sort(key=lambda x: HAPPY.index(x[0]))
        if any(seq[i][1] > seq[i + 1][1] for i in range(len(seq) - 1)):
            add(oid, "Out-of-order events", "Temporal", "Medium",
                {"happy_path_order": [(a, t.isoformat()) for a, t in seq]})
        dd = g[g.Activity == D]
        if o.Status == "Delivered" and pd.notna(o.DeliveredDate) and len(dd):
            d = (ts(dd.Timestamp.iloc[0]) - ts(o.DeliveredDate)).total_seconds() / 60
            ooo = [f for f in F if f["order"] == oid and f["rule"] == "Out-of-order events"]
            if abs(d) > 1 and ooo:
                ooo[0]["evidence"]["also_delivered_differs_from_OMS"] = {"OMS_DeliveredDate": o.DeliveredDate, "Analytics_Delivered": dd.Timestamp.iloc[0], "delta_minutes": d}
            elif abs(d) > 1:
                add(oid, "Timestamp shift", "Temporal", "Medium",
                    {"OMS_DeliveredDate": o.DeliveredDate, "Analytics_Delivered": dd.Timestamp.iloc[0], "delta_minutes": d,
                     "looks_like_tz_offset": d % 30 == 0 and abs(d) <= 840})
    M = {}
    for f in F:  # collapse per-event repeats into one finding per (order, rule)
        k = (f["order"], f["rule"])
        if k in M and "Activity" in f["evidence"]:
            M[k]["evidence"]["Activity"] = str(M[k]["evidence"]["Activity"]) + ", " + str(f["evidence"]["Activity"])
        else:
            M[k] = f
    return list(M.values())


def template(f):
    e, r, o = f["evidence"], f["rule"], f["order"]
    T = {
        "Order missing in Analytics": f"{o} exists in the OMS as {e.get('Status')} ({e.get('OrderAmount')} {e.get('Currency')}) but has no events in Analytics, so it is invisible to reporting and revenue is understated.",
        "Orphan case": f"{o} appears in Analytics with {e.get('events')} events but has no OMS record, so reports include an order that does not exist in the source of truth.",
        "Amount mismatch": f"On {o}, the {e.get('Activity')} event(s) carry {e.get('Analytics')} while the OMS says {e.get('OMS')} (diff {e.get('diff')}), which looks like rounding/precision loss in the sync.",
        "Currency mismatch": f"On {o}, the {e.get('Activity')} event(s) are tagged {e.get('Analytics')} but the OMS currency is {e.get('OMS')}, so the amount is misread by every downstream metric.",
        "Timestamp shift": f"{o} Delivered time differs by {e.get('delta_minutes')} minutes between OMS ({e.get('OMS_DeliveredDate')}) and Analytics ({e.get('Analytics_Delivered')})" + (", consistent with a timezone offset applied during sync." if e.get("looks_like_tz_offset") else "."),
        "Out-of-order events": f"{o} events are not in happy-path chronological order, which breaks cycle-time and process-mining variants.",
        "Duplicate activity": f"{o} has '{e.get('Activity')}' recorded {e.get('count')} times, inflating step counts and distorting throughput.",
        "Missing activity": f"{o} is {e.get('Status')} in the OMS but Analytics lacks '{e.get('missing')}', so the path is non-conformant.",
        "Future timestamp": f"{o} '{e.get('Activity')}' is stamped {e.get('Timestamp')}, in the future, likely a date/year transformation bug.",
        "Name casing differs": f"{o} customer name differs only by case/whitespace ({e.get('OMS')} vs {e.get('Analytics')}); passes the contract once normalised.",
        "Negative amount": f"{o} has OrderAmount {e.get('OrderAmount')} in the OMS (status {e.get('Status')}); a negative amount is invalid for a real order.",
    }
    return T.get(r, f"{o}: {r} - {json.dumps(e, default=str)}")


PROMPT = """You explain data-quality defects between an Order Management System and an analytics event log.
Given ONE finding as JSON, reply with ONLY JSON: {"explanation": "<2 plain sentences for a business reader>",
"likely_cause": "<one sentence, label it a hypothesis>", "severity": "Low|Medium|High|Critical"}.
Use only facts and numbers present in the finding. Do not invent values.
FINDING: """


def call_llm(f):
    msg = PROMPT + json.dumps(f, default=str)
    model = os.getenv("EXPLAINER_MODEL", "")
    if os.getenv("ANTHROPIC_API_KEY"):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
            data=json.dumps({"model": model or "claude-sonnet-4-6", "max_tokens": 400,
                             "messages": [{"role": "user", "content": msg}]}).encode(),
            headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        out = json.load(urllib.request.urlopen(req, timeout=30))["content"][0]["text"]
    elif os.getenv("LLM_BASE_URL"):
        h = {"content-type": "application/json"}
        if os.getenv("LLM_API_KEY"): h["authorization"] = "Bearer " + os.environ["LLM_API_KEY"]
        req = urllib.request.Request(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions", method="POST",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": msg}]}).encode(), headers=h)
        out = json.load(urllib.request.urlopen(req, timeout=60))["choices"][0]["message"]["content"]
    else:
        return None
    return json.loads(re.search(r"\{.*\}", out, re.S).group(0))


def guard(f, r):
    """Return (explanation, cause, severity, flags). Never lowers severity; rejects ungrounded output."""
    flags, base = [], f["base_severity"]
    if not r or not all(k in r for k in ("explanation", "likely_cause", "severity")) or r["severity"] not in RANK:
        return template(f), "n/a (offline/template)", base, ["template_used"]
    allowed = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(f, default=str)))
    bad = [n for n in re.findall(r"\d+(?:\.\d+)?", r["explanation"] + r["likely_cause"]) if n not in allowed]
    if bad:
        return template(f), "n/a (LLM output rejected)", base, ["ungrounded_numbers:" + ",".join(bad), "template_used"]
    if RANK[r["severity"]] < RANK[base]: flags.append(f"llm_downgrade_rejected({r['severity']}->{base})")
    return r["explanation"], r["likely_cause"], NAMES[max(RANK[base], RANK[r["severity"]])], flags


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--orders", required=True); a.add_argument("--events", required=True)
    a.add_argument("--out", default="."); a.add_argument("--now", help="override 'now' (ISO UTC) for reproducibility")
    a.add_argument("--offline", action="store_true")
    x = a.parse_args()
    oms, ev = pd.read_csv(x.orders), pd.read_csv(x.events)
    now = ts(x.now) if x.now else pd.Timestamp.now(tz="UTC")
    findings = detect(oms, ev, now)
    for i, f in enumerate(findings, 1):
        f["id"] = f"F{i:02d}"
        try: r = None if x.offline else call_llm(f)
        except Exception as ex: r = None; f.setdefault("flags", []).append(f"llm_error:{type(ex).__name__}")
        f["explanation"], f["likely_cause"], f["severity"], fl = guard(f, r)
        f["flags"] = f.get("flags", []) + fl
    findings.sort(key=lambda f: (-RANK[f["severity"]], f["order"]))
    flagged = {f["order"] for f in findings}
    clean = sorted(set(oms.OrderId) - flagged)  # decided by code, never by the LLM
    os.makedirs(x.out, exist_ok=True)
    json.dump(findings, open(f"{x.out}/findings.json", "w"), indent=2, default=str)
    L = [f"# OMS vs Analytics anomaly report\n", f"Orders: {len(oms)} | Events: {len(ev)} | Findings: {len(findings)} | "
         f"Orders with no findings: {len(clean)} | Mode: {'LLM' if any('template_used' not in f['flags'] for f in findings) else 'offline templates'}\n",
         "| ID | Sev | Order | Rule | Category |", "|---|---|---|---|---|"]
    L += [f"| {f['id']} | {f['severity']} | {f['order']} | {f['rule']} | {f['category']} |" for f in findings]
    L.append("\n## Details\n")
    for f in findings:
        L += [f"**{f['id']} [{f['severity']}] {f['order']} - {f['rule']}**", f"- {f['explanation']}",
              f"- Likely cause: {f['likely_cause']}", f"- Evidence: `{json.dumps(f['evidence'], default=str)}`",
              f"- Guardrail flags: {', '.join(f['flags']) or 'none'}\n"]
    L.append("## Checked, passed after normalisation\n" + "\n".join(NOTES) + "\n")
    L.append("## Clean (no rule fired)\n" + ", ".join(clean))
    open(f"{x.out}/report.md", "w").write("\n".join(L))
    print("\n".join(L[:3 + len(findings) + 2]))


if __name__ == "__main__":
    main()
