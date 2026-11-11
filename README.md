# InvoicePilotAI 🧾

**AI-Powered Invoice Management and Payment Automation**

InvoicePilotAI is a web-based invoice management application built with FastAPI, SQLite, and Google Gemini AI. It helps users create professional invoices, generate AI-powered invoice descriptions and payment reminders, manage payment statuses, and accept payments through PayPal Sandbox.

The application also converts invoice amounts from INR to USD using live exchange-rate data before creating PayPal orders.

## ✨ Features

- **Invoice Management:** Create and manage client invoices.
- **AI Invoice Generation:** Convert casual job descriptions into professional invoice descriptions using Google Gemini AI.
- **AI Payment Reminders:** Generate polite and professional payment reminder messages.
- **Dashboard:** View total invoices, revenue, pending invoices, and paid invoices.
- **Payment Verification:** Verify completed PayPal payments before updating invoice status.
- **PayPal Integration:** Create and capture PayPal Sandbox payments.
- **Currency Conversion:** Convert INR invoice amounts into USD using the Frankfurter exchange-rate API.
- **SQLite Database:** Store invoice records locally.
- **Responsive Interface:** Simple frontend built with HTML, CSS, and JavaScript.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API framework |
| SQLite | Database |
| HTML | Frontend structure |
| CSS | Frontend styling |
| JavaScript | Frontend functionality |
| Google Gemini AI | AI invoice and reminder generation |
| PayPal Sandbox | Payment integration and testing |
| Frankfurter API | INR-to-USD exchange-rate conversion |

## 📁 Project Structure

```text
InvoicePilotAI/
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── ai_service.py
├── currency_service.py
├── database.py
├── main.py
├── paypal_service.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

**Note:** `.env`, `invoices.db`, and Python virtual environment files are local files and should not be committed to GitHub.

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/nashra2508/InvoicePilotAI.git
```

### 2. Open the project folder

```bash
cd InvoicePilotAI
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a copy of `.env.example` named `.env`.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder values with your own credentials:

```env
GEMINI_API_KEY=your_gemini_api_key

PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

**Getting API credentials:**

- Google Gemini API key: https://aistudio.google.com/
- PayPal Sandbox credentials: https://developer.paypal.com/

Keep your actual API keys and secrets private. Never upload your `.env` file to GitHub.

### 7. Run the application

```bash
python -m uvicorn main:app --reload
```

### 8. Open the application

Frontend:

http://127.0.0.1:8000

FastAPI Swagger API documentation:

http://127.0.0.1:8000/docs

## 💳 PayPal Payment Integration

InvoicePilotAI integrates PayPal Sandbox for payment testing.

### Payment workflow

1. A user creates an invoice in INR.
2. The application retrieves the INR-to-USD exchange rate.
3. The invoice amount is converted into USD.
4. A PayPal Sandbox order is created.
5. The buyer approves the payment using a Sandbox Buyer account.
6. The backend retrieves and verifies the PayPal order.
7. If necessary, the backend captures the approved payment.
8. The backend verifies the completed payment and updates the invoice status to **Paid**.

### Currency conversion

The application uses the Frankfurter API to retrieve exchange-rate information.

### Payment testing

- Only PayPal Sandbox is configured for development and testing.
- Use Sandbox accounts rather than real PayPal accounts.
- No real payments should be made during testing.
- PayPal account country restrictions may apply. Currency conversion alone does not make a domestic transaction eligible for payment. Follow PayPal's current account and cross-border transaction requirements.

## 🤖 AI Integration

Google Gemini AI powers two main features.

### AI Invoice Generation

Users can enter a casual description of their work. Gemini AI converts it into a professional invoice draft containing:

- Client name
- Professional service description
- Invoice amount
- Due date

The AI is instructed not to invent missing invoice information.

### AI Payment Reminder

The application generates a short and professional payment reminder containing the client's name, service description, invoice amount, and due date.

## 🔗 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve the application frontend |
| GET | `/invoices` | Retrieve invoices |
| POST | `/invoices` | Create an invoice |
| POST | `/generate-invoice` | Generate an AI invoice draft |
| POST | `/generate-reminder` | Generate an AI payment reminder |
| GET | `/paypal-config` | Retrieve public PayPal configuration |
| POST | `/create-paypal-order` | Create a PayPal order |
| POST | `/capture-paypal-payment` | Capture or verify a PayPal payment |

For request and response details, run the application and visit `/docs`.

## 🗄️ Database

InvoicePilotAI uses SQLite to store invoice information.

The database is created locally as:

```text
invoices.db
```

The database stores invoice details such as:

- Invoice ID
- Client name
- Service description
- Invoice amount
- Due date
- Payment status

## 🔐 Security Notes

- Keep API keys and secrets inside `.env`.
- Do not commit `.env` or database files.
- Use PayPal Sandbox for development and testing.
- Validate payment details on the backend before updating payment status.
- Configure production credentials, HTTPS, and appropriate CORS restrictions before deployment.

## 🚀 Future Improvements

- Invoice PDF generation and download.
- Email-based invoice delivery.
- Automated payment reminder emails.
- Payment transaction history.
- Production PayPal integration.
- User authentication and account management.
- Cloud database and application deployment.

## 👥 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a new feature branch.
3. Make your changes.
4. Test your changes.
5. Submit a Pull Request.

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**InvoicePilotAI — Smarter Invoicing with AI and Automated Payments.**
