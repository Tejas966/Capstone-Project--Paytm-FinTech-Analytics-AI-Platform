# Capstone-Project--Paytm-FinTech-Analytics-AI-Platform
Capstone Project — Executive Certification in FinTech & Artificial Intelligence
Paytm FinTech Analytics & AI Platform
Paytm operates across several distinct financial businesses under one brand: merchant and UPI/wallet payments, consumer and merchant lending (Paytm Postpaid, BNPL-style credit), and wealth/advisory services (Paytm Money). Each of these businesses runs on a different mix of analyst tooling — spreadsheets and SQL for payments operations, applied machine learning for credit decisioning, and AI-assisted analysis for advisory — spanning the full analyst-to-ML skill set this capstone tests. In this capstone you join Paytm's analytics guild as an incoming analyst/associate and ship one connected platform made of three internally-linked parts: a payments-and-fraud analytics workbench (/payments_fraud_analytics), a credit-risk machine-learning pipeline (/credit_risk_lending_ml), and an AI-augmented advisory toolkit with a blockchain/crypto risk appendix (/ai_advisory_blockchain). All three live together in one repository — this is a single, coherent submission telling one Paytm story, not three unrelated exercises. Every technique required below is fully specified in this brief; nothing beyond it is required.

You may build the three parts in any order. Each part is graded independently against its own criteria, but they all live in, and are submitted as, one single public GitHub repository.

Total marks: 100 · Parts: 3 (/payments_fraud_analytics — 35, /credit_risk_lending_ml — 40, /ai_advisory_blockchain — 25)

Submission Guidelines (read first)
Submit exactly ONE public GitHub repository link for this entire project. Do not create separate repositories per part — there is one repo, containing all three part folders (/payments_fraud_analytics, /credit_risk_lending_ml, /ai_advisory_blockchain) at its root, plus one root README.md.
The root README.md must document: how to set up the project (a requirements.txt per part, or one consolidated requirements.txt, your choice — state which), how to run each of the three parts end to end, and a short summary of your design decisions for each part. Any written interpretation a task asks for lives as Markdown text — inside the root README, a part-level README, or notebook Markdown cells — not in a separate document type.
All deliverables are textual or spreadsheet/data artifacts: code lives in the repository as .py/.ipynb files, spreadsheet work is committed as a real .xlsx workbook, and every write-up lives as Markdown text inside the repository. No screenshots, presentation slides, PDFs, video, or audio are required or accepted anywhere in this project. Chart image files your code generates (e.g., saved .png plots for the dashboard task) may live inside the repository as supporting artifacts, but they are never a substitute for the required written interpretation — a grader must be able to assess your work from the text and data files alone.
Academic integrity: the code, analysis, and written interpretations must be your own. You may use standard library/framework documentation, but the reasoning and implementation must be authored by you.
Deadline: submit your single repository link by the date/time communicated separately on the LMS for this evaluation.
Git workflow (optional, unscored). As general engineering practice, you may use a feature-branch git workflow for this repository — creating a branch, committing to it at least twice, and merging it back into main. This is optional guidance, not a graded criterion for this capstone; no marks in grader_rubric.md depend on it.
Running the seed-data generator scripts. Both Part 1's and Part 2's generate_data.py scripts write their output CSVs via relative paths, so each must be run with its own part folder as the working directory — e.g. cd payments_fraud_analytics && python generate_data.py, and separately cd credit_risk_lending_ml && python generate_data.py — so the CSVs land alongside the script that produced them. Do not run either script from the repository root.
Spreadsheet tooling for Part 1. Build the Excel/Sheets workbook using Microsoft Excel, Google Sheets (free), or LibreOffice Calc (free) — any of the three is acceptable as long as the required VLOOKUP/HLOOKUP/pivot-table/nested-IF functionality is supported, which all three provide.
No paid services required anywhere in this project. Part 3's AI-advisory tasks default to a fully deterministic, keyless mock mode; read that part's fallback note before you begin.
All monetary figures in this project are in Indian Rupees (INR). Every synthetic dataset, example, and written analysis below uses INR — do not introduce $/USD anywhere.
Part 1 — Payments & Fraud Analytics (/payments_fraud_analytics) — 35 marks
Paytm vertical: Payments (UPI/wallet/QR merchant payments).

Paytm's payments operations team needs three things every fraud/ops analyst on the team must be able to do: clean and cross-reference merchant data in a spreadsheet the way regional-ops teams actually work, query a proper relational schema in SQL to catch fraud patterns, and turn cleaned data into an executive-ready dashboard. This part builds all three, plus a payment-reconciliation engine, against one synthetic Paytm transactions dataset you generate yourself with a fixed random seed (no real Paytm data exists or is used anywhere in this project).

Exact seed-data generation script (run this first, commit its output)
Create payments_fraud_analytics/generate_data.py with exactly this logic (you may reformat/comment it, but the parameters, seed, and injected-fraud counts below must not change, since the acceptance criteria depend on them):

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

CATEGORIES = ["grocery", "food_delivery", "recharge", "bill_payment", "travel",
              "ecommerce", "entertainment"]
