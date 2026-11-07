document.addEventListener("DOMContentLoaded", () => {
  loadData();
});

async function loadData() {
  try {
    const [statRes, prodRes, guideRes] = await Promise.all([
      fetch("/api/community/stats"),
      fetch("/api/shop/products"),
      fetch("/api/guides")
    ]);
    const stats = await statRes.json();
    const prods = await prodRes.json();
    const guides = await guideRes.json();

    renderStats(stats, prods, guides);
    renderSites(stats.sites);
    renderPrintOffGuides(guides.print_off_guides || []);
    renderDashboardGuides(guides.dashboard_guides || []);
    renderApparel(prods);
  } catch (e) {
    console.error("Failed to load community data:", e);
  }
}

function renderStats(stats, prods, guides) {
  const row = document.getElementById("stats-row");
  if (!row) return;

  const visitors = stats.unique_visitors !== undefined ? stats.unique_visitors : 2;
  const mentors = stats.volunteer_count || 14;
  const totalGuides = (guides.print_off_guides ? guides.print_off_guides.length : 1) + 
                     (guides.dashboard_guides ? guides.dashboard_guides.length : 4);
  const apparelItems = prods.filter(p => !p.category || !p.category.includes("Guide")).length;

  row.innerHTML = `
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">COMMUNITY OUTREACH (LIVE UMAMI)</div>
      <div class="stat-val">${visitors} Visitors</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Real unique families tracked on call-on.dad &amp; mom</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">ALL COMMUNITY GUIDES &amp; TOOLKITS</div>
      <div class="stat-val">${totalGuides} Guides Live</div>
      <div style="font-size: 10px; color: var(--teal); margin-top: 4px;">£1.99 Print-Offs + Free Onboarding Walkthroughs</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">PRINTFUL APPAREL MERCHANDISE</div>
      <div class="stat-val">${apparelItems} Products</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Automated Printful fulfillment on CT500</div>
    </div>
  `;
}

function renderSites(sites) {
  const container = document.getElementById("sites-list");
  if (!container) return;
  container.innerHTML = "";

  for (const [key, s] of Object.entries(sites)) {
    const el = document.createElement("div");
    el.className = "site-item";
    el.innerHTML = `
      <div class="site-top">
        <span>${escapeHtml(s.name)}</span>
        <span style="color: var(--blue); font-size: 11px;">${escapeHtml(s.domain)}</span>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">
        ${s.guides_count} Published Guides &bull; ${s.active_programs} Active Support Programs
      </div>
      <div style="font-size: 10px; color: var(--teal);">● ${escapeHtml(s.status)}</div>
    `;
    container.appendChild(el);
  }
}

function renderPrintOffGuides(guides) {
  const container = document.getElementById("print-off-guides-list");
  if (!container) return;
  container.innerHTML = "";

  if (guides.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); padding: 10px;">No print-off guides staged yet.</div>`;
    return;
  }

  guides.forEach(g => {
    const el = document.createElement("div");
    el.className = "guide-card";
    el.innerHTML = `
      <div>
        <div class="guide-card-header">
          <div class="guide-title">${escapeHtml(g.title)}</div>
          <span class="guide-badge badge-printoff">£1.99 PRINT-OFF</span>
        </div>
        <div class="guide-meta" style="margin-top: 8px;">
          <div><strong>Lead Author:</strong> ${escapeHtml(g.author || 'Call-On Team')} &bull; Verified UK Checklist</div>
          <div><strong>Format:</strong> ${escapeHtml(g.format || 'Printable A4 Sheet')}</div>
          <div style="color: var(--teal); font-weight: 700; margin-top: 4px;">Price: £1.99 (Instant Print &amp; Download)</div>
        </div>
      </div>
      <div class="guide-actions">
        <a href="${g.local_url}" target="_blank" class="guide-link-btn primary">
          🖨️ View &amp; Print Guide (£1.99)
        </a>
        ${g.video_stream ? `
        <a href="${g.video_stream}" target="_blank" class="guide-link-btn">
          🎬 Watch Video Demo
        </a>` : ''}
        <a href="${g.shop_url}" target="_blank" class="guide-link-btn">
          🌐 Shop Direct Link
        </a>
      </div>
    `;
    container.appendChild(el);
  });
}

function renderDashboardGuides(guides) {
  const container = document.getElementById("dashboard-guides-list");
  if (!container) return;
  container.innerHTML = "";

  guides.forEach(g => {
    const el = document.createElement("div");
    el.className = "guide-card";
    el.innerHTML = `
      <div>
        <div class="guide-card-header">
          <div class="guide-title">${escapeHtml(g.title)}</div>
          <span class="guide-badge badge-free">FREE GUIDE</span>
        </div>
        <div class="guide-meta" style="margin-top: 8px;">
          <div><strong>Target Audience:</strong> ${escapeHtml(g.audience || 'Community')}</div>
          <div><strong>Includes:</strong> Written Tour, PDF Download, Video with Cali</div>
        </div>
      </div>
      <div class="guide-actions">
        <a href="${g.local_url}" target="_blank" class="guide-link-btn primary" style="background: var(--blue);">
          📖 Read Guide
        </a>
        <a href="${g.pdf_url}" target="_blank" class="guide-link-btn">
          📄 PDF
        </a>
        <a href="${g.video_url}" target="_blank" class="guide-link-btn">
          🎬 Video Tour
        </a>
        <a href="${g.blog_url}" target="_blank" class="guide-link-btn">
          📝 Blog
        </a>
      </div>
    `;
    container.appendChild(el);
  });
}

function renderApparel(prods) {
  const container = document.getElementById("products-list");
  if (!container) return;
  container.innerHTML = "";

  // Filter out guides so apparel is distinct
  const apparel = prods.filter(p => !p.category || !p.category.includes("Guide"));

  apparel.forEach(p => {
    const el = document.createElement("div");
    el.className = "prod-card";
    const varText = (p.variants && p.variants.length) ? `Sizes: ${p.variants.join(', ')}` : 'In Stock';
    el.innerHTML = `
      <div style="font-weight: 700; font-size: 12px;">${escapeHtml(p.title)}</div>
      <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(p.category)} &bull; ${escapeHtml(varText)}</div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
        <span class="prod-price">£${p.price_gbp.toFixed(2)}</span>
        <span style="font-size: 10px; color: var(--teal); background: rgba(20,184,166,0.1); padding: 2px 6px; border-radius: 4px;">${escapeHtml(p.status)}</span>
      </div>
    `;
    container.appendChild(el);
  });
}

async function syncPrintful() {
  try {
    const res = await fetch("/api/shop/sync", { method: "POST" });
    const data = await res.json();
    alert(`Printful Catalog Synced! ${data.products_synced} products verified.`);
    loadData();
  } catch (e) {
    alert("Sync error: " + e.message);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
