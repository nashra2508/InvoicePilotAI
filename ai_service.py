
import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_invoice_draft(job_description):

    prompt = f"""
    You are a professional invoice assistant.

Convert the user's casual job description into
a short, clear and professional invoice description.

Use professional service names such as:
- Website Design and Development
- Logo Design
- Video Editing Services
- Graphic Design Services
- Digital Marketing Services

Do not simply copy casual wording.
Extract the client name, amount and due date accurately.
Never invent missing information.

    Return ONLY valid JSON with these fields:
    {{
        "client_name": "client name",
        "description": "work description",
        "amount": 0,
        "due_date": "YYYY-MM-DD"
    }}

    If information is missing, use an empty string
    for text fields and null for amount or due_date.

    Never invent an amount or due date.

    User description:
    {job_description}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    return json.loads(raw_text)
def generate_payment_reminder(client_name, description, amount, due_date):

    prompt = f"""
    You are a professional business payment assistant.

    Write a polite and professional payment reminder.

    Client: {client_name}
    Service: {description}
    Amount: ₹{amount}
    Due Date: {due_date}

    Include:
    - Client's name
    - Invoice amount
    - Service description
    - Due date
    - A polite request for payment

    Keep it short and professional.
    Return only the reminder message.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text.strip()