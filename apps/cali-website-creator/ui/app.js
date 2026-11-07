const API_BASE = window.location.pathname.startsWith("/proxy/")
  ? window.location.pathname.replace(/\/+$/, "")
  : "";

let currentTemplates = [];
let currentArchetypes = {};
let activeSiteId = null;
let currentCaddySnippet = "";
let currentPitchData = null;

document.addEventListener("DOMContentLoaded", () => {
  loadArchetypes();
  loadTemplates();
  loadPublishedSites();
  setupEventListeners();
});

async function loadArchetypes() {
  try {
    const res = await fetch(`${API_BASE}/api/vault/archetypes`);
    currentArchetypes = await res.json();
    renderArchetypeShowcase(currentArchetypes);
  } catch (e) {
    console.error("Failed to load archetypes:", e);
  }
}

function renderArchetypeShowcase(archetypes) {
  const container = document.getElementById("archetype-showcase-grid");
  if (!container) return;
  container.innerHTML = "";

  Object.values(archetypes).forEach(arch => {
    const card = document.createElement("div");
    card.className = "archetype-card";
    const featuresList = arch.features.map(f => `<li>${f}</li>`).join("");

    card.innerHTML = `
      <div>
        <div class="archetype-card-header">
          <span class="archetype-badge-pill">${arch.badge || '2026 ARCHETYPE'}</span>
          <span style="font-size: 11px; color: var(--text-dim); font-family: monospace;">:${arch.id}</span>
        </div>
        <div class="archetype-title">${arch.name}</div>
        <div class="archetype-subtitle">${arch.subtitle}</div>
        <ul class="archetype-feature-list">
          ${featuresList}
        </ul>
      </div>
      <button class="btn-apply-archetype" onclick="applyArchetypeFromVault('${arch.id}', '${arch.theme_default}')">
        ⚡ Apply Archetype to Mockup &rarr;
      </button>
    `;
    container.appendChild(card);
  });
}

function applyArchetypeFromVault(archId, defaultTheme) {
  const archSelect = document.getElementById("field-archetype");
  if (archSelect) archSelect.value = archId;
  if (defaultTheme) {
    const themeSelect = document.getElementById("field-theme");
    if (themeSelect) themeSelect.value = defaultTheme;
  }
  showToast(`Applied 2026 UI Archetype: ${archId}`);
  generateAndPreview();
  switchMode("canvas");
}

async function loadTemplates() {
  try {
    const res = await fetch(`${API_BASE}/api/templates`);
    currentTemplates = await res.json();
    populatePresetDropdown(currentTemplates);

    // Auto-select first template
    if (currentTemplates.length > 0) {
      applyTemplate(currentTemplates[0]);
      generateAndPreview();
    }
  } catch (e) {
    console.error("Failed to load templates:", e);
  }
}

function populatePresetDropdown(templates) {
  const dropdown = document.getElementById("preset-dropdown");
  if (!dropdown) return;
  dropdown.innerHTML = "";

  templates.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t.id;
    const icon = getIconForNiche(t.niche || "");
    opt.textContent = `${icon} ${t.business_name} (${t.niche})`;
    dropdown.appendChild(opt);
  });

  dropdown.addEventListener("change", (e) => {
    const selected = templates.find(t => t.id === e.target.value);
    if (selected) {
      applyTemplate(selected);
      generateAndPreview();
    }
  });
}

function getIconForNiche(niche) {
  if (!niche) return "🏢";
  const n = niche.toLowerCase();
  if (n.includes("trade") || n.includes("plumb")) return "🔧";
  if (n.includes("saas") || n.includes("cloud") || n.includes("tech")) return "✦";
  if (n.includes("advocacy") || n.includes("rights") || n.includes("consumer")) return "🛡️";
  if (n.includes("rest") || n.includes("food") || n.includes("bistro")) return "🍽️";
  if (n.includes("dent") || n.includes("health")) return "🦷";
  if (n.includes("fit") || n.includes("gym") || n.includes("box")) return "🥊";
  if (n.includes("legal") || n.includes("account") || n.includes("tax")) return "⚖️";
  if (n.includes("auto") || n.includes("detail") || n.includes("car")) return "🏎️";
  return "🏢";
}

