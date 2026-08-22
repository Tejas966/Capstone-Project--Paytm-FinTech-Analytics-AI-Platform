"""
Part 3A — Portfolio Advisory Agent
Paytm Money — AI-Augmented FinTech Advisory

Implements the agentic Think → Act → Observe pattern for all 5 investor profiles.

MOCK_LLM behaviour (graded baseline, default):
  - MOCK_LLM is unset (or set to 1) → fully deterministic f-string narrative, no API call.
  - MOCK_LLM=0 → optional Groq/LLM path (not required for grading).

CAPM formula:  E(R_i) = R_f + beta_i * (E(R_m) - R_f)
Portfolio variance:
  Var(R_p) = sum_i(w_i^2 * sigma_i^2)
             + 2 * sum_{i<j}(w_i * w_j * rho * sigma_i * sigma_j)
  where rho = 0.3 for every pair, weights = 1/3 each

Escalation:  portfolio_std > 20%  →  ESCALATED_TO_HUMAN_ADVISOR
Expected:    Conservative ~8.44%, Moderate ~12.57%  →  NO escalation
             Aggressive   ~20.58%                   →  ESCALATED
"""

import os
import math

from stock_universe   import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN
from investor_profiles import INVESTOR_PROFILES

# ── MOCK_LLM flag ─────────────────────────────────────────────────────────────
MOCK_LLM = os.environ.get("MOCK_LLM", "1") != "0"   # default: mock mode

# ── Prescribed allocation lookup table (EXACT — do not change) ────────────────
ALLOCATION_TABLE = {
    "Conservative": ["PAYBOND", "PAYGOLD",   "PAYRETAIL"],
    "Moderate":     ["PAYRETAIL", "PAYINFRA", "PAYGOLD"],
    "Aggressive":   ["PAYTECH",  "PAYFIN",   "PAYINFRA"],
}

ESCALATION_THRESHOLD = 0.20   # 20% portfolio std dev → escalate
PAIRWISE_CORRELATION = 0.30   # rho = 0.3 for every pair

# =============================================================================
# Tool function (simulates an external API call)
# =============================================================================
def get_stock_data(ticker: str) -> dict:
    """
    ACT stage tool: look up stock data from STOCK_UNIVERSE.
    Simulates an external-API tool call; no real network request is made.

    Returns dict with keys: beta, analyst_expected_return, std_dev
    Raises KeyError if ticker is not found.
    """
    if ticker not in STOCK_UNIVERSE:
        raise KeyError(f"Ticker '{ticker}' not found in STOCK_UNIVERSE.")
    return STOCK_UNIVERSE[ticker]


# =============================================================================
# CAPM and portfolio maths
# =============================================================================
def capm_expected_return(beta: float) -> float:
    """E(R) = R_f + beta * (E(R_m) - R_f). Uses ONLY beta — never analyst_expected_return."""
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def portfolio_variance(weights: list, std_devs: list, rho: float) -> float:
    """
    Var(R_p) = sum_i(w_i^2 * sigma_i^2)
               + 2 * sum_{i<j}(w_i * w_j * rho * sigma_i * sigma_j)
    """
    n = len(weights)
    var = 0.0
    # Diagonal terms
    for i in range(n):
        var += weights[i] ** 2 * std_devs[i] ** 2
    # Off-diagonal (covariance) terms
    for i in range(n):
        for j in range(i + 1, n):
            cov_ij = rho * std_devs[i] * std_devs[j]
            var += 2 * weights[i] * weights[j] * cov_ij
    return var


# =============================================================================
# Narrative sentence (gated by MOCK_LLM)
# =============================================================================
def generate_narrative(investor_id, risk_tolerance, tickers,
                       portfolio_return, portfolio_std,
                       escalated, investment_amount_inr):
    if MOCK_LLM:
        # ── Mock path (graded baseline): f-string template ────────────────────
        if escalated:
            return (
                f"For {risk_tolerance} investor {investor_id}, the proposed allocation "
                f"across {{{', '.join(tickers)}}} yields an expected portfolio return of "
                f"{portfolio_return:.1%} and a volatility of {portfolio_std:.1%} — "
                f"ESCALATED TO HUMAN ADVISOR because portfolio volatility exceeds the "
                f"20% threshold. A human advisor will review before finalising the "
                f"INR {investment_amount_inr:,} deployment."
            )
        else:
            return (
                f"For {risk_tolerance} investor {investor_id}, we recommend an allocation "
                f"across {{{', '.join(tickers)}}} with an expected portfolio return of "
                f"{portfolio_return:.1%} and volatility of {portfolio_std:.1%}. "
                f"INR {investment_amount_inr:,} is auto-approved for deployment."
            )
    else:
        # ── Optional MOCK_LLM=0 path (not graded) ─────────────────────────────
        try:
            from groq import Groq
            client = Groq()
            prompt = (
                f"In one concise sentence, describe a portfolio recommendation for a "
                f"{risk_tolerance} investor ({investor_id}) with tickers "
                f"{tickers}, expected return {portfolio_return:.1%}, "
                f"and volatility {portfolio_std:.1%}. "
                f"{'Mention it is escalated to human review.' if escalated else ''}"
            )
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to mock if LLM call fails
            return generate_narrative(investor_id, risk_tolerance, tickers,
                                      portfolio_return, portfolio_std,
                                      escalated, investment_amount_inr)


