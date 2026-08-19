"""
Part 1C — Payment Reconciliation
Paytm Payments Analytics

Reusable function reconcile_payments(ledger_df, gateway_df) that returns
four DataFrames:
  1. missing_in_gateway  — transactions in ledger but absent from gateway
  2. extra_in_gateway    — transactions in gateway but absent from ledger
  3. amount_mismatches   — transactions present in both but with different amount_inr
  4. status_mismatches   — transactions present in both but with different status

Run from inside payments_fraud_analytics/:
    cd payments_fraud_analytics && python reconcile.py
"""

import pandas as pd


def reconcile_payments(ledger_df: pd.DataFrame, gateway_df: pd.DataFrame):
    """
    Compare ledger vs gateway export and return four discrepancy DataFrames.

    Parameters
    ----------
    ledger_df   : DataFrame — the internal ledger (source of truth)
    gateway_df  : DataFrame — the payment gateway export

    Returns
    -------
    missing_in_gateway : rows in ledger not found in gateway (by transaction_id)
    extra_in_gateway   : rows in gateway not found in ledger (by transaction_id)
    amount_mismatches  : rows present in both but amount_inr differs
    status_mismatches  : rows present in both but status differs
    """

    ledger_ids  = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    # ── 1. Missing in gateway (in ledger, absent in gateway) ─────────────────
    missing_ids        = ledger_ids - gateway_ids
    missing_in_gateway = ledger_df[ledger_df["transaction_id"].isin(missing_ids)].copy()
    missing_in_gateway = missing_in_gateway.reset_index(drop=True)

    # ── 2. Extra in gateway (in gateway, absent in ledger) ───────────────────
    extra_ids        = gateway_ids - ledger_ids
    extra_in_gateway = gateway_df[gateway_df["transaction_id"].isin(extra_ids)].copy()
    extra_in_gateway = extra_in_gateway.reset_index(drop=True)

    # ── 3 & 4. Pairwise comparison for common transactions ───────────────────
    common_ids = ledger_ids & gateway_ids

    ledger_common  = ledger_df[ledger_df["transaction_id"].isin(common_ids)]
    gateway_common = gateway_df[gateway_df["transaction_id"].isin(common_ids)]

    merged = pd.merge(
        ledger_common[["transaction_id", "amount_inr", "status"]],
        gateway_common[["transaction_id", "amount_inr", "status"]],
        on="transaction_id",
        suffixes=("_ledger", "_gateway")
    )

    # ── 3. Amount mismatches ──────────────────────────────────────────────────
    amount_mask       = merged["amount_inr_ledger"] != merged["amount_inr_gateway"]
    amount_mismatches = merged[amount_mask].copy()
    amount_mismatches["amount_diff"] = (
        amount_mismatches["amount_inr_gateway"] - amount_mismatches["amount_inr_ledger"]
    )
    amount_mismatches = amount_mismatches.reset_index(drop=True)

    # ── 4. Status mismatches ─────────────────────────────────────────────────
    status_mask       = merged["status_ledger"] != merged["status_gateway"]
    status_mismatches = merged[status_mask].copy()
    status_mismatches = status_mismatches.reset_index(drop=True)

    return missing_in_gateway, extra_in_gateway, amount_mismatches, status_mismatches


# =============================================================================
# Run reconciliation against the actual committed CSVs
# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("Paytm Payment Reconciliation — ledger.csv vs gateway_export.csv")
    print("=" * 65)

    ledger_df  = pd.read_csv("ledger.csv")
    gateway_df = pd.read_csv("gateway_export.csv")

    print(f"\nLedger rows  : {len(ledger_df)}")
    print(f"Gateway rows : {len(gateway_df)}")

    missing, extra, amt_mis, stat_mis = reconcile_payments(ledger_df, gateway_df)

    n = len(ledger_df)   # denominator for rate checks

    print("\n" + "-" * 65)
    print(f"[1] Transactions MISSING in gateway (in ledger, not in gateway):")
    print(f"    Count : {len(missing)}  |  Injected rate ~5% of {n} = {int(0.05*n)}")
    print(missing[["transaction_id", "amount_inr", "status"]].to_string(index=False))

    print("\n" + "-" * 65)
    print(f"[2] Transactions EXTRA in gateway (in gateway, not in ledger):")
    print(f"    Count : {len(extra)}  |  Injected rate ~2% of {n} = {int(0.02*n)}")
    print(extra[["transaction_id", "amount_inr", "status"]].to_string(index=False))

    print("\n" + "-" * 65)
    print(f"[3] AMOUNT MISMATCHES (same transaction_id, different amount_inr):")
    print(f"    Count : {len(amt_mis)}  |  Injected rate ~3% of {n} = {int(0.03*n)}")
    print(amt_mis[["transaction_id", "amount_inr_ledger",
                   "amount_inr_gateway", "amount_diff"]].to_string(index=False))

    print("\n" + "-" * 65)
    print(f"[4] STATUS MISMATCHES (same transaction_id, different status):")
    print(f"    Count : {len(stat_mis)}  |  Injected rate ~2% of {n} = {int(0.02*n)}")
    print(stat_mis[["transaction_id", "status_ledger",
                    "status_gateway"]].to_string(index=False))

    print("\n" + "=" * 65)
    print("RECONCILIATION SUMMARY")
    print("=" * 65)
    print(f"{'Category':<35} {'Count':>6}  {'~Expected':>10}")
    print("-" * 55)
    print(f"{'Missing in gateway (~5%)':<35} {len(missing):>6}  {int(0.05*n):>10}")
    print(f"{'Extra in gateway (~2%)':<35} {len(extra):>6}  {int(0.02*n):>10}")
    print(f"{'Amount mismatches (~3%)':<35} {len(amt_mis):>6}  {int(0.03*n):>10}")
    print(f"{'Status mismatches (~2%)':<35} {len(stat_mis):>6}  {int(0.02*n):>10}")
    print("=" * 65)
    print("Reconciliation complete.")
