"""
Part 3C — Multi-Agent Bull/Bear/Synthesizer Debate
Paytm Money — AI-Augmented FinTech Advisory

Ticker chosen: PAYTECH (highest beta=1.55, std_dev=34%, aggressive growth play)

MOCK_LLM mode (graded baseline): each agent's argument is built from a template
referencing PAYTECH's actual numeric values. No network call.

Agents:
  - Bull       : optimistic case referencing expected return and beta
  - Bear       : pessimistic case referencing std_dev (volatility risk)
  - Synthesizer: balanced 2-3 sentence summary combining both views
"""

import os
import math

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN

MOCK_LLM = os.environ.get("MOCK_LLM", "1") != "0"

# Chosen ticker for the debate
DEBATE_TICKER = "PAYTECH"


def capm_return(beta):
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def bull_agent(ticker: str, data: dict) -> str:
    """Optimistic case: references expected return and beta."""
    er     = capm_return(data["beta"])
    beta   = data["beta"]
    std    = data["std_dev"]
    mkt_er = MARKET_RETURN

    if MOCK_LLM:
        return (
            f"[BULL] {ticker} is a compelling high-conviction buy. "
            f"With a CAPM-derived expected return of {er:.1%} against a market return "
            f"of {mkt_er:.1%}, the stock offers meaningful alpha potential. "
            f"Its beta of {beta:.2f} means it amplifies market upside — "
            f"in a bull market, {ticker} outperforms the index by a factor of {beta:.2f}x. "
            f"The {std:.0%} volatility is the price of entry for superior long-run compounding."
        )
    else:
        try:
            from groq import Groq
            client = Groq()
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": (
                    f"In 2-3 sentences, make a bullish case for stock {ticker} "
                    f"with beta={beta:.2f}, expected return={er:.1%}, std_dev={std:.0%}. "
                    f"Reference the actual numbers."
                )}],
                max_tokens=120,
            )
            return f"[BULL] {resp.choices[0].message.content.strip()}"
        except Exception:
            return bull_agent.__wrapped__(ticker, data)


def bear_agent(ticker: str, data: dict) -> str:
    """Pessimistic case: references std_dev as the primary risk."""
    er    = capm_return(data["beta"])
    beta  = data["beta"]
    std   = data["std_dev"]

    if MOCK_LLM:
        sharpe_approx = (er - RISK_FREE_RATE) / std
        return (
            f"[BEAR] {ticker} carries substantial downside risk that investors must not ignore. "
            f"A standard deviation of {std:.0%} highlights high historical volatility, presenting "
            f"a drawdown risk far beyond what most retail investors can stomach. "
            f"With a beta of {beta:.2f}, {ticker} will fall {beta:.2f}x harder than the market "
            f"in any broad downturn. The Sharpe-like ratio of only {sharpe_approx:.2f} "
            f"(excess return per unit of risk) is unattractive compared to safer alternatives."
        )
    else:
        try:
            from groq import Groq
            client = Groq()
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": (
                    f"In 2-3 sentences, make a bearish case for stock {ticker} "
                    f"with beta={beta:.2f}, expected return={er:.1%}, std_dev={std:.0%}. "
                    f"Focus on risk. Reference the actual numbers."
                )}],
                max_tokens=120,
            )
            return f"[BEAR] {resp.choices[0].message.content.strip()}"
        except Exception:
            return bear_agent.__wrapped__(ticker, data)


def synthesizer_agent(ticker: str, data: dict,
                       bull_arg: str, bear_arg: str) -> str:
    """Balanced 2-3 sentence summary combining bull and bear views."""
    er  = capm_return(data["beta"])
    std = data["std_dev"]

    if MOCK_LLM:
        return (
            f"[SYNTHESIZER] {ticker} presents a classic high-risk / high-reward profile: "
            f"the CAPM-expected return of {er:.1%} is attractive in absolute terms, "
            f"but the {std:.0%} annual volatility demands a long investment horizon and "
            f"robust risk tolerance to ride out drawdowns. "
            f"A balanced advisory position would be to include {ticker} only as a satellite "
            f"allocation (10-20% of portfolio) for investors with Aggressive risk tolerance "
            f"and a minimum 7-10 year horizon, pairing it with lower-beta anchors such as "
            f"PAYGOLD or PAYBOND to manage total portfolio variance below the 20% escalation threshold."
        )
    else:
        try:
            from groq import Groq
            client = Groq()
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": (
                    f"Synthesize the following bull and bear arguments about {ticker} "
                    f"(expected return={er:.1%}, std_dev={std:.0%}) into a 2-3 sentence "
                    f"balanced summary:\n\nBull: {bull_arg}\n\nBear: {bear_arg}"
                )}],
                max_tokens=150,
            )
            return f"[SYNTHESIZER] {resp.choices[0].message.content.strip()}"
        except Exception:
            return synthesizer_agent.__wrapped__(ticker, data, bull_arg, bear_arg)


# =============================================================================
# Run the debate
# =============================================================================
if __name__ == "__main__":
    mode = "MOCK (no network call)" if MOCK_LLM else "LLM (MOCK_LLM=0)"
    print(f"Multi-Agent Debate — Paytm Money  |  Mode: {mode}")
    print(f"Ticker: {DEBATE_TICKER}")
    print("=" * 70)

    data = STOCK_UNIVERSE[DEBATE_TICKER]
    er   = capm_return(data["beta"])

    print(f"\nStock data for {DEBATE_TICKER}:")
    print(f"  beta                    : {data['beta']:.2f}")
    print(f"  std_dev                 : {data['std_dev']:.0%}")
    print(f"  CAPM expected return    : {er:.2%}  "
          f"(R_f={RISK_FREE_RATE:.0%} + {data['beta']:.2f}*({MARKET_RETURN:.0%}-{RISK_FREE_RATE:.0%}))")
    print(f"  analyst_expected_return : {data['analyst_expected_return']:.0%}  "
          f"[NOT used in CAPM — reference only]")

    print("\n" + "=" * 70)
    print("AGENT ARGUMENTS")
    print("=" * 70)

    bull_arg  = bull_agent(DEBATE_TICKER, data)
    bear_arg  = bear_agent(DEBATE_TICKER, data)
    synth_arg = synthesizer_agent(DEBATE_TICKER, data, bull_arg, bear_arg)

    print(f"\n{bull_arg}\n")
    print(f"{bear_arg}\n")
    print(f"{synth_arg}\n")

    print("=" * 70)
    print("Debate complete. Each agent's argument references actual numeric values.")
