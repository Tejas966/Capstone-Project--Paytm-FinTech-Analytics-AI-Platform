# Part 1 — Payments & Fraud Analytics

**Paytm vertical:** UPI / Wallet / QR merchant payments  

---

## How to Run (end-to-end)

```bash
cd payments_fraud_analytics

# Step 1: Generate all CSVs (committed output included)
python generate_data.py

# Step 2: Build SQLite database and run all 9 SQL queries
python sql_queries.py

# Step 3: Run payment reconciliation
python reconcile.py

# Step 4: Generate 4-layer dashboard (saves PNGs to charts/)
python dashboard.py

# Step 5: (Re-)generate the Excel workbook
python generate_workbook.py
```

---

## Part A — Excel Merchant Workbook (`merchant_workbook.xlsx`)

**File:** `merchant_workbook.xlsx` — 5 sheets

| Sheet | Purpose |
|---|---|
| **Merchants** | Raw 40-merchant reference table |
| **Transactions** | Full 547-row ledger + VLOOKUP + nested IF columns |
| **HLOOKUP_Demo** | Horizontally-laid MDR fee-rate table + HLOOKUP formulas |
| **Pivot_Summary** | Real Excel PivotTable by merchant_id x status (created via xlwings) |
| **Unique_Days** | Qualifying merchant-day totals + classification for top 10 merchants |

### VLOOKUP (Transactions sheet, columns I–K)
```excel
=IFERROR(VLOOKUP($C2, Merchants!$A$2:$D$41, 2, FALSE), "Merchant not found")
```
- Uses **fixed range** with `$` absolute references (`$A$2:$D$41`)
- `IFERROR` wraps every lookup — any unmatched `merchant_id` shows `"Merchant not found"`
- Three VLOOKUP columns: `merchant_name` (col index 2), `category` (3), `region` (4)

### HLOOKUP (HLOOKUP_Demo sheet)
```excel
=HLOOKUP(B6, $B$2:$E$3, 2, FALSE)
```
- Reference table is horizontal: **payment methods across columns**, fee rate in the row below
- `row_index_num = 2` fetches the MDR fee % row

**MDR fee assumptions (illustrative, documented in workbook):**

| Method | MDR Fee % | Rationale |
|---|---|---|
| UPI | 0.25% | RBI-capped for small merchants |
| Wallet | 0.50% | Paytm Wallet interchange |
| Card | 1.80% | Average card interchange |
| Netbanking | 0.90% | Bank surcharge |

### Nested IF / AND Classification Rule
```excel
=IF(AND(
  SUMPRODUCT(($C$2:$C$548=$C2)*(LEFT($D$2:$D$548,10)=LEFT($D2,10))*$E$2:$E$548) > 5000,
  $K2 <> "East"
), "High-Value Merchant Day", "Standard")
```
**Documented rule:** A transaction is classified `"High-Value Merchant Day"` when:
1. The merchant's **daily transaction total** (sum of all `amount_inr` for the same `merchant_id` on the same calendar day, computed via `SUMPRODUCT`) exceeds **INR 5,000**
2. `region != "East"` (looked up via VLOOKUP in column K)

Both conditions must hold (AND logic). The `SUMPRODUCT` formula computes the daily total inline for each row by matching `merchant_id` (column C) and date portion of `transaction_time` (column D via `LEFT(...,10)`).

### Pivot Table (Pivot_Summary sheet)
- **Real Excel PivotTable** created via xlwings COM automation (not a static pandas export)
- Rows: `merchant_id` (all 40 merchants)
- Columns: `status` (captured, failed, chargeback)
- Data fields: `Total Amount (INR)` (Sum) and `Txn Count` (Count)
- Source data: Transactions sheet columns A:H

### Unique Days (Unique_Days sheet)
- Shows top 10 merchants by transaction count
- **qualifying_days**: count of calendar days where the merchant's daily total exceeded INR 5,000 (actual daily totals, not averages)
- **max_daily_total**: the highest single-day total for each merchant
- Classification applies the same IF/AND rule: qualifying days > 0 AND region != East

---

## Part B — SQL Fraud-Pattern Detection (`sql_queries.py` → `paytm_payments.db`)

### Schema (PK/FK declared)
```sql
merchants    (merchant_id PK, merchant_name, category, region)
users        (user_id PK, signup_date)
transactions (transaction_id PK, user_id FK→users, merchant_id FK→merchants,
              transaction_time, amount_inr, payment_method, status, risk_score)
```

### Queries Summary

| Query | Purpose | Clauses Used |
|---|---|---|
| Q1 | Top 15 high-value captured txns | SELECT DISTINCT, WHERE, ORDER BY, LIMIT |
| Q2 | GMV by payment method | GROUP BY, HAVING, COUNT, SUM, AVG |
| Q3 | Transactions + merchant details | INNER JOIN, WHERE, ORDER BY, LIMIT |
| Q4 | All merchants with stats (incl. 0-txn) | LEFT JOIN, GROUP BY, COALESCE, NULLIF |
| Q5 | Chargeback impact | COUNT, COUNT DISTINCT, SUM |
| Q6 | **Burner accounts** (required) | INNER JOIN, julianday(), boundary check |
| Q7 | **Velocity attacks** (required) | GROUP BY time bucket, HAVING COUNT ≥ 3 |
| Q8 | GMV by merchant category | INNER JOIN, GROUP BY |
| Q9 | Daily summary (dashboard prep) | DATE(), GROUP BY date |

