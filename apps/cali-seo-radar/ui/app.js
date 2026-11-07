/* Cali SEO & Search Radar - Frontend Controller */

let activeDomain = "cali-media.ltd";
let allDomains = [];

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  await fetchStatus();
  await loadDomains();
  await loadKeywords(activeDomain);
  await loadCrawlReport(activeDomain);
  runContentAudit();
}

/* 1. STATUS & SERPBEAR CONNECTIVITY */
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const badge = document.getElementById("ct120-status-badge");
    if (badge) {
      if (data.ct120_serpbear && data.ct120_serpbear.status === "connected") {
        badge.innerHTML = `CT120 SerpBear: <span style="color: var(--green); font-weight: 700;">● Connected</span>`;
      } else {
        badge.innerHTML = `CT120 SerpBear: <span style="color: var(--teal);">● Autonomous Radar Active</span>`;
      }
    }
  } catch (e) {
    console.warn("Status fetch failed:", e);
  }
}

/* 2. DOMAIN MANAGEMENT */
async function loadDomains() {
  try {
    const res = await fetch("/api/domains");
    allDomains = await res.json();

    const select = document.getElementById("active-domain-select");
    if (select) {
      select.innerHTML = "";
      allDomains.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d.id;
        opt.innerText = `${d.id} (${d.name || d.category})`;
        if (d.id === activeDomain) opt.selected = true;
        select.appendChild(opt);
      });
    }

    renderDomainsTable();
  } catch (e) {
    console.error("Load domains failed:", e);
  }
}

function onDomainChange() {
  const sel = document.getElementById("active-domain-select");
  activeDomain = sel.value;
  document.getElementById("crawl-url-input").value = `https://${activeDomain}`;
  loadKeywords(activeDomain);
  loadCrawlReport(activeDomain);
}

function renderDomainsTable() {
  const tbody = document.getElementById("domains-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  allDomains.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${d.id}</strong></td>
      <td>${d.name || '-'}</td>
      <td><span style="color: var(--text-muted);">${d.category || 'General'}</span></td>
      <td><strong style="color: var(--teal);">${d.health_score || 85}%</strong></td>
      <td>${(d.target_keywords || []).length} keywords</td>
      <td><span style="color: var(--green);">● Active</span></td>
      <td>
        <button class="btn btn-danger" style="padding: 2px 8px; font-size: 11px;" onclick="deleteDomain('${d.id}')">Remove</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function addNewDomain() {
  const id = document.getElementById("new-domain-id").value.trim().toLowerCase();
  const name = document.getElementById("new-domain-name").value.trim();
  const cat = document.getElementById("new-domain-cat").value.trim();

  if (!id) {
    alert("Please enter a domain name (e.g. call-on.info)");
    return;
  }

  try {
    await fetch("/api/domains/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ id, name, category: cat })
    });
    document.getElementById("new-domain-id").value = "";
    document.getElementById("new-domain-name").value = "";
    document.getElementById("new-domain-cat").value = "";
    await loadDomains();
    alert(`Domain ${id} registered successfully!`);
  } catch (e) {
    alert("Failed to add domain: " + e.message);
  }
}

async function deleteDomain(domainId) {
  if (!confirm(`Are you sure you want to remove ${domainId}?`)) return;
  try {
    await fetch("/api/domains/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ id: domainId })
    });
    await loadDomains();
  } catch (e) {
    alert("Failed to delete domain: " + e.message);
  }
}

/* 3. KEYWORD RANK RADAR */
async function loadKeywords(domainId) {
  try {
    const res = await fetch(`/api/keywords?domain=${encodeURIComponent(domainId)}`);
    const kws = await res.json();
    renderKeywords(kws);
  } catch (e) {
    console.error("Load keywords error:", e);
  }
}

