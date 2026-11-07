document.addEventListener("DOMContentLoaded", () => {
  loadSecurity();
});

async function loadSecurity() {
  try {
    const res = await fetch("/api/security/scan");
    const data = await res.json();
    renderStats(data);
    renderAssets(data.scanned_targets);
    renderThreats(data);
  } catch (e) {
    console.error("Security scan error:", e);
  }
}

function renderStats(data) {
  const row = document.getElementById("stats-row");
  if (!row) return;
  row.innerHTML = `
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">SECURITY POSTURE</div>
      <div class="stat-val" style="color: var(--teal);">${data.overall_grade}</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Zero high or critical exposures</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">ACTIVE THREATS BLOCKED</div>
      <div class="stat-val">${data.active_threats_blocked} Blocked</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Cloudflare WAF edge drops</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; color: var(--text-muted);">CROWDSEC IP BANS</div>
      <div class="stat-val">${data.crowdsec_bans} Active Bans</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">Proxmox node firewall synchronization</div>
    </div>
  `;
}

function renderAssets(assets) {
  const container = document.getElementById("assets-list");
  if (!container) return;
  container.innerHTML = "";

  assets.forEach(a => {
    const el = document.createElement("div");
    el.className = "asset-row";
    el.innerHTML = `
      <div>
        <div style="font-weight: 700; font-size: 13px;">${a.domain}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${a.waf_status} · Last Recon: ${a.last_scanned}</div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="tls-badge">TLS ${a.tls_grade}</span>
        <span style="font-size: 10px; color: #34d399; font-weight: 700;">● ${a.status}</span>
      </div>
    `;
    container.appendChild(el);
  });
}

function renderThreats(data) {
  const container = document.getElementById("threats-box");
  if (!container) return;
  const v = data.vulnerabilities;
  container.innerHTML = `
    <div style="display: flex; gap: 14px; margin-bottom: 8px; font-weight: 700;">
      <span style="color: #ef4444;">Critical: ${v.critical}</span>
      <span style="color: #f97316;">High: ${v.high}</span>
      <span style="color: #eab308;">Medium: ${v.medium}</span>
      <span style="color: #3b82f6;">Low: ${v.low}</span>
    </div>
    <p style="color: var(--text-muted); font-size: 11px;">
      All perimeter endpoints running behind Cloudflare proxy tunnels with strict HSTS enabled. Proxmox PBS backups isolated from network egress.
    </p>
  `;
}

