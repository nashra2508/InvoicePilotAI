import os
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_service import generate_invoice_draft, generate_payment_reminder
from currency_service import convert_inr_to_usd
from database import create_table, get_connection
from paypal_service import (
    PayPalError,
    capture_paypal_order,
    create_paypal_order,
    get_paypal_order,
)

app = FastAPI(title="InvoicePilotAI")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_table()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/paypal-config")
def get_paypal_config():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=500, detail="PayPal Client ID not configured"
        )
    return {"client_id": client_id}


@app.get("/invoices")
def get_invoices():
    conn = get_connection()
    try:
        invoices = conn.execute("SELECT * FROM invoices").fetchall()
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
            """
            INSERT INTO invoices
            (client_name, description, amount, due_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                invoice.client_name,
                invoice.description,
                invoice.amount,
                invoice.due_date.isoformat(),
                "Pending",
            ),
        )
        conn.commit()
        invoice_id = cursor.lastrowid
        return {
            "message": "Invoice created successfully",
            "invoice_id": invoice_id,
            "status": "Pending",
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
                """
                INSERT INTO invoices
                (client_name, description, amount, due_date, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    draft["client_name"],
                    draft["description"],
                    float(draft["amount"]),
                    draft["due_date"],
                    "Pending",
                ),
            )
            conn.commit()
            invoice_id = cursor.lastrowid
        finally:
            conn.close()

        return {
            "message": "AI invoice generated and saved successfully",
            "invoice_id": invoice_id,
            "invoice": draft,
            "status": "Pending",
        }
    except Exception as error:
        print(f"AI invoice generation error: {error}")
        return {"error": str(error)}


@app.post("/generate-reminder")
def create_payment_reminder(data: dict):
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return {"error": "Invoice ID is required"}

    conn = get_connection()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)
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
            invoice["due_date"],
        )
        return {
            "message": "Payment reminder generated successfully",
            "invoice_id": invoice_id,
            "reminder": reminder,
        }
    except Exception as error:
        print(f"Payment reminder error: {error}")
        return {"error": str(error)}


class PayPalOrderRequest(BaseModel):
    invoice_id: int
    order_id: str | None = None


@app.post("/create-paypal-order")
def create_payment_order(data: PayPalOrderRequest):
    conn = get_connection()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (data.invoice_id,),
        ).fetchone()

        if invoice is None:
            raise HTTPException(404, "Invoice not found")

        if invoice["status"] == "Paid":
            raise HTTPException(400, "Invoice already paid")

        # Check whether an existing order is reusable
        existing_order_id = invoice["paypal_order_id"]
        if existing_order_id:
            try:
                existing_order = get_paypal_order(existing_order_id)
                existing_status = existing_order.get("status")

                if existing_status in ("CREATED", "SAVED"):
                    return {
                        "order_id": existing_order_id,
                        "status": existing_status,
                        "inr_amount": invoice["amount"],
                        "usd_amount": invoice["paypal_usd_amount"],
                        "exchange_rate": None,
                        "rate_date": None,
                    }

                if existing_status == "COMPLETED":
                    raise HTTPException(
                        status_code=409,
                        detail="PayPal order is completed. Verify payment before creating another order.",
                    )
            except HTTPException:
                raise
            except Exception as e:
                print(
                    f"Notice: Could not reuse order {existing_order_id} ({e}); generating a new order."
                )

        usd_amount, exchange_rate, rate_date = convert_inr_to_usd(
            invoice["amount"]
        )

        order = create_paypal_order(usd_amount, data.invoice_id)

        conn.execute(
            """
            UPDATE invoices
            SET paypal_order_id = ?,
                paypal_usd_amount = ?
            WHERE invoice_id = ?
            """,
            (order["id"], str(usd_amount), data.invoice_id),
        )
        conn.commit()

        return {
            "order_id": order["id"],
            "status": order["status"],
            "inr_amount": invoice["amount"],
            "usd_amount": str(usd_amount),
            "exchange_rate": str(exchange_rate),
            "rate_date": rate_date,
        }

    except HTTPException:
        raise
    except PayPalError as pe:
        print(f"PayPal error creating order: {pe}")
        raise HTTPException(status_code=400, detail=str(pe))
    except Exception as error:
        print(f"Payment order creation error: {error}")
        raise HTTPException(
            status_code=500, detail=f"Payment order creation failed: {error}"
        )
    finally:
        conn.close()


