from flask import Flask, render_template, request, send_file
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)
EXCHANGE_RATE = 89  # USD to INR for revenue calculations only


# ✅ Format function added
def format_number(n, currency="USD"):
    try:
        n = float(n)
    except:
        return n

    if currency == "USD":
        if n >= 1_000_000:
            return f"${round(n/1_000_000, 2)}M"
        elif n >= 1_000:
            return f"${round(n/1_000, 2)}k"
        else:
            return f"${round(n, 2)}"

    # INR format
    if n >= 10_000_000:  # 1 crore+
        return f"₹{round(n/10_000_00, 2)}Cr"
    elif n >= 100_000:  # 1 lakh+
        return f"₹{round(n/100000, 2)}L"
    else:
        return f"₹{round(n, 2)}"


def clean_column_names(df):
    df.columns = (
        df.columns.str.strip()
        .str.replace('\n', ' ', regex=True)
        .str.replace('\r', '', regex=True)
        .str.replace(' +', ' ', regex=True)
    )
    return df


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            df = pd.read_excel(file)
            df = clean_column_names(df)

            # Drop any existing Profit columns
            df = df.loc[:, ~df.columns.str.contains("Profit", case=False)]

            # Ensure numeric columns exist
            numeric_cols = ["Billing Rate ($)", "Billable Hours"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                else:
                    df[col] = 0

            # Cost Rate/Yearly($)
            if "Cost Rate/Yearly($)" not in df.columns:
                df["Cost Rate/Yearly($)"] = 0
            else:
                df["Cost Rate/Yearly($)"] = df["Cost Rate/Yearly($)"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                df["Cost Rate/Yearly($)"] = pd.to_numeric(df["Cost Rate/Yearly($)"], errors="coerce").fillna(0)

            # ✅ Calculations
            df["Cost /Month (INR)"] = (df["Cost Rate/Yearly($)"] / 12).round(2)
            df["Billing Rate (INR)"] = df["Billing Rate ($)"] * EXCHANGE_RATE
            df["Revenue /Month ($)"] = df["Billing Rate ($)"] * df["Billable Hours"]
            df["Revenue /Yr ($)"] = df["Revenue /Month ($)"] * 12
            df["Revenue (INR)"] = df["Billing Rate (INR)"] * df["Billable Hours"]
            df["Profit (₹)"] = df["Revenue (INR)"] - df["Cost /Month (INR)"]
            df["Profitability (%)"] = df.apply(
                lambda row: (row["Profit (₹)"] / row["Revenue (INR)"] * 100)
                if row["Revenue (INR)"] != 0 else 0, axis=1
            )

            # ✅ Apply formatted values
            df["Billing Rate (INR)"] = df["Billing Rate (INR)"].apply(lambda x: format_number(x, "INR"))
            df["Revenue /Month ($)"] = df["Revenue /Month ($)"].apply(lambda x: format_number(x, "USD"))
            df["Revenue /Yr ($)"] = df["Revenue /Yr ($)"].apply(lambda x: format_number(x, "USD"))
            df["Revenue (INR)"] = df["Revenue (INR)"].apply(lambda x: format_number(x, "INR"))
            df["Cost /Month (INR)"] = df["Cost /Month (INR)"].apply(lambda x: format_number(x, "INR"))
            df["Cost Rate/Yearly($)"] = df["Cost Rate/Yearly($)"].apply(lambda x: format_number(x, "USD"))
            df["Profit (₹)"] = df["Profit (₹)"].apply(lambda x: format_number(x, "INR"))

            df["Profitability (%)"] = df["Profitability (%)"].round(2).astype(str) + "%"

            # Remove rows where all numeric columns are zero
            df = df.loc[~(df[["Billing Rate ($)", "Billable Hours"]].sum(axis=1) == 0)]

            # Save to Excel memory buffer
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_name = f"Revenue Assurance Output_{timestamp}.xlsx"

            return send_file(
                output,
                download_name=download_name,
                as_attachment=True,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    return render_template("index.html")


if __name__ == "__main__":
    print("✅ Flask app running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
