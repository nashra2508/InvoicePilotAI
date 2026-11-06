
import sqlite3

DATABASE_NAME = "invoices.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                paypal_order_id TEXT,
                paypal_capture_id TEXT,
                paypal_usd_amount TEXT
            )
        """)

        # Check existing database columns
        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(invoices)"
            ).fetchall()
        }

        # Add PayPal columns if they are missing
        if "paypal_order_id" not in existing_columns:
            conn.execute(
                "ALTER TABLE invoices ADD COLUMN paypal_order_id TEXT"
            )

        if "paypal_capture_id" not in existing_columns:
            conn.execute(
                "ALTER TABLE invoices ADD COLUMN paypal_capture_id TEXT"
            )
        if "paypal_usd_amount" not in existing_columns:
            conn.execute(
                "ALTER TABLE invoices ADD COLUMN paypal_usd_amount TEXT"
            )

        conn.commit()

    finally:
        conn.close()