function applyTemplate(t) {
  document.getElementById("field-business-name").value = t.business_name || t.title || "";
  document.getElementById("field-domain").value = t.domain_target || "prospect.call-on.media";
  document.getElementById("field-city").value = t.city || "United Kingdom";
  document.getElementById("field-phone").value = t.phone || "020 8123 4567";
  document.getElementById("field-title").value = t.niche || t.title || "Local Business";
  document.getElementById("field-theme").value = t.theme || "trust-blue";
  document.getElementById("field-headline").value = t.headline || "";
  document.getElementById("field-subhead").value = t.subhead || "";

  if (t.archetype) {
    const archEl = document.getElementById("field-archetype");
    if (archEl) archEl.value = t.archetype;
  }

  if (t.services && t.services.length >= 3) {
    document.getElementById("svc-title-1").value = t.services[0].title;
    document.getElementById("svc-price-1").value = t.services[0].price;
    document.getElementById("svc-title-2").value = t.services[1].title;
    document.getElementById("svc-price-2").value = t.services[1].price;
    document.getElementById("svc-title-3").value = t.services[2].title;
    document.getElementById("svc-price-3").value = t.services[2].price;
  }

  if (t.testimonial) {
    document.getElementById("field-quote").value = t.testimonial.quote || "";
    document.getElementById("field-author").value = t.testimonial.author || "";
  }
}

function switchMode(mode) {
  const btnCanvas = document.getElementById("btn-mode-canvas");
  const btnPitch = document.getElementById("btn-mode-pitch");
  const btnVault = document.getElementById("btn-mode-vault");
  const viewCanvas = document.getElementById("view-canvas");
  const viewPitch = document.getElementById("view-pitch");
  const viewVault = document.getElementById("view-vault");

  [btnCanvas, btnPitch, btnVault].forEach(b => b && b.classList.remove("active"));
  [viewCanvas, viewPitch, viewVault].forEach(v => v && v.classList.remove("active"));

  if (mode === "pitch") {
    btnPitch.classList.add("active");
    viewPitch.classList.add("active");
  } else if (mode === "vault") {
    btnVault.classList.add("active");
    viewVault.classList.add("active");
  } else {
    btnCanvas.classList.add("active");
    viewCanvas.classList.add("active");
  }
}