REGIONS = ["North", "South", "East", "West"]
METHODS = ["UPI", "Wallet", "Card", "Netbanking"]
METHOD_WEIGHTS = [0.55, 0.20, 0.15, 0.10]
AMOUNTS_INR = [49, 99, 149, 299, 499, 799, 1499, 2999, 4999]
AMOUNT_WEIGHTS = [0.18, 0.16, 0.14, 0.14, 0.12, 0.10, 0.08, 0.05, 0.03]

# --- 40 merchants ---
merchants = pd.DataFrame({
    "merchant_id": range(1, 41),
    "merchant_name": [f"Merchant_{i:03d}" for i in range(1, 41)],
    "category": [random.choice(CATEGORIES) for _ in range(40)],
    "region": [random.choice(REGIONS) for _ in range(40)],
})

# --- 350 established users, signed up 30-730 days before the window start ---
window_start = datetime(2026, 1, 1)
users = pd.DataFrame({
    "user_id": range(1, 351),
    "signup_date": [window_start - timedelta(days=random.randint(30, 730)) for _ in range(350)],
})

# --- 500 baseline transactions over a 30-day window ---
rows = []
for i in range(500):
    txn_time = window_start + timedelta(
        days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    status = np.random.choice(["captured", "failed", "chargeback"], p=[0.92, 0.06, 0.02])
    rows.append({
        "transaction_id": f"TXN{100000+i}",
        "user_id": random.randint(1, 350),
        "merchant_id": random.randint(1, 40),
        "transaction_time": txn_time,
        "amount_inr": np.random.choice(AMOUNTS_INR, p=AMOUNT_WEIGHTS),
        "payment_method": np.random.choice(METHODS, p=METHOD_WEIGHTS),
        "status": status,
        "risk_score": random.randint(0, 100),
    })

# --- inject 15 "burner account" chargeback frauds: brand-new users (< 30 days old) ---
next_user_id = 351
for i in range(15):
    txn_time = window_start + timedelta(days=random.randint(10, 29), hours=random.randint(0, 23))
    signup = txn_time - timedelta(days=random.randint(1, 25))
    users = pd.concat([users, pd.DataFrame([{"user_id": next_user_id, "signup_date": signup}])],
                       ignore_index=True)
    rows.append({
        "transaction_id": f"TXN{200000+i}",
        "user_id": next_user_id,
        "merchant_id": random.randint(1, 40),
        "transaction_time": txn_time,
        "amount_inr": random.choice([999, 1999, 2999, 4999]),
        "payment_method": "Card",
        "status": "chargeback",
        "risk_score": random.randint(70, 100),
    })
    next_user_id += 1

# --- inject 8 velocity-attack clusters: 4 rapid-fire txns each within a 5-minute window ---
for cluster in range(8):
    victim_user = random.randint(1, 350)
    base_time = window_start + timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))
    for k in range(4):
        rows.append({
            "transaction_id": f"TXN{300000 + cluster*4 + k}",
            "user_id": victim_user,
            "merchant_id": random.randint(1, 40),
            "transaction_time": base_time + timedelta(minutes=k),
            "amount_inr": random.choice([299, 399, 499]),
            "payment_method": "Card",
            "status": "captured" if k == 3 else "failed",
            "risk_score": random.randint(60, 95),
        })

ledger = pd.DataFrame(rows)  # 500 + 15 + 32 = 547 rows
merchants.to_csv("merchants.csv", index=False)
users.to_csv("users.csv", index=False)
ledger.to_csv("ledger.csv", index=False)

# --- build the deliberately-discrepant "gateway export" copy for reconciliation ---
gateway = ledger.copy()
n = len(gateway)
missing_idx = np.random.choice(n, size=int(0.05 * n), replace=False)
gateway = gateway.drop(index=missing_idx).reset_index(drop=True)

mismatch_idx = np.random.choice(len(gateway), size=int(0.03 * n), replace=False)
gateway.loc[mismatch_idx, "amount_inr"] = gateway.loc[mismatch_idx, "amount_inr"] + \
    np.random.choice([-100, -50, 50, 100], size=len(mismatch_idx))

extra_rows = []
for i in range(int(0.02 * n)):
    extra_rows.append({
        "transaction_id": f"TXNX{9000+i}", "user_id": random.randint(1, 350),
        "merchant_id": random.randint(1, 40),
        "transaction_time": window_start + timedelta(days=random.randint(0, 29)),
        "amount_inr": random.choice(AMOUNTS_INR), "payment_method": random.choice(METHODS),
        "status": "captured", "risk_score": random.randint(0, 100),
    })
gateway = pd.concat([gateway, pd.DataFrame(extra_rows)], ignore_index=True)

status_idx = np.random.choice(len(gateway), size=int(0.02 * n), replace=False)
gateway.loc[status_idx, "status"] = "failed"

gateway.to_csv("gateway_export.csv", index=False)
Do not invent your own transaction data — grading is demonstrated against this exact generation logic (seed 42), which yields a 547-row ledger (500 baseline + 15 burner-account chargebacks + 32 velocity-attack rows across 8 clusters of 4) and a deliberately-discrepant gateway export (~5% missing, ~3% amount-mismatched, ~2% extra, ~2% status-differing, applied on top of the 547-row ledger). Commit merchants.csv, users.csv, ledger.csv, and gateway_export.csv alongside generate_data.py.

