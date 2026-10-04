# Order-to-Cash Integration — Test Strategy & Scenario Design

## 1. Business Requirement Breakdown

The system connects an **Order Management System (OMS)** with an **Analytics Event Platform**. OMS is the source of truth, while Analytics stores the order lifecycle as events using **CaseId = OrderId**.

### Expected lifecycle

**Happy flow:** `Cart → Confirmed → Shipped → Delivered`

**Valid branches:**
- `Confirmed → Cancelled`
- `Shipped / Delivered → Returned`

Cart orders must **not** be synchronised to Analytics.

### Key business rules

- Every non-Cart order must have an **Order Placed** event.
- Delivered orders must contain **Placed → Confirmed → Shipped → Delivered**.
- Cancelled and Returned are valid terminal outcomes.
- Amount and Currency must match between OMS and Analytics.
- OrderAmount must not be negative.
- Analytics timestamps must be UTC, in lifecycle order and not future-dated.
- Every Analytics CaseId must exist as an OMS OrderId.
- CustomerName comparison should ignore case and leading/trailing spaces.

---

# 2. Test Strategy

Testing will cover **UI, API and Data**, followed by end-to-end reconciliation.

### UI / Frontend

| What I will validate | How |
|---|---|
| Order creation and mandatory fields | Create an order with valid/invalid values and verify validation |
| Order details | Verify OrderId, Customer, Amount, Currency and Status |
| Lifecycle changes | Verify valid transitions and ensure invalid transitions are blocked |
| Saved state | Refresh/reopen the order and confirm the latest values are retained |
| UI → Sync trigger | Verify a valid lifecycle change results in the expected downstream event |

**UI automation:** Automate the repeatable core order flow and key validations so that when the UI or related functionality changes, the same checks can be run automatically during regression instead of being repeated manually each time.

### Backend / API

Validate:

- Required fields, data types and request/response structure.
- Valid requests create the expected order/event.
- Missing or invalid OrderId and mandatory fields are rejected.
- Invalid amount, currency, status or timestamp is rejected/handled correctly.
- Unknown OrderId is handled correctly.
- Duplicate requests/events do not create unintended duplicates.
- A valid OMS/API change reaches Analytics correctly.

### Data Validation

Treat OMS as the source of truth and compare:

**OMS Order → OrderId → Analytics CaseId → Analytics Events**

Check:

- **Completeness:** no eligible orders/events are missing.
- **Correctness:** Amount, Currency and Customer values match.
- **Referential integrity:** every CaseId exists in OMS.
- **Process sequence:** events follow the expected lifecycle.
- **Duplicates:** no unintended repeated events.
- **Time:** timestamps are UTC, chronological and not future-dated.
- **Normalisation:** differences only in case or extra spaces are not treated as mismatches.
- **Timeliness:** events reach Analytics within the expected sync window.
- **Cart exclusion:** Cart orders do not create Analytics events.

---

# 3. If I Have Only One Hour to Test

Whenever I receive a requirement with limited testing time, I first make sure the **main business flow works without a blocker**.

1. **Environment & prerequisites:** Confirm OMS, Analytics, test data and sync are available.
2. **Core flow:** Test the main order flow from creation through the expected lifecycle.
3. **Blocker check:** If the core flow fails, identify the blocker, raise it with the development team and stop spending time on lower-priority scenarios.
4. **Smoke coverage:** If the core flow works, quickly verify the important UI, API and integration functions.
5. **P0 checks:** Validate the highest-risk areas — missing orders/events, CaseId mapping, Amount/Currency and lifecycle sequence.
6. **Negative/branch coverage:** Check Cart exclusion, Cancelled/Returned flows, invalid transitions, duplicates and key boundary cases.
7. **Final reconciliation:** Confirm OMS and Analytics agree and record any defects/evidence.

This approach ensures that limited time is spent first on **whether the product works, whether there is a blocker, and whether the core business data is trustworthy**.

---

# 4. Prioritised Test Scenarios

**P0 = Critical | P1 = High | P2 = Medium**

| ID | Layer | Scenario | Priority | Technique | Expected Result |
|---|---|---|---|---|---|
| TC-01 | E2E | Complete Cart → Confirmed → Shipped → Delivered | P0 | E2E | Flow completes and expected events are created |
| TC-02 | E2E | Complete Cart → Confirmed → Shipped → Returned | P0 | E2E | Returned flow is represented correctly |
| TC-03 | Data | Check all non-Cart OMS orders exist in Analytics | P0 | Reconciliation | No eligible order is missing |
| TC-04 | Data | Check Cart orders do not create Analytics events | P0 | Negative reconciliation | Zero Analytics events for Cart orders |
| TC-05 | Data | Check Analytics CaseId exists in OMS | P0 | ID comparison | No orphan records |
| TC-06 | Data | Compare Amount and Currency | P0 | Data comparison | Values match exactly |
| TC-07 | Data | Check Delivered event sequence | P0 | Sequence check | Placed → Confirmed → Shipped → Delivered |
| TC-08 | API | Send valid event and verify sync to Analytics | P0 | API/E2E | Event is successfully created |
| TC-09 | Data | Check event timestamps | P0 | Time validation | UTC, chronological and not future-dated |
| TC-10 | UI | Verify order details and current status | P1 | UI functional | Correct values/status displayed |
| TC-11 | UI | Attempt invalid lifecycle transition | P1 | Negative test | Invalid action is blocked/rejected |
| TC-12 | Data | Check Cancelled and Returned sequences | P1 | Sequence check | Valid terminal flow is represented correctly |
| TC-13 | Data | Detect invalid lifecycle sequence | P1 | Sequence check | Skipped/invalid event sequence is detected |
| TC-14 | Data | Detect duplicate lifecycle events | P1 | Duplicate check | Unintended duplicate is detected |
| TC-15 | API | Send request without mandatory OrderId | P1 | Negative API | Request is rejected |
| TC-16 | API | Send duplicate event with the same event details | P1 | Duplicate handling | Duplicate request does not create an unintended duplicate event |
| TC-17 | Data | Test negative OrderAmount | P1 | Boundary test | Invalid amount is rejected/not propagated |
| TC-18 | Data | Compare CustomerName ignoring case/spaces | P2 | Normalisation | Equivalent names are not mismatched |
| TC-19 | UI | Submit missing/invalid mandatory data | P2 | Boundary test | Validation is shown; order is not submitted |
| TC-20 | Data | Check sync timeliness | P2 | Timing check | Event reaches Analytics within expected window |

---

# 5. Exit Criteria / QA Sign-off

I would provide QA sign-off when:

- The core order flow works end-to-end without a blocker.
- No unresolved **P0** defects remain.
- All eligible OMS orders/events are correctly represented in Analytics.
- Cart orders are not incorrectly synchronised.
- No orphan records or unintended duplicates are found.
- Amount, Currency and Customer data are correctly reconciled.
- Lifecycle sequences and timestamps follow the business rules.
- Cancelled and Returned flows work as expected.
- Critical API negative cases are handled correctly.
- Any remaining defects are understood, documented and accepted by the relevant stakeholders.

## Quality Principle

> **A successful test is not only proving that the order works in OMS. It is proving that the same business transaction remains complete, correct and traceable from OMS → Sync/API → Analytics.**

The goal is therefore to prevent **silent data defects** — missing orders, incorrect values, wrong sequences or timestamps — from reaching the reporting and process-mining layer.