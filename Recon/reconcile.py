# ============================================================
# OMS vs Analytics reconciliation  (Order-to-Cash)
#
# Run:    python3 reconcile.py
# Needs:  orders.csv and analytics_event_log.csv in the SAME folder
# Output: DEFECT_REPORT.md (and a short summary on screen)
#
# Idea: OMS is the source of truth. For every OMS order we check
# whether Analytics has the right events, values and timestamps.
# ============================================================

import csv
from datetime import datetime, timezone

OMS_FILE = "orders.csv"
EVENTS_FILE = "analytics_event_log.csv"
REPORT_FILE = "DEFECT_REPORT.md"

# Current UTC time as text, same format as the data (used for the "no future date" rule).
# Text in this format can be compared directly: "2027-..." is bigger than "2026-..."
now_time = datetime.now(timezone.utc)
now_text = now_time.strftime("%Y-%m-%dT%H:%M:%SZ")

# ------------------------------------------------------------
# Rule tables
# ------------------------------------------------------------
# Events that MUST exist for each OMS status
required_events = {
    "Confirmed": ["Order Placed", "Order Confirmed"],
    "Shipped": ["Order Placed", "Order Confirmed", "Order Shipped"],
    "Delivered": ["Order Placed", "Order Confirmed", "Order Shipped", "Order Delivered"],
    "Cancelled": ["Order Placed", "Order Confirmed", "Order Cancelled"],
    "Returned": ["Order Placed", "Order Confirmed", "Order Shipped", "Order Returned"],
}

# Events that are allowed but not compulsory (a Returned order may or may not be Delivered first)
optional_events = {
    "Returned": ["Order Delivered"],
}

# Position of each event in the lifecycle (used to check the order of events)
step_number = {
    "Order Placed": 1,
    "Order Confirmed": 2,
    "Order Shipped": 3,
    "Order Delivered": 4,
    "Order Cancelled": 5,
    "Order Returned": 5,
}

defects = []       # real rule violations
not_defects = []   # things that look like a mismatch but are expected behaviour


def add_defect(case, category, rule, severity, how, evidence):
    """Save one defect in the defects list."""
    defect = {
        "case": case,
        "category": category,
        "rule": rule,
        "severity": severity,
        "how": how,
        "evidence": evidence,
    }
    defects.append(defect)


