import os
import pandas as pd
from datetime import datetime

# ====== PATH SETUP ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SOURCE_DIR = os.path.join(DATA_DIR, "source")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

# ensure folders exist
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== CLEAN CURRENCY FUNCTION ======
def clean_currency(value):
    """Remove $ and ₹ and commas; convert to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).replace("$", "").replace("₹", "").replace(",", "").strip()
    try:
        return float(value)
    except:
        return 0.0

# ====== MAIN PROCESS FUNCTION ======
def process_file(file_path):
    print(f"🔹 Reading file: {os.path.basename(file_path)}")
    df = pd.read_excel(file_path)

    # ===== CLEAN AND STANDARDIZE COLUMN NAMES =====
    df.columns = [' '.join(str(c).replace("\n", " ").split()).strip() for c in df.columns]

    # ===== REMOVE COMPLETELY EMPTY ROWS =====
    df = df.dropna(how="all")

    # ---- Clean numeric columns automatically ----
    numeric_keywords = ["$", "₹", "Rate", "Revenue", "Cost", "Profit", "Hours"]
    for col in df.columns:
        if any(key in col for key in numeric_keywords):
            df[col] = df[col].apply(clean_currency)

    # ===== APPLY FORMULAS =====
    # Ensure required columns exist
    if "Billing Rate ($)" not in df.columns or "Billable Hours" not in df.columns:
        print(f"⚠️ Skipping file {os.path.basename(file_path)}: Missing required columns")
        return

    df["Billing Rate (INR)"] = df["Billing Rate ($)"] * 89
    df["Revenue /Month ($)"] = df["Billing Rate ($)"] * df["Billable Hours"]
    df["Revenue /Yr ($)"] = df["Revenue /Month ($)"] * 12
    df["Revenue (INR)"] = df["Billing Rate (INR)"] * df["Billable Hours"]

    if "Cost /Month (INR)" in df.columns:
        df["Profit (₹)"] = df["Revenue (INR)"] - df["Cost /Month (INR)"]
    else:
        df["Profit (₹)"] = df["Revenue (INR)"]

    df["Profitability (%)"] = df.apply(
        lambda row: 0 if row["Revenue (INR)"] == 0 else (row["Profit (₹)"] / row["Revenue (INR)"]) * 100,
        axis=1,
    )

    # round results
    df = df.round(2)

    # ===== REMOVE ORIGINAL Profit / Profitability % COLUMNS =====
    for col in ["Profit", "Profitability %"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # ====== SAVE OUTPUT ======
    out_filename = f"Processed_Revenue_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, out_filename)
    df.to_excel(output_path, index=False)
    print(f"✅ Output Excel saved: {output_path}")

# ====== MAIN DRIVER ======
def main():
    excel_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith((".xlsx", ".xls"))]
    if not excel_files:
        print("⚠️ No Excel files found in data/source/")
        return

    for file in excel_files:
        process_file(os.path.join(SOURCE_DIR, file))

    print("\n🎉 All files processed successfully!")

if __name__ == "__main__":
    main()
