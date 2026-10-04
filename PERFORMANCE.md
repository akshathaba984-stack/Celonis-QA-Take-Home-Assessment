# Performance Test Plan

## 1. Objective

The purpose of this test is to check how the Order-to-Cash sync API behaves when it receives different levels of order/event traffic.

The main things I want to verify are:

- Can the API handle the expected volume?
- Does response time remain acceptable when the load increases?
- Does the API handle sudden batch traffic?
- Does the error rate increase under load?
- Does the system recover after the load comes down?
- Does high load cause any data loss or duplicate events?

This is a **performance test design only**. I have not executed the test because a performance environment, API endpoint and expected production capacity were not provided as part of the assessment.

---

## 2. Scope

### In Scope

- Order sync/ingest API
- Response time
- Throughput
- Error rate
- Behaviour during normal load
- Behaviour during increased/burst load
- Behaviour under sustained load
- Basic validation of the resulting order/event data

### Out of Scope

- UI performance
- Browser performance
- Infrastructure benchmarking
- Database performance testing separately
- Production performance testing

---

## 3. Workload Approach

I would test the API in a few stages instead of immediately sending a very high number of requests.

The idea is to start with a small load, understand the normal behaviour, and then gradually increase the load.

For example:

| Scenario | Example Load | Duration | Purpose |
|---|---:|---:|---|
| Baseline | 100 requests/sec | 15 min | Understand normal behaviour |
| Load | 500 requests/sec | 30 min | Check expected load |
| Burst | 300 → 1,000 requests/sec | 10–15 min | Simulate batch traffic |
| Stress | 500 → 1,500+ requests/sec | Until degradation | Find the breaking/degradation point |
| Soak | 300–500 requests/sec | 2–4 hours | Check stability over time |

These numbers are only starting assumptions because the actual production traffic and API capacity are not provided.

Before execution, I would discuss the expected volume with the engineering team and adjust these numbers accordingly.

---

# 4. Test Scenarios

## 4.1 Baseline Test

First, I would run the API with a relatively low and stable load.

For example:

**100 requests/sec for 15 minutes**

The purpose is to understand the normal response time and error rate.

I would record:

- Average response time
- p95 response time
- p99 response time
- Requests processed per second
- Error rate

This becomes the baseline against which the other tests can be compared.

---

## 4.2 Load Test

Next, I would increase the traffic gradually.

For example:

**100 → 250 → 500 requests/sec**

I would keep each level for enough time to see whether the system remains stable.

The main question here is:

> Can the API handle the expected enterprise load without a significant increase in response time or errors?

---

## 4.3 Burst Test

This is particularly important for this use case because the requirement mentions **bursty batch loads**.

Instead of sending a constant number of requests, I would simulate something like:

**300 requests/sec → sudden increase to 1,000 requests/sec → back to 300 requests/sec**

This helps check whether the API can handle a sudden increase in traffic.

I would also check what happens after the burst:

- Does the API recover?
- Does the response time return to normal?
- Are there failed requests?
- Is there any backlog?
- Are the expected events eventually created?

---

## 4.4 Stress Test

The stress test would gradually increase the load beyond the expected level.

For example:

**500 → 1,000 → 1,500 → 2,000 requests/sec**

The objective is not simply to make the system fail.

I want to understand **at what point the system starts showing unacceptable behaviour**.

I would look for:

- Increasing response time
- Increasing error rate
- Timeouts
- HTTP 5xx errors
- Reduced throughput
- Whether the system recovers after the load is removed

---

## 4.5 Soak Test

For a soak test, I would keep a reasonably high but stable load for a longer period.

For example:

**300–500 requests/sec for 2–4 hours**

This is useful for finding issues that may not appear during a short test.

For example:

- Gradual increase in response time
- Increasing error rate
- Memory/resource issues
- Growing backlog
- Throughput reducing over time

---

# 5. What I Would Measure

The main performance measurements would be:

### Response Time

How long the API takes to respond.

I would mainly look at **p95 and p99**, rather than only the average.

For example, if the average response time is 500 ms but p99 is 5 seconds, some users/requests are still experiencing a significant delay.

### Throughput

How many requests the API can process in a given period.

For example:

**500 requests/sec**