function setupEventListeners() {
  // Dynamic host links for remote tablet / Tailscale support
  const currentHost = window.location.hostname || "127.0.0.1";
  const currentProto = window.location.protocol || "http:";
  const healthLink = document.getElementById("link-health-scanner");
  const hubLink = document.getElementById("link-central-hub");
  if (healthLink) healthLink.href = `${currentProto}//${currentHost}:8796`;
  if (hubLink) hubLink.href = `${currentProto}//${currentHost}:8800`;

  // Sidebar Collapse Toggle
  const sidebar = document.getElementById("sidebar-pane");
  const toggleBtn = document.getElementById("btn-toggle-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
    });
  }

  // Mode Switchers
  document.getElementById("btn-mode-canvas").addEventListener("click", () => switchMode("canvas"));
  document.getElementById("btn-mode-pitch").addEventListener("click", () => switchMode("pitch"));
  document.getElementById("btn-mode-vault").addEventListener("click", () => switchMode("vault"));
  document.getElementById("btn-quick-pitch").addEventListener("click", () => switchMode("pitch"));
  document.getElementById("btn-back-to-canvas").addEventListener("click", () => switchMode("canvas"));
  document.getElementById("btn-vault-back").addEventListener("click", () => switchMode("canvas"));

  // Form submission
  const form = document.getElementById("builder-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    generateAndPreview();
  });

  // Archetype direct change listener
  const archSelect = document.getElementById("field-archetype");
  if (archSelect) {
    archSelect.addEventListener("change", () => {
      generateAndPreview();
    });
  }

  // VIBE & BRAND EXTRACTOR ACTION
  const vibeBtn = document.getElementById("btn-extract-vibe");
  const vibeInput = document.getElementById("vibe-url-input");
  const vibeStatus = document.getElementById("vibe-status");

  if (vibeBtn && vibeInput) {
    const handleExtract = async () => {
      const url = vibeInput.value.trim();
      if (!url) {
        vibeStatus.className = "vibe-status error";
        vibeStatus.textContent = "Please enter a URL (e.g. apex-plumbing.co.uk)";
        vibeStatus.classList.remove("hidden");
        return;
      }

      vibeStatus.className = "vibe-status";
      vibeStatus.textContent = "🔍 Inspecting DOM, styles, and brand tokens...";
      vibeStatus.classList.remove("hidden");

      try {
        const res = await fetch(`${API_BASE}/api/vault/extract-tokens`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: url })
        });
        const tokens = await res.json();

        if (tokens.business_name) {
          document.getElementById("field-business-name").value = tokens.business_name;
        }
        if (tokens.city) {
          document.getElementById("field-city").value = tokens.city;
        }
        if (tokens.phone) {
          document.getElementById("field-phone").value = tokens.phone;
        }
        if (tokens.recommended_archetype) {
          document.getElementById("field-archetype").value = tokens.recommended_archetype;
        }

        vibeStatus.className = "vibe-status";
        vibeStatus.innerHTML = `✦ Vibe Cloned! Matched <strong>${tokens.recommended_archetype}</strong> (${tokens.primary_color})`;
        showToast(`Vibe Extracted from ${tokens.business_name || url}!`);
        
        // Re-generate preview immediately with new vibe tokens
        generateAndPreview();
      } catch (err) {
        vibeStatus.className = "vibe-status error";
        vibeStatus.textContent = "Inspection failed; fallback defaults applied.";
      }
    };

    vibeBtn.addEventListener("click", handleExtract);
    vibeInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleExtract();
      }
    });
  }

  // Viewport switchers
  const vpDesk = document.getElementById("view-desktop");
  const vpMob = document.getElementById("view-mobile");
  const frameContainer = document.getElementById("viewport-frame-container");

  vpDesk.addEventListener("click", () => {
    vpDesk.classList.add("active");
    vpMob.classList.remove("active");
    frameContainer.className = "viewport-desktop";
  });

  vpMob.addEventListener("click", () => {
    vpMob.classList.add("active");
    vpDesk.classList.remove("active");
    frameContainer.className = "viewport-mobile";
  });

  // Open in tab (if button present)
  const openTabBtn = document.getElementById("btn-open-tab");
  if (openTabBtn) {
    openTabBtn.addEventListener("click", () => {
      if (activeSiteId) {
        window.open(`${API_BASE}/preview/${activeSiteId}/index.html`, "_blank");
      }
    });
  }

  // Caddy modal
  const modal = document.getElementById("caddy-modal");
  document.getElementById("btn-export-caddy").addEventListener("click", () => {
    modal.classList.remove("hidden");
  });
  document.getElementById("close-modal").addEventListener("click", () => {
    modal.classList.add("hidden");
  });
  document.getElementById("btn-copy-caddy").addEventListener("click", () => {
    navigator.clipboard.writeText(currentCaddySnippet);
    showToast("Caddy configuration copied!");
  });

  // Pitch Tabs
  document.querySelectorAll(".pitch-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".pitch-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".pitch-tab-pane").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.getAttribute("data-tab");
      document.getElementById(target).classList.add("active");
    });
  });
}

