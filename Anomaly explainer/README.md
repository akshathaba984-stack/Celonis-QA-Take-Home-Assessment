# Data-Diff Anomaly Explainer (OMS ↔ Analytics)

## What it does

You give it two CSV files:

* **OMS orders**
* **Analytics event log**

It finds the mismatches between them, gives each one a severity (**Low, Medium, High, Critical**), and explains it in plain language: what is wrong, the likely cause, and what to check next. Results can be filtered, searched by order number, and downloaded as **Excel** or **CSV**.

> **Note:** the browser version uses ready-written explanations and makes **no AI calls**. The optional LLM-assisted explanation layer is in `anomaly_explainer.py`.

It builds on the deterministic reconciliation approach from **Part C**. Fixed rules decide whether a defect exists. AI is only an explanation layer, never the source of truth.

---

## Quick start (about 30 seconds)

1. Download or clone this repo and **extract it**. Do not open files from inside a zip or an email preview.
2. Right-click **`anomaly_explainer.html`**, choose **Open with**, then Chrome, Edge, Firefox or Safari.
3. Box 1: choose `sample_data/<OMS orders file>.csv`
   Box 2: choose `sample_data/<Analytics event log file>.csv`
4. Click **Run analysis**.

**Expected result: 11 defects and 10 clean orders.**

No install, internet connection or API key is needed. The CSV files are processed in the browser and are not uploaded anywhere.

**Cannot open it locally?** Use the hosted copy: `<GitHub Pages link>`

---

## Known blockers / things a reviewer should know

* If the HTML shows as plain text or a blank page, open it with a browser (right-click, Open with). It does not work from inside a zip or an email preview.
* The browser version makes no AI calls. The LLM path exists only in `anomaly_explainer.py`, and **it was not run against a live API key** during this assessment.
* `anomaly_explainer.py` needs Python 3 and pandas:
  ```
  pip install pandas
  python anomaly_explainer.py --orders sample_data/<orders>.csv --events sample_data/<events>.csv --out out --offline
  ```
  Without `--offline`, set `ANTHROPIC_API_KEY`, or `LLM_BASE_URL` for any OpenAI-compatible endpoint such as local Ollama.
* The Python version covers the core rules only. On messy data its findings can differ slightly from the browser version. The browser version is the reference.

---

## How the AI-assisted approach works

Defect detection and AI interpretation are kept separate on purpose.

### 1. Deterministic validation (source of truth)

Fixed rules compare the two files and check for:

* Missing orders and orphan cases
* Amount and currency mismatches (exact comparison)
* Timestamp problems: future dates, wrong event order, timezone shifts
* Duplicate, missing or unexpected lifecycle events
* Customer name differences (ignoring capital letters and extra spaces)
* Unreadable values, which are reported and never skipped

Each rule has a fixed minimum severity. Because this layer is plain code, it cannot overlook a small difference like `1234.56` vs `1234.60`.

### 2. AI-assisted explanation (optional, Python script)

The LLM is given an already-detected anomaly and is used to:

* Explain the mismatch in plain language
* Suggest a likely cause (labelled as a hypothesis)
* Suggest what to check next
* Suggest a severity

Guardrails:

* The LLM can **raise** a severity but never **lower** it.
* It cannot add or remove findings. The defect list and the clean list come only from code.
* If its answer contains numbers that are not in the source data, or is badly formed, or the API call fails, the answer is discarded and the template explanation is used. The defect is still reported.

The LLM must never silently turn a real defect into a pass.

---

## Result on the sample data

**11 defects and 10 clean orders.**

| Order | Defect |
|---|---|
| ORD-1006 | Delivered order missing from Analytics |
| ORD-1007 | Amount mismatch (1234.6 vs 1234.56) |
| ORD-1008 | Currency mismatch (USD vs EUR) |
| ORD-1009 | Delivery time shifted by 5.5 hours (timezone suspected) |
| ORD-1010 | Shipped recorded after Delivered |
| ORD-1011 | Duplicate Shipped event |
| ORD-1012 | Missing Confirmed event |
| ORD-1013 | Missing Delivered event |
| ORD-1014 | Negative amount (Cart) |
| ORD-1018 | Future timestamp |
| ORD-9999 | Orphan case: in Analytics, not in the OMS |

`ORD-1015` is treated as clean: its name differs only by capital letters, which the contract allows after normalisation.

---

## Where it would fail in real life

This is a lightweight demonstration, not a production system.

* It only catches defect types that have a rule. "Clean" means no rule fired, not that the order is perfect.
* Severity ignores order value, so a very large order is treated like a small one.
* Suggested causes are hypotheses and need confirming from system logs or API traces.
* It loads everything into browser memory, so it will not cope with millions of events without a backend.
* Sending real customer or transaction data to an external LLM is a privacy risk. Use masking, an approved enterprise model, or a local model.
* The LLM should never be the only judge of whether a defect exists.

### Guardrails I would add for production

* A seeded-defect test: inject known bad rows and fail the build if any are not reported.
* Regular manual review of a sample of "clean" orders.
* Comparison against past runs, to catch defect types that have no rule yet.
* Weighting severity by order value.

---

## AI usage

Claude was used to help design and build this artifact. I reviewed the implementation and explanations against:

* The challenge's sync contract
* The Part C reconciliation rules
* The supplied sample data and its known defect list