function renderKeywords(kws) {
  const tbody = document.getElementById("keywords-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  let top3 = 0;
  let top10 = 0;
  let shifts = 0;

  kws.forEach(k => {
    if (k.position <= 3) top3++;
    if (k.position <= 10) top10++;
    if (k.change !== 0) shifts++;

    let rankClass = "rank-other";
    if (k.position <= 3) rankClass = "rank-top3";
    else if (k.position <= 10) rankClass = "rank-top10";

    let changeHtml = `<span class="change-flat">—</span>`;
    if (k.change > 0) {
      changeHtml = `<span class="change-up">▲ +${k.change}</span>`;
    } else if (k.change < 0) {
      changeHtml = `<span class="change-down">▼ ${k.change}</span>`;
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${k.keyword}</strong></td>
      <td><span class="rank-badge ${rankClass}">#${k.position}</span></td>
      <td>${changeHtml}</td>
      <td>${k.search_volume.toLocaleString()} /mo</td>
      <td><span style="color: ${k.difficulty === 'High' ? 'var(--red)' : (k.difficulty === 'Medium' ? 'var(--yellow)' : 'var(--green)')}; font-weight: 600;">${k.difficulty}</span></td>
      <td><a href="${k.url}" target="_blank" style="color: var(--teal); text-decoration: none; word-break: break-all;">${k.url}</a></td>
      <td style="color: var(--text-dim); font-size: 11px;">${k.last_updated}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("stat-total-kws").innerText = kws.length;
  document.getElementById("stat-top3").innerText = top3;
  document.getElementById("stat-top10").innerText = top10;
  document.getElementById("stat-shifts").innerText = shifts > 0 ? `+${shifts} active` : "Stable";
}

async function addKeyword() {
  const input = document.getElementById("new-keyword-input");
  const kw = input.value.trim();
  if (!kw) return;

  try {
    await fetch("/api/keywords/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ domain: activeDomain, keyword: kw })
    });
    input.value = "";
    loadKeywords(activeDomain);
  } catch (e) {
    alert("Failed to add keyword: " + e.message);
  }
}

async function refreshKeywords() {
  try {
    const res = await fetch("/api/keywords/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ domain: activeDomain })
    });
    const data = await res.json();
    renderKeywords(data.keywords || []);
  } catch (e) {
    alert("Refresh failed: " + e.message);
  }
}

function exportKeywordsCSV() {
  const table = document.querySelector(".radar-table");
  if (!table) return;

  const rows = Array.from(table.querySelectorAll("tr"));
  const csvContent = rows.map(row => {
    const cells = Array.from(row.querySelectorAll("th, td"));
    return cells.map(cell => `"${cell.innerText.replace(/"/g, '""').trim()}"`).join(",");
  }).join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${activeDomain}_serp_rankings_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/* 4. SITE CRAWLER */
async function loadCrawlReport(domainId) {
  try {
    const res = await fetch(`/api/crawler/report?domain=${encodeURIComponent(domainId)}`);
    const report = await res.json();
    displayCrawlReport(report);
  } catch (e) {
    console.error("Load crawl report error:", e);
  }
}

async function runLiveCrawl() {
  const url = document.getElementById("crawl-url-input").value.trim();
  if (!url) return;

  const btn = event.target;
  const originalText = btn.innerText;
  btn.innerText = "⏳ Crawling...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/crawler/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ url })
    });
    const report = await res.json();
    displayCrawlReport(report);
  } catch (e) {
    alert("Crawl failed: " + e.message);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

function displayCrawlReport(r) {
  if (!r) return;

  document.getElementById("crawl-status-code").innerText = r.status_code ? `${r.status_code} OK` : "Offline";
  document.getElementById("crawl-status-code").style.color = (r.status_code >= 200 && r.status_code < 300) ? "var(--green)" : "var(--red)";

  document.getElementById("crawl-latency").innerText = `${r.latency_ms || 0} ms`;
  document.getElementById("crawl-words").innerText = `${(r.seo && r.seo.word_count ? r.seo.word_count.toLocaleString() : 0)} words`;
  document.getElementById("crawl-score").innerText = `${r.health_score || 0} / 100`;

  // Update top header health pill
  const pill = document.getElementById("domain-health-pill");
  if (pill) {
    const score = r.health_score || 85;
    pill.innerText = `● Health: ${score}% (Grade ${score >= 90 ? 'A+' : (score >= 80 ? 'A' : 'B')})`;
    pill.className = `health-pill ${score >= 80 ? 'health-good' : 'health-warn'}`;
  }

  // Meta signals
  const seo = r.seo || {};
  document.getElementById("meta-title-val").innerText = seo.title || "(Missing)";
  document.getElementById("meta-desc-val").innerText = seo.meta_description || "(Missing)";
  document.getElementById("meta-canonical-val").innerText = seo.canonical || "(None)";
  document.getElementById("meta-robots-val").innerText = seo.robots_directive || "index, follow";
  document.getElementById("meta-h1-val").innerText = (seo.h1 && seo.h1.length) ? seo.h1.join(" | ") : "(None)";

  // Issues & recommendations
  const issuesList = document.getElementById("crawl-issues-list");
  if (issuesList) {
    issuesList.innerHTML = "";
    const issues = r.issues || [];
    const recs = r.recommendations || [];

    if (issues.length === 0) {
      issuesList.innerHTML = `<div style="color: var(--green); font-size: 11px;">✓ No critical SEO errors detected on this page!</div>`;
    } else {
      issues.forEach(i => {
        const item = document.createElement("div");
        const color = i.type === "critical" ? "var(--red)" : (i.type === "warning" ? "var(--yellow)" : "var(--teal)");
        item.innerHTML = `<span style="color: ${color}; font-weight: 700;">[${i.type.toUpperCase()}]</span> ${i.msg}`;
        issuesList.appendChild(item);
      });
    }

    if (recs.length > 0) {
      const recHeader = document.createElement("div");
      recHeader.style.marginTop = "8px";
      recHeader.style.fontWeight = "700";
      recHeader.style.color = "var(--text-muted)";
      recHeader.innerText = "Actionable Steps:";
      issuesList.appendChild(recHeader);

      recs.forEach(rec => {
        const item = document.createElement("div");
        item.style.color = "var(--text-muted)";
        item.style.fontSize = "11px";
        item.innerHTML = `→ ${rec}`;
        issuesList.appendChild(item);
      });
    }
  }
}

/* 5. CONTENT AUDITOR */
let auditTimeout = null;

function runContentAudit() {
  clearTimeout(auditTimeout);
  auditTimeout = setTimeout(async () => {
    const text = document.getElementById("content-body").value;
    const target_keyword = document.getElementById("content-target-kw").value;
    const title = document.getElementById("content-title").value;
    const meta_description = document.getElementById("content-desc").value;

    try {
      const res = await fetch("/api/audit/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ text, target_keyword, title, meta_description, slug: target_keyword.replace(/\s+/g, "-").toLowerCase() })
      });
      const data = await res.json();
      displayContentAudit(data);
    } catch (e) {
      console.error("Content audit error:", e);
    }
  }, 250);
}

function displayContentAudit(data) {
  if (!data) return;

  document.getElementById("content-score-badge").innerText = `${data.overall_score} / 100`;
  document.getElementById("content-score-badge").style.color = data.overall_score >= 85 ? "var(--teal)" : (data.overall_score >= 70 ? "var(--yellow)" : "var(--red)");

  const km = data.keyword_metrics || {};
  document.getElementById("content-kw-density").innerText = `${km.density_percent}% (${km.occurrences}x)`;
  document.getElementById("content-readability").innerText = `${data.readability.label} (${data.readability.flesch_score})`;

  // Checks list
  const checksList = document.getElementById("content-checks-list");
  if (checksList) {
    checksList.innerHTML = "";
    (data.checks || []).forEach(c => {
      const div = document.createElement("div");
      const icon = c.status === "pass" ? "✓" : (c.status === "warn" ? "⚠" : "✗");
      const color = c.status === "pass" ? "var(--green)" : (c.status === "warn" ? "var(--yellow)" : "var(--red)");
      div.innerHTML = `<span style="color: ${color}; font-weight: 700; width: 14px; display: inline-block;">${icon}</span> ${c.msg}`;
      checksList.appendChild(div);
    });
  }

  // Google SERP Preview
  const serp = data.serp_preview || {};
  document.getElementById("serp-preview-url").innerText = serp.url || "";
  document.getElementById("serp-preview-title").innerText = serp.title || "";
  document.getElementById("serp-preview-desc").innerText = serp.description || "";

  // Schema output
  document.getElementById("schema-json-output").innerText = JSON.stringify(data.generated_schema || {}, null, 2);
}

/* 6. TAB SWITCHING */
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const targetContent = document.getElementById(tabId);
  if (targetContent) targetContent.classList.add("active");

  const btn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.getAttribute("onclick").includes(tabId));
  if (btn) btn.classList.add("active");
}

function jsonBody(obj) {
  return JSON.stringify(obj);
}
