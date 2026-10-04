# Order-to-Cash (OMS ↔ Analytics) Quality & AI Engineering Suite

This repository contains my submission for the **AI Engineer – Quality** take-home assessment.

The work covers test strategy, UI automation, integration data validation, performance strategy, and an AI-assisted quality artifact. My approach was to apply QA judgement and requirement understanding first, and use AI to accelerate implementation and exploration where appropriate.

## Project Map

| Part | Location | Purpose |
|---|---|---|
| **A** | `STRATEGY.md` | Test strategy, risk analysis, scenarios, and coverage across UI, API, and data |
| **B** | `demoblaze-playwright/` | Playwright-based UI automation for the DemoBlaze application |
| **C** | `Recon/` | OMS ↔ Analytics reconciliation and defect reporting |
| **D** | `PERFORMANCE.md` | Performance, load, stress, and soak testing strategy |
| **E1** | `AI_WORKLOG.md` | AI tools used, prompts, outputs, limitations, and human evaluation |
| **E2** | `Anomaly explainer/` | AI-assisted data-diff anomaly explanation artifact |

---

## Quick Start

### Part A — Test Strategy

Open:

```text
STRATEGY.md
```

This is a documentation-only deliverable and requires no setup.

---

### Part B — Playwright Automation

Navigate to:

```text
demoblaze-playwright/
```

The folder contains its own README with setup, execution, and reporting instructions.

Typical setup and execution:

```bash
cd demoblaze-playwright
npm install
npx playwright install chromium
npm test
```

The detailed test coverage and reporting instructions are available in the folder's `README.md`.

---

### Part C — Integration Data Validation

Navigate to:

```text
Recon/
```

Contents:

```text
Recon/
├── Reconcile.py
├── Defect_Report.md
├── <OMS orders CSV>
└── <Analytics event log CSV>
```

- `Reconcile.py` contains the reconciliation logic.
- The two CSV files are the input datasets.
- `Defect_Report.md` contains the identified findings and defect details.

---

### Part D — Performance Strategy

Open:

```text
PERFORMANCE.md
```

This contains the proposed workload model, performance scenarios, SLIs/SLOs, test types, and execution approach.

---

### Part E1 — AI Work Log

Open:

```text
AI_WORKLOG.md
```

This documents how AI was used across the assessment, including where it helped, where it fell short, and how QA judgement was kept in the process.

---

### Part E2 — AI-Assisted Quality Artifact

Navigate to:

```text
Anomaly explainer/
```

Contents:

```text
Anomaly explainer/
├── anomaly_explainer.html
├── anomaly_explainer.py
└── README.md
```

For the simplest demonstration, open:

```text
Anomaly explainer/anomaly_explainer.html
```

The browser-based version can be run locally without installation, an API key, or internet access.

For the optional LLM-assisted path and additional details, refer to the folder's `README.md`.

---

## Headline Approach

### QA Ownership

My core strength is **QA analysis, requirement understanding, and problem solving**. Given a requirement or business workflow, I can build the test approach, identify risks, challenge the happy path, break the process from different angles, identify defects, and assess whether the expected behaviour is actually being met.

I applied this approach across the assessment, including the Order-to-Cash workflow, integration data validation, performance considerations, and AI-assisted quality engineering.

### AI as an Accelerator

I used AI extensively to accelerate implementation and explore solutions. I provided the requirements, business context, expected quality criteria, and direction through prompts, while keeping human QA evaluation in the loop rather than blindly accepting AI output.

### Human Validation Before AI Interpretation

For the integration data validation and anomaly-explainer work, I first understood the data contract and manually determined what should be considered a valid finding, including the expected defect types and severity.

AI was then used to help implement and explain that approach. It was **not treated as the authority for deciding whether the underlying data was correct**.

### Playwright Experience

The Playwright portion represents my practical hands-on application of automation to the assessment. While my existing strength is in QA analysis and manual/conversational testing, I used this exercise to build practical Playwright experience while applying the same principles of requirement analysis, scenario coverage, assertions, and defect identification.

### Practical Scope

The implementation is intentionally assessment-sized rather than positioned as a production-ready framework. Assumptions, limitations, and known failure modes are documented where relevant.

## Reproducibility

Each major part is either directly runnable from the repository or includes supporting documentation with its execution details.

Any optional AI path requiring external model/API configuration has its dependencies and validation status documented separately.
