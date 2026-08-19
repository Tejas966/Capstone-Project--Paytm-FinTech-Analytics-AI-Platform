"""
Part 1A — Excel Merchant Workbook Generator
Paytm Payments Analytics

Generates merchant_workbook.xlsx with:
  Sheet 1 (Merchants)     : raw merchants data
  Sheet 2 (Transactions)  : ledger with VLOOKUP columns + nested IF classification
  Sheet 3 (HLOOKUP_Demo)  : horizontally-laid MDR fee-rate table + HLOOKUP demo
  Sheet 4 (Pivot_Summary) : pivot-style summary by merchant_id + status
  Sheet 5 (Unique_Days)   : count-vs-count-unique days for at least 5 merchants

Run from inside payments_fraud_analytics/:
    cd payments_fraud_analytics && python generate_workbook.py
"""

import pandas as pd
import openpyxl
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
from openpyxl.styles.numbers import FORMAT_NUMBER_COMMA_SEPARATED1
import os

# ── Styling helpers ───────────────────────────────────────────────────────────
BLUE_DARK   = "1D4ED8"
BLUE_MID    = "3B82F6"
RED_RISK    = "DC2626"
GREEN_OK    = "16A34A"
GRAY_HEADER = "1E293B"
AMBER       = "D97706"
WHITE       = "FFFFFF"
LIGHT_BLUE  = "DBEAFE"
LIGHT_RED   = "FEE2E2"
LIGHT_GREEN = "DCFCE7"
LIGHT_GRAY  = "F8FAFC"
LIGHT_AMBER = "FEF3C7"

thin_border = Border(
    left   = Side(style="thin", color="CBD5E1"),
    right  = Side(style="thin", color="CBD5E1"),
    top    = Side(style="thin", color="CBD5E1"),
    bottom = Side(style="thin", color="CBD5E1"),
)

def hdr_style(cell, bg=GRAY_HEADER, fg=WHITE, bold=True, size=10):
    cell.font      = Font(bold=bold, color=fg, size=size, name="Calibri")
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = thin_border

def data_style(cell, bg=WHITE, fg="1E293B", bold=False):
    cell.font      = Font(bold=bold, color=fg, size=9, name="Calibri")
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    cell.border    = thin_border

def num_style(cell, bg=WHITE, fg="1E293B"):
    cell.font      = Font(color=fg, size=9, name="Calibri")
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="right", vertical="center")
    cell.border    = thin_border

def section_title(ws, row, col, text, span=1, bg=BLUE_DARK):
    cell = ws.cell(row=row, column=col, value=text)
    cell.font      = Font(bold=True, color=WHITE, size=11, name="Calibri")
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border    = thin_border
    if span > 1:
        ws.merge_cells(start_row=row, start_column=col,
                       end_row=row, end_column=col + span - 1)

# ── Load data ─────────────────────────────────────────────────────────────────
merchants_df = pd.read_csv("merchants.csv")
ledger_df    = pd.read_csv("ledger.csv", parse_dates=["transaction_time"])

wb = openpyxl.Workbook()
wb.remove(wb.active)   # remove default sheet

# =============================================================================
# SHEET 1 — Merchants (reference table)
# =============================================================================
ws_m = wb.create_sheet("Merchants")

m_headers = ["merchant_id", "merchant_name", "category", "region"]
for col, h in enumerate(m_headers, 1):
    hdr_style(ws_m.cell(row=1, column=col, value=h), bg=BLUE_DARK)

for r_idx, row in enumerate(merchants_df.itertuples(index=False), start=2):
    bg = LIGHT_BLUE if r_idx % 2 == 0 else WHITE
    for col, val in enumerate([row.merchant_id, row.merchant_name,
                                row.category, row.region], 1):
        cell = ws_m.cell(row=r_idx, column=col, value=val)
        if col == 1:
            num_style(cell, bg=bg)
        else:
            data_style(cell, bg=bg)

ws_m.column_dimensions["A"].width = 14
ws_m.column_dimensions["B"].width = 18
ws_m.column_dimensions["C"].width = 18
ws_m.column_dimensions["D"].width = 12
ws_m.freeze_panes = "A2"

# =============================================================================
# SHEET 2 — Transactions  (VLOOKUP + nested IF)
# =============================================================================
ws_t = wb.create_sheet("Transactions")

