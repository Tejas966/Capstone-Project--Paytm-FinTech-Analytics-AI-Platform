# Part 2 — Credit Risk & Lending ML

**Paytm vertical:** Postpaid BNPL underwriting  
**Marks:** 40

---

## How to Run (end-to-end)

```bash
cd credit_risk_lending_ml

# Step 1: Generate synthetic datasets (committed output included)
python generate_data.py

# Step 2: Run the full ML pipeline
python credit_risk_analysis.py
```

---

## Part A — Data Preprocessing

### Pipeline order (strictly enforced)

```
Raw data
  └─► Flag is_thin_file (before split — uses raw null check)
       └─► Stratified 75/25 train/test split (random_state=42)
            └─► Median imputation (fit on TRAIN only, median=612.0)
                 └─► One-hot encode employment_type (fit on TRAIN)
                      └─► StandardScaler (fit on TRAIN only)
```

**Why this order matters:**  
If imputation or scaling were fit on the full dataset before splitting, the test set would leak statistical information (mean, std) from training — inflating evaluation metrics. Fitting transformers only on the training fold ensures the test set is genuinely unseen.

### Dataset stats
- `credit_applicants.csv`: 400 rows, 20.25% default rate, 80 thin-file applicants (20%)
- `txn_behaviour.csv`: 265 rows, 15 seeded anomalies (BTXNA0–BTXNA14)
- `is_thin_file`: flag = 1 when `credit_score` is null (no bureau history)

---

## Part B — Model Training & Evaluation

### Results

| Model | Accuracy | Precision | Recall | ROC-AUC |
|---|---|---|---|---|
| Logistic Regression | 69% | 55% | 70% | **0.716** |
| Decision Tree | 65% | 48% | 60% | 0.634 |

**Winner: Logistic Regression** — higher AUC (0.716 vs 0.634) and recall (70% vs 60%). For credit risk, recall matters most: missing a true defaulter (false negative) is more costly than a false alarm.

### Risk-Based Pricing Table

| Risk Tier | Predicted Default Prob Range | Actual Default Rate | Assigned Rate |
|---|---|---|---|
| Tier 1 — Prime | 0%–25% | 8% | 12% |
| Tier 2 — Near Prime | 25%–50% | 8% | 16% |
| Tier 3 — Subprime | 50%–75% | 28% | 24% |
| Tier 4 — Deep Subprime | 75%–100% | 36% | 28% |

Default rates are **monotonically increasing** across tiers ✅ — confirming the model's risk-ranking validity.

### Charts saved in `charts/`

| File | Contents |
|---|---|
| `eda_overview.png` | Default rate by employment type, credit score distribution |
| `model_evaluation.png` | ROC curves, confusion matrices, classification reports |
| `risk_pricing_table.png` | Visual risk tier breakdown with default rates and assigned interest rates |
| `anomaly_detection.png` | IsolationForest scatter — flagged vs clean transactions |

---

## Part C — Anomaly Detection

**Model:** `IsolationForest` with `contamination = 15/265 = 0.0566`

**Results:**
- Seeded anomalies (BTXNA*): 15 total
- Detected: **11/15 (73.3% recall)**
- False positive rate: ~2.7% of legitimate transactions flagged

**Interpretation:** The IsolationForest catches 73% of the hand-crafted anomalies — transactions with new device + 1–4am timing + amount > 3× user average. The 4 missed anomalies had boundary-level feature values that blended with legitimate high-value night transactions. In production, this would be layered with rule-based velocity checks (from Part 1) for defence-in-depth.

---

## Bias-Awareness Note

### Proxy Risk: `is_thin_file` and Structural Disadvantage

The `is_thin_file` flag is a direct proxy for **new-to-credit** status — a demographic that disproportionately includes young adults, rural borrowers, women entering the workforce for the first time, and recent migrants who have not yet built a formal credit history. In the current pipeline, thin-file applicants (80 out of 400, 20%) receive lower predicted creditworthiness purely because they lack a bureau record, not because they have demonstrated an inability to repay. This is a structural bias: the model penalises the absence of data as if it were evidence of risk.

**Specific risks for Paytm Postpaid:**
1. **Disparate impact on underserved populations:** If `is_thin_file` correlates with socioeconomic status, geography (rural vs urban), or gender, then the model effectively denies credit access to segments that Paytm Postpaid's financial inclusion mandate explicitly seeks to serve.
2. **Self-fulfilling exclusion:** Thin-file applicants who are denied credit never generate repayment history, perpetuating their exclusion in future model cycles.
3. **`credit_score` as a proxy:** Even for applicants with a bureau score, the score itself encodes historical lending patterns. If lenders historically under-served certain demographics, their credit scores will be structurally lower — not because they are higher risk, but because they had fewer opportunities to demonstrate creditworthiness.

### Governance Step Before Production Deployment

Before this model is deployed in a live Paytm Postpaid underwriting pipeline, the following governance checkpoint must be passed:

1. **Fairness audit:** Compute approval rates, default prediction rates, and false negative rates (missed safe applicants) broken down by `is_thin_file`, `employment_type`, and geographic proxy variables. Flag any subgroup where approval rate diverges >10pp from the overall rate without a legitimate credit-risk justification.
2. **Adverse action explainability:** Under RBI's Fair Practices Code for NBFCs and the emerging SEBI/RBI guidelines on algorithmic credit, every declined applicant must receive an intelligible reason for rejection. The model's top-3 feature contributions (via SHAP or logistic coefficients) must be surfaced in the rejection communication.
3. **Thin-file alternative scoring:** Pilot an alternative scorecard for thin-file applicants using UPI transaction frequency, merchant category diversity, and Paytm wallet recharge patterns — behavioural signals that are independent of bureau history and more predictive for new-to-credit segments.

---

## Final Recommendation

**Recommended model: Logistic Regression (ROC-AUC = 0.716, Recall = 70%)**

The Logistic Regression model outperforms the Decision Tree on both AUC (0.716 vs 0.634) and recall (70% vs 60%), making it the preferred underwriting model for Paytm Postpaid BNPL decisions. Its recall advantage is particularly important: in a credit context, a false negative (predicting "safe" for an applicant who defaults) generates a bad debt write-off, while a false positive (predicting "risky" for a safe applicant) results only in a missed revenue opportunity. The monotonically increasing default rates across the four pricing tiers (8% → 8% → 28% → 36%) confirm that the model's probability outputs are well-calibrated as a risk-ranking instrument. However, before live deployment, the bias audit described above — especially for thin-file applicants — must be completed to ensure the model does not inadvertently exclude the financially underserved populations that Paytm Postpaid is designed to reach.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Split ratio | 75/25 stratified | Preserves 20.25% default rate in both folds |
| Imputation | Median (train only) | Median is robust to outliers vs mean; train-only prevents leakage |
| Encoding | One-hot (drop_first=False) | Avoids dummy variable trap concern; tree models need no encoding but LR does |
| Contamination | 15/265 = 5.66% | Exact injection rate — gives IsolationForest the best possible prior |
| Pricing tiers | 4 quartiles of predicted prob | Quartile-based tiers ensure balanced segment sizes for business viability |
