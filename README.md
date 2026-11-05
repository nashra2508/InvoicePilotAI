# InvoicePilotAI 🧾

**AI-Powered Invoice Management and Payment Automation**

InvoicePilotAI is a web-based invoice management application built with FastAPI, SQLite, and Google Gemini AI. It helps users create professional invoices, generate AI-powered invoice descriptions and payment reminders, manage payment statuses, and accept payments through PayPal Sandbox.

The application also converts invoice amounts from INR to USD using live exchange-rate data before creating PayPal orders.

## ✨ Features

- **Invoice Management:** Create and manage client invoices.
- **AI Invoice Generation:** Convert casual job descriptions into professional invoice descriptions using Google Gemini AI.
- **AI Payment Reminders:** Generate polite and professional payment reminder messages.
- **Dashboard:** View total invoices, revenue, pending invoices, and paid invoices.
- **Payment Status:** Update invoice payment status.
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
| Frankfurter API | INR to USD exchange-rate conversion |

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
├── .gitignore
├── .env
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
.venv\Scripts\Activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the root directory.

Add your own API credentials:

```env
GEMINI_API_KEY=your_gemini_api_key

PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

**Important:**
- Never upload your `.env` file to GitHub.
- Never share your PayPal Client Secret or Gemini API key.
- Use PayPal Sandbox credentials for testing.
- Do not use real payment credentials for development testing.

### 7. Run the application

```bash
python -m uvicorn main:app --reload
```

### 8. Open the application

Frontend:

```text
http://127.0.0.1:8000
```

FastAPI Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## 💳 PayPal Payment Integration

InvoicePilotAI integrates PayPal Sandbox for payment testing.

The payment workflow:

1. A user creates an invoice in INR.
2. The application retrieves the INR-to-USD exchange rate.
3. The invoice amount is converted into USD.
4. A PayPal Sandbox order is created.
5. The user completes the checkout using a Sandbox Buyer account.
6. The backend captures the PayPal payment.
7. The invoice payment status is updated.

**Currency conversion:** The application uses the Frankfurter API to retrieve exchange-rate information.

**Payment testing:** Only PayPal Sandbox is configured for development. No real payments should be made during testing.

## 🤖 AI Integration

Google Gemini AI powers two main features:

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

The backend exposes the following main endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve the application frontend |
| GET | `/invoices` | Retrieve invoices |
| POST | `/invoices` | Create an invoice |
| POST | `/generate-invoice` | Generate an AI invoice draft |
| POST | `/generate-reminder` | Generate an AI payment reminder |
| PUT | `/invoices/{invoice_id}/pay` | Update invoice payment status |
| GET | `/paypal-config` | Retrieve public PayPal configuration |
| POST | `/create-paypal-order` | Create a PayPal order |
| POST | `/capture-paypal-payment` | Capture a PayPal payment |

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
- Validate payment details on the backend before using this application in production.
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

This project is intended for educational and development purposes. Add a suitable open-source license before distributing it as an open-source project.

---

**InvoicePilotAI — Smarter Invoicing with AI and Automated Payments.**