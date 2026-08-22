"""
Part 3B — Structured Disclosure Extraction
Paytm Money — AI-Augmented FinTech Advisory

Implements extract_signals(snippet) -> dict with keys:
  - risk_flags      : list of identified risk phrases
  - hedging_detected: bool
  - sentiment       : "confident" | "cautious" | "neutral"

MOCK_LLM mode (graded baseline): pure keyword/regex rules, no network call.
Optional MOCK_LLM=0: LLM path with JSON validation and fallback.

Acceptance criteria (verified below):
  - doc_02 (litigation) -> risk_flags non-empty
  - doc_01 or doc_04 (assuming / cautiously) -> hedging_detected = True
  - doc_05 (confident / approved) -> sentiment = "confident"
"""

import os
import re

from disclosure_snippets import DISCLOSURE_SNIPPETS

MOCK_LLM = os.environ.get("MOCK_LLM", "1") != "0"


# ── Keyword / regex rule sets ─────────────────────────────────────────────────
RISK_PATTERNS = [
    (r"\blitigation\b",                         "litigation risk"),
    (r"\bregulat\w+\b",                         "regulatory risk"),
    (r"\bregulatory notice\b",                  "regulatory notice"),
    (r"\bcompliance\b",                         "compliance risk"),
    (r"\btop (?:three|3|two|2|four|4) customers\b", "customer concentration risk"),
    (r"(\d{2,3})\s*percent\s+of\s+total revenue",   "revenue concentration risk"),
    (r"\bexposure\b",                           "financial exposure"),
    (r"\bdata.locali[sz]ation\b",              "data-localisation risk"),
    (r"\bformer vendor\b",                      "vendor dispute risk"),
]

HEDGING_PATTERNS = [
    r"\bassuming\b",
    r"\bcautiously\b",
    r"\bvisibility\b",
    r"\blimited\b.*\bvisibility\b",
    r"\bgiven\s+macro\s+uncertainty\b",
    r"\bsubject\s+to\b",
    r"\bexpect\b.*\bstable\b",
]

CONFIDENT_PATTERNS = [
    r"\bconfident\b",
    r"\bapproved\b",
    r"\blong.term strategy\b",
    r"\bexpanded capital expenditure\b",
]

CAUTIOUS_PATTERNS = HEDGING_PATTERNS   # cautious sentiment triggered by hedging


def _mock_extract(snippet: str) -> dict:
    """Pure keyword/regex extraction — no LLM, no network call."""
    text = snippet.lower()

    # Risk flags
    risk_flags = []
    for pattern, label in RISK_PATTERNS:
        if re.search(pattern, text):
            if label not in risk_flags:
                risk_flags.append(label)

    # Hedging detection
    hedging_detected = any(re.search(p, text) for p in HEDGING_PATTERNS)

    # Sentiment
    is_confident = any(re.search(p, text) for p in CONFIDENT_PATTERNS)
    is_cautious  = hedging_detected

    if is_confident and not is_cautious:
        sentiment = "confident"
    elif is_cautious:
        sentiment = "cautious"
    else:
        sentiment = "neutral"

    return {
        "risk_flags":       risk_flags,
        "hedging_detected": hedging_detected,
        "sentiment":        sentiment,
    }


def extract_signals(snippet: str) -> dict:
    """
    Public API: extract risk flags, hedging, and sentiment from a disclosure snippet.

    Parameters
    ----------
    snippet : str — company disclosure text

    Returns
    -------
    dict with keys: risk_flags (list), hedging_detected (bool), sentiment (str)
    """
    if MOCK_LLM:
        return _mock_extract(snippet)
    else:
        # Optional MOCK_LLM=0 path (not graded)
        try:
            from groq import Groq
            import json

            schema_desc = (
                'Return JSON with keys: '
                '"risk_flags" (list of strings), '
                '"hedging_detected" (bool), '
                '"sentiment" (one of "confident", "cautious", "neutral"). '
                'No other keys.'
            )
            client = Groq()
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Analyse this company disclosure snippet and {schema_desc}\n\n"
                        f"Snippet: {snippet}"
                    )
                }],
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            # Validate schema — retry once on failure
            assert isinstance(result.get("risk_flags"), list)
            assert isinstance(result.get("hedging_detected"), bool)
            assert result.get("sentiment") in ("confident", "cautious", "neutral")
            return result
        except Exception:
            # Fallback to mock
            return _mock_extract(snippet)


# =============================================================================
# Run against all 6 disclosure snippets
# =============================================================================
if __name__ == "__main__":
    mode = "MOCK (no network call)" if MOCK_LLM else "LLM (MOCK_LLM=0)"
    print(f"Disclosure Extraction — Paytm Money  |  Mode: {mode}")
    print("=" * 70)

    for snippet in DISCLOSURE_SNIPPETS:
        doc_id  = snippet.split(":")[0]
        preview = snippet[:80] + ("..." if len(snippet) > 80 else "")
        result  = extract_signals(snippet)

        print(f"\n{doc_id.upper()}")
        print(f"  Snippet : {preview}")
        print(f"  risk_flags       : {result['risk_flags']}")
        print(f"  hedging_detected : {result['hedging_detected']}")
        print(f"  sentiment        : {result['sentiment']}")

    # ── Acceptance criteria verification ──────────────────────────────────────
    print(f"\n{'='*70}")
    print("ACCEPTANCE CRITERIA VERIFICATION")
    print(f"{'='*70}")

    results_map = {s.split(":")[0]: extract_signals(s) for s in DISCLOSURE_SNIPPETS}

    check1 = len(results_map["doc_02"]["risk_flags"]) > 0
    check2 = results_map["doc_01"]["hedging_detected"] or \
             results_map["doc_04"]["hedging_detected"]
    check3 = results_map["doc_05"]["sentiment"] == "confident"
    check4 = results_map["doc_06"]["risk_flags"] != []    # regulatory notice

    print(f"  doc_02 has risk_flags (litigation): {check1}  "
          f"-> {'PASS' if check1 else 'FAIL'}")
    print(f"  doc_01 or doc_04 hedging_detected:  {check2}  "
          f"-> {'PASS' if check2 else 'FAIL'}")
    print(f"  doc_05 sentiment == 'confident':    {check3}  "
          f"-> {'PASS' if check3 else 'FAIL'}")
    print(f"  doc_06 has risk_flags (regulatory): {check4}  "
          f"-> {'PASS' if check4 else 'FAIL'}")

    overall = all([check1, check2, check3, check4])
    print(f"\nOverall: {'ALL PASS' if overall else 'SOME FAILURES'}")