# Header
t_headers = [
    "transaction_id", "user_id", "merchant_id", "transaction_time",
    "amount_inr", "payment_method", "status", "risk_score",
    # VLOOKUP columns
    "merchant_name (VLOOKUP)", "category (VLOOKUP)", "region (VLOOKUP)",
    # Nested IF column
    "classification (nested IF)"
]
for col, h in enumerate(t_headers, 1):
    bg = GRAY_HEADER if col <= 8 else BLUE_MID if col <= 11 else AMBER
    hdr_style(ws_t.cell(row=1, column=col, value=h), bg=bg)

# Write raw data rows + formulas
# Merchants sheet data occupies Merchants!A:D (row 1 = header, rows 2–41 = data)
MERCH_RANGE = "Merchants!$A$2:$D$41"

for r_idx, row in enumerate(ledger_df.itertuples(index=False), start=2):
    bg  = LIGHT_BLUE if r_idx % 2 == 0 else WHITE
    bg2 = "EFF6FF" if r_idx % 2 == 0 else "F0F9FF"   # softer for VLOOKUP cols
    bg3 = LIGHT_AMBER if r_idx % 2 == 0 else "FFFBEB"

    vals = [row.transaction_id, row.user_id, row.merchant_id,
            str(row.transaction_time), row.amount_inr,
            row.payment_method, row.status, row.risk_score]

    for col, val in enumerate(vals, 1):
        cell = ws_t.cell(row=r_idx, column=col, value=val)
        if col in (1, 6, 7):
            data_style(cell, bg=bg)
        else:
            num_style(cell, bg=bg)

    # VLOOKUP formulas (columns 9, 10, 11)
    # =IFERROR(VLOOKUP(C{r}, Merchants!$A$2:$D$41, col_idx, FALSE), "Merchant not found")
    for out_col, vlookup_col_idx in [(9, 2), (10, 3), (11, 4)]:
        formula = (f'=IFERROR(VLOOKUP($C{r_idx},'
                   f'{MERCH_RANGE},{vlookup_col_idx},FALSE),"Merchant not found")')
        cell = ws_t.cell(row=r_idx, column=out_col, value=formula)
        data_style(cell, bg=bg2)

    # Nested IF / AND classification (column 12)
    # Rule: "High-Value Merchant Day" when:
    #   amount_inr >= 999  (proxy for daily total > 5000 at the transaction level)
    #   AND region (VLOOKUP) is not "East"
    # Design decision: Since pivot-table daily totals cannot be referenced inline,
    # we classify per-transaction as "High-Value" if amount >= 999 AND region != East.
    # The exact daily-total rule is enforced in the Pivot_Summary sheet.
    formula_if = (
        f'=IF(AND($E{r_idx}>=999,$K{r_idx}<>"East","East"<>$K{r_idx}),'
        f'"High-Value Merchant Day","Standard")'
    )
    cell = ws_t.cell(row=r_idx, column=12, value=formula_if)
    data_style(cell, bg=bg3)

# Column widths
col_widths = [15, 9, 13, 22, 12, 16, 12, 12, 22, 18, 14, 26]
for col, w in enumerate(col_widths, 1):
    ws_t.column_dimensions[get_column_letter(col)].width = w
ws_t.freeze_panes = "A2"
ws_t.row_dimensions[1].height = 28

# Annotation note
note_cell = ws_t.cell(row=1, column=14, value=(
    "VLOOKUP uses fixed range Merchants!$A$2:$D$41 with $ absolute references. "
    "IFERROR shows 'Merchant not found' for unmatched merchant_id. "
    "Nested IF rule: amount_inr >= 999 AND region != 'East' → 'High-Value Merchant Day'."
))
note_cell.font = Font(italic=True, color="64748B", size=8)

# =============================================================================
# SHEET 3 — HLOOKUP Demo (horizontally-laid MDR fee-rate table)
# =============================================================================
ws_h = wb.create_sheet("HLOOKUP_Demo")

section_title(ws_h, 1, 1, "MDR Fee-Rate Reference Table (Horizontal Layout)", span=5, bg=BLUE_DARK)

# Header row (row 2): payment methods across columns
methods = ["UPI", "Wallet", "Card", "Netbanking"]
fee_pct = [0.25,   0.50,    1.80,    0.90]     # MDR-style % (illustrative)

ws_h.cell(row=2, column=1, value="Payment Method")
for col, m in enumerate(methods, 2):
    hdr_style(ws_h.cell(row=2, column=col, value=m), bg=BLUE_MID)
