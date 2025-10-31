import pandas as pd
import pyodbc
from datetime import datetime
from cryptography.fernet import Fernet

# ==============================
# CONFIGURATION
# ==============================
EXCEL_PATH = r"data\source\Project Revenue Profit_Oct25.xlsx"

SQL_SERVER = "10.130.205.15"
DATABASE = "RevenueAssurance"
USERNAME = "sa"
PASSWORD = "kmg@sqlstd2014"
TABLE_NAME = "Revenue_Assurance_Input"

# Encryption key (save this securely)
ENCRYPTION_KEY = b'FnlRuBcB3T_3CUqykFDBC_U-ltJ-K8geiy739Gn6Y2k='
fernet = Fernet(ENCRYPTION_KEY)

# Columns to encrypt
ENCRYPT_COLUMNS = ['Billable Hours', 'Cost Rate/Yearly($)', 'Cost /Month (INR)']

# ==============================
# STEP 1: READ EXCEL FILE
# ==============================
print("Reading Excel file...")
df = pd.read_excel(EXCEL_PATH)

# ==============================
# STEP 2: CLEAN COLUMN NAMES
# ==============================
df.columns = [col.replace("\n", " ").replace('"', '').strip() for col in df.columns]
df.columns = [' '.join(col.split()) for col in df.columns]

print("Columns after cleaning:")
print(df.columns.tolist())

# ==============================
# STEP 3: HANDLE BLANK CELLS AND ENCRYPT
# ==============================
for col in df.columns:
    if col != "Month":
        df[col] = df[col].apply(lambda x: None if pd.isna(x) or str(x).strip() == "" else str(x))

# Encrypt specific columns
for col in ENCRYPT_COLUMNS:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: fernet.encrypt(x.encode()).decode() if x else None)

# Add Created/Updated Dates
df["Created_Date"] = datetime.now().date()
df["Updated_Date"] = None

# ==============================
# STEP 4: CONNECT TO SQL SERVER
# ==============================
print("Connecting to SQL Server...")
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SQL_SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ==============================
# STEP 5: INSERT DATA INTO TABLE
# ==============================
columns = df.columns.tolist()

insert_sql = f"""
INSERT INTO {TABLE_NAME} ({', '.join(f'[{col}]' for col in columns)})
VALUES ({', '.join(['?'] * len(columns))})
"""

print("Inserting records into SQL Server...")
for _, row in df.iterrows():
    values = [row[col] for col in columns]
    cursor.execute(insert_sql, values)

conn.commit()
cursor.close()
conn.close()
print("✅ Data uploaded successfully with encryption!")