Tasks
Part A — Excel/Sheets merchant workbook

Open ledger.csv and merchants.csv in Excel/Google Sheets. Build a workbook merchant_workbook.xlsx with:
A VLOOKUP (fixed range with $ absolute references) that pulls each transaction's merchant_name, category, and region from the merchants sheet into a transactions-view sheet, using IFERROR/IFNA to show "Merchant not found" for any unmatched merchant_id.
An HLOOKUP demonstration on a small horizontally-laid-out reference table you add (e.g., a one-row-per-payment-method fee-tier lookup: UPI/Wallet/Card/Netbanking with their MDR-style fee percentages of your choosing, stated in the workbook).
A nested IF/AND classification column labeling each transaction "High-Value Merchant Day" when a merchant's daily transaction total (via a pivot table) exceeds INR 5,000 and its region is not "East", using distinct, documented cutoffs if you choose a different rule — state your exact rule in the workbook.
A pivot table summarizing total amount_inr and count of transactions by merchant_id and status, plus a count-vs-count-unique comparison (unique days transacted vs. total transaction count) for at least 5 merchants.
Part B — SQL fraud-pattern detection

Load merchants.csv, users.csv, and ledger.csv into a normalized SQLite database paytm_payments.db with a schema that has merchants(merchant_id PK, ...), users(user_id PK, signup_date), and transactions(transaction_id PK, user_id FK, merchant_id FK, ...).
Write and execute at least 6 SQL queries (with output) collectively covering SELECT/WHERE/ORDER BY/LIMIT/DISTINCT, GROUP BY/HAVING, at least one INNER JOIN and one LEFT JOIN, and specifically:
Quantify chargeback impact: count of chargeback transactions, unique users affected, total chargeback amount.
Identify burner accounts: users whose signup_date is less than 30 days before their transaction's transaction_time, restricted to status = 'chargeback'. Make the boundary explicit and unambiguous: 0 <= (transaction_time - signup_date).days < 30 — the signup must be on or before the transaction (never a negative age) and strictly less than 30 days earlier (never exactly 30 days or more). Your query must surface at least the 15 seeded burner-account rows.
Detect velocity attacks: users with 3 or more transactions within any 10-minute window. Your query must surface at least the 8 seeded velocity clusters. Grading clarification: your result is correct if, when grouped by user_id and a rounded/floored 10-minute time bucket of transaction_time, all 8 seeded clusters (each identifiable by its victim user_id and the cluster's earliest transaction_time) appear as distinct qualifying groups — graders check for the presence of all 8 seeded (user_id, approximate-cluster-start-time) combinations, NOT an exact row-count or exact-bucket-boundary match, since overlapping 10-minute windows can be grouped multiple reasonable ways.
Part C — Python payment reconciliation

In reconcile.py (or a notebook), write a reusable function reconcile_payments(ledger_df, gateway_df) that returns four DataFrames: transactions missing in the gateway export, transactions missing in the ledger (extra in gateway), amount mismatches (with the computed difference), and status mismatches — using set operations on transaction_id and pd.merge for the pairwise comparisons. Run it against ledger.csv vs. gateway_export.csv and report all four discrepancy counts; they must be consistent with the ~5%/~3%/~2%/~2% injection rates in generate_data.py.
Part D — Four-layer analytics dashboard (code-generated, not a live BI tool)

Using matplotlib/plotly, build a four-layer dashboard as a set of saved chart images plus written interpretation (no live Looker Studio/Power BI dependency is required for grading):
Headline layer: print/display 3–5 scorecards (total GMV in INR, overall success rate, reconciliation match rate, chargeback ratio). Use these exact definitions for the scorecard metrics:
match_rate = (count of transactions present in BOTH ledger.csv and gateway_export.csv with an identical amount_inr AND an identical status) / (total transaction count in ledger.csv). Amount mismatches, status mismatches, and rows missing in either file all count as NOT matched for this scorecard number. (This definition affects only this single headline number — the four discrepancy categories reconcile_payments(...) returns in Part C are unaffected and continue to be reported separately.)
chargeback_ratio (headline) = (count of transactions with status == "chargeback") / (count of all transactions), platform-wide, expressed as a percentage — count-based, not amount-based.
Trends layer: a time-series chart of daily GMV and daily chargeback count over the 30-day window.
Breakdown layer: a bar chart of GMV by payment_method and by category (joined from merchants).
Details layer: a table, rendered as a saved image (not a live/printed DataFrame), of the top 10 merchants by transaction count, with conditional highlighting (e.g., a flag column) for any merchant whose chargeback_ratio exceeds 1%, using the same count-based definition as above but scoped to that one merchant: chargeback_ratio (per-merchant) = (count of that merchant's transactions with status == "chargeback") / (count of all of that merchant's transactions).
Each chart must carry a 2–4 sentence written interpretation. (Optional, ungraded stretch — must not affect your required submission: if you want the extra practice, publish the committed CSVs to an actual Looker Studio dashboard (free, Google-account based, no payment required) and link it in your README. This is entirely optional; the required, graded deliverable is the code-generated chart set above.)
Acceptance criteria (your submission is complete when…)
generate_data.py runs end to end and reproduces the exact 547-row ledger, the users and merchants tables, and the discrepant gateway export described above (seed 42).
merchant_workbook.xlsx contains a working fixed-range VLOOKUP with IFERROR handling, an HLOOKUP demonstration, a documented nested IF/AND classification rule, and a pivot table with a count-vs-count-unique comparison for at least 5 merchants.
The SQLite schema has the three tables with declared PK/FK relationships; ≥ 6 SQL queries are present with output, collectively covering every required clause plus both join types, and the burner-account query surfaces all 15 seeded rows while the velocity-attack query surfaces all 8 seeded clusters.
reconcile_payments(...) returns all four discrepancy categories with counts consistent with the injected 5%/3%/2%/2% rates, run against the exact committed CSVs.
All four dashboard layers are present as saved chart images (the details layer is a saved image, never a live/printed DataFrame) with a written interpretation for each; the headline match_rate and chargeback_ratio scorecards use the exact definitions stated in the task above, and the per-merchant high-risk flag (chargeback_ratio > 1%, using the same count-based, per-merchant-scoped definition) is correctly computed in the details-layer table.
README documents install/run steps and every design decision (fee-tier assumptions, classification cutoffs, chart choices).
Submission
This part lives at /payments_fraud_analytics inside the single project repository: generate_data.py + its four committed CSVs, merchant_workbook.xlsx, the SQLite database (or its exact recreation script) with the SQL queries and their output, reconcile.py, the saved dashboard chart images, and a short part-level note (in /payments_fraud_analytics/README.md or the root README) with every required written interpretation.

Part 2 — Credit Risk & Lending ML (/credit_risk_lending_ml) — 40 marks
Paytm vertical: Postpaid / Lending (BNPL-style consumer and merchant credit).

Paytm Postpaid needs to decide, for each applicant, a probability of default and a risk-based interest rate, built with real scikit-learn code. This part builds that pipeline end to end on a synthetic applicant dataset, adds a lightweight fraud-adjacent anomaly-detection sub-task on transaction behaviour, and closes with a written bias-awareness note.

Exact seed-data generation script
Create credit_risk_lending_ml/generate_data.py with exactly this logic:

import numpy as np
import pandas as pd

np.random.seed(42)
N = 400

age = np.random.randint(21, 60, N)
monthly_income_inr = np.random.randint(15000, 150000, N)
existing_loans_count = np.random.randint(0, 5, N)
credit_utilization_ratio = np.round(np.random.uniform(0.05, 0.95, N), 2)
upi_monthly_inflow_inr = np.random.randint(2000, 120000, N)
bounced_payments_count = np.random.poisson(1.2, N)
employment_type = np.random.choice(["salaried", "self_employed", "gig"], N,
                                    p=[0.55, 0.30, 0.15])
credit_bureau_score = np.random.randint(300, 900, N).astype(float)

# 20% of applicants are "new to credit" (thin-file): no bureau score at all
thin_file_idx = np.random.choice(N, size=int(0.20 * N), replace=False)
credit_bureau_score[thin_file_idx] = np.nan

# risk score combines income (protective), bounced payments and utilization (risky),
# and UPI inflow (protective, alternate-data signal) -- deliberately usable even
# when credit_bureau_score is missing
z_income = (monthly_income_inr - monthly_income_inr.mean()) / monthly_income_inr.std()
z_bounced = (bounced_payments_count - bounced_payments_count.mean()) / (bounced_payments_count.std() + 1e-9)
z_util = (credit_utilization_ratio - credit_utilization_ratio.mean()) / credit_utilization_ratio.std()
z_upi = (upi_monthly_inflow_inr - upi_monthly_inflow_inr.mean()) / upi_monthly_inflow_inr.std()

risk_score = -2.25 + (-0.9 * z_income) + (0.8 * z_bounced) + (0.7 * z_util) + (-0.5 * z_upi) \
    + np.random.normal(0, 0.6, N)
default_prob = 1 / (1 + np.exp(-risk_score))
default = (np.random.uniform(0, 1, N) < default_prob).astype(int)

df = pd.DataFrame({
    "applicant_id": [f"APP{1000+i}" for i in range(N)],
    "age": age,
    "monthly_income_inr": monthly_income_inr,
    "existing_loans_count": existing_loans_count,
    "credit_utilization_ratio": credit_utilization_ratio,
    "upi_monthly_inflow_inr": upi_monthly_inflow_inr,
    "bounced_payments_count": bounced_payments_count,
    "credit_bureau_score": credit_bureau_score,
    "employment_type": employment_type,
    "default": default,
})
df.to_csv("credit_applicants.csv", index=False)
print(df["default"].value_counts(normalize=True))

# --- second dataset: transaction-behaviour rows for anomaly detection ---
M = 250
behaviour = pd.DataFrame({
    "txn_id": [f"BTXN{5000+i}" for i in range(M)],
    "applicant_id": np.random.choice(df["applicant_id"], M),
    "txn_hour": np.random.randint(6, 23, M),
    "is_new_device": np.random.choice([0, 1], M, p=[0.9, 0.1]),
    "txn_amount_inr": np.random.choice([199, 499, 999, 1999, 3999], M,
                                        p=[0.30, 0.28, 0.22, 0.13, 0.07]),
    "channel": np.random.choice(["P2P", "P2M"], M, p=[0.4, 0.6]),
})
# inject 15 deliberate anomalies: new device, unusual hour (1-4am), high amount
anomalies = pd.DataFrame({
    "txn_id": [f"BTXNA{i}" for i in range(15)],
    "applicant_id": np.random.choice(df["applicant_id"], 15),
    "txn_hour": np.random.randint(1, 5, 15),
    "is_new_device": 1,
    "txn_amount_inr": np.random.choice([14999, 19999, 24999], 15),
    "channel": "P2P",
})
behaviour = pd.concat([behaviour, anomalies], ignore_index=True)  # 265 rows total
behaviour.to_csv("txn_behaviour.csv", index=False)
This yields 400 credit-applicant rows with a default rate in the roughly 15–25% range (the exact rate depends on the seeded draw — print and report your measured rate; it must fall in this range, giving enough positive and negative cases for a meaningful classifier), 80 of which (20%) have a missing credit_bureau_score to represent new-to-credit applicants, and a separate 265-row transaction-behaviour table with 15 deliberately injected anomalies (new device + unusual hour + high amount) among 250 normal rows. Do not invent your own applicant data — commit credit_applicants.csv and txn_behaviour.csv exactly as produced by this script.

Tasks
Part A — EDA and preprocessing

Load credit_applicants.csv. Report the exact measured default rate and the exact percentage of missing credit_bureau_score values. For rows with a missing bureau score, do not drop them (that would discard every new-to-credit applicant, the population alternate data is specifically meant to serve) — instead engineer a binary is_thin_file flag (1 where credit_bureau_score is missing, 0 otherwise). This flag is a direct not-missing/missing indicator computed straight from the raw data, so it is safe to compute at this stage — it does not depend on any fitted statistic. Do not impute the missing scores yet in this task; imputation happens in Task 2, after the train/test split, to avoid leaking test-set information into training.
Split into train/test (75/25, stratified on default, justify the stratification choice; use random_state=42 for the split so results are reproducible), then, in this order:
Compute the median of the non-missing credit_bureau_score values using only the training split, and use that exact training-derived median value to fill missing scores in both the training split and the test split — explicitly justifying this alternate-data-driven imputation choice in writing. This must come from training data only, exactly mirroring the StandardScaler fit-on-train-only rule below — never compute the median from the full (train+test) dataset.
Encode employment_type (one-hot or label encoding, your choice, stated in writing).
Scale numeric features with StandardScaler, fit only on the training split.
Part B — Classification models

Train Logistic Regression and a Decision Tree Classifier (DecisionTreeClassifier(random_state=42)) on the identical train/test split.
Evaluate both models with a confusion matrix, accuracy, precision, recall, F1, and ROC curve + AUC, presented side by side in a comparison table.
Risk-based pricing table: using the logistic regression's predicted probabilities, bucket applicants into at least 4 risk tiers (e.g., quartiles of predicted default probability) and assign each tier an illustrative interest-rate range in percent (lower risk → lower rate), reporting the actual observed default rate within each tier to check monotonicity (lower-risk tiers should show a lower actual default rate than higher-risk tiers).
Part C — Anomaly detection and optional segmentation

Load txn_behaviour.csv. Select the numeric behavioural features (txn_hour, is_new_device, txn_amount_inr), standardize them, and run scikit-learn's IsolationForest(random_state=42, contamination=...) with a contamination rate matching the injected anomaly proportion (15 / 265 ≈ 5.7%). Report how many of the 15 seeded anomalies (txn_id starting with BTXNA) were flagged as anomalous, as a simple recall check against your own injected ground truth.
Optional (ungraded stretch, does not affect required marks): run K-Means clustering (with the elbow method or Calinski-Harabasz index to pick k) on standardized credit_applicants.csv features to segment applicants into behavioural groups, and note in writing whether any cluster over-indexes on the default label.
Part D — Bias-awareness note and final recommendation

Write a short (200–400 word) note in your README addressing: even with no explicit gender/location field in this dataset, could any of employment_type, monthly_income_inr, or credit_bureau_score act as a correlated proxy for a protected attribute in a real deployment, and what governance step (e.g., a maker-checker human-in-the-loop review for declined thin-file applicants) would you recommend before this model goes live.
Write a final model-comparison table (both classifiers' metrics from Task 4, the Isolation Forest recall from Task 6) and a 3–5 sentence recommendation of which classifier you would deploy for Paytm Postpaid and why, referencing specific metric values.
Acceptance criteria (your submission is complete when…)
generate_data.py runs end to end and reproduces credit_applicants.csv (400 rows, measured default rate reported and in the 15–25% range, exactly 80 rows with a missing credit_bureau_score) and txn_behaviour.csv (265 rows, 15 seeded anomalies).
The thin-file handling strategy is implemented and justified in writing, in the correct order: the is_thin_file flag is engineered directly from the raw data in Task 1 (no imputation yet); the train/test split happens next; median imputation of credit_bureau_score is computed from the training split only and then applied to fill missing values in both splits; no row is ever dropped.
Train/test split is stratified, uses random_state=42, and all preprocessing (median imputation, encoding, scaling) is fit only on the training split.
Both classifiers are trained on the identical split; the full evaluation suite is reported for both, side by side.
The risk-based pricing table shows ≥ 4 tiers with a monotonically increasing (or materially so) observed default rate from lowest- to highest-risk tier.
IsolationForest is run on the standardized behavioural features with a contamination rate matching the seeded anomaly proportion, and the recall against the 15 seeded BTXNA* anomalies is explicitly reported.
The bias-awareness note names at least one specific correlated-proxy risk and one concrete governance step.
The final comparison table and recommendation are present and reference specific metric values.
Submission
This part lives at /credit_risk_lending_ml inside the single project repository: generate_data.py + its two committed CSVs, the EDA/modeling notebook(s)/script(s), any saved chart images, and a short part-level note (in /credit_risk_lending_ml/README.md or the root README) with the risk-pricing table, the Isolation Forest recall result, the bias-awareness note, and the final recommendation.

Part 3 — AI-Augmented FinTech Advisory & Blockchain Risk (/ai_advisory_blockchain) — 25 marks
Paytm vertical: Money / Wealth advisory, plus a blockchain/crypto risk appendix.

Paytm Money needs a lightweight AI-assisted advisory toolkit: a portfolio-allocation agent grounded in CAPM and portfolio variance, a structured-extraction helper for company-disclosure text, and a bull/bear/synthesizer debate demo — all built using the agentic think-act-observe pattern and LLM structured JSON extraction, not a retrieval/vector-database pipeline (this part deliberately does not ask for embeddings, a vector database, or LangGraph, unlike a typical RAG build). It closes with a DCF valuation calculator and a shorter written blockchain/crypto risk appendix, since that content is treated at a conceptual/descriptive depth here rather than a hands-on build depth.

LLM calls — offline mock is the graded baseline (read before starting): every LLM "reasoning" step in this part is gated behind a single environment variable, MOCK_LLM. Left unset, or set to MOCK_LLM=1, the service runs the fully deterministic, rule-based mock logic described below — no signup, no API key, and no network call to any LLM provider. This is the default state and is what gets graded; your submission must be fully correct using only this path.

(Optional, ungraded extension — must not affect your required submission: if you want the extra practice, set MOCK_LLM=0 and use Groq's API free tier (console.groq.com) as your LLM backend. It requires only a free account signup — no credit card and no payment is ever required for the free tier, though it carries a request-rate quota. If Groq is unavailable to you for any reason, any other LLM API with a genuinely free tier, not merely a time-limited trial, is an acceptable substitute. This MOCK_LLM=0 path is entirely optional and is graded with MOCK_LLM left at its default, so every required output must be fully correct using only the mock baseline.)

Exact seed data (copy these into your repository as-is)
Stock universe (stock_universe.py, a ready-to-run dict — no transcription required):

STOCK_UNIVERSE = {
    "PAYFIN":  {"beta": 1.35, "analyst_expected_return": 0.16, "std_dev": 0.28},
    "PAYRETAIL": {"beta": 0.85, "analyst_expected_return": 0.11, "std_dev": 0.17},
    "PAYINFRA": {"beta": 1.10, "analyst_expected_return": 0.135, "std_dev": 0.22},
    "PAYGOLD": {"beta": 0.20, "analyst_expected_return": 0.08, "std_dev": 0.12},
    "PAYBOND": {"beta": 0.05, "analyst_expected_return": 0.065, "std_dev": 0.04},
    "PAYTECH": {"beta": 1.55, "analyst_expected_return": 0.19, "std_dev": 0.34},
}
RISK_FREE_RATE = 0.07
MARKET_RETURN = 0.13
(These are illustrative fictional tickers for this exercise, not real listed securities. analyst_expected_return is a separate illustrative reference figure — e.g., representing an outside analyst's view — and is intentionally not used anywhere in your CAPM computation. Your agent's CAPM expected-return calculation uses ONLY beta via the CAPM formula below; the resulting computed figure is expected to differ from analyst_expected_return, which is not a bug.)

Investor profiles (investor_profiles.py):

INVESTOR_PROFILES = [
    {"investor_id": "INV01", "risk_tolerance": "Conservative", "horizon_years": 3, "investment_amount_inr": 200000},
    {"investor_id": "INV02", "risk_tolerance": "Moderate", "horizon_years": 7, "investment_amount_inr": 500000},
    {"investor_id": "INV03", "risk_tolerance": "Aggressive", "horizon_years": 12, "investment_amount_inr": 300000},
    {"investor_id": "INV04", "risk_tolerance": "Moderate", "horizon_years": 5, "investment_amount_inr": 800000},
    {"investor_id": "INV05", "risk_tolerance": "Aggressive", "horizon_years": 2, "investment_amount_inr": 150000},
]
Disclosure snippets (disclosure_snippets.py — use this exact text):

DISCLOSURE_SNIPPETS = [
    "doc_01: Assuming input costs remain stable through the next two quarters, we expect "
    "margins to hold at current levels.",
    "doc_02: The company faces an ongoing litigation matter related to a former vendor "
    "contract; management believes the exposure is not material.",
    "doc_03: Our top three customers together account for approximately 42 percent of "
    "total revenue this year.",
    "doc_04: We remain cautiously optimistic about demand recovery, though visibility "
    "beyond the next quarter is limited given macro uncertainty.",
    "doc_05: The board is confident in the long-term strategy and has approved an "
    "expanded capital expenditure plan for the coming year.",
    "doc_06: A recent regulatory notice has been received regarding data-localization "
    "compliance; the company is in active dialogue with the regulator.",
]
Tasks
Part A — Portfolio advisory agent (agentic think-act-observe pattern)

Implement an agent loop in advisory_agent.py with three explicit stages:
Think: read one investor profile and determine its allocation using the required, prescribed lookup table below — this is not a free-choice mapping, it is the exact rule every submission must implement:
Conservative risk_tolerance -> equal-weight (1/3 each) across {"PAYBOND", "PAYGOLD", "PAYRETAIL"}
Moderate risk_tolerance     -> equal-weight (1/3 each) across {"PAYRETAIL", "PAYINFRA", "PAYGOLD"}
Aggressive risk_tolerance   -> equal-weight (1/3 each) across {"PAYTECH", "PAYFIN", "PAYINFRA"}
Act (tool call): call a get_stock_data(ticker) "tool" function that looks up beta/analyst_expected_return/std_dev from STOCK_UNIVERSE for each ticker in the prescribed allocation (this simulates an external-API tool call; no real API is needed since the data is local).
Observe → decide: using the prescribed 1/3-each allocation for the investor's risk_tolerance tier, compute the portfolio's CAPM-expected return (per stock, E(R) = R_f + β(E(R_m) − R_f), using ONLY beta — never analyst_expected_return — then weight-averaged across the 3 tickers) and portfolio variance using: Var(R_p) = Σᵢ wᵢ²σᵢ² + 2·Σ_{i<j} wᵢwⱼ·Cov(Rᵢ,Rⱼ), with Cov(Rᵢ,Rⱼ) = ρ·σᵢ·σⱼ and a stated pairwise correlation ρ = 0.3 for every pair of the three tickers in the prescribed allocation. Convert variance to portfolio standard deviation.
Human-in-the-loop escalation: if the computed portfolio standard deviation exceeds 20%, do not auto-finalize the recommendation — instead print/return an "ESCALATED_TO_HUMAN_ADVISOR" flag with the computed numbers attached. Otherwise, finalize the recommendation. With the prescribed allocation table and ρ = 0.3, the expected pattern is deterministic: Conservative (INV01, ~8.44% std dev) and Moderate (INV02, INV04, ~12.57% std dev) must NOT escalate; Aggressive (INV03, INV05, ~20.58% std dev) must escalate.
The final narrative sentence describing the recommendation is the only part gated by MOCK_LLM. Mock mode (graded baseline): build the sentence from an f-string template inserting the computed numbers (e.g., f"For {risk_tolerance} investor {investor_id}, we recommend an allocation across {tickers} with an expected portfolio return of {return:.1%} and volatility of {vol:.1%}."). Optional MOCK_LLM=0 extension: prompt the LLM to phrase the same numbers more naturally. Run all 5 investor profiles and record each result.
Part B — Structured disclosure extraction

In extract_disclosure.py, implement extract_signals(snippet: str) -> dict returning {"risk_flags": [...], "hedging_detected": bool, "sentiment": "confident"|"cautious"|"neutral"}. Mock mode (graded baseline): use keyword/regex rules — flag "litigation", "regulatory", or "customer concentration"-style phrasing as risk flags; flag hedging phrases containing "assuming", "cautiously", or "visibility"; classify sentiment as "confident" if the snippet contains "confident"/"approved", "cautious" if it contains a hedging phrase, else "neutral" — no LLM call made. Optional MOCK_LLM=0 extension: call the LLM instead, validating its JSON output against the same schema (retry once on a validation failure before falling back to the mock result). Run this against all 6 committed disclosure snippets and record the output.
Part C — Multi-agent debate demo

Implement a 3-agent debate in debate.py for one ticker of your choice from STOCK_UNIVERSE: a bull agent, a bear agent, and a synthesizer. Mock mode (graded baseline): build each agent's argument from a template referencing that ticker's actual beta/analyst_expected_return/std_dev numbers (e.g., bull: "With an expected return of {r:.1%} against a beta of {b:.2f}, this offers attractive risk-adjusted upside."; bear: references the std_dev as a risk); the synthesizer combines both into a 2–3 sentence balanced summary — no LLM call made. Optional MOCK_LLM=0 extension: call the LLM for richer arguments instead.
Part D — DCF valuation calculator

In dcf_calculator.py, implement a discounted-cash-flow valuation for a hypothetical Paytm business line, given (as inputs you choose and state in writing): a base free-cash-flow figure computed as unlevered Free Cash Flow to the Firm (FCFF), using the formula FCFF = EBIT × (1 − tax rate) + D&A − CapEx − ΔNet Working Capital (or an equivalent unlevered formula you state), in INR; a 5-year projected growth rate that fades to a lower terminal growth rate; and a WACC you compute from R_e = R_f + β(E(R_m) − R_f) (cost of equity, using any STOCK_UNIVERSE beta) blended with an illustrative after-tax cost of debt you choose, weighted by an illustrative capital-structure split. Constraint on the terminal growth rate: choose it at least 3 percentage points below your base-case WACC, so that even after the ±1 percentage-point sensitivity adjustments (WACC − 1pp on one axis, growth + 1pp on the other), WACC still exceeds terminal growth in every one of the 9 grid cells — as a required self-check before submitting, confirm WACC − terminal_growth ≥ 1 percentage point in the worst-case sensitivity cell. Project 5 years of free cash flow, compute a terminal value via the growing-perpetuity formula, discount everything to present value, and produce a sensitivity table varying the discount rate and terminal growth rate by ±1 percentage point each (a 3×3 grid). Cross-check your DCF output against a simple EV/EBITDA multiple (choose an illustrative EBITDA and multiple, stated in writing) and comment in 2–3 sentences on how the two estimates compare.
Part E — Blockchain/crypto risk-analysis appendix (written, no code required)

Write blockchain_risk_note.md (600–900 words) covering:
A short assessment of what a hypothetical "Paytm Crypto Insights" watchlist feature would need to get right on stablecoin type and DeFi/DAO governance risk before Paytm could responsibly surface it to retail users (reference the fiat-collateralized vs. algorithmic stablecoin distinction and tokenomics/DAO governance risks).
A crypto-as-an-asset-class recommendation for Paytm Money: using the standard finding that CAPM-style portfolio theory does not favor including an asset lacking intrinsic value/dividends, such as cryptocurrency, in an optimal portfolio, together with low/negative correlation with traditional assets, heavy-tailed/ positively-skewed returns, survivorship bias, and high transaction costs, state a specific, justified maximum allocation percentage (or a justified "zero allocation") recommendation for a retail advisory product.
A short section applying the T.A.N.G. (Temptation/Authority/Need/Greed) fraud framework to identify the two social-engineering risk vectors you consider most relevant to a UPI/wallet + lending + wealth platform specifically, and one bank-side real-time defense mechanism that mitigates each.
Acceptance criteria (your submission is complete when…)
The advisory agent's think/act/observe stages are all present and clearly separated in code; the allocation for each investor profile matches the prescribed lookup table exactly (Conservative → PAYBOND/PAYGOLD/PAYRETAIL, Moderate → PAYRETAIL/PAYINFRA/ PAYGOLD, Aggressive → PAYTECH/PAYFIN/PAYINFRA, each equal-weighted); get_stock_data(...) is used as the tool call; CAPM expected return (computed from beta only, never analyst_expected_return) and portfolio variance/std are computed correctly for all 5 investor profiles; the human-in-the-loop escalation flag correctly fires whenever computed portfolio std exceeds 20% and is suppressed otherwise — deterministically, INV01 (~8.44% std dev) and INV02/INV04 (~12.57% std dev) do NOT escalate, while INV03 and INV05 (~20.58% std dev) DO escalate; the narrative sentence is correctly gated by MOCK_LLM with the mock path fully deterministic and correct.
extract_signals(...) runs against all 6 committed disclosure snippets in mock mode with no network call, and correctly flags at least the litigation snippet (doc_02) as a risk flag, at least one hedging-phrase snippet as hedging_detected=True, and the board-approval snippet (doc_05) as "confident".
The 3-agent debate demo runs in mock mode with no network call, and each agent's argument text references the chosen ticker's actual numeric values.
The DCF calculator produces a 5-year unlevered FCFF projection (computed via the stated EBIT × (1 − tax) + D&A − CapEx − ΔNWC formula or an equivalent stated unlevered formula), a terminal value, a WACC computed from the stated CAPM/cost-of-debt/weights, a 3×3 sensitivity table in which WACC exceeds terminal growth in every one of the 9 grid cells (terminal growth chosen ≥ 3 percentage points below base-case WACC), and an EV/EBITDA cross-check with a written comparison.
blockchain_risk_note.md addresses all three required sections (stablecoin/DAO risk, a specific justified crypto-allocation recommendation, and the T.A.N.G.-framework analysis with a named bank-side defense per vector) at the stated length.
README documents which MOCK_LLM mode was used for the recorded run transcripts (plus free-tier usage notes, only if the optional extension was attempted).
Submission
This part lives at /ai_advisory_blockchain inside the single project repository: stock_universe.py, investor_profiles.py, disclosure_snippets.py, advisory_agent.py, extract_disclosure.py, debate.py, dcf_calculator.py, blockchain_risk_note.md, and a short part-level note (in /ai_advisory_blockchain/README.md or the root README) with the recorded example run transcripts (all recorded with MOCK_LLM left at its default) and the DCF sensitivity table.