### Key Fraud Query Results

**Q6 — Burner Accounts:**  
Boundary: `0 <= (julianday(transaction_time) - julianday(signup_date)) < 30`  
Result: **15 / 15 seeded burner-account rows found** ✅ (TXN200000–TXN200014)

**Q7 — Velocity Attacks:**  
Method: floor `transaction_time` to 10-minute bucket using `SUBSTR(..., 1, 15) || '0:00'`, group by `(user_id, bucket)`, filter `COUNT >= 3`  
Result: **8 / 8 seeded velocity clusters found** ✅

---

## Part C — Payment Reconciliation (`reconcile.py`)

### Function
```python
reconcile_payments(ledger_df, gateway_df)
    → (missing_in_gateway, extra_in_gateway, amount_mismatches, status_mismatches)
```

**Implementation:**
- Uses **set operations** on `transaction_id` for missing / extra detection
- Uses **`pd.merge`** for pairwise amount and status comparison on common IDs

### Results vs Ledger (547 rows)

| Discrepancy Type | Found | Expected (~%) |
|---|---|---|
| Missing in gateway (~5%) | **27** | 27 ✅ |
| Extra in gateway (~2%) | **10** | 10 ✅ |
| Amount mismatches (~3%) | **16** | 16 ✅ |
| Status mismatches (~2%) | **9** | ~10 ✅ |

All counts are consistent with the injection rates in `generate_data.py`.

---

## Part D — Dashboard (`dashboard.py` → `charts/`)

### Layer 1 — Headline Scorecards (`charts/layer1_scorecards.png`)

| Metric | Value | Definition |
|---|---|---|
| **Total GMV** | INR 382,603 | Sum of all `amount_inr` in ledger |
| **Success Rate** | 85.56% | `captured` txns / all txns |
| **Recon Match Rate** | 90.49% | Txns in BOTH files with identical `amount_inr` AND `status` / total ledger |
| **Chargeback Ratio** | 5.12% | Count of `chargeback` txns / all txns (count-based, not amount-based) |

**Interpretation:** Total GMV of INR 382K was processed over the 30-day window. The 90.49% match rate reflects the deliberately-injected gateway discrepancies. A 5.12% chargeback ratio — far above a healthy <1% industry benchmark — is driven primarily by the 15 seeded burner-account fraudsters and warrants immediate escalation to the risk team.

### Layer 2 — Daily Trends (`charts/layer2_trends.png`)

**Interpretation:** Daily GMV ranges from ~INR 4K to ~INR 28K with no strong weekly seasonality, consistent with the uniform random distribution used in data generation. Chargeback spikes on Jan 23 (4 chargebacks) and Jan 29 (3 chargebacks) align with late-month burner-account activity injected into the dataset (velocity attacks are distinct and do not result in chargebacks). Ops teams should configure real-time alerts when any single day exceeds 3 chargebacks or when GMV drops >50% below the 30-day rolling average.

### Layer 3 — GMV Breakdown (`charts/layer3_breakdown.png`)

**Interpretation:** UPI dominates GMV (consistent with the 55% method weight), followed by Wallet, Card, and Netbanking — mirroring Paytm's real-world UPI-first strategy. Ecommerce and Travel lead GMV by category (avg ticket INR 768 and 753), while Grocery drives the most transaction count at a lower ticket (INR ~631). This high-frequency / low-value pattern in Grocery signals different fraud risk than the high-value ecommerce chargebacks.

### Layer 4 — Merchant Details Table (`charts/layer4_merchant_table.png`)

**Per-merchant chargeback rule:** `chargeback_ratio = count(chargeback txns) / count(all txns for that merchant)` — count-based, merchant-scoped.  
**Flag threshold:** > 1%

**Interpretation:** 6 of the top 10 merchants by transaction count are flagged as high-risk (chargeback ratio > 1%), with Merchant_029 at a severe 15.79%. These merchants should be placed on a Paytm Risk Watch List for immediate investigation — the pattern is consistent with either compromised POS terminals or coordinated fraud rings targeting specific merchant locations. The details layer is rendered as a saved image (not a live DataFrame) to satisfy the submission requirement.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| MDR fee rates | UPI 0.25%, Wallet 0.50%, Card 1.80%, Netbanking 0.90% | Illustrative industry approximations; documented in workbook |
| Excel nested IF | SUMPRODUCT daily total > 5000 AND region != "East" | Computes merchant's daily total inline via SUMPRODUCT; classifies as "High-Value Merchant Day" |
| Velocity bucket | Floor to 10-min bucket via `SUBSTR(txn_time,1,15)||'0:00'` | Deterministic SQLite-compatible approach; surfaces all 8 seeded clusters |
| Burner boundary | `0 <= age_days < 30` using `julianday()` | Matches the brief's explicit boundary spec |
| Match rate | Requires identical `amount_inr` AND `status` in both files | Per the brief's exact definition |
| Chargeback ratio | Count-based (not amount-based) | Per brief specification |