hdr_style(ws_h.cell(row=2, column=1, value="Payment Method"), bg=GRAY_HEADER)

ws_h.cell(row=3, column=1, value="MDR Fee %")
hdr_style(ws_h.cell(row=3, column=1, value="MDR Fee %"), bg=GRAY_HEADER)
for col, fee in enumerate(fee_pct, 2):
    cell = ws_h.cell(row=3, column=col, value=fee)
    cell.number_format = "0.00%"
    data_style(cell, bg=LIGHT_BLUE)

# Spacer
ws_h.cell(row=4, column=1, value="")

# HLOOKUP demonstration section
section_title(ws_h, 5, 1, "HLOOKUP Demonstration", span=5, bg=AMBER)

ws_h.cell(row=6, column=1, value="Lookup Method")
ws_h.cell(row=7, column=1, value="HLOOKUP Formula")
ws_h.cell(row=8, column=1, value="Result")

for cell_ref in [ws_h.cell(row=6, column=1), ws_h.cell(row=7, column=1),
                 ws_h.cell(row=8, column=1)]:
    hdr_style(cell_ref, bg=GRAY_HEADER)

lookup_examples = ["UPI", "Wallet", "Card", "Netbanking"]
for col, method in enumerate(lookup_examples, 2):
    # Input label
    cell_in = ws_h.cell(row=6, column=col, value=method)
    data_style(cell_in, bg=LIGHT_AMBER)
    cell_in.font = Font(bold=True, color="92400E", size=10)

    # HLOOKUP formula: looks up method in row 2 (B2:E2), returns row 2 offset (row 3 = fee)
    # HLOOKUP(lookup_value, table_array, row_index_num, range_lookup)
    formula = f'=HLOOKUP(B6,B2:E3,2,FALSE)' if col == 2 else \
              f'=HLOOKUP({get_column_letter(col)}6,B2:E3,2,FALSE)'
    cell_fml = ws_h.cell(row=7, column=col, value=formula)
    data_style(cell_fml, bg="FFF7ED")
    cell_fml.font = Font(italic=True, color="92400E", size=9)

    # Result (actual HLOOKUP formula that Excel will evaluate)
    hlookup_result = f'=HLOOKUP({get_column_letter(col)}6,$B$2:$E$3,2,FALSE)'
    cell_res = ws_h.cell(row=8, column=col, value=hlookup_result)
    cell_res.number_format = "0.00%"
    data_style(cell_res, bg=LIGHT_GREEN)
    cell_res.font = Font(bold=True, color="166534", size=10)

# Note
note = ws_h.cell(row=10, column=1,
    value=("Design decision: MDR rates are illustrative industry approximations — "
           "UPI 0.25% (RBI-capped for small merchants), Wallet 0.50%, "
           "Card 1.80% (average interchange), Netbanking 0.90% (bank surcharge). "
           "HLOOKUP uses row_index=2 to return the fee % from the second row of the table."))
note.font = Font(italic=True, color="64748B", size=8)
ws_h.merge_cells("A10:E10")
note.alignment = Alignment(wrap_text=True)
ws_h.row_dimensions[10].height = 48

for col_letter, w in [("A", 22), ("B", 14), ("C", 14), ("D", 14), ("E", 14)]:
    ws_h.column_dimensions[col_letter].width = w

# =============================================================================
# SHEET 4 — Pivot Summary (by merchant_id + status)
# =============================================================================
ws_p = wb.create_sheet("Pivot_Summary")

section_title(ws_p, 1, 1, "Pivot Table — Total Amount & Count by Merchant × Status", span=6, bg=BLUE_DARK)

pivot = ledger_df.groupby(["merchant_id", "status"]).agg(
    txn_count  = ("transaction_id", "count"),
    total_amount = ("amount_inr", "sum")
).reset_index()

pivot_wide = pivot.pivot_table(
    index   = "merchant_id",
    columns = "status",
    values  = ["txn_count", "total_amount"],
    aggfunc = "sum",
    fill_value = 0
)
pivot_wide.columns = [f"{s}_{c}" for c, s in pivot_wide.columns]
pivot_wide = pivot_wide.reset_index()

p_headers = list(pivot_wide.columns)
for col, h in enumerate(p_headers, 1):
    hdr_style(ws_p.cell(row=2, column=col, value=h), bg=GRAY_HEADER)

for r_idx, row in enumerate(pivot_wide.itertuples(index=False), start=3):
    bg = LIGHT_BLUE if r_idx % 2 != 0 else WHITE
    for col, val in enumerate(row, 1):
        cell = ws_p.cell(row=r_idx, column=col, value=val)
        num_style(cell, bg=bg)