@app.post("/capture-paypal-payment")
def capture_payment(data: PayPalOrderRequest):
    conn = get_connection()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (data.invoice_id,),
        ).fetchone()

        if invoice is None:
            raise HTTPException(404, "Invoice not found")

        if invoice["status"] == "Paid":
            return {
                "message": "Payment already verified",
                "invoice_id": data.invoice_id,
                "capture_id": invoice["paypal_capture_id"],
                "status": "Paid",
            }

        order_id = invoice["paypal_order_id"]
        expected_amount = invoice["paypal_usd_amount"]

        if not data.order_id:
            raise HTTPException(
                status_code=400, detail="PayPal order ID is required"
            )

        if data.order_id != order_id:
            raise HTTPException(
                status_code=400, detail="PayPal order ID mismatch"
            )

        if not order_id or not expected_amount:
            raise HTTPException(
                status_code=400,
                detail="PayPal order or expected amount not found",
            )

        # Retrieve the existing PayPal order first
        result = get_paypal_order(order_id)

        # Capture only if PayPal has not completed the payment
        if result.get("status") == "APPROVED":
            result = capture_paypal_order(order_id)
        elif result.get("status") != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"PayPal order is not approved or completed (current status: {result.get('status')})",
            )

        # Verify order status
        if result.get("status") != "COMPLETED":
            raise HTTPException(400, "Payment not completed")

        # Get purchase and capture details
        purchase_units = result.get("purchase_units", [])
        if not purchase_units:
            raise HTTPException(400, "Invalid PayPal purchase details")

        purchase = purchase_units[0]

        # Verify invoice reference
        custom_ref = purchase.get("custom_id") or purchase.get("reference_id")
        if custom_ref and custom_ref != str(data.invoice_id):
            raise HTTPException(400, "Invoice reference mismatch")

        # Extract capture details
        captures = purchase.get("payments", {}).get("captures", [])
        if captures:
            capture = captures[0]

            if capture.get("status") and capture.get("status") != "COMPLETED":
                raise HTTPException(400, "Capture not completed")

            captured_amount = capture.get("amount", {})
            if (
                captured_amount.get("currency_code")
                and captured_amount.get("currency_code") != "USD"
            ):
                raise HTTPException(400, "Payment currency mismatch")

            if captured_amount.get("value") and expected_amount:
                try:
                    actual_amount = Decimal(captured_amount["value"])
                    required_amount = Decimal(expected_amount)
                    if actual_amount != required_amount:
                        raise HTTPException(400, "Payment amount mismatch")
                except (InvalidOperation, TypeError):
                    pass

            capture_id = capture.get("id") or result.get("id")
        else:
            capture_id = result.get("id") or f"CAP-{order_id}"

        # Update invoice status to 'Paid' in database
        conn.execute(
            """
            UPDATE invoices
            SET status = 'Paid',
                paypal_capture_id = ?
            WHERE invoice_id = ?
            """,
            (capture_id, data.invoice_id),
        )
        conn.commit()

        return {
            "message": "PayPal payment successfully verified. Status changed to Paid.",
            "invoice_id": data.invoice_id,
            "capture_id": capture_id,
            "status": "Paid",
        }

    except HTTPException:
        raise
    except PayPalError as pe:
        print(f"PayPal capture error: {pe}")
        raise HTTPException(status_code=400, detail=str(pe))
    except Exception as error:
        print(f"Payment capture error: {error}")
        raise HTTPException(
            status_code=500, detail=f"Payment processing failed: {error}"
        )
    finally:
        conn.close()


@app.put("/invoices/{invoice_id}/pay")
@app.post("/invoices/{invoice_id}/pay")
def mark_invoice_as_paid(invoice_id: int):
    conn = get_connection()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchone()

        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice["status"] == "Paid":
            return {
                "message": "Invoice already marked as Paid",
                "invoice_id": invoice_id,
                "status": "Paid",
            }

        conn.execute(
            """
            UPDATE invoices
            SET status = 'Paid'
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        )
        conn.commit()

        return {
            "message": "Invoice status successfully updated to Paid",
            "invoice_id": invoice_id,
            "status": "Paid",
        }
    finally:
        conn.close()
