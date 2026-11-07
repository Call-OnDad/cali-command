let cachedDocs = [];

document.addEventListener("DOMContentLoaded", () => {
  loadDocsData();
  setupSearch();
});

async function loadDocsData() {
  try {
    const [docRes, filRes] = await Promise.all([
      fetch("/api/docs/list"),
      fetch("/api/corporate/filings")
    ]);
    cachedDocs = await docRes.json();
    const filings = await filRes.json();

    renderStats(cachedDocs, filings);
    renderFilings(filings);
    renderDocs(cachedDocs);
  } catch (e) {
    console.error("Docs load error:", e);
  }
}

function setupSearch() {
  const searchInput = document.getElementById("doc-search");
  if (!searchInput) return;
  searchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderDocs(cachedDocs);
      return;
    }
    const filtered = cachedDocs.filter(d => 
      (d.title && d.title.toLowerCase().includes(q)) ||
      (d.category && d.category.toLowerCase().includes(q)) ||
      (d.summary && d.summary.toLowerCase().includes(q)) ||
      (d.type && d.type.toLowerCase().includes(q))
    );
    renderDocs(filtered);
  });
}

function renderStats(docs, filings) {
  const row = document.getElementById("stats-row");
  if (!row) return;
  row.innerHTML = `
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">CORPORATE STATUS</div>
      <div class="stat-val" style="color: var(--teal); font-size: 18px;">Active & Good Standing</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Companies House #${filings.company_number}</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">INDEXED KNOWLEDGE & LESSONS</div>
      <div class="stat-val">${docs.length} Vault Items</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Audited SOPs, Retrospectives, & Post-Mortems</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">ONLYOFFICE WORKSPACE</div>
      <div class="stat-val" style="color: var(--yellow); font-size: 18px;">CT110 Connected</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Real-time collaborative document editing</div>
    </div>
  `;
}

function renderFilings(filings) {
  const container = document.getElementById("filings-box");
  if (!container) return;
  container.innerHTML = `
    <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px;">${filings.company_name}</div>
    <div style="color: var(--text-muted); margin-bottom: 4px;">Company Number: <strong>${filings.company_number}</strong> (${filings.jurisdiction})</div>
    <div style="color: var(--text-muted); margin-bottom: 4px;">Legal Status: <span style="color: var(--teal); font-weight: 600;">${filings.company_status}</span></div>
    <div style="color: var(--text-muted); margin-bottom: 4px;">Next Accounts Due: <strong>${filings.accounts_next_due}</strong></div>
    <div style="color: var(--text-muted); margin-bottom: 12px;">Next Confirmation Statement: <strong>${filings.confirmation_statement_next_due}</strong></div>
    <a href="${filings.onlyoffice_endpoint}" target="_blank" style="color: var(--yellow); text-decoration: underline; font-weight: 600;">
      Launch OnlyOffice Collaboration Suite &rarr;
    </a>
  `;
}

function renderDocs(docs) {
  const container = document.getElementById("docs-list");
  if (!container) return;
  container.innerHTML = "";

  if (docs.length === 0) {
    container.innerHTML = `<div style="padding: 16px; color: var(--text-muted); font-size: 12px;">No matching documents found in Knowledge Base.</div>`;
    return;
  }

  docs.forEach(d => {
    const el = document.createElement("div");
    el.className = "doc-row";
    el.innerHTML = `
      <div style="flex: 1;">
        <div style="font-weight: 700; font-size: 13px; color: #fff;">${d.title}</div>
        <div style="font-size: 11px; color: var(--teal); margin: 2px 0;">${d.category} · ${d.type}</div>
        <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">${d.summary || ""}</div>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); text-align: right; min-width: 80px;">
        ${d.last_modified}
      </div>
    `;
    container.appendChild(el);
  });
}
