
async function loadInvoices() {
    try {
        const response = await fetch("http://127.0.0.1:8000/invoices");
        const invoices = await response.json();

        const total = invoices.length;

        const pending = invoices.filter(
            invoice => invoice.status === "Pending"
        ).length;

        const paid = invoices.filter(
            invoice => invoice.status === "Paid"
        ).length;

        const revenue = invoices.reduce(
            (sum, invoice) => sum + Number(invoice.amount),
            0
        );

        document.getElementById("totalInvoices").textContent = total;
        document.getElementById("totalRevenue").textContent =
            "₹" + revenue.toLocaleString("en-IN");
        document.getElementById("pendingInvoices").textContent = pending;
        document.getElementById("paidInvoices").textContent = paid;

        const table = document.getElementById("invoiceTable");

        table.innerHTML = "";

      
invoices.forEach(invoice => {
    const row = document.createElement("tr");

    [
        invoice.invoice_id,
        invoice.client_name,
        invoice.description,
        "₹" + Number(invoice.amount).toLocaleString("en-IN"),
        invoice.due_date,
        invoice.status
    ].forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
    });

    const actionCell = document.createElement("td");
    const button = document.createElement("button");

    button.textContent = "Generate Reminder";

    button.addEventListener("click", async () => {
        button.disabled = true;
        button.textContent = "Generating...";

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/generate-reminder",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        invoice_id: invoice.invoice_id
                    })
                }
            );

            const result = await response.json();

            if (!response.ok || result.error) {
                throw new Error(result.error || "Request failed");
            }

            alert(result.reminder);

        } catch (error) {
            alert("Error: " + error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Generate Reminder";
        }
    });
   const paidButton = document.createElement("button");

paidButton.textContent = "Mark as Paid";

paidButton.style.marginLeft = "8px";

paidButton.addEventListener("click", async () => {
    try {
        const response = await fetch(
            `http://127.0.0.1:8000/invoices/${invoice.invoice_id}/pay`,
            {
                method: "PUT"
            }
        );

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        alert("Invoice marked as Paid!");

        loadInvoices();

    } catch (error) {
        alert("Error: " + error.message);
    }
});

actionCell.appendChild(paidButton);
    actionCell.appendChild(button);
    row.appendChild(actionCell);
    table.appendChild(row);
});


    } catch (error) {
        console.error("Error loading invoices:", error);
    }
}

loadInvoices();
