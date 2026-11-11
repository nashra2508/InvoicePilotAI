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
                const response = await fetch("/create-paypal-order", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        invoice_id: invoice.invoice_id
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    const msg = result.detail || "Could not create PayPal order";
                    alert("Order creation error: " + msg);
                    throw new Error(msg);
                }

                console.log("PayPal order created successfully:", result);
                return result.order_id;
            },

            onApprove: async function (data) {
                try {
                    const response = await fetch("/capture-paypal-payment", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            invoice_id: invoice.invoice_id,
                            order_id: data.orderID
                        })
                    });

                    const result = await response.json();

                    if (!response.ok) {
                        const errMsg = result.detail || "Payment capture failed";
                        alert("PayPal Payment Status: " + errMsg);
                        throw new Error(errMsg);
                    }

                    // Immediately reload invoices to update status and dashboard cards from Pending to Paid
                    await loadInvoices();

                    setTimeout(() => {
                        alert(
                            "Payment successful! Invoice #" +
                            invoice.invoice_id +
                            " status changed to Paid."
                        );
                    }, 50);

                } catch (err) {
                    console.error("Capture processing error:", err);
                    setTimeout(() => {
                        alert("Payment capture notice: " + err.message);
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
                console.error("PayPal button error:", error);

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
                        "PayPal transaction notice: " +
                        (
                            error && error.message
                                ? error.message
                                : "Payment attempt declined or interrupted. Ensure using an international PayPal Sandbox account with test funds."
                        )
                    );
                }, 50);
            }

        }).render(container);

    } catch (error) {
        console.error("PayPal setup error:", error);
        container.textContent = "PayPal unavailable: " + error.message;
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

            // Columns: ID, Client, Description, Amount, Due Date
            [
                invoice.invoice_id,
                invoice.client_name,
                invoice.description,
                "₹" + Number(invoice.amount).toLocaleString("en-IN"),
                invoice.due_date
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            // Status Column with colored badge
            const statusCell = document.createElement("td");
            const statusBadge = document.createElement("span");
            statusBadge.className =
                invoice.status === "Paid" ? "badge badge-paid" : "badge badge-pending";
            statusBadge.textContent = invoice.status;
            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);

            // Action Column
            const actionCell = document.createElement("td");

            if (invoice.status === "Pending") {
                // Generate Reminder button
                const reminderButton = document.createElement("button");
                reminderButton.textContent = "Generate Reminder";

                reminderButton.addEventListener("click", async () => {
                    reminderButton.disabled = true;
                    reminderButton.textContent = "Generating...";

                    try {
                        const res = await fetch("/generate-reminder", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                invoice_id: invoice.invoice_id
                            })
                        });

                        const result = await res.json();

                        if (!res.ok || result.error) {
                            throw new Error(result.error || "Request failed");
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

                // PayPal button container
                const paypalContainer = document.createElement("div");
                paypalContainer.id = "paypal-button-" + invoice.invoice_id;
                paypalContainer.style.marginTop = "10px";
                paypalContainer.style.minWidth = "150px";

                actionCell.appendChild(paypalContainer);
                renderPayPalButton(paypalContainer, invoice);

            } else {
                // For Paid invoices: show confirmed payment badge
                const paidIndicator = document.createElement("div");
                paidIndicator.className = "paid-indicator";
                paidIndicator.textContent = "✓ Paid";
                if (invoice.paypal_capture_id) {
                    paidIndicator.title =
                        "PayPal Capture ID: " + invoice.paypal_capture_id;
                }
                actionCell.appendChild(paidIndicator);
            }

            row.appendChild(actionCell);
            table.appendChild(row);
        });

    } catch (error) {
        console.error("Error loading invoices:", error);
    }
}


// AI Invoice Generator - Single Event Listener
document.getElementById("generateAiInvoiceButton").addEventListener(
    "click",
    async function () {
        const description = document.getElementById(
            "aiJobDescription"
        ).value.trim();

        const message = document.getElementById("aiInvoiceMessage");
        const button = this;

        if (!description) {
            message.textContent = "Please enter an invoice description.";
            return;
        }

        button.disabled = true;
        button.textContent = "Generating...";
        message.textContent = "AI is generating your invoice...";

        try {
            const response = await fetch("/generate-invoice", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    job_description: description
                })
            });

            const result = await response.json();

            if (!response.ok || result.error) {
                throw new Error(result.error || "Invoice generation failed");
            }

            message.textContent = "Invoice generated successfully!";
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
