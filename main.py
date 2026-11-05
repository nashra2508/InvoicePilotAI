
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import create_table, get_connection
from ai_service import generate_invoice_draft, generate_payment_reminder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import date
from paypal_service import create_paypal_order, capture_paypal_order
from currency_service import convert_inr_to_usd


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


# PayPal public Client ID for frontend SDK
@app.get("/paypal-config")
def get_paypal_config():
    client_id = os.getenv("PAYPAL_CLIENT_ID")

    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="PayPal Client ID not configured"
        )

    return {
        "client_id": client_id
    }


@app.get("/invoices")
def get_invoices():
    conn = get_connection()

    try:
        invoices = conn.execute(
            "SELECT * FROM invoices"
        ).fetchall()

        return [dict(invoice) for invoice in invoices]

    finally:
        conn.close()


class InvoiceCreate(BaseModel):
    client_name: str
    description: str
    amount: float
    due_date: date


@app.post("/invoices")
def create_invoice(invoice: InvoiceCreate):
    conn = get_connection()

    try:
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

        return {
            "message": "Invoice created successfully",
            "invoice_id": invoice_id,
            "status": "Pending"
        }

    finally:
        conn.close()


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

        try:
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

        finally:
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

    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (invoice_id,)
        ).fetchone()

    finally:
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

    try:
        cursor = conn.execute(
            "UPDATE invoices SET status = 'Paid' WHERE invoice_id = ?",
            (invoice_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Invoice not found"}

        return {
            "message": "Invoice marked as Paid successfully",
            "invoice_id": invoice_id,
            "status": "Paid"
        }

    finally:
        conn.close()


class PayPalOrderRequest(BaseModel):
    invoice_id: int


@app.post("/create-paypal-order")
def create_payment_order(data: PayPalOrderRequest):

    conn = get_connection()

    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (data.invoice_id,)
        ).fetchone()

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        if invoice["status"] == "Paid":
            raise HTTPException(
                status_code=400,
                detail="Invoice already paid"
            )

        usd_amount, exchange_rate, rate_date = convert_inr_to_usd(
            invoice["amount"]
        )

        order = create_paypal_order(
            usd_amount,
            data.invoice_id
        )

        conn.execute(
            "UPDATE invoices SET paypal_order_id = ? WHERE invoice_id = ?",
            (order["id"], data.invoice_id)
        )

        conn.commit()

        return {
            "order_id": order["id"],
            "status": order["status"],
            "inr_amount": invoice["amount"],
            "usd_amount": str(usd_amount),
            "exchange_rate": str(exchange_rate),
            "rate_date": rate_date
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        conn.close()


@app.post("/capture-paypal-payment")
def capture_payment(data: PayPalOrderRequest):

    conn = get_connection()

    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (data.invoice_id,)
        ).fetchone()

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        if invoice["status"] == "Paid":
            raise HTTPException(
                status_code=400,
                detail="Invoice already paid"
            )

        order_id = invoice["paypal_order_id"]

        if not order_id:
            raise HTTPException(
                status_code=400,
                detail="PayPal order not found"
            )

        result = capture_paypal_order(order_id)

        if result.get("status") != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail="Payment not completed"
            )

        capture_id = (
            result["purchase_units"][0]["payments"]["captures"][0]["id"]
        )

        conn.execute(
            """UPDATE invoices
               SET status = 'Paid', paypal_capture_id = ?
               WHERE invoice_id = ?""",
            (capture_id, data.invoice_id)
        )

        conn.commit()

        return {
            "message": "PayPal payment successful",
            "invoice_id": data.invoice_id,
            "capture_id": capture_id,
            "status": "Paid"
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        conn.close()
