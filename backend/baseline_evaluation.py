"""
baseline_evaluation.py
======================
Phase 3 — Baseline Evaluation Script
Project: Shared-Account Elimination Workflow Using Accountable Delegation
         and Session Attribution

What this script does
─────────────────────
Reads the two synthetic datasets and evaluates the BASELINE scenario:
  • system_logs.csv       → represents the legacy environment (no attribution)
  • privileged_actions.csv → represents the Review-1 prototype (with attribution)

Calculates
──────────
  Baseline (legacy shared-account environment)
    • Total sensitive actions
    • Individually attributable actions  → always 0 in the baseline
    • Shared-account-attributed actions → shared account is the only identity known
    • Unattributed actions
    • Individual Attribution Rate (IAR)  = individually_attributable / total × 100

  Prototype (Review-1 delegation workflow) — for comparison only
    • Same metrics, computed from privileged_actions.csv

Outputs
───────
  baseline_results.json   — machine-readable results
  baseline_report.html    — visual chart and table (open in any browser)
  (console)               — plain-text summary report

Run
───
  cd backend
  python baseline_evaluation.py

  # or specify a custom data directory
  python baseline_evaluation.py --data ./data --out ./results
"""

import csv
import json
import os
import argparse
from datetime import datetime

# ── Default paths ─────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(BASE_DIR, "data")
DEFAULT_OUT  = BASE_DIR                          # same folder as this script

# ── Sensitivity levels that count as "sensitive" ──────────────────────────────
SENSITIVE_LEVELS = {"HIGH", "CRITICAL"}

# ── Attribution status values in privileged_actions.csv ───────────────────────
STATUS_ATTRIBUTED = "ATTRIBUTED"
STATUS_UNATTR     = "UNATTRIBUTED"
STATUS_DENIED     = "PERMISSION_DENIED"


# ═════════════════════════════════════════════════════════════════════════════
# 1.  READ CSV
# ═════════════════════════════════════════════════════════════════════════════

def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ═════════════════════════════════════════════════════════════════════════════
# 2.  BASELINE ANALYSIS  (system_logs.csv)
# ═════════════════════════════════════════════════════════════════════════════

