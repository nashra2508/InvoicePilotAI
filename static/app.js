
let paypalSdkPromise = null;

// Load PayPal SDK using the public Client ID from backend
async function loadPayPalSdk() {
    const configResponse = await fetch("/paypal-config");

    if (!configResponse.ok) {
        throw new Error("Could not load PayPal configuration");
    }

    const config = await configResponse.json();

    if (!config.client_id) {
        throw new Error("PayPal Client ID is missing");
    }

    const existingScript = document.querySelector(
        'script[src*="paypal.com/sdk/js"]'
    );

    if (existingScript) {
        if (
            existingScript.src.includes(
                "client-id=" + encodeURIComponent(config.client_id)
            ) &&
            window.paypal
        ) {
            return;
        }

        existingScript.remove();
        delete window.paypal;
        paypalSdkPromise = null;
    }

    if (paypalSdkPromise) {
        return paypalSdkPromise;
    }

    paypalSdkPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");

        script.src =
            "https://www.paypal.com/sdk/js?client-id=" +
            encodeURIComponent(config.client_id) +
            "&currency=USD&intent=capture";

        script.onload = () => resolve();

        script.onerror = () => {
            paypalSdkPromise = null;
            reject(new Error("PayPal SDK failed to load"));
        };

        document.head.appendChild(script);
    });

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

        if (!window.paypal || !window.paypal.Buttons) {
            throw new Error("PayPal SDK is unavailable");
        }

        container.innerHTML = "";

        window.paypal.Buttons({

            createOrder: async function () {
                const response = await fetch(
                    "/create-paypal-order",
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
                try {
                    const response = await fetch(
                        "/capture-paypal-payment",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                invoice_id: invoice.invoice_id,
                                order_id: data.orderID
                            })
                        }
                    );

                    const result = await response.json();

                    if (!response.ok) {
                        throw new Error(
                            result.detail || "Payment capture failed"
                        );
                    }

                    setTimeout(() => {
                        alert(
                            "Payment successful! Invoice marked as Paid."
                        );
                    }, 50);

                    await loadInvoices();

                } catch (err) {
                    console.error("Capture error:", err);

                    setTimeout(() => {
                        alert("Payment capture failed: " + err.message);
                    }, 50);
                }
            },

            onCancel: function (data) {
                console.log("PAYPAL CANCEL DATA:", data);

                setTimeout(() => {
                    alert("PayPal payment was cancelled.");
                }, 50);
            },

            onError: function (error) {
                console.error("PayPal error:", error);

                if (
                    error &&
                    error.message &&
                    error.message.includes(
                        "No ack for postMessage onCancel"
                    )
                ) {
                    return;
                }

                setTimeout(() => {
                    alert(
                        "PayPal payment error: " +
                        (
                            error && error.message
                                ? error.message
                                : "Please try again."
                        )
                    );
                }, 50);
            }

        }).render(container);

    } catch (error) {
        console.error("PayPal button error:", error);
        container.textContent =
            "PayPal unavailable: " + error.message;
    }
}


// Load all invoices
async function loadInvoices() {
    try {
        const response = await fetch("/invoices");

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
                        "/generate-reminder",
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

            // PayPal button for Pending invoices
            if (invoice.status === "Pending") {
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


// AI Invoice Generator
document.getElementById("generateAiInvoiceButton").addEventListener(
    "click",
    async function () {

        const description = document.getElementById(
            "aiJobDescription"
        ).value.trim();

        const message = document.getElementById("aiInvoiceMessage");

        const button = this;

        if (!description) {
            message.textContent =
                "Please enter an invoice description.";
            return;
        }

        button.disabled = true;
        button.textContent = "Generating...";

        message.textContent =
            "AI is generating your invoice...";

        try {
            const response = await fetch(
                "/generate-invoice",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        job_description: description
                    })
                }
            );

            const result = await response.json();

            if (!response.ok || result.error) {
                throw new Error(
                    result.error || "Invoice generation failed"
                );
            }

            message.textContent =
                "Invoice generated successfully!";

            document.getElementById("aiJobDescription").value = "";

            await loadInvoices();

        } catch (error) {
            message.textContent = "Error: " + error.message;

            console.error("AI Invoice Error:", error);

        } finally {
            button.disabled = false;
            button.textContent = "Generate Invoice with AI";
        }
    }
);


// Start dashboard
loadInvoices();