# ------------------------------------------------------------
# STEP 1: Read both files
# ------------------------------------------------------------
orders = []
with open(OMS_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        orders.append(row)

events = []
with open(EVENTS_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        events.append(row)

# Group Analytics events by CaseId, e.g. events_by_case["ORD-1001"] = [4 events]
events_by_case = {}
for e in events:
    case_id = e["CaseId"].strip()
    if case_id not in events_by_case:
        events_by_case[case_id] = []
    events_by_case[case_id].append(e)

# List of all OMS order ids
oms_ids = []
for o in orders:
    oms_ids.append(o["OrderId"].strip())

# ------------------------------------------------------------
# STEP 2: Check every OMS order, one by one
# ------------------------------------------------------------
ordering_flagged = []   # orders where we already reported a wrong event order

for order in orders:
    order_id = order["OrderId"].strip()
    status = order["Status"].strip()
    oms_amount = float(order["OrderAmount"])
    oms_currency = order["Currency"].strip()
    order_events = events_by_case.get(order_id, [])   # empty list if no events

    # ---- Rule: OrderAmount must not be negative (all orders, including Cart)
    if oms_amount < 0:
        if status == "Cart":
            severity = "Low"      # Cart does not sync, so low impact
        else:
            severity = "High"
        add_defect(order_id, "Value correctness (OMS source data)",
                   "OrderAmount must not be negative",
                   severity,
                   "Checked OrderAmount < 0 on every OMS row",
                   "OMS OrderAmount = " + order["OrderAmount"] + " " + oms_currency + ", Status = " + status)

    # ---- Rule: Carts do not sync
    if status == "Cart":
        if len(order_events) > 0:
            add_defect(order_id, "Completeness / sync contract",
                       "Carts do not sync to Analytics",
                       "Medium",
                       "Cart order looked up in Analytics",
                       str(len(order_events)) + " events found for a Cart order")
        else:
            # No events for a Cart is EXPECTED - not a defect
            not_defects.append([order_id, "Cart order has no Analytics events",
                                "Rule 'Carts do not sync' - this is expected behaviour"])
        continue   # nothing more to check for a Cart

    # ---- COMPLETENESS: a non-Cart order must have at least one event in Analytics
    if len(order_events) == 0:
        add_defect(order_id, "Completeness",
                   "Every non-Cart order must have at least an Order Placed event in Analytics",
                   "High",
                   "OMS OrderId looked up in Analytics CaseId - no match",
                   "OMS Status = " + status + ", Amount = " + order["OrderAmount"] + " " + oms_currency +
                   "; 0 events in Analytics (order dropped by sync)")
        continue   # no events, so the other checks make no sense

    # Make a simple list of the activity names, e.g. ["Order Placed", "Order Shipped"]
    actual = []
    for e in order_events:
        actual.append(e["Activity"].strip())

    # ---- PROCESS: duplicate events
    already_checked = []
    for step in actual:
        if step not in already_checked:
            already_checked.append(step)
            if actual.count(step) > 1:
                add_defect(order_id, "Process conformance (duplicate event)",
                           "Missing or duplicate lifecycle events must be identified",
                           "Medium",
                           "Counted how many times each activity appears per CaseId",
                           "'" + step + "' appears " + str(actual.count(step)) + " times (OMS Status = " + status + ")")

    # ---- PROCESS: missing events
    missing = []
    for step in required_events[status]:
        if step not in actual:
            missing.append(step)
    if len(missing) > 0:
        if status == "Delivered":
            severity = "High"
        else:
            severity = "Medium"
        add_defect(order_id, "Process conformance (missing event)",
                   "Delivered orders need the full happy path; every non-Cart order follows its valid lifecycle branch",
                   severity,
                   "Compared Analytics activities with expected sequence for OMS Status '" + status + "'",
                   "Missing: " + ", ".join(missing) +
                   ". Expected: " + " -> ".join(required_events[status]) +
                   ". Actual: " + " -> ".join(actual))

    # ---- PROCESS: events that should not exist for this status
    allowed = required_events[status] + optional_events.get(status, [])
    unexpected = []
    for step in actual:
        if step not in allowed and step not in unexpected:
            unexpected.append(step)
    if len(unexpected) > 0:
        add_defect(order_id, "Process conformance (unexpected event)",
                   "Every non-Cart order follows its valid lifecycle branch",
                   "Medium",
                   "Compared Analytics activities with allowed list for Status '" + status + "'",
                   "Unexpected: " + ", ".join(unexpected) + " for an OMS order in status " + status)

    # ---- VALUE: amount on every event must match OMS
    bad_amount = []
    for e in order_events:
        if float(e["Amount"]) != oms_amount:
            bad_amount.append(e)
    if len(bad_amount) > 0:
        details = []
        for e in bad_amount:
            details.append(e["Activity"] + ": Analytics " + e["Amount"] + " vs OMS " + order["OrderAmount"])
        add_defect(order_id, "Value correctness (amount)",
                   "Amount on every Analytics event must match the OMS OrderAmount exactly",
                   "High",
                   "Compared Analytics Amount with OMS OrderAmount on each event",
                   str(len(bad_amount)) + " of " + str(len(order_events)) + " events differ - " + "; ".join(details))

    # ---- VALUE: currency on every event must match OMS
    bad_currency = []
    for e in order_events:
        if e["Currency"].strip() != oms_currency:
            bad_currency.append(e)
    if len(bad_currency) > 0:
        details = []
        for e in bad_currency:
            details.append(e["Activity"] + ": " + e["Currency"])
        add_defect(order_id, "Value correctness (currency)",
                   "Currency on every Analytics event must match the OMS Currency",
                   "High",
                   "Compared Analytics Currency with OMS Currency on each event",
                   str(len(bad_currency)) + " of " + str(len(order_events)) + " events differ (OMS = " +
                   oms_currency + ") - " + "; ".join(details))

    # ---- VALUE: customer name. NORMALISE first: strip spaces + lower case
    oms_name = order["CustomerName"].strip().lower()
    name_defect_reported = False
    only_case_or_space_diff = False
    for e in order_events:
        analytics_name = e["CustomerName"].strip().lower()
        if analytics_name != oms_name:
            # Different even after normalising = real defect (report once per order)
            if name_defect_reported == False:
                add_defect(order_id, "Value correctness (customer name)",
                           "CustomerName must match after trimming and ignoring case",
                           "Medium",
                           "Compared names after strip() + lower()",
                           e["Activity"] + ": Analytics '" + e["CustomerName"] + "' vs OMS '" + order["CustomerName"] + "'")
                name_defect_reported = True
        elif e["CustomerName"] != order["CustomerName"]:
            # Same after normalising, but the raw text was different = NOT a defect
            only_case_or_space_diff = True
            raw_analytics_name = e["CustomerName"]
    if only_case_or_space_diff == True and name_defect_reported == False:
        not_defects.append([order_id,
                            "CustomerName differs only by case/spaces: OMS '" + order["CustomerName"] +
                            "' vs Analytics '" + raw_analytics_name + "'",
                            "Rule: compare CustomerName trimmed and case-insensitive - expected behaviour"])

    # ---- TIME: no timestamp may be in the future
    for e in order_events:
        if e["Timestamp"].strip() > now_text:
            add_defect(order_id, "Temporal correctness (future date)",
                       "No timestamp may be in the future",
                       "High",
                       "Compared every Analytics Timestamp with the current UTC time",
                       e["Activity"] + " timestamp " + e["Timestamp"] + " is in the future (checked at " +
                       now_time.strftime("%Y-%m-%d %H:%M") + " UTC)")

    # ---- TIME: events must be in lifecycle order when sorted by time
    # Make a list of (timestamp, step number, activity) and sort it by time
    time_list = []
    for e in order_events:
        activity = e["Activity"].strip()
        time_list.append((e["Timestamp"].strip(), step_number[activity], activity))
    time_list.sort()

    # Compare each event with the one before it. If the step number goes DOWN, the order is wrong.
    for i in range(1, len(time_list)):
        earlier = time_list[i - 1]
        later = time_list[i]
        if later[1] < earlier[1]:
            ordering_flagged.append(order_id)
            add_defect(order_id, "Temporal correctness (ordering)",
                       "Event timestamps must be non-decreasing in lifecycle order",
                       "Medium",
                       "Sorted events by Timestamp and checked the lifecycle step never goes backwards",
                       "'" + later[2] + "' (" + later[0] + ") happened BEFORE '" +
                       earlier[2] + "' (" + earlier[0] + ")")
            break   # report only the first problem for this order

    # ---- TIME / UTC: Delivered event time vs OMS DeliveredDate (both should be UTC)
    if order["DeliveredDate"].strip() != "":
        for e in order_events:
            if e["Activity"].strip() == "Order Delivered":
                oms_time = datetime.strptime(order["DeliveredDate"].strip(), "%Y-%m-%dT%H:%M:%SZ")
                analytics_time = datetime.strptime(e["Timestamp"].strip(), "%Y-%m-%dT%H:%M:%SZ")
                difference_hours = (analytics_time - oms_time).total_seconds() / 3600

                if difference_hours != 0 and abs(difference_hours) < 24:
                    # Small difference = looks like a timezone shift
                    add_defect(order_id, "Temporal correctness (timezone)",
                               "All Analytics timestamps are UTC",
                               "Medium",
                               "Compared the Order Delivered event time with OMS DeliveredDate",
                               "Analytics " + e["Timestamp"] + " vs OMS " + order["DeliveredDate"] +
                               " -> shifted by " + format(difference_hours, "+.1f") +
                               " hours (looks like a non-UTC / timezone offset)")
                elif difference_hours != 0 and order_id not in ordering_flagged:
                    # Big difference, and not already explained by the ordering defect
                    add_defect(order_id, "Temporal correctness",
                               "All Analytics timestamps are UTC",
                               "Medium",
                               "Compared the Order Delivered event time with OMS DeliveredDate",
                               "Analytics " + e["Timestamp"] + " vs OMS " + order["DeliveredDate"] +
                               " (" + format(difference_hours, "+.1f") + " hours)")

# ------------------------------------------------------------
# STEP 3: REFERENTIAL INTEGRITY - Analytics cases that have no OMS order (orphans)
# ------------------------------------------------------------
for case_id in events_by_case:
    if case_id not in oms_ids:
        case_events = events_by_case[case_id]
        names = []
        for e in case_events:
            names.append(e["Activity"])
        add_defect(case_id, "Referential integrity",
                   "Analytics must not contain an event for an OrderId that does not exist in OMS",
                   "High",
                   "Compared every distinct CaseId in Analytics against the OrderId list in OMS",
                   str(len(case_events)) + " events (" + ", ".join(names) + ") exist in Analytics, but " +
                   case_id + " is not in OMS")

# ------------------------------------------------------------
# STEP 4: Give each defect an ID and find the clean orders
# ------------------------------------------------------------
number = 1
for d in defects:
    d["id"] = "DEF-" + format(number, "02d")
    number = number + 1

defect_cases = []
for d in defects:
    defect_cases.append(d["case"])

clean_cases = []
for order_id in oms_ids:
    if order_id not in defect_cases:
        clean_cases.append(order_id)

# ------------------------------------------------------------
# STEP 5: Write DEFECT_REPORT.md and print a short summary
# ------------------------------------------------------------
notes = """
## 3. Normalisation applied
- **CustomerName**: `strip()` (remove leading/trailing spaces) and `lower()` (ignore case) on both sides before comparing. Source: business rule.
- **Timestamps**: all are UTC text like `2026-08-01T09:00:00Z`. They are compared as dates/times (same format, so text order = time order).
- **Amount**: converted from text to a number, then compared exactly (1234.56 vs 1234.6 is a mismatch).
- **Currency / CaseId / Activity**: spaces trimmed only (no case change, since no rule asks for it).

## 4. Assumptions (not stated in the rules - please confirm)
- **A1**: The OMS `DeliveredDate` is the UTC reference for the `Order Delivered` event time. A difference under 24 hours is reported as a timezone shift. A bigger difference is only reported if the ordering check has not already flagged the order.
- **A2**: A `Returned` order may or may not have passed through `Order Delivered` (OMS table allows Shipped -> Returned and Delivered -> Returned), so `Order Delivered` is optional there.
- **A3**: A `Cancelled` order is expected to have Placed -> Confirmed -> Cancelled (OMS allows Cancelled only from Confirmed).
- **A4**: The negative amount on a **Cart** order is reported as a **Low** defect. The rule says OrderAmount "must not be negative" and does not exempt Carts. It does not affect Analytics because Carts do not sync. Confirm with the business whether Cart is exempt.
- **A5**: `Order Placed` is about 5 minutes after OMS `CreatedDate` on every order. Treated as normal sync lag. No rule covers it, so it is not checked.
- **A6**: The "future" check uses the clock of the machine running the script (UTC).
- **A7**: Input files are the CSVs (`orders.csv`, `analytics_event_log.csv`) as supplied in the brief.
"""

# Which brief dimension is covered by which check: [dimension, check, start of defect category]
coverage = [
    ["Completeness", "Every non-Cart OMS order has events in Analytics", "Completeness"],
    ["Referential integrity", "Every Analytics CaseId exists in OMS", "Referential integrity"],
    ["Value correctness - amount", "Analytics Amount = OMS OrderAmount", "Value correctness (amount)"],
    ["Value correctness - currency", "Analytics Currency = OMS Currency", "Value correctness (currency)"],
    ["Value correctness - customer name", "Equal after trim + lower case", "Value correctness (customer name)"],
    ["Value correctness - negative amount", "OrderAmount >= 0", "Value correctness (OMS"],
    ["Temporal - timezone / UTC", "Delivered event time vs OMS DeliveredDate", "Temporal correctness (timezone)"],
    ["Temporal - ordering", "Lifecycle never goes backwards by time", "Temporal correctness (ordering)"],
    ["Temporal - future dates", "No timestamp after current UTC time", "Temporal correctness (future"],
    ["Process - duplicate events", "Each activity at most once", "Process conformance (duplicate"],
    ["Process - missing events", "Expected sequence for the OMS status", "Process conformance (missing"],
    ["Process - unexpected events", "No activity outside the valid branch", "Process conformance (unexpected"],
    ["Cart handling", "Carts must not sync", "Completeness / sync contract"],
]

report = open(REPORT_FILE, "w", encoding="utf-8")

report.write("# Defect Report - OMS vs Analytics Event Log reconciliation\n\n")
report.write("Generated by `reconcile.py` on " + now_time.strftime("%Y-%m-%d %H:%M") + " UTC.\n\n")

report.write("## 1. Result at a glance\n")
report.write("- OMS orders: **" + str(len(orders)) + "** | Analytics events: **" + str(len(events)) +
             "** | Analytics cases: **" + str(len(events_by_case)) + "**\n")
report.write("- Real defects: **" + str(len(defects)) + "** (across " + str(len(set(defect_cases))) + " order IDs)\n")
report.write("- Expected-behaviour items (NOT defects): **" + str(len(not_defects)) + "**\n")
report.write("- Orders with no defect: " + ", ".join(clean_cases) + "\n\n")

report.write("Validations performed: completeness, orphan cases, Cart handling, negative amount, "
             "amount, currency, customer name, duplicate events, missing events, unexpected events, "
             "future timestamps, timestamp ordering, UTC/timezone check.\n\n")

report.write("### Coverage of the brief's validation dimensions\n\n")
report.write("| Dimension | Check performed | Defects found |\n|---|---|---|\n")
for item in coverage:
    found = []
    for d in defects:
        if d["category"].startswith(item[2]):
            found.append(d["id"])
    if len(found) > 0:
        found_text = ", ".join(found)
    else:
        found_text = "None found (check ran, data clean)"
    report.write("| " + item[0] + " | " + item[1] + " | " + found_text + " |\n")

report.write("\n## 2. Defects\n\n")
report.write("| ID | Case / Order | Category | Rule violated | Severity | How detected | Evidence |\n")
report.write("|---|---|---|---|---|---|---|\n")
for d in defects:
    report.write("| " + d["id"] + " | " + d["case"] + " | " + d["category"] + " | " + d["rule"] + " | " +
                 d["severity"] + " | " + d["how"] + " | " + d["evidence"] + " |\n")

report.write("\n### Expected behaviour - deliberately NOT reported as defects\n\n")
report.write("| Case / Order | Observation | Why it is not a defect |\n|---|---|---|\n")
for item in not_defects:
    report.write("| " + item[0] + " | " + item[1] + " | " + item[2] + " |\n")

report.write(notes)
report.close()

# Short summary on screen
print("Orders: " + str(len(orders)) + " | Events: " + str(len(events)))
print("Real defects: " + str(len(defects)) + " | Expected behaviour (not defects): " + str(len(not_defects)))
print("")
for d in defects:
    print(d["id"] + "  " + d["case"] + "  " + d["severity"] + "  " + d["category"])
    print("        " + d["evidence"])
print("")
print("NOT defects:")
for item in not_defects:
    print("  " + item[0] + ": " + item[1])
print("")
print("Report written to " + REPORT_FILE)