async function generateAndPreview() {
  const bName = document.getElementById("field-business-name").value;
  const payload = {
    business_name: bName,
    domain: document.getElementById("field-domain").value,
    city: document.getElementById("field-city").value,
    phone: document.getElementById("field-phone").value,
    title: document.getElementById("field-title").value,
    theme: document.getElementById("field-theme").value,
    archetype: document.getElementById("field-archetype").value,
    headline: document.getElementById("field-headline").value,
    subhead: document.getElementById("field-subhead").value,
    cta_text: "Contact Us",
    features: [
      {
        title: document.getElementById("svc-title-1").value,
        desc: "High quality professional delivery guaranteed.",
        price: document.getElementById("svc-price-1").value
      },
      {
        title: document.getElementById("svc-title-2").value,
        desc: "Experienced certified specialists on call.",
        price: document.getElementById("svc-price-2").value
      },
      {
        title: document.getElementById("svc-title-3").value,
        desc: "Comprehensive warranty and transparent pricing.",
        price: document.getElementById("svc-price-3").value
      }
    ],
    testimonial: {
      quote: document.getElementById("field-quote").value,
      author: document.getElementById("field-author").value
    }
  };

  try {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      activeSiteId = data.site_id;
      currentCaddySnippet = data.metadata.caddyfile_snippet;
      document.getElementById("caddy-snippet").textContent = currentCaddySnippet;
      document.getElementById("preview-url-bar").textContent = `https://${data.metadata.domain}/preview/${data.site_id}`;

      // Update iframe
      const frame = document.getElementById("preview-frame");
      frame.src = `${API_BASE}/preview/${data.site_id}/index.html`;

      // Update Sales Pitch Studio
      currentPitchData = data.pitch;
      if (currentPitchData) {
        document.getElementById("pitch-client-name").textContent = bName;
        document.getElementById("pitch-email-subject").textContent = currentPitchData.email_subject || `Website mockup for ${bName}`;
        document.getElementById("pitch-email-body").textContent = currentPitchData.email_body || "";
        document.getElementById("pitch-dm-body").textContent = currentPitchData.dm_body || "";
        document.getElementById("pitch-phone-body").textContent = `Hi, Antony Brown from Cali Media Ltd. Calling about ${bName}'s online presence in ${payload.city}...`;
      }

      loadPublishedSites();
    }
  } catch (e) {
    console.error("Generate error:", e);
  }
}

async function loadPublishedSites() {
  try {
    const res = await fetch(`${API_BASE}/api/sites/list`);
    const sites = await res.json();
    const container = document.getElementById("published-list");
    if (!container) return;

    if (!sites || sites.length === 0) {
      container.innerHTML = `<div class="empty-hint">Saved mockups will appear here.</div>`;
      return;
    }

    container.innerHTML = "";
    sites.slice(0, 8).forEach(s => {
      const item = document.createElement("div");
      item.className = "published-item";
      const bTitle = s.business_name || s.title || s.id;
      const archBadge = s.archetype ? `<span style="font-size: 9px; color: var(--teal); border: 1px solid rgba(20,184,166,0.3); padding: 1px 4px; border-radius: 3px; margin-left: 4px;">${s.archetype}</span>` : "";
      item.innerHTML = `
        <div class="pub-title">${bTitle} ${archBadge}</div>
        <div class="pub-meta">${s.city || s.domain}</div>
      `;
      item.onclick = () => {
        activeSiteId = s.id;
        document.getElementById("preview-url-bar").textContent = `https://${s.domain}/preview/${s.id}`;
        document.getElementById("preview-frame").src = `${API_BASE}/preview/${s.id}/index.html`;
        if (s.caddyfile_snippet) {
          currentCaddySnippet = s.caddyfile_snippet;
          document.getElementById("caddy-snippet").textContent = currentCaddySnippet;
        }
        if (s.pitch) {
          document.getElementById("pitch-client-name").textContent = bTitle;
          document.getElementById("pitch-email-subject").textContent = s.pitch.email_subject || "";
          document.getElementById("pitch-email-body").textContent = s.pitch.email_body || "";
          document.getElementById("pitch-dm-body").textContent = s.pitch.dm_body || "";
        }
        switchMode("canvas");
      };
      container.appendChild(item);
    });
  } catch (e) {
    console.error("Failed to load published sites:", e);
  }
}

function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.textContent || el.innerText;
  navigator.clipboard.writeText(text);
  showToast("Copied script to clipboard!");
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 2400);
}
