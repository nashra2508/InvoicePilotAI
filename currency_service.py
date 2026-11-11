import datetime
from decimal import Decimal, ROUND_HALF_UP
import requests

PRIMARY_API = "https://api.frankfurter.dev/v1/latest?base=INR&symbols=USD"
SECONDARY_API = "https://api.frankfurter.app/latest?from=INR&to=USD"
FALLBACK_RATE = Decimal("0.012")  # Approximate fallback rate (~83.3 INR/USD)


def get_inr_to_usd_rate():
    # Try primary endpoint
    for endpoint in (PRIMARY_API, SECONDARY_API):
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "rates" in data and "USD" in data["rates"]:
                    rate = Decimal(str(data["rates"]["USD"]))
                    if rate > 0:
                        return rate, data.get("date", datetime.date.today().isoformat())
        except Exception as e:
            print(f"Warning: Currency API {endpoint} error: {e}")
            continue

    # Fallback if both external APIs are unreachable or offline
    print(f"Using fallback exchange rate: {FALLBACK_RATE}")
    return FALLBACK_RATE, datetime.date.today().isoformat()


def convert_inr_to_usd(amount):
    inr_amount = Decimal(str(amount))

    if inr_amount <= 0:
        raise ValueError("Invoice amount must be positive")

    rate, rate_date = get_inr_to_usd_rate()

    usd_amount = (inr_amount * rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if usd_amount <= 0:
        usd_amount = Decimal("0.01")

    return usd_amount, rate, rate_date
