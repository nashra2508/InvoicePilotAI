
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_table, get_connection
from ai_service import generate_invoice_draft,generate_payment_reminder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
app = FastAPI(title="InvoicePilotAI")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    create_table()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/invoices")
def get_invoices():
    conn = get_connection()
    invoices = conn.execute(
        "SELECT * FROM invoices"
    ).fetchall()
    conn.close()

    return [dict(invoice) for invoice in invoices]

from pydantic import BaseModel
from datetime import date


class InvoiceCreate(BaseModel):
    client_name: str
    description: str
    amount: float
    due_date: date


@app.post("/invoices")
def create_invoice(invoice: InvoiceCreate):
    conn = get_connection()

    cursor = conn.execute(
        """INSERT INTO invoices
        (client_name, description, amount, due_date, status)
        VALUES (?, ?, ?, ?, ?)""",
        (
            invoice.client_name,
            invoice.description,
            invoice.amount,
            invoice.due_date.isoformat(),
            "Pending"
        )
    )

    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Invoice created successfully",
        "invoice_id": invoice_id,
        "status": "Pending"
    }

from pydantic import BaseModel


class JobDescription(BaseModel):
    job_description: str


@app.post("/generate-invoice")
def generate_invoice(data: JobDescription):

    if not data.job_description.strip():
        return {"error": "Job description cannot be empty"}

    try:
        draft = generate_invoice_draft(data.job_description)

        if not draft.get("client_name") or not draft.get("description"):
            return {"error": "Please provide the missing invoice details"}

        if not draft.get("amount") or not draft.get("due_date"):
            return {"error": "Amount and due date are required"}

        conn = get_connection()

        cursor = conn.execute(
            """INSERT INTO invoices
            (client_name, description, amount, due_date, status)
            VALUES (?, ?, ?, ?, ?)""",
            (
                draft["client_name"],
                draft["description"],
                float(draft["amount"]),
                draft["due_date"],
                "Pending"
            )
        )

        conn.commit()
        invoice_id = cursor.lastrowid
        conn.close()

        return {
            "message": "AI invoice generated and saved successfully",
            "invoice_id": invoice_id,
            "invoice": draft,
            "status": "Pending"
        }

    except Exception as error:
        return {"error": str(error)}
    

@app.post("/generate-reminder")
def create_payment_reminder(data: dict):

    invoice_id = data.get("invoice_id")

    if not invoice_id:
        return {"error": "Invoice ID is required"}

    conn = get_connection()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE invoice_id = ?",
        (invoice_id,)
    ).fetchone()

    conn.close()

    if invoice is None:
        return {"error": "Invoice not found"}

    try:
        reminder = generate_payment_reminder(
            invoice["client_name"],
            invoice["description"],
            invoice["amount"],
            invoice["due_date"]
        )

        return {
            "message": "Payment reminder generated successfully",
            "invoice_id": invoice_id,
            "reminder": reminder
        }

    except Exception as error:
        return {"error": str(error)}
@app.put("/invoices/{invoice_id}/pay")
def mark_invoice_paid(invoice_id: int):

    conn = get_connection()

    cursor = conn.execute(
        "UPDATE invoices SET status = 'Paid' WHERE invoice_id = ?",
        (invoice_id,)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return {"error": "Invoice not found"}

    return {
        "message": "Invoice marked as Paid successfully",
        "invoice_id": invoice_id,
        "status": "Paid"
    }


