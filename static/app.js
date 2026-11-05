
let paypalSdkPromise = null;

// Load PayPal SDK using the public Client ID from backend
async function loadPayPalSdk() {
    if (window.paypal) {
        return;
    }

    if (paypalSdkPromise) {
        return paypalSdkPromise;
    }

    paypalSdkPromise = (async () => {
        const configResponse = await fetch(
            "http://127.0.0.1:8000/paypal-config"
        );

        if (!configResponse.ok) {
            throw new Error("Could not load PayPal configuration");
        }

        const config = await configResponse.json();

        if (!config.client_id) {
            throw new Error("PayPal Client ID is missing");
        }

        const script = document.createElement("script");

        script.src =
            "https://www.paypal.com/sdk/js?client-id=" +
            encodeURIComponent(config.client_id) +
            "&currency=USD&intent=capture";

        script.onload = () => {};
        
        document.head.appendChild(script);

        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = () => reject(
                new Error("PayPal SDK failed to load")
            );
        });
    })();

    try {
        await paypalSdkPromise;
    } catch (error) {
        paypalSdkPromise = null;
        throw error;
    }
}


// Create PayPal button for an invoice
async function renderPayPalButton(container, invoice) {
    try {
        await loadPayPalSdk();

        if (!window.paypal) {
            throw new Error("PayPal SDK is unavailable");
        }

        window.paypal.Buttons({

            createOrder: async function () {
                const response = await fetch(
                    "http://127.0.0.1:8000/create-paypal-order",
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

                if (!response.ok) {
                    throw new Error(
                        result.detail || "Could not create PayPal order"
                    );
                }

                console.log("PayPal order:", result);

                return result.order_id;
            },

            onApprove: async function (data) {
                const response = await fetch(
                    "http://127.0.0.1:8000/capture-paypal-payment",
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

                if (!response.ok) {
                    throw new Error(
                        result.detail || "Payment capture failed"
                    );
                }

                alert("Payment successful! Invoice marked as Paid.");

                loadInvoices();
            },

            onCancel: function () {
                alert("PayPal payment was cancelled.");
            },

            onError: function (error) {
                console.error("PayPal error:", error);
                alert("PayPal payment failed. Please try again.");
            }

        }).render(container);

    } catch (error) {
        console.error("PayPal button error:", error);
        container.textContent = "PayPal unavailable: " + error.message;
    }
}


// Load all invoices
async function loadInvoices() {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/invoices"
        );

        if (!response.ok) {
            throw new Error("Could not load invoices");
        }

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


            // Generate Reminder button
            const reminderButton = document.createElement("button");

            reminderButton.textContent = "Generate Reminder";

            reminderButton.addEventListener("click", async () => {

                reminderButton.disabled = true;
                reminderButton.textContent = "Generating...";

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
                        throw new Error(
                            result.error || "Request failed"
                        );
                    }

                    alert(result.reminder);

                } catch (error) {
                    alert("Error: " + error.message);

                } finally {
                    reminderButton.disabled = false;
                    reminderButton.textContent = "Generate Reminder";
                }
            });


            actionCell.appendChild(reminderButton);


            // Existing Mark as Paid button
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

                    if (!response.ok || result.error) {
                        throw new Error(
                            result.error || "Request failed"
                        );
                    }

                    alert("Invoice marked as Paid!");

                    loadInvoices();

                } catch (error) {
                    alert("Error: " + error.message);
                }
            });


            if (invoice.status === "Pending") {

                actionCell.appendChild(paidButton);

                // PayPal button container
                const paypalContainer = document.createElement("div");

                paypalContainer.id =
                    "paypal-button-" + invoice.invoice_id;

                paypalContainer.style.marginTop = "10px";
                paypalContainer.style.minWidth = "150px";

                actionCell.appendChild(paypalContainer);

                renderPayPalButton(paypalContainer, invoice);
            }


            row.appendChild(actionCell);

            table.appendChild(row);
        });

    } catch (error) {
        console.error("Error loading invoices:", error);
    }
}


// Start dashboard
loadInvoices();
