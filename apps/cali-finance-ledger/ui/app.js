/**
 * app.js - Cali Commercial & Finance Ledger Interactive UI
 * Manages product margins, operating expense tracking, and client invoicing.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadSummary();
  loadMargins();
  loadExpenses();
  loadInvoices();

  // Set default invoice due date to +14 days
  const dueInput = document.getElementById("inv-due-date");
  if (dueInput) {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    dueInput.value = d.toISOString().split("T")[0];
  }
});

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));

  const targetPane = document.getElementById(`pane-${tabId}`);
  if (targetPane) targetPane.classList.add("active");

  const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.getAttribute("onclick").includes(tabId));
  if (activeBtn) activeBtn.classList.add("active");
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.style.display = "flex";
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.style.display = "none";
}

/* -----------------------------------------------------------
 * 1. LOAD FINANCIAL SUMMARY & KPIS
 * ----------------------------------------------------------- */
async function loadSummary() {
  try {
    const res = await fetch("/api/finance/summary");
    if (!res.ok) return;
    const data = await res.json();

    const sym = data.currency_symbol || "£";
    document.getElementById("kpi-gross-rev").innerText = `${sym}${data.gross_revenue_ytd.toFixed(2)}`;
    document.getElementById("kpi-monthly-exp").innerText = `${sym}${data.monthly_fixed_overhead.toFixed(2)} / mo`;
    document.getElementById("kpi-net-profit").innerText = `${sym}${data.net_profit_ytd.toFixed(2)}`;
    document.getElementById("kpi-margin-pct").innerText = `Margin: ${data.profit_margin_pct}%`;
    document.getElementById("kpi-corp-tax").innerText = `${sym}${data.corporation_tax_reserve.toFixed(2)}`;
  } catch (err) {
    console.error("Failed to load financial summary:", err);
  }
}

/* -----------------------------------------------------------
 * 2. PRODUCT PROFIT MARGINS (PRINTFUL)
 * ----------------------------------------------------------- */
async function loadMargins(notify = false) {
  const tbody = document.getElementById("margins-table-body");
  if (!tbody) return;
  if (notify) tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--teal);">🔄 Synchronizing with Printful Store #18266176...</td></tr>`;

  try {
    const res = await fetch("/api/finance/margins");
    if (!res.ok) return;
    const data = await res.json();
    const prods = data.products || [];

    tbody.innerHTML = "";
    prods.forEach(p => {
      const row = document.createElement("tr");
      const marginColor = p.margin_pct >= 45 ? "var(--green)" : "var(--yellow)";
      row.innerHTML = `
        <td>
          <strong>${p.title}</strong><br>
          <small style="color: var(--text-dim);">ID: ${p.id}</small>
        </td>
        <td><strong>£${p.retail_price.toFixed(2)}</strong></td>
        <td style="color: var(--text-muted);">£${p.base_cost.toFixed(2)}</td>
        <td style="color: var(--green); font-weight: 700;">+£${p.net_margin.toFixed(2)}</td>
        <td><strong style="color: ${marginColor};">${p.margin_pct}%</strong></td>
        <td><span style="font-size: 10px; background: rgba(20, 184, 166, 0.15); color: var(--teal); padding: 2px 6px; border-radius: 4px;">Printful On-Demand</span></td>
      `;
      tbody.appendChild(row);
    });

    if (notify) alert("Printful product margins synced successfully!");
  } catch (err) {
    console.error("Failed to load product margins:", err);
  }
}

/* -----------------------------------------------------------
 * 3. OPERATING OVERHEAD & EXPENSES
 * ----------------------------------------------------------- */
async function loadExpenses() {
  const tbody = document.getElementById("expenses-table-body");
  if (!tbody) return;

  try {
    const res = await fetch("/api/finance/expenses");
    if (!res.ok) return;
    const data = await res.json();
    const expenses = data.expenses || [];

    tbody.innerHTML = "";
    expenses.forEach(e => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><span style="font-size: 10px; font-weight: 700; background: var(--bg-input); padding: 2px 6px; border-radius: 4px;">${e.category}</span></td>
        <td><strong>${e.description}</strong></td>
        <td style="color: var(--text-muted);">${e.vendor}</td>
        <td><strong style="color: var(--yellow);">£${parseFloat(e.amount).toFixed(2)}</strong></td>
        <td>${e.recurrence}</td>
        <td><span style="font-size: 10px; color: var(--green);">● ${e.status}</span></td>
        <td>
          <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px; color: var(--red);" onclick="handleDeleteExpense(${e.id}, '${e.description}')">Delete</button>
        </td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to load expenses:", err);
  }
}

async function handleCreateExpense(e) {
  e.preventDefault();
  const category = document.getElementById("exp-category").value;
  const description = document.getElementById("exp-desc").value;
  const vendor = document.getElementById("exp-vendor").value;
  const amount = parseFloat(document.getElementById("exp-amount").value);
  const recurrence = document.getElementById("exp-recurrence").value;

  try {
    const res = await fetch("/api/finance/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category, description, vendor, amount, recurrence })
    });
    const d = await res.json();
    if (d.ok) {
      closeModal("modal-expense");
      loadExpenses();
      loadSummary();
      alert(d.message || "Expense added successfully!");
    }
  } catch (err) {
    alert(`Failed to add expense: ${err.message}`);
  }
}