### Error Rate

Percentage of requests that fail.

I would look particularly at:

- HTTP 4xx
- HTTP 5xx
- Timeouts

### Recovery

After a burst or stress test, I would check whether the system returns to its normal behaviour.

---

# 6. Initial Performance Targets

Since the assessment does not provide actual API SLAs, I would use the following as initial targets for the test design:

| Metric | Initial Target |
|---|---|
| p95 response time | ≤ 1 second |
| p99 response time | ≤ 2 seconds |
| Error rate | < 1% |
| HTTP 5xx errors | < 0.5% |
| Timeout rate | < 0.5% |
| Recovery after burst | Return close to baseline |

These are **proposed test targets**, not claims about the actual system.

Before executing the test, I would confirm the expected SLA/SLO with the engineering team.

---

# 7. Data Validation During Performance Testing

For this particular application, performance cannot be looked at only from the API response.

The API is moving Order-to-Cash data from the OMS to the Analytics Event Platform.

So after a performance test, I would also validate a sample of the processed orders.

For example, if I send 1,000 orders during a burst test, I would check whether the expected records were eventually created.

I would specifically look for:

- Missing orders
- Duplicate events
- Orphan CaseIds
- Incorrect amounts
- Incorrect currencies
- Incorrect timestamps
- Missing lifecycle events
- Incorrect event sequence

This is important because an API could technically return successful responses while the downstream data still has problems.

---

# 8. Test Data

The test data should contain different types of orders, such as:

- Delivered orders
- Cancelled orders
- Returned orders
- Different order amounts
- Different currencies
- Different customer names
- Different lifecycle timestamps

I would use unique OrderIds/CaseIds for large-volume testing so that duplicate-key issues do not affect the results.

I would also keep a smaller set of orders aside for detailed post-test reconciliation.

---

# 9. Monitoring

If monitoring is available, I would check both API-level and system-level metrics.

### API level

- Requests/sec
- Response time
- p95/p99 latency
- Error rate
- Timeout rate
- HTTP status codes

### System level

- CPU
- Memory
- Database utilisation
- Queue/backlog
- Network utilisation

The purpose is to understand not just **that** performance degraded, but also whether there is an obvious system-level reason for the degradation.

---

# 10. Tool

For actual execution, I would use **k6** for this API-level performance testing.

The reason is that this is primarily an API/load-testing requirement, and k6 can be used to model:

- Gradual load increase
- Steady load
- Burst traffic
- Stress testing
- Performance thresholds

I have kept this submission at the **test-design level** rather than adding a runnable k6 script because the assessment does not provide a runnable API endpoint, authentication details or a performance environment.

---

# 11. Entry Criteria

Before executing the test, I would confirm:

- Performance environment is available
- API endpoint is available
- Authentication details are available
- Test data is available
- Expected traffic volume is known
- API SLA/SLO is agreed
- Monitoring is available

---

# 12. Exit Criteria

I would consider the test successful when:

- Expected load can be handled within the agreed response-time target
- Error rate remains within the agreed limit
- Expected throughput is achieved
- No significant data loss or duplicate events are found
- The system recovers after a burst
- No unexplained critical performance issue remains

---

# 13. Limitations

The exact performance numbers cannot be finalised from the information provided in the assessment.

The assessment does not provide:

- Production traffic volume
- API SLA
- Infrastructure details
- Maximum supported throughput
- Batch-size limits
- Performance environment
- API authentication details

Therefore, the workload and SLO values in this document are proposed starting points.

For an actual execution, I would first confirm these values with the engineering/product team.

---

# 14. Summary

My approach is to start with a baseline, gradually increase the load, simulate a burst, go beyond the expected load to understand the degradation point, and finally run a sustained-load test.

For this Order-to-Cash integration, I would also connect the performance test back to data validation.

The main questions I want the test to answer are:

1. Can the sync API handle the expected enterprise load?
2. What happens when there is a sudden batch spike?
3. At what point does performance start degrading?
4. Does the system recover after the load reduces?
5. Does sustained load create stability issues?
6. Does high load cause missing, duplicate or incorrect downstream events?

This gives a basic performance-testing approach while keeping the focus on the business risk of the Order-to-Cash integration.