def analyse_baseline(logs: list[dict]) -> dict:
    """
    In the baseline environment, individual_identified is ALWAYS 'NO'.
    The system knows the shared account but cannot identify the individual.

    Rules applied here:
      - "Sensitive" = sensitivity in {HIGH, CRITICAL}
      - "Individually attributable" = individual_identified == 'YES'
        (will always be 0 in the baseline dataset by design)
      - "Shared-account attributed" = sensitive action where only the shared
        account is known (individual_identified == 'NO')
      - "Unattributed" = log_status in {ANONYMOUS_ACTION, WEAK_EVIDENCE}
        (no shared account identity either — e.g. no badge, no session token)
    """
    all_logs          = logs
    sensitive_logs    = [l for l in logs if l.get("sensitivity","").upper() in SENSITIVE_LEVELS]

    # Individual attribution: never happens in baseline
    individually_attr = [l for l in sensitive_logs
                         if l.get("individual_identified","NO").upper() == "YES"]

    # Shared account is the only identity known
    shared_acct_attr  = [l for l in sensitive_logs
                         if l.get("individual_identified","NO").upper() == "NO"
                         and l.get("log_status","") not in {"ANONYMOUS_ACTION","WEAK_EVIDENCE"}]

    # Truly unattributed — not even a shared account can be confirmed
    unattributed      = [l for l in sensitive_logs
                         if l.get("log_status","") in {"ANONYMOUS_ACTION","WEAK_EVIDENCE"}]

    # Permission denied (logged but blocked)
    perm_denied       = [l for l in sensitive_logs
                         if l.get("log_status","") == "PERMISSION_DENIED"]

    total   = len(sensitive_logs)
    ind_n   = len(individually_attr)
    shared_n= len(shared_acct_attr)
    unattr_n= len(unattributed)
    denied_n= len(perm_denied)

    iar = round(ind_n / total * 100, 2) if total > 0 else 0.0

    # Per-account breakdown
    account_breakdown = {}
    for log in sensitive_logs:
        acct = log.get("shared_account_id","UNKNOWN")
        app  = log.get("application","UNKNOWN")
        key  = f"{acct} ({app})"
        if key not in account_breakdown:
            account_breakdown[key] = {"total":0, "individually_attr":0, "shared_attr":0, "unattr":0}
        account_breakdown[key]["total"] += 1
        if log.get("individual_identified","NO").upper() == "YES":
            account_breakdown[key]["individually_attr"] += 1
        elif log.get("log_status","") in {"ANONYMOUS_ACTION","WEAK_EVIDENCE"}:
            account_breakdown[key]["unattr"] += 1
        else:
            account_breakdown[key]["shared_attr"] += 1

    # Sensitivity distribution
    high_count     = sum(1 for l in sensitive_logs if l.get("sensitivity","").upper() == "HIGH")
    critical_count = sum(1 for l in sensitive_logs if l.get("sensitivity","").upper() == "CRITICAL")

    return {
        "mode":                        "BASELINE (Legacy Shared-Account Environment)",
        "evaluated_at":                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_log_records":           len(all_logs),
        "total_sensitive_actions":     total,
        "individually_attributable":   ind_n,
        "shared_account_attributed":   shared_n,
        "unattributed":                unattr_n,
        "permission_denied":           denied_n,
        "individual_attribution_rate": iar,
        "sensitivity_breakdown": {
            "high":     high_count,
            "critical": critical_count,
        },
        "account_breakdown": account_breakdown,
        "finding": (
            "In the baseline environment, ZERO sensitive actions can be attributed "
            "to an individual. The system identifies only the shared account. "
            "This means individual accountability is impossible."
        ),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 3.  PROTOTYPE ANALYSIS  (privileged_actions.csv)
# ═════════════════════════════════════════════════════════════════════════════

def analyse_prototype(actions: list[dict]) -> dict:
    """
    In the prototype, each action is linked to a delegation session which
    binds the individual identity to the shared account via a token.
    """
    all_actions    = actions
    sensitive_acts = [a for a in actions if a.get("sensitivity","").upper() in SENSITIVE_LEVELS]

    individually_attr = [a for a in sensitive_acts
                         if a.get("attribution_status","") == STATUS_ATTRIBUTED]
    unattributed      = [a for a in sensitive_acts
                         if a.get("attribution_status","") == STATUS_UNATTR]
    perm_denied       = [a for a in sensitive_acts
                         if a.get("attribution_status","") == STATUS_DENIED]

    total  = len(sensitive_acts)
    ind_n  = len(individually_attr)
    unattr = len(unattributed)
    denied = len(perm_denied)

    iar = round(ind_n / total * 100, 2) if total > 0 else 0.0

    # Confidence breakdown
    confidence_counts = {"HIGH":0, "MEDIUM":0, "LOW":0, "N/A":0}
    for a in individually_attr:
        conf = a.get("attribution_confidence","HIGH").upper()
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    # Scenario breakdown
    scenario_counts = {}
    for a in sensitive_acts:
        tag = a.get("scenario_tag","normal")
        scenario_counts[tag] = scenario_counts.get(tag, 0) + 1

    high_count     = sum(1 for a in sensitive_acts if a.get("sensitivity","").upper() == "HIGH")
    critical_count = sum(1 for a in sensitive_acts if a.get("sensitivity","").upper() == "CRITICAL")

    return {
        "mode":                        "PROTOTYPE (Accountable Delegation Workflow)",
        "evaluated_at":                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_action_records":        len(all_actions),
        "total_sensitive_actions":     total,
        "individually_attributable":   ind_n,
        "shared_account_attributed":   0,     # no longer needed in prototype
        "unattributed":                unattr,
        "permission_denied":           denied,
        "individual_attribution_rate": iar,
        "sensitivity_breakdown": {
            "high":     high_count,
            "critical": critical_count,
        },
        "confidence_breakdown": confidence_counts,
        "scenario_breakdown": scenario_counts,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 4.  PRINT REPORT
# ═════════════════════════════════════════════════════════════════════════════

def print_report(baseline: dict, prototype: dict) -> None:
    sep = "=" * 62

    print(f"\n{sep}")
    print(f"  PHASE 3 -- BASELINE EVALUATION REPORT")
    print(f"  Project: Shared-Account Elimination Workflow")
    print(f"  Evaluated: {baseline['evaluated_at']}")
    print(sep)

    print(f"\n  SECTION 1 -- BASELINE (Legacy Environment)")
    print("  " + "-" * 58)
    b = baseline
    print(f"  Total log records           : {b['total_log_records']}")
    print(f"  Total sensitive actions     : {b['total_sensitive_actions']}")
    print(f"    Severity HIGH             : {b['sensitivity_breakdown']['high']}")
    print(f"    Severity CRITICAL         : {b['sensitivity_breakdown']['critical']}")
    print(f"  Individually attributable   : {b['individually_attributable']}")
    print(f"  Shared-account attributed   : {b['shared_account_attributed']}")
    print(f"  Unattributed (anonymous)    : {b['unattributed']}")
    print(f"  Permission denied           : {b['permission_denied']}")
    print()
    print(f"  Individual Attribution Rate : {b['individual_attribution_rate']}%")
    print()
    print(f"  Finding:")
    for line in b["finding"].split("."):
        line = line.strip()
        if line:
            print(f"    {line}.")

    print(f"\n  SECTION 2 -- PROTOTYPE (Delegation Workflow)")
    print("  " + "-" * 58)
    p = prototype
    print(f"  Total action records        : {p['total_action_records']}")
    print(f"  Total sensitive actions     : {p['total_sensitive_actions']}")
    print(f"    Severity HIGH             : {p['sensitivity_breakdown']['high']}")
    print(f"    Severity CRITICAL         : {p['sensitivity_breakdown']['critical']}")
    print(f"  Individually attributable   : {p['individually_attributable']}")
    print(f"  Unattributed                : {p['unattributed']}")
    print(f"  Permission denied           : {p['permission_denied']}")
    print()
    print(f"  Individual Attribution Rate : {p['individual_attribution_rate']}%")

    improvement = round(p["individual_attribution_rate"] - b["individual_attribution_rate"], 2)

    print(f"\n  SECTION 3 -- IMPROVEMENT (Baseline -> Prototype)")
    print("  " + "-" * 58)
    bar_len  = 50
    b_filled = int(b["individual_attribution_rate"] / 100 * bar_len)
    p_filled = int(p["individual_attribution_rate"] / 100 * bar_len)
    print(f"  Baseline  [{('#' * b_filled).ljust(bar_len)}] {b['individual_attribution_rate']:6.2f}%")
    print(f"  Prototype [{('#' * p_filled).ljust(bar_len)}] {p['individual_attribution_rate']:6.2f}%")
    print()
    print(f"  IAR improvement : +{improvement}%")
    print()

    print("  SECTION 4 — PER ACCOUNT BREAKDOWN (Baseline)")
    print("  " + "-" * 58)
    print(f"  {'Account':<30} {'Total':>6} {'Indiv':>6} {'Shared':>7} {'Unatr':>6}")
    print(f"  {'-'*30} {'-'*6} {'-'*6} {'-'*7} {'-'*6}")
    for acct, counts in sorted(b["account_breakdown"].items()):
        print(f"  {acct:<30} {counts['total']:>6} "
              f"{counts['individually_attr']:>6} "
              f"{counts['shared_attr']:>7} "
              f"{counts['unattr']:>6}")

    print(f"\n{sep}\n")


# ═════════════════════════════════════════════════════════════════════════════
# 5.  SAVE JSON
# ═════════════════════════════════════════════════════════════════════════════

def save_json(baseline: dict, prototype: dict, out_dir: str) -> str:
    improvement = round(
        prototype["individual_attribution_rate"] - baseline["individual_attribution_rate"], 2
    )

    results = {
        "project": "Shared-Account Elimination Workflow — Review 1",
        "phase":   "Phase 3 — Baseline Evaluation",
        "baseline":  baseline,
        "prototype": prototype,
        "comparison": {
            "baseline_iar":  baseline["individual_attribution_rate"],
            "prototype_iar": prototype["individual_attribution_rate"],
            "improvement":   improvement,
            "verdict": (
                "The baseline shows 0% individual attribution. "
                f"The Review-1 prototype achieves {prototype['individual_attribution_rate']}% IAR, "
                f"an improvement of +{improvement} percentage points."
            ),
        },
    }

    path = os.path.join(out_dir, "baseline_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"  Saved  ->  {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 6.  GENERATE HTML CHART REPORT
# ═════════════════════════════════════════════════════════════════════════════

def save_html_report(baseline: dict, prototype: dict, out_dir: str) -> str:
    b_iar    = baseline["individual_attribution_rate"]
    p_iar    = prototype["individual_attribution_rate"]
    b_unattr = round(100 - b_iar, 2)
    p_unattr = round(100 - p_iar, 2)
    improv   = round(p_iar - b_iar, 2)

    b_total = baseline["total_sensitive_actions"]
    p_total = prototype["total_sensitive_actions"]

    # Account breakdown rows
    acct_rows = ""
    for acct, counts in sorted(baseline["account_breakdown"].items()):
        acct_rows += f"""
        <tr>
          <td>{acct}</td>
          <td>{counts['total']}</td>
          <td class="red">{counts['individually_attr']}</td>
          <td>{counts['shared_attr']}</td>
          <td class="amber">{counts['unattr']}</td>
        </tr>"""

    # Scenario rows
    scen_rows = ""
    for tag, count in sorted(prototype.get("scenario_breakdown",{}).items()):
        scen_rows += f"<tr><td>{tag}</td><td>{count}</td></tr>"

    # Computed percentages needed inside the f-string
    sa_pct = round(baseline['shared_account_attributed'] / b_total * 100, 1) if b_total else 0
    ua_pct = round(baseline['unattributed'] / b_total * 100, 1) if b_total else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Phase 3 — Baseline Evaluation | SharedGuard</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  :root{{
    --bg:#0a0d14; --surface:#111827; --card:#1a2235; --border:#1e2d45;
    --blue:#3b82f6; --cyan:#06b6d4; --green:#10b981;
    --amber:#f59e0b; --red:#ef4444; --purple:#8b5cf6;
    --text:#f1f5f9; --muted:#94a3b8; --dim:#475569;
    --mono:'JetBrains Mono',monospace; --sans:'Inter',sans-serif;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:var(--sans);
        font-size:14px;line-height:1.6;padding:32px;min-height:100vh}}
  h1{{font-size:26px;font-weight:800;margin-bottom:4px;
      background:linear-gradient(90deg,var(--blue),var(--cyan));
      -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  h2{{font-size:15px;font-weight:700;color:var(--muted);margin:28px 0 14px;
      text-transform:uppercase;letter-spacing:.07em}}
  .subtitle{{color:var(--muted);font-size:13px;margin-bottom:32px}}
  .grid{{display:grid;gap:18px;margin-bottom:24px}}
  .g2{{grid-template-columns:1fr 1fr}}
  .g3{{grid-template-columns:1fr 1fr 1fr}}
  .g4{{grid-template-columns:repeat(4,1fr)}}
  .card{{background:var(--card);border:1px solid var(--border);
         border-radius:14px;padding:22px}}
  .stat-val{{font-size:42px;font-weight:800;line-height:1;margin-bottom:4px}}
  .stat-lbl{{font-size:12px;color:var(--muted);font-weight:500}}
  .red{{color:#f87171}}.green{{color:#34d399}}.amber{{color:#fbbf24}}
  .blue{{color:#60a5fa}}.cyan{{color:#67e8f9}}
  .chart-wrap{{position:relative;height:260px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  thead th{{background:rgba(255,255,255,.03);padding:10px 12px;text-align:left;
            font-size:11px;font-weight:600;text-transform:uppercase;
            letter-spacing:.06em;color:var(--dim);border-bottom:1px solid var(--border)}}
  tbody tr{{border-bottom:1px solid rgba(255,255,255,.04)}}
  tbody tr:hover{{background:rgba(255,255,255,.025)}}
  tbody td{{padding:10px 12px;color:var(--muted)}}
  tbody td:first-child{{color:var(--text);font-weight:500}}
  .badge{{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:600}}
  .b-red{{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.25)}}
  .b-green{{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.25)}}
  .b-amber{{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.25)}}
  .b-blue{{background:rgba(59,130,246,.15);color:#60a5fa;border:1px solid rgba(59,130,246,.25)}}
  .formula{{background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:10px;
            padding:16px 20px;font-family:var(--mono);font-size:13px;
            color:var(--muted);margin-bottom:24px;line-height:2}}
  .formula strong{{color:var(--text);font-size:15px}}
  .improv-box{{text-align:center;padding:36px;}}
  .improv-val{{font-size:80px;font-weight:800;line-height:1;
               background:linear-gradient(90deg,var(--green),var(--cyan));
               -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .progress{{height:8px;background:rgba(255,255,255,.06);border-radius:99px;
             overflow:hidden;margin-top:10px}}
  .progress-fill{{height:100%;border-radius:99px}}
  footer{{margin-top:40px;text-align:center;color:var(--dim);font-size:12px}}
</style>
</head>
<body>

<h1>Phase 3 — Baseline Evaluation</h1>
<p class="subtitle">
  Project: Shared-Account Elimination Workflow &nbsp;|&nbsp;
  Generated: {baseline['evaluated_at']} &nbsp;|&nbsp; Review 1
</p>

<!-- Metric formula -->
<div class="formula">
  <strong>Individual Attribution Rate (IAR)</strong><br/>
  IAR = Individually Attributable Sensitive Actions &divide; Total Sensitive Actions &times; 100
</div>

<!-- IAR Comparison Cards -->
<h2>IAR Comparison — Baseline vs Prototype</h2>
<div class="grid g2">
  <div class="card">
    <div class="stat-lbl">&#10060; Baseline — Legacy Shared-Account Environment</div>
    <div class="stat-val red" style="margin-top:12px">{b_iar:.2f}%</div>
    <div class="stat-lbl" style="margin-top:6px">
      {baseline['individually_attributable']} of {b_total} sensitive actions individually attributed
    </div>
    <div class="progress" style="margin-top:14px">
      <div class="progress-fill" style="width:{b_iar}%;background:var(--red)"></div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--dim)">
      The system can only record the <strong style="color:var(--amber)">shared account</strong>.
      Individual identity is unknown.
    </div>
  </div>
  <div class="card">
    <div class="stat-lbl">&#9989; Prototype — Accountable Delegation Workflow</div>
    <div class="stat-val green" style="margin-top:12px">{p_iar:.2f}%</div>
    <div class="stat-lbl" style="margin-top:6px">
      {prototype['individually_attributable']} of {p_total} sensitive actions individually attributed
    </div>
    <div class="progress" style="margin-top:14px">
      <div class="progress-fill" style="width:{p_iar}%;background:linear-gradient(90deg,var(--green),var(--cyan))"></div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--dim)">
      Every action is linked to an individual via a
      <strong style="color:var(--cyan)">delegation token</strong>.
    </div>
  </div>
</div>

<!-- Stat Cards -->
<h2>Baseline — Sensitive Action Breakdown</h2>
<div class="grid g4">
  <div class="card">
    <div class="stat-val blue">{b_total}</div>
    <div class="stat-lbl">Total Sensitive Actions<br/>(HIGH + CRITICAL)</div>
  </div>
  <div class="card">
    <div class="stat-val red">0</div>
    <div class="stat-lbl">Individually Attributable<br/>(IAR = 0%)</div>
  </div>
  <div class="card">
    <div class="stat-val amber">{baseline['shared_account_attributed']}</div>
    <div class="stat-lbl">Shared-Account Attributed<br/>(identity unknown)</div>
  </div>
  <div class="card">
    <div class="stat-val" style="color:var(--purple)">{baseline['unattributed']}</div>
    <div class="stat-lbl">Unattributed<br/>(anonymous / weak evidence)</div>
  </div>
</div>

<!-- Charts -->
<h2>Visual Comparison</h2>
<div class="grid g2">
  <div class="card">
    <div style="font-size:12px;font-weight:600;color:var(--dim);margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em">
      Baseline — Attribution Distribution
    </div>
    <div class="chart-wrap">
      <canvas id="baselineDonut"></canvas>
    </div>
  </div>
  <div class="card">
    <div style="font-size:12px;font-weight:600;color:var(--dim);margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em">
      IAR Comparison (Baseline vs Prototype)
    </div>
    <div class="chart-wrap">
      <canvas id="iarBar"></canvas>
    </div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <div style="font-size:12px;font-weight:600;color:var(--dim);margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em">
      Baseline — Sensitivity Breakdown
    </div>
    <div class="chart-wrap">
      <canvas id="sensitivityBar"></canvas>
    </div>
  </div>
  <div class="card">
    <div style="font-size:12px;font-weight:600;color:var(--dim);margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em">
      Prototype — Attribution Confidence
    </div>
    <div class="chart-wrap">
      <canvas id="confidenceBar"></canvas>
    </div>
  </div>
</div>

<!-- Improvement banner -->
<h2>Improvement</h2>
<div class="card improv-box">
  <div style="font-size:14px;color:var(--muted);margin-bottom:8px">
    IAR Improvement (Baseline &#8594; Prototype)
  </div>
  <div class="improv-val">+{improv}%</div>
  <div style="margin-top:14px;font-size:14px;color:var(--muted)">
    From <strong style="color:var(--red)">{b_iar}%</strong> to
    <strong style="color:var(--green)">{p_iar}%</strong>
  </div>
</div>

<!-- Per-account baseline table -->
<h2>Baseline — Per Shared Account Breakdown</h2>
<div class="card">
  <table>
    <thead>
      <tr>
        <th>Shared Account</th>
        <th>Total Sensitive</th>
        <th>Individually Attr.</th>
        <th>Shared-Acct Attr.</th>
        <th>Unattributed</th>
      </tr>
    </thead>
    <tbody>
      {acct_rows}
    </tbody>
  </table>
</div>

<!-- Prototype scenario table -->
<h2>Prototype — Scenario Breakdown</h2>
<div class="card">
  <table>
    <thead>
      <tr><th>Scenario Tag</th><th>Sensitive Actions</th></tr>
    </thead>
    <tbody>
      {scen_rows}
    </tbody>
  </table>
</div>

<!-- Baseline problem statement -->
<h2>Why the Baseline Fails</h2>
<div class="card" style="padding:24px 28px">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px">
    <div>
      <div style="font-size:20px;margin-bottom:8px">&#128272;</div>
      <div style="font-weight:700;margin-bottom:6px">Shared Credentials</div>
      <div style="color:var(--muted);font-size:13px">
        Multiple employees share one login. When a sensitive action is logged,
        only the shared account name is recorded.
      </div>
    </div>
    <div>
      <div style="font-size:20px;margin-bottom:8px">&#9888;&#65039;</div>
      <div style="font-weight:700;margin-bottom:6px">Zero Individual Accountability</div>
      <div style="color:var(--muted);font-size:13px">
        IAR = 0%. It is impossible to determine <em>which</em> person
        approved a payment or deleted a record.
      </div>
    </div>
    <div>
      <div style="font-size:20px;margin-bottom:8px">&#128202;</div>
      <div style="font-weight:700;margin-bottom:6px">Audit Gap</div>
      <div style="color:var(--muted);font-size:13px">
        {baseline['shared_account_attributed']} HIGH/CRITICAL actions are
        attributed only to a shared account. Investigators cannot identify the responsible individual.
      </div>
    </div>
  </div>
</div>

<footer>
  SharedGuard &mdash; Review 1 Prototype &nbsp;&bull;&nbsp;
  Shared-Account Elimination Workflow &nbsp;&bull;&nbsp;
  Phase 3 Baseline Evaluation
</footer>

<script>
const OPTS = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{
    legend: {{ labels: {{ color: '#94a3b8', font: {{ family: 'Inter', size: 12 }}, boxWidth: 12, padding: 14 }} }},
    tooltip: {{ backgroundColor: '#1a2235', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: '#1e2d45', borderWidth: 1 }}
  }}
}};

// Baseline donut
new Chart(document.getElementById('baselineDonut'), {{
  type: 'doughnut',
  data: {{
    labels: ['Individually Attributed ({b_iar}%)', 'Shared-Account Only ({sa_pct:.1f}%)', 'Unattributed ({ua_pct:.1f}%)'],
    datasets: [{{
      data: [{baseline['individually_attributable']}, {baseline['shared_account_attributed']}, {baseline['unattributed']}],
      backgroundColor: ['#10b98133','#f59e0b33','#ef444433'],
      borderColor:     ['#10b981',  '#f59e0b',  '#ef4444'],
      borderWidth: 2, hoverOffset: 4
    }}]
  }},
  options: {{ ...OPTS, cutout: '68%' }}
}});

// IAR comparison bar
new Chart(document.getElementById('iarBar'), {{
  type: 'bar',
  data: {{
    labels: ['Baseline\\n(Legacy)', 'Prototype\\n(Delegation)'],
    datasets: [{{
      label: 'IAR %',
      data: [{b_iar}, {p_iar}],
      backgroundColor: ['#ef444433','#10b98133'],
      borderColor:     ['#ef4444',  '#10b981'],
      borderWidth: 2, borderRadius: 8
    }}]
  }},
  options: {{
    ...OPTS,
    plugins: {{ ...OPTS.plugins, legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ min:0, max:100, grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8', callback: v => v + '%' }} }}
    }}
  }}
}});

// Sensitivity bar
new Chart(document.getElementById('sensitivityBar'), {{
  type: 'bar',
  data: {{
    labels: ['HIGH', 'CRITICAL'],
    datasets: [{{
      label: 'Baseline Sensitive Actions',
      data: [{baseline['sensitivity_breakdown']['high']}, {baseline['sensitivity_breakdown']['critical']}],
      backgroundColor: ['#f59e0b33','#ef444433'],
      borderColor:     ['#f59e0b',  '#ef4444'],
      borderWidth: 2, borderRadius: 6
    }}]
  }},
  options: {{
    ...OPTS,
    plugins: {{ ...OPTS.plugins, legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8' }} }}
    }}
  }}
}});

// Confidence bar (prototype)
const conf = {json.dumps(prototype.get('confidence_breakdown', {}))};
new Chart(document.getElementById('confidenceBar'), {{
  type: 'bar',
  data: {{
    labels: Object.keys(conf),
    datasets: [{{
      label: 'Attribution Confidence',
      data: Object.values(conf),
      backgroundColor: ['#10b98133','#3b82f633','#f59e0b33','#47556933'],
      borderColor:     ['#10b981',  '#3b82f6',  '#f59e0b',  '#475569'],
      borderWidth: 2, borderRadius: 6
    }}]
  }},
  options: {{
    ...OPTS,
    plugins: {{ ...OPTS.plugins, legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ color: 'rgba(255,255,255,.04)' }}, ticks: {{ color: '#94a3b8' }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""

    path = os.path.join(out_dir, "baseline_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved  ->  {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 7.  MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main(data_dir: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    logs_path    = os.path.join(data_dir, "system_logs.csv")
    actions_path = os.path.join(data_dir, "privileged_actions.csv")

    # Guard
    for p in [logs_path, actions_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    print("\nReading datasets ...")
    logs    = read_csv(logs_path)
    actions = read_csv(actions_path)
    print(f"  system_logs.csv        : {len(logs)} records")
    print(f"  privileged_actions.csv : {len(actions)} records")

    print("\nRunning baseline analysis ...")
    baseline  = analyse_baseline(logs)

    print("Running prototype analysis (for comparison) ...")
    prototype = analyse_prototype(actions)

    print_report(baseline, prototype)

    print("Writing output files ...")
    save_json(baseline, prototype, out_dir)
    save_html_report(baseline, prototype, out_dir)

    print(f"""
Done.
  baseline_results.json  ->  open with any JSON viewer
  baseline_report.html   ->  open in Chrome / Edge / Firefox

Key result
  Baseline IAR  = {baseline['individual_attribution_rate']}%
  Prototype IAR = {prototype['individual_attribution_rate']}%
  Improvement   = +{round(prototype['individual_attribution_rate'] - baseline['individual_attribution_rate'], 2)}%
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 3 — Baseline Evaluation Script"
    )
    parser.add_argument(
        "--data", default=DEFAULT_DATA,
        help="Directory containing system_logs.csv and privileged_actions.csv"
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUT,
        help="Directory for baseline_results.json and baseline_report.html"
    )
    args = parser.parse_args()
    main(args.data, args.out)
