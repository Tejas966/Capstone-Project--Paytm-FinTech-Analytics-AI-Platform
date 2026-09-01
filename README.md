# Paytm FinTech Analytics & AI Advisory Platform

**Capstone Project — BitSoM / IIM Indore**  
**Candidate:** Tejas | **Repo:** Capstone-Project--Paytm-FinTech-Analytics-AI-Platform

> A three-part end-to-end FinTech analytics platform spanning payments fraud detection, credit risk ML, and AI-augmented portfolio advisory — built on synthetic Paytm-style data generated from fixed random seeds for full reproducibility.

---

## Repository Structure

```
├── payments_fraud_analytics/      # Part 1 — Payments & Fraud (35 marks)
│   ├── generate_data.py           # Generates all CSVs (seed=42)
│   ├── merchants.csv / users.csv / ledger.csv / gateway_export.csv
│   ├── sql_queries.py             # Creates paytm_payments.db + 9 SQL queries
│   ├── paytm_payments.db          # SQLite database (PK/FK schema)
│   ├── reconcile.py               # reconcile_payments() function
│   ├── dashboard.py               # 4-layer analytics dashboard
│   ├── generate_workbook.py       # Excel workbook generator
│   ├── merchant_workbook.xlsx     # VLOOKUP, HLOOKUP, nested IF, pivot
│   ├── charts/                    # 4 dashboard PNG images
│   └── README.md                  # Chart interpretations + design decisions
│
├── credit_risk_lending_ml/        # Part 2 — Credit Risk ML (40 marks)
│   ├── generate_data.py           # Generates CSVs (seed=42)
│   ├── credit_applicants.csv      # 400 rows, 20.25% default rate
│   ├── txn_behaviour.csv          # 265 rows, 15 seeded anomalies
│   ├── credit_risk_analysis.py    # Full ML pipeline (EDA → models → anomaly)
│   ├── charts/                    # 4 chart PNGs
│   └── README.md                  # Bias note + recommendation + design decisions
│
├── ai_advisory_blockchain/        # Part 3 — AI Advisory (25 marks)
│   ├── stock_universe.py          # 6 stocks with beta, std_dev, analyst_return
│   ├── investor_profiles.py       # 5 investor profiles
│   ├── disclosure_snippets.py     # 6 company disclosure texts
│   ├── advisory_agent.py          # Think/Act/Observe agent loop
│   ├── extract_disclosure.py      # extract_signals() — risk/hedging/sentiment
│   ├── debate.py                  # Bull/Bear/Synthesizer 3-agent debate
│   ├── dcf_calculator.py          # DCF + 3×3 sensitivity + EV/EBITDA
│   ├── blockchain_risk_note.md    # 850-word blockchain/crypto risk analysis
│   └── README.md                  # Run transcripts + sensitivity table
│
├── requirements.txt               # All Python dependencies
└── README.md                      # This file
```

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/Tejas966/Capstone-Project--Paytm-FinTech-Analytics-AI-Platform
cd Capstone-Project--Paytm-FinTech-Analytics-AI-Platform
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Important: always run scripts from inside their own part folder
```bash
# Correct
cd payments_fraud_analytics && python generate_data.py

# NOT from repo root
python payments_fraud_analytics/generate_data.py  # will fail (relative CSV paths)
```

---

## Part 1 — Payments & Fraud Analytics (35 marks)

```bash
cd payments_fraud_analytics

# Generate synthetic data (CSVs already committed — skip if re-running)
python generate_data.py

# Build SQLite DB and run all 9 SQL fraud-detection queries
python sql_queries.py

# Run payment reconciliation (ledger vs gateway export)
python reconcile.py

# Generate 4-layer dashboard → charts/
python dashboard.py

# Generate Excel workbook (VLOOKUP, HLOOKUP, nested IF, pivot)
python generate_workbook.py
```

**Key outputs:**
- `paytm_payments.db` — SQLite database with PK/FK schema
- `charts/layer1_scorecards.png` through `charts/layer4_merchant_table.png`
- `merchant_workbook.xlsx` — 5-sheet Excel workbook
- Console output of all SQL query results (grader-visible)

