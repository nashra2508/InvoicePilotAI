import os
import requests
from dotenv import load_dotenv

load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv(
    "PAYPAL_BASE_URL",
    "https://api-m.sandbox.paypal.com"
)


class PayPalError(Exception):
    def __init__(self, message, status_code=None, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


def get_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    base_url = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    if not client_id or not client_secret:
        raise PayPalError("PayPal credentials (PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET) are missing from .env")

    if client_id.strip() == client_secret.strip():
        raise PayPalError(
            "PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env are identical. "
            "Please paste the actual Client Secret from your PayPal Developer Dashboard."
        )

    response = requests.post(
        f"{base_url}/v1/oauth2/token",
        auth=(client_id, client_secret),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        timeout=30
    )

    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = err_data.get("error_description") or err_data.get("error") or response.text
        except Exception:
            err_msg = response.text
        raise PayPalError(
            f"PayPal authentication failed ({response.status_code}): {err_msg}",
            status_code=response.status_code
        )

    return response.json()["access_token"]


def create_paypal_order(amount, invoice_id):
    token = get_access_token()
    base_url = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    response = requests.post(
        f"{base_url}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(invoice_id),
                "custom_id": str(invoice_id),
                "description": f"Invoice #{invoice_id} Payment",
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}"
                }
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "brand_name": "InvoicePilotAI",
                        "landing_page": "NO_PREFERENCE",
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "PAY_NOW"
                    }
                }
            }
        },
        timeout=30
    )

    if response.status_code not in (200, 201):
        try:
            err_data = response.json()
            details = err_data.get("details", [])
            desc = details[0].get("description") if details else err_data.get("message")
        except Exception:
            desc = response.text
        raise PayPalError(
            f"PayPal order creation failed ({response.status_code}): {desc}",
            status_code=response.status_code
        )

    return response.json()


def capture_paypal_order(order_id):
    token = get_access_token()
    base_url = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    response = requests.post(
        f"{base_url}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json={},
        timeout=30
    )

    if response.status_code not in (200, 201):
        try:
            err_data = response.json()
            details = err_data.get("details", [])
            if details:
                issue = details[0].get("issue", "DECLINED")
                desc = details[0].get("description", "Payment capture declined")
                msg = f"PayPal payment declined [{issue}]: {desc}"
            else:
                msg = err_data.get("message", "Payment capture failed")
        except Exception:
            msg = response.text
        raise PayPalError(msg, status_code=response.status_code)

    return response.json()


def get_paypal_order(order_id):
    token = get_access_token()
    base_url = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    response = requests.get(
        f"{base_url}/v2/checkout/orders/{order_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=30
    )

    if response.status_code != 200:
        try:
            err_data = response.json()
            msg = err_data.get("message") or response.text
        except Exception:
            msg = response.text
        raise PayPalError(
            f"Could not retrieve PayPal order ({response.status_code}): {msg}",
            status_code=response.status_code
        )

    return response.json()
