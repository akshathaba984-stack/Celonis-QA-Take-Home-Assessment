# AI WORK LOG

## Table of Contents

- [Part A: Test Strategy & Scenario Design](#part-a-test-strategy--scenario-design)
- [Part B: Automation Framework (Playwright + JavaScript)](#part-b-automation-framework-playwright--javascript)
- [Part C: Integration Data Validation](#part-c-integration-data-validation)
- [Part D: Performance & Load Testing](#part-d-performance--load-testing)
- [Part E: AI Artifact – Data-Diff Anomaly Explainer](#part-e-ai-artifact--data-diff-anomaly-explainer)

---

## Part A: Test Strategy & Scenario Design

> **My approach:** I believe understanding the product, system, and business requirements is the foundation of any project, whether we are working as QA, developers, or in any other role. I therefore kept the initial requirement understanding, test strategy, and testing decisions human-driven, while using AI only where it could support the process.

### 1. AI Tools Used

- Claude 4.5 Haiku

### 2. Why I Used AI Here

- I first studied the requirements and created my own test strategy and prioritized scenarios.
- I then used Haiku mainly to structure and format my finalized strategy into a clean Markdown deliverable.

### 3. What AI Produced Well

- Provided a clean Markdown structure and scenario table format.
- Helped organize my finalized content into a readable deliverable.

### 4. Where AI Fell Short

- As a secondary QA coverage check, AI suggested some generic testing areas such as cross-browser testing and page load time that were not relevant to this integration-focused requirement.
- It also did not independently highlight some of the important sync rules, such as Cart orders not being synced, UTC timestamp validation, and case-insensitive customer name comparison.

### 5. How I Verified & Fixed It

- I studied the specification myself and built the testing foundation around the actual OMS-to-Analytics sync contract.
- I drafted the test strategy and prioritized scenarios based on business impact and data integrity risks.
- I reviewed the AI suggestions against the requirements, removed irrelevant suggestions, and ensured the final strategy covered the important business and data rules.
- I used AI mainly for formatting and structuring the finalized Markdown deliverable.

---

## Part B: Automation Framework (Playwright + JavaScript)

### 1. AI Tool Used

- Cursor IDE

### 2. Why I Used Cursor IDE

I am currently developing my hands-on Playwright skills and have not yet used Playwright extensively in my daily work. However, I did not want to skip the automation portion of the assessment.

I have a strong foundation in understanding what needs to be validated from a UI testing perspective, including identifying the user journey, defining test scenarios, determining meaningful assertions, and considering maintainability of the automation.

I also wanted to demonstrate my ability to effectively leverage AI-assisted development to bridge the gap between my QA knowledge and my current level of hands-on Playwright implementation.

I chose Cursor because it allowed me to work directly within the project folder and use AI assistance while creating the Playwright framework. It helped accelerate the implementation of the project structure, page objects, test flow, configuration, and supporting documentation.

### 3. How I Used AI

Before generating the implementation, I explored the Demoblaze application and defined the UI flow and validations I wanted to automate.

I then provided Cursor with the required scenario and framework expectations, including:

- Demoblaze laptop flow
- MacBook Air selection
- Add-to-cart validation
- Cart validation
- Product price validation
- Place Order form validation
- Page Object Model structure
- Playwright configuration
- HTML reporting
- README and run instructions

Cursor generated the initial Playwright framework and implementation based on these requirements.

### 4. How I Verified the AI-Generated Output

I did not treat the generated code as automatically correct.

I verified the implementation by:

- Manually exploring the Demoblaze application to understand the actual user flow.
- Reviewing the generated project structure and test scenario.
- Installing the required dependencies and Playwright browser.
- Running the test locally from the terminal.
- Confirming that the complete test scenario executed successfully.
- Reviewing the Playwright HTML report to confirm the execution result and the individual test steps.

The final test execution completed successfully with **1 passed test and 0 failed tests**.

### 5. Human Validation / QA Responsibility

My primary contribution was defining the testing approach, business flow, validations, and expected behaviour, while using AI to accelerate the Playwright implementation.

I treated the AI-generated implementation as an implementation aid rather than as a replacement for QA validation. The generated automation was executed against the application and its result was verified through the local test execution and Playwright report.

### 6. AI Usage Reflection

The main benefit of using AI in this task was accelerating the implementation of the automation framework while allowing me to focus on the QA aspects of the problem: understanding the application flow, deciding what should be validated, defining the test scenario, and reviewing the execution result.

The main limitation is that AI-generated automation still requires human review and execution. AI can generate an implementation based on assumptions about the application, so successful generation alone was not considered sufficient validation.

---

## Part C: Integration Data Validation

**AI Tool Used:** Claude Sonnet 5.5

### How I Used AI

I first performed a manual, human-in-the-loop evaluation of `orders.csv` and `analytics_event_log.csv` to understand the expected data integrity issues and define the validation rules.

Based on this understanding, I wrote the initial prompt myself, describing the required reconciliation checks and expected output. I then used Claude Sonnet 4.5 to generate the Python reconciliation script. The prompt used for this is documented separately and attached for reference.

### Where AI Helped

- Converted my validation requirements into a working reconciliation script.
- Automated repetitive comparisons across the two CSV files.
- Generated a structured defect report covering completeness, referential integrity, value correctness, temporal checks, and event sequence.

### Where AI Fell Short

The initial script produced some false positives because the AI did not fully understand certain data variations and business rules. For example, formatting differences and valid business branches were initially treated as defects.

I manually reviewed these findings against the source data and refined the validation logic.

### How I Verified the Result

I compared the script-generated findings with my initial manual findings and verified the reported defects directly against the source CSVs. Only validated mismatches were considered final defects.

### My Role

My focus was on defining what needs to be validated, identifying expected defects, evaluating AI output, and ensuring the final results were trustworthy. AI was used as an implementation accelerator, not as the final decision-maker.

---

## Part D: Performance & Load Testing

### 1. AI Tools Used

- ChatGPT

### 2. Why I Used AI Here

- I used the LLM mainly to help organise and structure the `PERFORMANCE.md` strategy document based on the given assessment requirement.
- I defined the main test approach and used AI to help organise the scenarios, workload model, SLIs/SLOs and document structure.
- I did not use AI to create or execute a performance test script for this part.

### 3. What AI Produced Well

- Helped structure the document around the required baseline, load, stress and soak scenarios, along with a burst scenario relevant to the stated batch-load requirement.
- Helped identify the main performance metrics to consider, such as latency, throughput and error rate.
- Helped connect performance testing with the business risk of the integration, including checking for missing or duplicate downstream events.

### 4. Where AI Fell Short

- **Assumptions presented as targets:** The initial AI suggestions included specific workload and SLO values even though actual production traffic and API capacity were not provided. I kept these only as initial test assumptions and clearly stated that they would need to be confirmed before execution.
- **Overly detailed recommendations:** Some of the initial suggestions were more detailed than necessary for this assessment. I simplified them and removed areas that I could not confidently explain or justify.

---

## Part E: AI Artifact – Data-Diff Anomaly Explainer

### 1. Approach

I selected the Data-Diff Anomaly Explainer because it directly builds on my strong foundational QA understanding demonstrated in Part A and my Part C Integration Data Validation work.

Before building the artifact, I had already reviewed the provided CSV files, understood the expected data flow, and identified the seeded defects through my own QA analysis and reconciliation approach. These findings became my baseline for deciding what the artifact should detect, what should be explained, and how the output should be verified.

The prompt used to build the artifact is attached separately for reference.

### 2. How I Used AI

I used Claude Sonnet 5.5 to build the working AI artifact based on the QA requirements and validation behavior I had defined.

I treated the AI output as an implementation aid rather than assuming that the generated result was correct. My focus was on defining the expected behavior, identifying what needed to be verified, and validating the final output against known results.

### 3. Verification Performed

I ran the artifact using the provided CSV files and verified its findings against two independent QA baselines:

- Defects identified during my manual review of the CSV data.
- Defects identified through my Part C reconciliation script.

I compared the anomalies reported by the artifact against these known findings to confirm whether the artifact was detecting the expected issues correctly.

### 4. Where AI Helped / Where AI Fell Short

AI helped by quickly converting my QA requirements and expected validation behavior into a working artifact.

AI fell short in a few areas that required iterative QA verification:

- The initial UI and formatting were not clear enough.
- The first download functionality displayed a download option, but the file was not actually downloaded when tested.
- It did not always correctly distinguish between a genuine data defect and a false positive/expected variation. I had to provide additional guidance based on my QA understanding of the expected data behavior.
- I had to identify these issues through testing and re-prompt the AI with specific corrections.

This reinforced the importance of QA validation of AI-generated output rather than accepting it at face value, particularly when determining whether an anomaly is a real defect.

### 5. QA Outcome

After the corrections, I re-ran the artifact and verified its results against my manual findings and Part C reconciliation output.

The reported anomalies matched the expected defects, giving me confidence that the artifact was functioning as intended for the provided dataset.