async function handleDeleteExpense(id, desc) {
  if (!confirm(`Delete expense '${desc}' (#${id})?`)) return;
  try {
    const res = await fetch("/api/finance/expenses/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id })
    });
    const d = await res.json();
    if (d.ok) {
      loadExpenses();
      loadSummary();
    }
  } catch (err) {
    alert(`Failed to delete expense: ${err.message}`);
  }
}

/* -----------------------------------------------------------
 * 4. CLIENT INVOICING & QUOTES
 * ----------------------------------------------------------- */
async function loadInvoices() {
  const tbody = document.getElementById("invoices-table-body");
  if (!tbody) return;

  try {
    const res = await fetch("/api/finance/invoices");
    if (!res.ok) return;
    const data = await res.json();
    const invoices = data.invoices || [];

    tbody.innerHTML = "";
    if (invoices.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No client invoices generated yet. Click "+ Create Client Invoice" to generate one.</td></tr>`;
      return;
    }

    invoices.forEach(inv => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong style="color: var(--teal); font-family: monospace;">#${inv.invoice_number}</strong></td>
        <td>
          <strong>${inv.client_name}</strong>
          ${inv.client_company ? `<br><small style="color: var(--text-dim);">${inv.client_company}</small>` : ''}
        </td>
        <td>${inv.issue_date}</td>
        <td>${inv.due_date}</td>
        <td><strong style="color: #fff; font-size: 13px;">£${parseFloat(inv.total).toFixed(2)}</strong></td>
        <td><span style="font-size: 10px; background: rgba(59, 130, 246, 0.15); color: var(--blue); padding: 2px 6px; border-radius: 4px;">${inv.status.toUpperCase()}</span></td>
        <td>
          <a href="/api/finance/invoices/${inv.id}/html" target="_blank" class="btn btn-primary" style="padding: 2px 8px; font-size: 10px;">View / Print Invoice ↗</a>
        </td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to load invoices:", err);
  }
}

function addInvoiceItemRow() {
  const container = document.getElementById("invoice-items-rows");
  if (!container) return;
  const row = document.createElement("div");
  row.className = "inv-item-row";
  row.innerHTML = `
    <input type="text" class="item-desc" placeholder="Service / Item Description" required>
    <input type="number" class="item-qty" placeholder="Qty" value="1" min="1" style="width: 60px;" required>
    <input type="number" class="item-price" placeholder="Price (£)" step="0.01" value="100.00" style="width: 100px;" required>
  `;
  container.appendChild(row);
}

async function handleCreateInvoice(e) {
  e.preventDefault();
  const client_name = document.getElementById("inv-client-name").value;
  const client_company = document.getElementById("inv-client-company").value;
  const client_email = document.getElementById("inv-client-email").value;
  const due_date = document.getElementById("inv-due-date").value;
  const notes = document.getElementById("inv-notes").value;

  const itemRows = document.querySelectorAll(".inv-item-row");
  const items = [];
  itemRows.forEach(r => {
    const desc = r.querySelector(".item-desc").value;
    const qty = parseInt(r.querySelector(".item-qty").value) || 1;
    const price = parseFloat(r.querySelector(".item-price").value) || 0.0;
    if (desc) items.push({ description: desc, quantity: qty, price: price });
  });

  if (items.length === 0) {
    alert("Please add at least one line item to the invoice.");
    return;
  }

  try {
    const res = await fetch("/api/finance/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_name, client_company, client_email, due_date, notes, items })
    });
    const d = await res.json();
    if (d.ok) {
      closeModal("modal-invoice");
      loadInvoices();
      loadSummary();
      alert(`Invoice ${d.invoice_number} created successfully! Total: £${d.total.toFixed(2)}`);
      // Open invoice in new tab for immediate printing
      window.open(`/api/finance/invoices/${d.id}/html`, "_blank");
    }
  } catch (err) {
    alert(`Failed to create invoice: ${err.message}`);
  }
}