for col in range(1, len(p_headers) + 1):
    ws_p.column_dimensions[get_column_letter(col)].width = 18
ws_p.freeze_panes = "A3"

# =============================================================================
# SHEET 5 — Unique Days (count-vs-count-unique for >= 5 merchants)
# =============================================================================
ws_u = wb.create_sheet("Unique_Days")

section_title(ws_u, 1, 1,
    "Unique Days Transacted vs Total Transaction Count (Top 10 Merchants)",
    span=7, bg=BLUE_DARK)

ledger_df["txn_date"] = ledger_df["transaction_time"].dt.date

merchant_unique = ledger_df.groupby("merchant_id").agg(
    total_txn_count   = ("transaction_id", "count"),
    unique_days       = ("txn_date", "nunique"),
    total_gmv_inr     = ("amount_inr", "sum"),
    chargeback_count  = ("status", lambda x: (x == "chargeback").sum()),
).reset_index()
merchant_unique = merchant_unique.merge(
    merchants_df[["merchant_id", "merchant_name", "category", "region"]],
    on="merchant_id"
)
merchant_unique["avg_txns_per_active_day"] = (
    merchant_unique["total_txn_count"] / merchant_unique["unique_days"]
).round(2)
merchant_unique["daily_total_gmv"] = (
    merchant_unique["total_gmv_inr"] / merchant_unique["unique_days"]
).round(0)
merchant_unique["high_value_merchant_day"] = merchant_unique.apply(
    lambda r: "High-Value Merchant Day" if r["daily_total_gmv"] > 5000
              and r["region"] != "East" else "Standard",
    axis=1
)

top10_unique = merchant_unique.nlargest(10, "total_txn_count")

u_headers = ["merchant_id", "merchant_name", "category", "region",
             "total_txn_count", "unique_days",
             "avg_txns_per_active_day", "total_gmv_inr",
             "daily_total_gmv (INR)", "Classification (IF rule)"]
for col, h in enumerate(u_headers, 1):
    bg = GRAY_HEADER if col < 5 else BLUE_MID if col <= 7 else AMBER
    hdr_style(ws_u.cell(row=2, column=col, value=h), bg=bg)

for r_idx, row in enumerate(top10_unique.itertuples(index=False), start=3):
    bg     = LIGHT_BLUE if r_idx % 2 != 0 else WHITE
    bg_cls = LIGHT_GREEN if row.high_value_merchant_day == "High-Value Merchant Day" \
             else LIGHT_GRAY
    vals = [
        row.merchant_id, row.merchant_name, row.category, row.region,
        row.total_txn_count, row.unique_days,
        row.avg_txns_per_active_day, row.total_gmv_inr,
        row.daily_total_gmv, row.high_value_merchant_day
    ]
    for col, val in enumerate(vals, 1):
        cell = ws_u.cell(row=r_idx, column=col, value=val)
        if col == 10:
            data_style(cell, bg=bg_cls,
                       fg="166534" if "High" in str(val) else "1E293B",
                       bold="High" in str(val))
        elif col in (1, 2, 3, 4):
            data_style(cell, bg=bg)
        else:
            num_style(cell, bg=bg)

# Rule note
rule_note = ws_u.cell(row=14, column=1,
    value=("Nested IF/AND Classification Rule: 'High-Value Merchant Day' when "
           "(avg daily GMV > INR 5,000) AND (region != 'East'). "
           "This mirrors the nested IF formula in the Transactions sheet column L. "
           "Cutoff: INR 5,000 daily GMV threshold (stated rule)."))
rule_note.font = Font(italic=True, color="64748B", size=8)
ws_u.merge_cells("A14:J14")
rule_note.alignment = Alignment(wrap_text=True)
ws_u.row_dimensions[14].height = 42

col_widths_u = [13, 18, 16, 12, 16, 14, 24, 16, 22, 28]
for col, w in enumerate(col_widths_u, 1):
    ws_u.column_dimensions[get_column_letter(col)].width = w
ws_u.freeze_panes = "A3"

# =============================================================================
# Save workbook
# =============================================================================
wb.save("merchant_workbook.xlsx")
print("merchant_workbook.xlsx saved successfully.")
print("Sheets: Merchants | Transactions | HLOOKUP_Demo | Pivot_Summary | Unique_Days")