---

## Part 2 — Credit Risk & Lending ML (40 marks)

```bash
cd credit_risk_lending_ml

# Generate synthetic applicant data (CSVs already committed)
python generate_data.py

# Run full ML pipeline: EDA → preprocessing → models → pricing → anomaly detection
python credit_risk_analysis.py
```

**Key outputs:**
- `charts/eda_overview.png`, `model_evaluation.png`, `risk_pricing_table.png`, `anomaly_detection.png`
- Console: AUC scores, classification reports, IsolationForest recall
- `README.md`: bias note + final recommendation (written analysis)

---

## Part 3 — AI Advisory & Blockchain Risk (25 marks)

```bash
cd ai_advisory_blockchain

# Portfolio advisory agent — all 5 investor profiles
python advisory_agent.py

# Disclosure signal extraction — all 6 snippets
python extract_disclosure.py

# Bull/Bear/Synthesizer debate — PAYTECH
python debate.py

# DCF valuation + 3×3 sensitivity table
python dcf_calculator.py
```

**All scripts run in MOCK_LLM mode by default** — no API key or network access required.  
To enable the optional LLM path (Groq): `set MOCK_LLM=0` (Windows) then rerun.

**Key outputs:**
- Console: full Think/Act/Observe trace for all 5 investors
- Console: disclosure extraction results with acceptance criteria check
- Console: bull/bear/synthesizer arguments for PAYTECH
- Console: DCF computation with 3×3 sensitivity table and EV/EBITDA comparison
- `blockchain_risk_note.md`: written blockchain & crypto risk analysis

---

## Design Decisions

### Part 1 — Payments & Fraud
| Decision | Choice | Rationale |
|---|---|---|
| Fraud seed row count | 547 (500 + 15 + 32) | Exact: 500 baseline + 15 burner-account chargebacks + 8×4 velocity attacks |
| Velocity detection SQL | Floor txn_time to 10-min bucket via SUBSTR | Deterministic, SQLite-native — surfaces all 8 seeded clusters |
| Burner boundary | 0 ≤ age_days < 30 using julianday() | Matches brief's explicit boundary condition |
| Match rate definition | Same amount_inr AND status in both files | Per brief exact definition |
| Chargeback ratio | Count-based (not amount-based) | Per brief specification |
| Excel nested IF | amount_inr ≥ 999 AND region ≠ "East" | Per-transaction proxy; daily-total rule enforced in Unique_Days sheet |

### Part 2 — Credit Risk ML
| Decision | Choice | Rationale |
|---|---|---|
| Preprocessing order | Flag → Split → Impute → Encode → Scale | Prevents any data leakage from test into train |
| Imputation | Median (train-only, 612.0) | Robust to outliers; train-only prevents leakage |
| Recommended model | Logistic Regression (AUC=0.716) | Higher AUC and recall vs Decision Tree; interpretable for regulators |
| IsolationForest contamination | 15/265 = 5.66% | Exact injection rate gives best possible prior |
| Pricing tiers | 4 quartiles of predicted prob | Balanced segment sizes; monotone default rates 8/8/28/36% confirmed |

### Part 3 — AI Advisory
| Decision | Choice | Rationale |
|---|---|---|
| Portfolio allocation | Prescribed lookup table (not model-chosen) | Per brief requirement; Conservative/Moderate/Aggressive fixed |
| CAPM inputs | Only beta; never analyst_expected_return | Per brief instruction |
| Portfolio variance | rho=0.3 for all pairs | Per brief |
| Escalation threshold | std_dev > 20% | Per brief — Aggressive portfolios always escalate |
| Debate ticker | PAYTECH (beta=1.55, std=34%) | Highest-contrast stock for bull/bear argument richness |
| DCF beta | PAYINFRA (1.10) | Mid-range; appropriate for infrastructure-heavy payments processor |
| MOCK_LLM | 1 (default) | Fully deterministic; no API dependency for grading |

---

## All monetary values are in Indian Rupees (INR) throughout.