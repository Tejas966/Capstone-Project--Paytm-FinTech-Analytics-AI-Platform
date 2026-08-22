# Part 3 — AI-Augmented FinTech Advisory & Blockchain Risk

**Paytm vertical:** Money / Wealth advisory + blockchain risk appendix  
**Marks:** 25  
**MOCK_LLM mode used for all recorded run transcripts:** `MOCK_LLM=1` (default — no API key required)

---

## How to Run (end-to-end)

```bash
cd ai_advisory_blockchain

# Part A: Portfolio advisory agent (all 5 investors)
python advisory_agent.py

# Part B: Structured disclosure extraction (all 6 snippets)
python extract_disclosure.py

# Part C: Bull/Bear/Synthesizer debate (PAYTECH)
python debate.py

# Part D: DCF calculator + sensitivity table
python dcf_calculator.py
```

All scripts run in **MOCK_LLM mode** (default). No API key or network access required.

---

## Part A — Portfolio Advisory Agent (`advisory_agent.py`)

### Think → Act → Observe Pattern

**THINK**: Reads investor's `risk_tolerance` and maps it to the prescribed allocation table (exact, not free-choice):

| Risk Tolerance | Allocation (equal 1/3 each) |
|---|---|
| Conservative | PAYBOND, PAYGOLD, PAYRETAIL |
| Moderate | PAYRETAIL, PAYINFRA, PAYGOLD |
| Aggressive | PAYTECH, PAYFIN, PAYINFRA |

**ACT**: Calls `get_stock_data(ticker)` tool function for each of the 3 tickers — simulates an external API call returning `beta`, `std_dev`, `analyst_expected_return` from `STOCK_UNIVERSE`.

**OBSERVE → DECIDE**:
- Computes CAPM expected return per stock: `E(R) = R_f + β × (E(R_m) − R_f)` using **only beta** (never `analyst_expected_return`)
- Weight-averages across 3 tickers (w = 1/3 each) → portfolio expected return
- Computes portfolio variance: `Var = Σ wᵢ²σᵢ² + 2Σᵢ<ⱼ wᵢwⱼρσᵢσⱼ` with **ρ = 0.3** for all pairs
- Takes square root → portfolio std dev
- If `portfolio_std > 20%` → `ESCALATED_TO_HUMAN_ADVISOR`

### Run Transcript (MOCK_LLM=1)

| Investor | Risk | Tickers | E(R) | Std Dev | Decision |
|---|---|---|---|---|---|
| INV01 | Conservative | PAYBOND+PAYGOLD+PAYRETAIL | 9.20% | **8.44%** | AUTO_APPROVED |
| INV02 | Moderate | PAYRETAIL+PAYINFRA+PAYGOLD | 11.30% | **12.57%** | AUTO_APPROVED |
| INV03 | Aggressive | PAYTECH+PAYFIN+PAYINFRA | 15.00% | **20.58%** | ESCALATED_TO_HUMAN_ADVISOR |
| INV04 | Moderate | PAYRETAIL+PAYINFRA+PAYGOLD | 11.30% | **12.57%** | AUTO_APPROVED |
| INV05 | Aggressive | PAYTECH+PAYFIN+PAYINFRA | 15.00% | **20.58%** | ESCALATED_TO_HUMAN_ADVISOR |

Escalation verification: INV01, INV02, INV04 — NOT escalated ✅ | INV03, INV05 — ESCALATED ✅ | **ALL PASS**

---

## Part B — Disclosure Extraction (`extract_disclosure.py`)

`extract_signals(snippet)` returns `{risk_flags, hedging_detected, sentiment}` using keyword/regex rules — no LLM, no network call.

| Doc | Key Signal | risk_flags | hedging_detected | sentiment |
|---|---|---|---|---|
| doc_01 | "Assuming input costs..." | [] | **True** | cautious |
| doc_02 | "ongoing litigation matter" | **[litigation risk, ...]** | False | neutral |
| doc_03 | "42% customer concentration" | [concentration risk] | False | neutral |
| doc_04 | "cautiously optimistic...visibility..." | [] | **True** | cautious |
| doc_05 | "confident...approved capex" | [] | False | **confident** |
| doc_06 | "regulatory notice...data-localization" | **[regulatory risk, ...]** | False | neutral |

**Acceptance criteria:** doc_02 risk_flag ✅ | doc_01/doc_04 hedging ✅ | doc_05 confident ✅ | **ALL PASS**

---

## Part C — Multi-Agent Debate (`debate.py`)

**Ticker chosen:** `PAYTECH` (beta=1.55, std_dev=34%, CAPM E(R)=16.3%)

