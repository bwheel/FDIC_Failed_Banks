#!/usr/bin/env python3
import sqlite3
import requests
import csv
import io
import gzip

# -------------------------------
# Configuration
# -------------------------------
CSV_URL = "https://www.fdic.gov/bank-failures/download-data.csv"
DB_FILE = "fdic_failed_banks.db"
GZ_FILE = "fdic_failed_banks.db.gz"

# -------------------------------
# Download CSV
# -------------------------------
print(f"Downloading CSV from {CSV_URL}...")
resp = requests.get(CSV_URL)
resp.raise_for_status()

csv_text = resp.content.decode("windows-1252").replace("\xa0", "")
csv_file = io.StringIO(csv_text)
reader = csv.DictReader(csv_file)
next(reader)  # skip first row
# -------------------------------
# Create SQLite Database
# -------------------------------
print(f"Creating SQLite database {DB_FILE}...")
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Drop tables if exist
cur.execute("DROP TABLE IF EXISTS failed_banks;")
cur.execute("DROP TABLE IF EXISTS failed_banks_fts;")

# Create regular table
cur.execute("""
CREATE TABLE failed_banks (
    bank_name TEXT,
    city TEXT,
    state TEXT,
    cert TEXT,
    acquiring_institution TEXT,
    closing_date TEXT,
    fund TEXT
);
""")

# Create FTS5 table for full-text search including state and cert
cur.execute("""
CREATE VIRTUAL TABLE failed_banks_fts USING fts5(
    bank_name,
    city,
    state,
    cert,
    acquiring_institution,
    content='failed_banks',
    content_rowid='rowid'
);
""")

# -------------------------------
# Insert data
# -------------------------------
rows = []
for row in reader:
    rows.append(
        (
            row.get("Bank Name", "").strip(),
            row.get("City", "").strip(),
            row.get("State", "").strip(),
            row.get("Cert", "").strip(),
            row.get("Acquiring Institution", "").strip(),
            row.get("Closing Date", "").strip(),
            row.get("Fund", "").strip(),
        )
    )

print(f"Inserting {len(rows)} rows into main table...")
cur.executemany(
    """
INSERT INTO failed_banks (
    bank_name, city, state, cert, acquiring_institution, closing_date, fund
) VALUES (?, ?, ?, ?, ?, ?, ?)
""",
    rows,
)

# Populate FTS table
print("Populating FTS table...")
cur.execute("""
INSERT INTO failed_banks_fts (
    rowid, bank_name, city, state, cert, acquiring_institution
)
SELECT rowid, bank_name, city, state, cert, acquiring_institution
FROM failed_banks;
""")

conn.commit()
conn.close()

# -------------------------------
# Gzip the SQLite database
# -------------------------------
print(f"Gzipping database to {GZ_FILE}...")
with open(DB_FILE, "rb") as f_in, gzip.open(GZ_FILE, "wb") as f_out:
    f_out.writelines(f_in)

print("Done!")
