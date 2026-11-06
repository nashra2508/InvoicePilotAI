from decimal import Decimal, ROUND_HALF_UP
import requests

EXCHANGE_RATE_API = "https://api.frankfurter.dev/v2/rate/INR/USD"


def get_inr_to_usd_rate():
    response = requests.get(
        EXCHANGE_RATE_API,
        timeout=15
    )
    response.raise_for_status()

    data = response.json()
    rate = Decimal(str(data["rate"]))

    if rate <= 0:
        raise ValueError("Invalid exchange rate")

    return rate, data["date"]


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
        raise ValueError("Converted amount too small")

    return usd_amount, rate, rate_date