**Bull agent:** References E(R)=16.3% vs market return 13%, beta=1.55x market amplification.

**Bear agent:** References std_dev=34% (implies -68% in a 2-sigma year), beta=1.55 downside amplification, Sharpe-like ratio of 0.27.

**Synthesizer:** Combines both — recommends PAYTECH only as a 10-20% satellite allocation for Aggressive investors with 7-10yr horizon, paired with lower-beta anchors to keep portfolio std < 20%.

All agent arguments reference actual numeric values from `STOCK_UNIVERSE`. No network call in mock mode.

---

## Part D — DCF Calculator (`dcf_calculator.py`)

### Stated Inputs (Paytm Payments Processing Division — Hypothetical)

| Input | Value | Rationale |
|---|---|---|
| EBIT | INR 50 Cr | Illustrative for a mid-scale payments processing unit |
| Tax rate | 25% | Indian corporate tax rate |
| D&A | INR 8 Cr | Infrastructure depreciation |
| CapEx | INR 12 Cr | Annual server/infrastructure investment |
| Delta NWC | INR 3 Cr | Working capital build for growth |
| **Base FCFF** | **INR 30.5 Cr** | EBIT×(1-t) + D&A − CapEx − ΔNWC |
| 5-yr growth | 12% | High-growth phase for payments scale-up |
| Terminal growth gT | 3% | Long-run GDP-aligned growth |

### WACC Computation

| Component | Value |
|---|---|
| Beta used | 1.10 (PAYINFRA from STOCK_UNIVERSE) |
| Cost of equity Re | 7% + 1.10×(13%−7%) = **13.60%** |
| After-tax cost of debt | 8%×(1−25%) = **6.00%** |
| Capital structure | 70% equity / 30% debt |
| **WACC** | **11.32%** |

**Constraint check:** WACC − gT = 8.32% ≥ 3pp ✅ | Worst-case (WACC−1pp, gT+1pp): gap = 6.32% ≥ 1pp ✅

### 3×3 Sensitivity Table (Enterprise Value, INR Cr)

| WACC \ gT | gT = 2% | gT = 3% | gT = 4% |
|---|---|---|---|
| WACC = 10.32% | 562.9 | 622.5 | 700.9 |
| **WACC = 11.32% (base)** | **499.4** | **544.6** | **602.0** |
| WACC = 12.32% | 448.4 | 483.5 | 527.1 |

All 9 cells: WACC > gT confirmed. Min gap = 6.32% ≥ 1pp ✅

### EV/EBITDA Cross-Check

| Method | EV (INR Cr) |
|---|---|
| DCF | 544.6 |
| EV/EBITDA (15× EBITDA of INR 58Cr) | 870 |
| Delta | −37.4% |

**Written comparison:** The DCF value of INR 544.6 Cr sits 37.4% below the EV/EBITDA anchor of INR 870 Cr. The gap is explained by the DCF's conservative WACC of 11.32% discounting 5 years of 12% growth — the market multiple implicitly assumes higher terminal value expectations embedded in a 15× EBITDA. In practice, the two methods bracket a reasonable valuation range (INR 545–870 Cr); a financial advisor would use the midpoint (~INR 700 Cr) as a working enterprise value, subject to scenario analysis on the growth rate assumption.

---

## Part E — Blockchain Risk Note

See [`blockchain_risk_note.md`](./blockchain_risk_note.md) for the full 600–900 word analysis covering:
1. Stablecoin types (fiat-collateralised vs. algorithmic) and DeFi/DAO governance risk
2. Crypto allocation recommendation for Paytm Money (0–2% maximum; zero for most users)
3. T.A.N.G. fraud framework — Greed (fake investment schemes) and Authority (fake RBI compliance calls) vectors with bank-side real-time defenses

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Debate ticker | PAYTECH | Highest beta (1.55) and std_dev (34%) — richest numerical contrast for bull/bear |
| DCF beta | PAYINFRA (1.10) | Mid-range beta appropriate for an infrastructure-heavy payments processor |
| DCF growth 5yr | 12% | Conservative for Indian fintech; Paytm payments volume historically grew 20%+ |
| Terminal growth | 3% | Below India long-run nominal GDP (~6%) to be conservative; easily satisfies 3pp gap |
| WACC equity weight | 70/30 | Typical for growth-stage fintech before significant debt capacity |
| MOCK_LLM | 1 (default) | Fully deterministic, no API dependency — required for grading |
| Stablecoin recommendation | Fiat-backed only for retail | Algorithmic stablecoins are unsuitable for retail exposure given Terra/Luna precedent |
| Crypto max allocation | 0–2% | Consistent with CAPM theory, Indian tax environment, RBI regulatory stance |