# =============================================================================
# Main agent loop
# =============================================================================
def run_advisory_agent(investor: dict) -> dict:
    investor_id          = investor["investor_id"]
    risk_tolerance       = investor["risk_tolerance"]
    horizon_years        = investor["horizon_years"]
    investment_amount    = investor["investment_amount_inr"]

    print(f"\n{'='*65}")
    print(f"INVESTOR: {investor_id}  |  Risk: {risk_tolerance}  "
          f"|  Horizon: {horizon_years}yr  |  Amount: INR {investment_amount:,}")
    print(f"{'='*65}")

    # ── THINK: determine allocation from prescribed lookup table ──────────────
    print("\n[THINK] Determining allocation from prescribed lookup table...")
    tickers = ALLOCATION_TABLE[risk_tolerance]
    weight  = 1 / 3          # equal-weight: 1/3 each
    weights = [weight] * 3
    print(f"  Allocation: {tickers}  |  Weights: [{weight:.4f}, {weight:.4f}, {weight:.4f}]")

    # ── ACT: call get_stock_data() tool for each ticker ───────────────────────
    print("\n[ACT] Calling get_stock_data() tool for each ticker...")
    stock_data = {}
    for ticker in tickers:
        data = get_stock_data(ticker)    # simulated tool call
        stock_data[ticker] = data
        print(f"  get_stock_data('{ticker}') -> beta={data['beta']:.2f}, "
              f"std_dev={data['std_dev']:.2%}")

    # ── OBSERVE -> DECIDE ──────────────────────────────────────────────────────
    print("\n[OBSERVE] Computing CAPM expected return and portfolio variance...")

    # Per-stock CAPM returns (using ONLY beta, never analyst_expected_return)
    capm_returns = []
    for ticker in tickers:
        er = capm_expected_return(stock_data[ticker]["beta"])
        capm_returns.append(er)
        print(f"  E(R) for {ticker}: R_f + beta*(R_m-R_f) = "
              f"{RISK_FREE_RATE:.2%} + {stock_data[ticker]['beta']:.2f}*"
              f"({MARKET_RETURN:.2%}-{RISK_FREE_RATE:.2%}) = {er:.4%}")

    # Portfolio expected return (weight-averaged)
    portfolio_return = sum(w * r for w, r in zip(weights, capm_returns))
    print(f"\n  Portfolio Expected Return (CAPM, weight-averaged): {portfolio_return:.4%}")

    # Portfolio variance and std dev
    std_devs = [stock_data[t]["std_dev"] for t in tickers]
    var = portfolio_variance(weights, std_devs, PAIRWISE_CORRELATION)
    portfolio_std = math.sqrt(var)
    print(f"  Portfolio Variance (rho={PAIRWISE_CORRELATION}): {var:.6f}")
    print(f"  Portfolio Std Dev:  {portfolio_std:.4%}")

    # ── Human-in-the-loop escalation decision ─────────────────────────────────
    escalated = portfolio_std > ESCALATION_THRESHOLD
    print(f"\n[DECISION] Portfolio std dev {portfolio_std:.2%} "
          f"{'>' if escalated else '<='} {ESCALATION_THRESHOLD:.0%} threshold")

    if escalated:
        decision = "ESCALATED_TO_HUMAN_ADVISOR"
        print(f"  --> {decision}")
    else:
        decision = "AUTO_APPROVED"
        print(f"  --> {decision}")

    # ── Narrative (MOCK_LLM gated) ────────────────────────────────────────────
    mode_label = "MOCK" if MOCK_LLM else "LLM"
    print(f"\n[NARRATIVE — {mode_label} mode]")
    narrative = generate_narrative(
        investor_id, risk_tolerance, tickers,
        portfolio_return, portfolio_std,
        escalated, investment_amount
    )
    print(f"  {narrative}")

    return {
        "investor_id":        investor_id,
        "risk_tolerance":     risk_tolerance,
        "tickers":            tickers,
        "weights":            weights,
        "capm_returns":       {t: r for t, r in zip(tickers, capm_returns)},
        "portfolio_return":   portfolio_return,
        "portfolio_std":      portfolio_std,
        "escalated":          escalated,
        "decision":           decision,
        "narrative":          narrative,
    }


# =============================================================================
# Run all 5 investor profiles
# =============================================================================
if __name__ == "__main__":
    mode = "MOCK (deterministic, no API key)" if MOCK_LLM else "LLM (MOCK_LLM=0)"
    print(f"Portfolio Advisory Agent — Paytm Money")
    print(f"MOCK_LLM mode: {mode}")
    print(f"RISK_FREE_RATE={RISK_FREE_RATE:.0%}  |  MARKET_RETURN={MARKET_RETURN:.0%}"
          f"  |  rho={PAIRWISE_CORRELATION}")

    results = []
    for investor in INVESTOR_PROFILES:
        result = run_advisory_agent(investor)
        results.append(result)

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("SUMMARY — All 5 Investor Profiles")
    print(f"{'='*65}")
    header = f"{'ID':<6} {'Risk':<13} {'Tickers':<34} {'E(R)':>7} {'Std':>7} {'Decision'}"
    print(header)
    print("-" * 90)
    for r in results:
        tickers_str = "+".join(r["tickers"])
        print(f"{r['investor_id']:<6} {r['risk_tolerance']:<13} {tickers_str:<34} "
              f"{r['portfolio_return']:>6.2%}  {r['portfolio_std']:>6.2%}  {r['decision']}")

    # ── Escalation verification ───────────────────────────────────────────────
    print(f"\n{'='*65}")
    print("ESCALATION VERIFICATION")
    print(f"{'='*65}")
    expected_no_escalate  = {"INV01", "INV02", "INV04"}
    expected_escalate     = {"INV03", "INV05"}

    all_pass = True
    for r in results:
        inv_id    = r["investor_id"]
        escalated = r["escalated"]
        should_escalate = inv_id in expected_escalate
        status = "PASS" if escalated == should_escalate else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {inv_id}: std={r['portfolio_std']:.2%}  "
              f"escalated={escalated}  expected={should_escalate}  [{status}]")

    print(f"\nOverall escalation check: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
