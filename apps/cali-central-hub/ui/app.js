/**
 * app.js - Cali Mission Control & Executive AI Chief of Staff
 * Conversational delegation, at-a-glance attention center, and embedded in-app module viewer.
 */

const API_BASE = (window.location.protocol === 'tauri:' || window.location.hostname === 'tauri.localhost' || window.location.protocol === 'asset:')
  ? 'http://192.168.0.60:8800'
  : '';

function getModuleUrl(port) {
  if (API_BASE) {
    return `${API_BASE}/proxy/${port}/`;
  }
  // If accessing over HTTPS (e.g. cali.call-on.media) or remote LAN/NetBird, route through the secure hub proxy
  if (window.location.protocol === 'https:' || (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')) {
    return `/proxy/${port}/`;
  }
  const host = window.location.hostname || "127.0.0.1";
  const protocol = window.location.protocol || "http:";
  return `${protocol}//${host}:${port}`;
}

let chatHistory = [];
let isSending = false;
let currentFleet = [];
let currentView = 'chat';

function switchView(viewName) {
  currentView = viewName;
  const tabChat = document.getElementById("tab-chat");
  const tabMgmt = document.getElementById("tab-mgmt");
  const viewChat = document.getElementById("view-chat-container");
  const viewMgmt = document.getElementById("view-mgmt-container");
  const viewTitle = document.getElementById("hub-view-title");

  if (viewName === 'management') {
    if (tabChat) tabChat.classList.remove("active");
    if (tabMgmt) tabMgmt.classList.add("active");
    if (viewChat) viewChat.style.display = "none";
    if (viewMgmt) viewMgmt.style.display = "flex";
    if (viewTitle) viewTitle.innerText = "📊 Full Business Management Dashboard";
    loadFullDashboard();
  } else {
    if (tabMgmt) tabMgmt.classList.remove("active");
    if (tabChat) tabChat.classList.add("active");
    if (viewMgmt) viewMgmt.style.display = "none";
    if (viewChat) viewChat.style.display = "flex";
    if (viewTitle) viewTitle.innerText = "💬 Executive Chat with Cali";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadChatHistory();
  refreshDashboard();
  loadSettings();

  // Auto-refresh passive stream & attention center every 6 seconds
  setInterval(refreshDashboard, 6000);
});

/* -----------------------------------------------------------
 * 1. AT-A-GLANCE EXECUTIVE ATTENTION CENTER
 * ----------------------------------------------------------- */
async function loadAttention() {
  try {
    const res = await fetch(`${API_BASE}/api/attention`);
    if (!res.ok) return;
    const data = await res.json();
    renderAttention(data);
  } catch (e) {
    console.error("Failed to load attention summary:", e);
  }
}

async function loadTrafficPulse() {
  try {
    const res = await fetch(`${API_BASE}/api/traffic`);
    if (!res.ok) return;
    const data = await res.json();
    const visEl = document.getElementById("pulse-visitors");
    const pvEl = document.getElementById("pulse-pageviews");
    if (visEl) visEl.innerText = data.total_visitors != null ? data.total_visitors : '0';
    if (pvEl) pvEl.innerText = data.total_pageviews != null ? data.total_pageviews : '0';
  } catch (e) {
    console.error("Failed to load traffic pulse:", e);
  }
}

function renderAttention(data) {
  // 1. Header Ticker Tape
  const container = document.getElementById("attention-items");
  if (container) {
    container.innerHTML = "";
    if (!data.items || data.items.length === 0) {
      container.innerHTML = `<span style="font-size: 11px; color: var(--text-dim);">All systems normal · No pending decisions</span>`;
      container.style.animation = "none";
    } else {
      const createPill = (item) => {
        const pill = document.createElement("div");
        pill.className = `attention-pill ${item.severity === 'action' ? 'action' : ''}`;
        pill.title = `${item.title}: ${item.detail} (Click to open)`;
        pill.innerHTML = `
          <span>${item.icon || '📌'}</span>
          <strong>${item.title}</strong>
        `;
        pill.onclick = () => {
          openAppViewer(item.module_id, item.department, item.port, getModuleUrl(item.port));
        };
        return pill;
      };
      data.items.forEach(item => container.appendChild(createPill(item)));
      data.items.forEach(item => container.appendChild(createPill(item)));
      const duration = Math.max(25, data.items.length * 6);
      container.style.animation = `ticker-slide ${duration}s linear infinite`;
    }
  }

  // 2. Right-Hand Sovereign Operations Pulse List
  const pulseList = document.getElementById("pulse-attention-list");
  if (pulseList) {
    pulseList.innerHTML = "";
    if (!data.items || data.items.length === 0) {
      pulseList.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 15px; font-size: 11px;">Zero open defects · All departments optimal</div>`;
    } else {
      data.items.forEach(item => {
        const card = document.createElement("div");
        card.className = "fleet-card";
        card.style.padding = "7px 10px";
        card.style.gap = "8px";
        card.innerHTML = `
          <div class="fleet-info" style="gap: 8px; min-width: 0; flex: 1;">
            <span style="font-size: 15px; flex-shrink: 0;">${item.icon || '📌'}</span>
            <div style="min-width: 0; overflow: hidden;">
              <div style="font-weight: 700; font-size: 11px; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${item.title}
              </div>
              <div style="font-size: 10px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${item.detail}
              </div>
            </div>
          </div>
          <div class="fleet-actions" style="flex-shrink: 0;">
            <button class="btn-mini btn-in-cali" onclick="openAppViewer('${item.module_id}', '${item.department.replace(/'/g, "\\'")}', ${item.port}, getModuleUrl(${item.port}))" style="font-size: 9px; padding: 3px 7px;">
              ${item.action_label || 'View'}
            </button>
          </div>
        `;
        pulseList.appendChild(card);
      });
    }
  }
  const badge = document.getElementById("pulse-attention-badge");
  if (badge) badge.innerText = `${data.items ? data.items.length : 0} Active`;
}


/* -----------------------------------------------------------
 * 2. EMBEDDED IN-APP MODULE VIEWER
 * ----------------------------------------------------------- */
async function openAppViewer(modId, modName, port, url) {
  const modal = document.getElementById("app-viewer-modal");
  const iframe = document.getElementById("viewer-iframe");
  const title = document.getElementById("viewer-title");
  const extLink = document.getElementById("viewer-external-link");

  const effectiveUrl = getModuleUrl(port);
  title.innerHTML = `<strong>${modName}</strong> <span style="font-size: 11px; color: var(--text-muted); margin-left: 8px;">Port :${port}</span>`;
  if (extLink) extLink.href = effectiveUrl;

  // Check if module is currently stopped
  const modObj = currentFleet.find(m => m.id === modId);
  if (modObj && modObj.status !== "ONLINE") {
    // Launch it first
    title.innerHTML = `<span>⚡</span> <strong>Starting ${modName}...</strong>`;
    await launchModule(modId, false);
    setTimeout(() => {
      iframe.src = effectiveUrl;
      title.innerHTML = `<strong>${modName}</strong> <span style="font-size: 11px; color: var(--teal); margin-left: 8px;">● Online (Port :${port})</span>`;
    }, 2000);
  } else {
    iframe.src = effectiveUrl;
  }

  modal.style.display = "flex";
}

function closeAppViewer() {
  const modal = document.getElementById("app-viewer-modal");
  const iframe = document.getElementById("viewer-iframe");
  iframe.src = "about:blank";
  modal.style.display = "none";
  refreshDashboard();
}

function toggleNativeFullscreen() {
  const elem = document.documentElement;
  const btn = document.getElementById("viewer-fullscreen-btn");
  if (!document.fullscreenElement && !document.webkitFullscreenElement) {
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    }
    if (btn) btn.innerHTML = "🗗 Windowed";
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
    if (btn) btn.innerHTML = "⛶ Fullscreen";
  }
}


/* -----------------------------------------------------------
 * 3. FLEET MODULES OBSERVER & 1-CLICK LAUNCHERS
 * ----------------------------------------------------------- */
async function loadFleet() {
  try {
    const res = await fetch(`${API_BASE}/api/fleet`);
    if (!res.ok) return;
    currentFleet = await res.json();
    renderFleet(currentFleet);
  } catch (e) {
    console.error("Failed to load fleet:", e);
  }
}

function renderFleet(fleet) {
  const sidebarContainer = document.getElementById("sidebar-dept-list");
  
  const onlineCount = fleet.filter(m => m.status === "ONLINE").length;
  const sidebarKpiEl = document.getElementById("sidebar-kpi-fleet");
  if (sidebarKpiEl) sidebarKpiEl.innerText = `${onlineCount}/${fleet.length} Active`;

  // POPULATE CLEAN, SPACIOUS LEFT SIDEBAR DEPARTMENT DIRECTORY (SOLE LOCATION FOR MODULES)
  if (sidebarContainer) {
    sidebarContainer.innerHTML = "";
    fleet.forEach(mod => {
      const isOnline = mod.status === "ONLINE";
      const item = document.createElement("div");
      item.className = "sidebar-dept-item";
      item.title = `${mod.name} (Port :${mod.port}) - Click to launch`;
      item.innerHTML = `
        <div class="sidebar-dept-left">
          <span class="sidebar-dept-icon">${mod.icon || '📦'}</span>
          <span class="sidebar-dept-name">${mod.name.split(' (')[0]}</span>
        </div>
        <div class="sidebar-dept-right">
          <span class="sidebar-dept-port">:${mod.port}</span>
          <span class="sidebar-dept-dot ${isOnline ? 'online' : 'stopped'}">●</span>
        </div>
      `;
      item.onclick = () => {
        openAppViewer(mod.id, mod.name, mod.port, mod.url);
      };
      sidebarContainer.appendChild(item);
    });
  }
}

async function startAndOpenModule(modId, modName, port, url) {
  openAppViewer(modId, modName, port, url);
}

async function launchModule(moduleId, showNotice = true) {
  try {
    const res = await fetch(`${API_BASE}/api/module/launch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: moduleId })
    });
    const data = await res.json();
    if (showNotice) {
      if (data.status === "success") {
        alert(`Starting module... Port will be online in a few seconds.`);
        setTimeout(refreshDashboard, 2000);
      } else {
        alert(`Launch notice: ${data.message}`);
      }
    }
  } catch (e) {
    if (showNotice) alert("Launch error: " + e.message);
  }
}


/* -----------------------------------------------------------
 * 4. TALK TO CALI (CHAT & DELEGATION)
 * ----------------------------------------------------------- */
async function loadChatHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/cali/history`);
    if (!res.ok) return;
    chatHistory = await res.json();
    renderChatHistory();
  } catch (e) {
    console.error("Failed to load chat history:", e);
  }
}

function renderChatHistory() {
  const container = document.getElementById("chat-thread");
  if (!container) return;
  container.innerHTML = "";

  chatHistory.forEach(msg => {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${msg.role}`;

    let toolsHtml = "";
    if (Array.isArray(msg.tools_called) && msg.tools_called.length > 0) {
      msg.tools_called.forEach(tc => {
        const toolName = tc.tool || "tool";
        const toolAction = tc.result?.action || "Autonomous Action";
        const icon = toolName.includes("video") ? "🎬" : (toolName.includes("social") ? "📱" : (toolName.includes("seo") ? "🔍" : (toolName.includes("shop") ? "🛍️" : (toolName.includes("security") ? "🛡️" : (toolName.includes("filings") ? "🏛️" : "🏥")))));
        toolsHtml += `
          <div class="tool-chip">
            <span>${icon}</span>
            <span><strong>${toolAction}:</strong> ${tc.result?.title || tc.result?.brand || tc.result?.domain || 'Executed'}</span>
          </div>
        `;
      });
    }

    bubble.innerHTML = `
      <div>${formatMarkdown(msg.content)}</div>
      ${toolsHtml}
      <div class="bubble-meta">${msg.timestamp || ''}</div>
    `;
    container.appendChild(bubble);
  });

  container.scrollTop = container.scrollHeight;
}

function formatMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 1px 4px; border-radius: 3px;">$1</code>')
    .replace(/\n/g, '<br>');
}

function handleInputKey(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChatMessage();
  }
}

function useQuickPrompt(text) {
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = text;
    sendChatMessage();
  }
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg || isSending) return;

  isSending = true;
  input.value = "";
  const btn = document.getElementById("btn-send");
  if (btn) btn.disabled = true;

  // Optimistic user bubble
  chatHistory.push({
    role: "user",
    content: msg,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });
  renderChatHistory();

  // Temporary thinking indicator
  const container = document.getElementById("chat-thread");
  const thinkingBubble = document.createElement("div");
  thinkingBubble.className = "chat-bubble assistant";
  thinkingBubble.id = "thinking-bubble";
  thinkingBubble.innerHTML = `<span style="color: var(--teal);">● Cali is coordinating with department engines...</span>`;
  container.appendChild(thinkingBubble);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/api/cali/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const replyData = await res.json();

    const tb = document.getElementById("thinking-bubble");
    if (tb) tb.remove();

    chatHistory.push(replyData);
    renderChatHistory();

    // Trigger immediate refresh of incoming stream & attention bar
    refreshDashboard();

  } catch (err) {
    const tb = document.getElementById("thinking-bubble");
    if (tb) tb.remove();

    chatHistory.push({
      role: "assistant",
      content: `I ran into an issue connecting to my brain backend: ${err.message}. Please check AI Settings or try again.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    renderChatHistory();
  } finally {
    isSending = false;
    if (btn) btn.disabled = false;
    if (input) input.focus();
  }
}


/* -----------------------------------------------------------
 * 5. PASSIVE MONITORING & LIVE STREAM
 * ----------------------------------------------------------- */
async function refreshDashboard() {
  try {
    await Promise.all([
      loadTelemetry(),
      loadAttention(),
      loadTrafficPulse(),
      loadFleet(),
      loadEvents()
    ]);
    if (currentView === 'management') {
      await loadFullDashboard();
    }
  } catch (err) {
    console.warn("Passive telemetry warning:", err);
  }
}

async function loadTelemetry() {
  try {
    const res = await fetch(`${API_BASE}/api/telemetry`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.disk) {
      document.getElementById("telemetry-disk").innerText = `${data.disk.free_gb} GB Free`;
    }
    if (data.timestamp) {
      document.getElementById("telemetry-time").innerText = data.timestamp.split(" ")[1] || data.timestamp;
    }
  } catch (e) {}
}

async function loadEvents() {
  try {
    const res = await fetch(`${API_BASE}/api/events`);
    if (!res.ok) return;
    const events = await res.json();
    renderEvents(events);
  } catch (e) {}
}

function renderEvents(events) {
  const container = document.getElementById("event-stream-container");
  if (!container) return;
  container.innerHTML = "";

  if (events.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-dim); font-size: 11px; padding: 14px; text-align: center;">
        No incoming activity recorded yet across the modules.
      </div>
    `;
    return;
  }

  events.slice(0, 8).forEach(evt => {
    const item = document.createElement("div");
    item.className = "event-card";
    item.innerHTML = `
      <div class="event-top">
        <div class="event-source">
          <span>${evt.icon || '📌'}</span>
          <span>${evt.source}</span>
        </div>
        <span class="event-time">${evt.timestamp}</span>
      </div>
      <div class="event-title">${evt.title}</div>
      <div class="event-detail">${evt.detail}</div>
      <span class="event-badge">${evt.badge || 'EVENT'}</span>
    `;
    container.appendChild(item);
  });
}


/* -----------------------------------------------------------
 * 6. AI SETTINGS MODAL
 * ----------------------------------------------------------- */
async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/cali/settings`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.provider) document.getElementById("cfg-provider").value = data.provider;
    if (data.base_url) document.getElementById("cfg-base-url").value = data.base_url;
    if (data.model) document.getElementById("cfg-model").value = data.model;
    if (data.api_key_masked) {
      document.getElementById("cfg-key-status").innerText = `Currently configured: ${data.api_key_masked}`;
    }
  } catch (e) {}
}

function openSettingsModal() {
  loadSettings();
  document.getElementById("settings-modal").style.display = "flex";
}

function closeSettingsModal() {
  document.getElementById("settings-modal").style.display = "none";
}

function toggleProviderFields() {
  const prov = document.getElementById("cfg-provider").value;
  const urlInput = document.getElementById("cfg-base-url");
  const modelInput = document.getElementById("cfg-model");

  if (prov === "openrouter") {
    urlInput.value = "https://openrouter.ai/api/v1";
    modelInput.value = "google/gemini-2.5-flash";
  } else if (prov === "litellm") {
    urlInput.value = "http://127.0.0.1:4000/v1";
    modelInput.value = "nexus-main";
  }
}

async function saveSettings() {
  const provider = document.getElementById("cfg-provider").value;
  const baseUrl = document.getElementById("cfg-base-url").value.trim();
  const apiKey = document.getElementById("cfg-api-key").value.trim();
  const model = document.getElementById("cfg-model").value.trim();

  const payload = { provider, base_url: baseUrl, model };
  if (apiKey) payload.api_key = apiKey;

  try {
    const res = await fetch(`${API_BASE}/api/cali/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    alert("Cali intelligence settings updated successfully!");
    closeSettingsModal();
  } catch (e) {
    alert("Error saving settings: " + e.message);
  }
}

/* -----------------------------------------------------------
 * 7. FULL BUSINESS MANAGEMENT DASHBOARD (UMAMI CT163 + OPERATIONS)
 * ----------------------------------------------------------- */
async function loadFullDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard/full`);
    if (!res.ok) return;
    const data = await res.json();
    renderFullDashboard(data);
  } catch (e) {
    console.error("Failed to load full dashboard:", e);
  }
}

function renderFullDashboard(data) {
  // 1. KPI cards
  const t24 = data.traffic_24h || {};
  const totVisEl = document.getElementById("mgmt-total-visitors");
  const totPvEl = document.getElementById("mgmt-total-pageviews");
  if (totVisEl) totVisEl.innerText = t24.total_visitors !== undefined ? t24.total_visitors : '-';
  if (totPvEl) totPvEl.innerText = `Pageviews: ${t24.total_pageviews || 0}`;

  const onlineCount = (data.fleet || []).filter(m => m.status === 'ONLINE').length;
  const fleetEl = document.getElementById("mgmt-fleet-health");
  if (fleetEl) fleetEl.innerText = `${onlineCount}/${(data.fleet || []).length} Online`;

  const attEl = document.getElementById("mgmt-attention-count");
  if (attEl) attEl.innerText = `${data.attention?.total_items || 0} Items`;

  // 2. Traffic Grid (Umami CT163)
  const trafficContainer = document.getElementById("traffic-cards-container");
  if (trafficContainer && t24.domains) {
    trafficContainer.innerHTML = "";
    Object.entries(t24.domains).forEach(([dom, stats]) => {
      const card = document.createElement("div");
      card.className = "traffic-card";
      card.title = `Click to open Umami CT163 analytics for ${dom}`;
      card.innerHTML = `
        <div class="traffic-card-head">
          <span class="traffic-card-domain">${dom}</span>
          <span class="traffic-status-dot"></span>
        </div>
        <div class="traffic-metric-main">
          <span class="traffic-num-big">${stats.visitors || 0}</span>
          <span class="traffic-lbl-dim">Unique Visitors (24h)</span>
        </div>
        <div class="traffic-meta-row">
          <span>Views: <strong>${stats.pageviews || 0}</strong></span>
          <span>Bounce: <strong>${stats.bounce_rate || 0}%</strong></span>
        </div>
      `;
      card.onclick = () => {
        window.open("http://192.168.0.163:3000", "_blank");
      };
      trafficContainer.appendChild(card);
    });
  }

  // 3. Attention Action Center
  const attList = document.getElementById("mgmt-attention-list");
  if (attList && data.attention?.items) {
    attList.innerHTML = "";
    data.attention.items.forEach(item => {
      const card = document.createElement("div");
      card.className = "action-card";
      card.innerHTML = `
        <div class="action-card-left">
          <span class="action-card-icon">${item.icon || '📌'}</span>
          <div class="action-card-details">
            <span class="action-card-title">${item.title}</span>
            <span class="action-card-desc">${item.detail}</span>
          </div>
        </div>
        <button class="action-card-btn" onclick="openAppViewer('${item.module_id}', '${item.department}', ${item.port}, 'http://127.0.0.1:${item.port}')">
          ${item.action_label || 'Open Engine ↗'}
        </button>
      `;
      attList.appendChild(card);
    });
  }

  // 4. Merch products
  const merchList = document.getElementById("mgmt-merch-list");
  if (merchList && data.merch_products) {
    merchList.innerHTML = "";
    data.merch_products.forEach(p => {
      const item = document.createElement("div");
      item.className = "merch-item";
      item.innerHTML = `
        <span class="merch-name">${p.title}</span>
        <span class="merch-price">£${p.price.toFixed(2)}</span>
      `;
      merchList.appendChild(item);
    });
  }

  // 5. SEO keywords
  const seoList = document.getElementById("mgmt-seo-list");
  if (seoList && data.seo_keywords) {
    seoList.innerHTML = "";
    data.seo_keywords.forEach(kw => {
      const item = document.createElement("div");
      item.className = "seo-kw-item";
      const changeStr = kw.change > 0 ? `+${kw.change}` : (kw.change === 0 ? 'stable' : kw.change);
      item.innerHTML = `
        <span class="seo-kw-name">${kw.keyword} (${kw.domain || 'dad'})</span>
        <span class="seo-kw-pos">#${kw.position} (${changeStr})</span>
      `;
      seoList.appendChild(item);
    });
  }

  // 5b. Authorised Engagements
  const engList = document.getElementById("mgmt-engagements-list");
  if (engList && data.engagements) {
    engList.innerHTML = "";
    const cntEl = document.getElementById("mgmt-engagements-count");
    if (cntEl) cntEl.innerText = `${data.engagements.length} Active`;
    data.engagements.forEach(eng => {
      const item = document.createElement("div");
      item.className = "merch-item";
      item.innerHTML = `
        <span class="merch-name">${eng.name}</span>
        <span class="merch-price" style="font-size: 10px; color: var(--text-muted);">${(eng.targets || []).slice(0, 2).join(', ')}</span>
      `;
      engList.appendChild(item);
    });
  }

  // 6. Fleet grid wide
  const fleetGrid = document.getElementById("mgmt-fleet-grid");
  if (fleetGrid && data.fleet) {
    fleetGrid.innerHTML = "";
    data.fleet.forEach(m => {
      const card = document.createElement("div");
      card.className = "fleet-card-wide";
      const isOnline = m.status === 'ONLINE';
      const icon = m.id === 'video_studio' ? '🎬' : (m.id === 'seo_radar' ? '🔍' : (m.id === 'social_hub' ? '📱' : (m.id === 'community_sites' ? '🌐' : (m.id === 'health_checker' ? '🏥' : (m.id === 'security_radar' ? '🛡️' : '📄')))));
      card.innerHTML = `
        <div class="fleet-wide-top">
          <div class="fleet-wide-brand">
            <span>${icon}</span>
            <strong>${m.name}</strong>
          </div>
          <span class="status-badge ${isOnline ? 'online' : 'stopped'}">${isOnline ? '● ONLINE' : '○ STOPPED'}</span>
        </div>
        <div class="fleet-wide-desc">
          Port :${m.port} · ${m.department || 'Operations'}<br>
          <span style="font-size: 10px; color: var(--text-dim);">${isOnline ? `Latency: ${m.latency_ms}ms` : 'Click below to start'}</span>
        </div>
        <div class="fleet-wide-actions">
          <button class="btn-open-inapp" onclick="openAppViewer('${m.id}', '${m.name}', ${m.port}, '${m.url}')">
            ${isOnline ? 'Open in Cali ↗' : 'Start & Open ⚡'}
          </button>
          <button class="btn-open-tab" onclick="window.open('${m.url}', '_blank')">
            ↗ Tab
          </button>
        </div>
      `;
      fleetGrid.appendChild(card);
    });
  }

  // 6. Proxmox & Homelab Infrastructure Overwatch
  if (data.proxmox) {
    renderProxmoxOverwatch(data.proxmox);
  }
}

/* -----------------------------------------------------------
 * 8. CLIENT WEBSITE HEALTH CHECKER (PRE-SALES & AUDITS)
 * ----------------------------------------------------------- */
async function runClientAudit() {
  const input = document.getElementById("input-client-domain");
  const btn = document.getElementById("btn-run-audit");
  const resultDiv = document.getElementById("client-audit-result");
  const domain = input.value.trim();

  if (!domain) {
    alert("Please enter a domain or URL to audit.");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Auditing...";
  resultDiv.style.display = "block";
  resultDiv.innerHTML = `<span style="color: var(--teal);">Running non-intrusive diagnostic pass on ${domain}...</span>`;

  try {
    const res = await fetch("http://127.0.0.1:8796/api/audit/client", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain })
    });
    const audit = await res.json();
    if (!res.ok || audit.error) {
      resultDiv.innerHTML = `<span style="color: var(--red);">Audit failed: ${audit.error || 'Server error'}</span>`;
      return;
    }

    const gradeColor = audit.grade === 'A' ? 'var(--green)' : (audit.grade === 'B' ? 'var(--teal)' : 'var(--yellow)');
    resultDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 8px;">
        <div>
          <strong style="font-size: 14px; color: #fff;">${audit.domain}</strong>
          <span style="font-size: 11px; color: var(--text-muted); margin-left: 8px;">IP: ${audit.ip_address || 'Resolved'}</span>
        </div>
        <div style="font-size: 16px; font-weight: 800; color: ${gradeColor};">
          Score: ${audit.score}/100 (${audit.grade})
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px; margin-bottom: 10px;">
        <div>SSL: <strong>${audit.ssl?.valid ? '✅ ' + audit.ssl.days_remaining + 'd left' : '❌ Issue'}</strong></div>
        <div>Latency: <strong>${audit.facts?.latency_ms || 40}ms</strong></div>
        <div>Mobile: <strong>${audit.facts?.has_viewport ? '✅ Responsive' : '⚠️ Missing'}</strong></div>
      </div>

      <div style="background: var(--bg-input); padding: 8px; border-radius: 6px; font-size: 11px; margin-bottom: 8px;">
        <strong>Identified Opportunities (${(audit.findings || []).length}):</strong>
        <ul style="padding-left: 16px; margin-top: 4px; color: var(--text-muted);">
          ${(audit.findings || []).slice(0, 3).map(f => `<li>${f.category}: ${f.issue}</li>`).join('')}
        </ul>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <span style="font-size: 11px; font-weight: 700; color: var(--teal);">Ready-to-Send Client Pitch:</span>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 10px;" onclick="copyPitchText()">📋 Copy Pitch</button>
        </div>
        <textarea id="pitch-textarea" style="width: 100%; height: 90px; background: var(--bg-input); border: 1px solid var(--border); color: var(--text-main); font-size: 10px; border-radius: 4px; padding: 6px; font-family: monospace;" readonly>${audit.client_pitch}</textarea>
      </div>
    `;
  } catch (err) {
    resultDiv.innerHTML = `<span style="color: var(--red);">Could not connect to Health Checker suite on port 8796 (${err.message})</span>`;
  } finally {
    btn.disabled = false;
    btn.innerText = "Run Audit 🚀";
  }
}

function copyPitchText() {
  const ta = document.getElementById("pitch-textarea");
  if (ta) {
    navigator.clipboard.writeText(ta.value);
    alert("Client proposal pitch copied to clipboard!");
  }
}

/* -----------------------------------------------------------
 * 9. PROXMOX HOST & HOMELAB FLEET OVERWATCH
 * ----------------------------------------------------------- */
let allProxmoxContainers = [];

function renderProxmoxOverwatch(px) {
  if (!px || px.error) {
    const banner = document.getElementById("px-updates-banner");
    if (banner) {
      banner.style.display = "block";
      banner.innerHTML = `<span style="color: var(--yellow);">⚠️ Proxmox Bridge Notice: ${px?.error || 'Proxmox node offline or unreachable.'}</span>`;
    }
    return;
  }

  // 1. Host Vitals Strip
  const host = px.host || {};
  const cpuEl = document.getElementById("px-cpu-val");
  const loadEl = document.getElementById("px-load-val");
  if (cpuEl) cpuEl.innerText = `${host.cpu_pct !== undefined ? host.cpu_pct : 0}% CPU`;
  if (loadEl) loadEl.innerText = `Load: ${host.load1 || 0}, ${host.load5 || 0}, ${host.load15 || 0}`;

  const ramEl = document.getElementById("px-ram-val");
  const ramSub = document.getElementById("px-ram-sub");
  if (ramEl && host.mem_used) {
    const usedGb = (host.mem_used / (1024**3)).toFixed(1);
    const totGb = (host.mem_total / (1024**3)).toFixed(1);
    ramEl.innerText = `${host.mem_pct || 0}% RAM`;
    if (ramSub) ramSub.innerText = `${usedGb} GB / ${totGb} GB`;
  }

  const ctVal = document.getElementById("px-containers-val");
  const ctSub = document.getElementById("px-containers-sub");
  if (ctVal) ctVal.innerText = `${px.running_count || 0} / ${px.containers_count || 0} Running`;
  if (ctSub) ctSub.innerText = `${px.stopped_count || 0} Stopped (e.g. CT125 sandbox)`;

  const bkVal = document.getElementById("px-backups-val");
  const bkSub = document.getElementById("px-backups-sub");
  const bk = px.backups_summary || {};
  if (bkVal) bkVal.innerText = `Active (${bk.recent_jobs_count || 0} jobs)`;
  if (bkSub) bkSub.innerText = `${bk.pbs_groups_count || 0} PBS backup groups`;

  // 2. Pending OS Updates Banner
  const updBanner = document.getElementById("px-updates-banner");
  const upd = px.updates_summary || {};
  if (updBanner) {
    if (upd.upgradable_total > 0) {
      updBanner.style.display = "block";
      updBanner.style.background = "rgba(245, 158, 11, 0.1)";
      updBanner.style.borderColor = "rgba(245, 158, 11, 0.3)";
      const flaggedList = (upd.flagged_containers || []).map(c => `
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 6px 10px; border-radius: 4px; margin-top: 4px;">
          <div>
            <strong>CT${c.vmid} (${c.name}):</strong> <span style="color: var(--yellow);">${c.upgradable_count} pending update(s)</span>
          </div>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 11px;" onclick="runContainerUpgrade(${c.vmid}, '${c.name}')">Run apt upgrade</button>
        </div>
      `).join('');

      updBanner.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="color: var(--yellow); font-size: 13px;">⚠️ Pending OS Package Updates (${upd.upgradable_total} packages waiting across ${upd.containers_with_updates_count} container(s))</strong>
          <button class="btn btn-secondary" style="font-size: 10px; padding: 2px 6px;" onclick="checkFleetUpdatesNow(this)">Re-check</button>
        </div>
        ${flaggedList}
      `;
    } else if (upd.checking) {
      updBanner.style.display = "block";
      updBanner.innerHTML = `<span>🔄 <strong>Fleet update check in progress:</strong> Refreshing package indices across containers...</span>`;
    } else {
      updBanner.style.display = "block";
      updBanner.style.background = "rgba(16, 185, 129, 0.1)";
      updBanner.style.borderColor = "rgba(16, 185, 129, 0.3)";
      updBanner.innerHTML = `<span style="color: var(--green); font-size: 12px;">✅ <strong>Proxmox Container Fleet is 100% Up to Date:</strong> Zero pending OS package updates waiting.</span>`;
    }
  }

  // 3. Container Fleet Cards Grid
  allProxmoxContainers = px.containers || [];
  renderContainerCards(allProxmoxContainers);

  // 4. Homelab Services Pulse Grid
  const pulseGrid = document.getElementById("px-pulse-grid");
  const pulseSum = document.getElementById("px-pulse-summary");
  const pulse = px.pulse_services || {};
  if (pulseSum) pulseSum.innerText = `${px.services_summary?.online || 0} / ${px.services_summary?.total || 0} Online`;

  if (pulseGrid) {
    pulseGrid.innerHTML = "";
    Object.entries(pulse).forEach(([k, s]) => {
      const isUp = s.up;
      const chip = document.createElement("div");
      chip.style.cssText = `background: ${isUp ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.15)'}; border: 1px solid ${isUp ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.4)'}; border-radius: 4px; padding: 3px 8px; font-size: 11px; display: flex; align-items: center; gap: 5px;`;
      chip.innerHTML = `
        <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: ${isUp ? 'var(--green)' : 'var(--red)'};"></span>
        <strong style="color: #fff;">${s.label || k}</strong>
      `;
      pulseGrid.appendChild(chip);
    });
  }
}

function renderContainerCards(cts) {
  const grid = document.getElementById("px-containers-grid");
  const filterCount = document.getElementById("px-filter-count");
  if (filterCount) filterCount.innerText = `Showing ${cts.length} containers`;
  if (!grid) return;
  grid.innerHTML = "";

  cts.forEach(c => {
    const isRunning = c.status === 'running';
    const hasUpdates = (c.upgradable_count || 0) > 0;
    const card = document.createElement("div");
    card.style.cssText = `background: var(--bg-card); border: 1px solid ${isRunning ? 'var(--border)' : 'rgba(239, 68, 68, 0.3)'}; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 6px;`;
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: ${isRunning ? 'var(--green)' : 'var(--red)'};"></span>
            <strong style="font-size: 13px; color: #fff;">CT${c.ctid || c.vmid}</strong>
            <span style="font-size: 11px; color: var(--text-muted);">${c.friendly_name || c.name}</span>
          </div>
          <small style="font-size: 10px; color: var(--text-dim);">${c.category || ''}</small>
        </div>
        <span style="font-size: 9px; font-weight: 700; padding: 2px 5px; border-radius: 3px; background: ${isRunning ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.2)'}; color: ${isRunning ? 'var(--green)' : 'var(--red)'};">${(c.status || '').toUpperCase()}</span>
      </div>

      ${isRunning ? `
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; font-size: 10px; margin-top: 2px;">
          <div>CPU: <strong>${c.cpu_pct || 0}%</strong></div>
          <div>RAM: <strong>${c.mem_mb || 0}MB</strong></div>
          <div>Disk: <strong>${c.disk_pct || 0}%</strong></div>
        </div>
      ` : '<div style="font-size: 11px; color: var(--text-dim);">Container is stopped</div>'}

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; padding-top: 4px; border-top: 1px solid var(--border);">
        <div style="font-size: 10px;">
          ${hasUpdates ? `<span style="color: var(--yellow); font-weight: 700;">⚠️ ${c.upgradable_count} update(s)</span>` : '<span style="color: var(--text-dim);">Up to date</span>'}
        </div>
        <div style="display: flex; gap: 4px;">
          ${hasUpdates ? `<button class="btn btn-secondary" style="padding: 2px 6px; font-size: 9px; color: var(--yellow);" onclick="runContainerUpgrade(${c.ctid || c.vmid}, '${c.friendly_name}')">Upgrade</button>` : ''}
          ${isRunning ? `
            <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 9px;" onclick="containerPowerAction(${c.ctid || c.vmid}, 'reboot', '${c.friendly_name}')">Reboot</button>
            <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 9px; color: var(--red);" onclick="containerPowerAction(${c.ctid || c.vmid}, 'shutdown', '${c.friendly_name}')">Stop</button>
          ` : `
            <button class="btn btn-primary" style="padding: 2px 6px; font-size: 9px;" onclick="containerPowerAction(${c.ctid || c.vmid}, 'start', '${c.friendly_name}')">Start</button>
          `}
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function filterContainers() {
  const q = (document.getElementById("px-search-input")?.value || "").toLowerCase().trim();
  if (!q) {
    renderContainerCards(allProxmoxContainers);
    return;
  }
  const filtered = allProxmoxContainers.filter(c => {
    const id = String(c.ctid || c.vmid || "");
    const name = (c.friendly_name || c.name || "").toLowerCase();
    const cat = (c.category || "").toLowerCase();
    return id.includes(q) || name.includes(q) || cat.includes(q);
  });
  renderContainerCards(filtered);
}

async function containerPowerAction(vmid, action, name) {
  if (!confirm(`Are you sure you want to ${action.toUpperCase()} ${name} (CT${vmid})?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/proxmox/container/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vmid, action })
    });
    const d = await res.json();
    alert(`Command ${action.toUpperCase()} sent to CT${vmid}: ${d.data || d.result || d.message || 'Success'}`);
    refreshProxmoxOverwatch();
  } catch (err) {
    alert(`Failed to execute ${action} on CT${vmid}: ${err.message}`);
  }
}

async function runContainerUpgrade(vmid, name) {
  if (!confirm(`Run apt-get upgrade on CT${vmid} (${name}) now in the background?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/proxmox/updates/upgrade`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vmid })
    });
    const d = await res.json();
    alert(d.result || d.message || `Upgrade queued on CT${vmid}!`);
    refreshProxmoxOverwatch();
  } catch (err) {
    alert(`Failed to start upgrade on CT${vmid}: ${err.message}`);
  }
}

async function checkFleetUpdatesNow(btn) {
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Scanning Fleet...";
  }
  try {
    const res = await fetch(`${API_BASE}/api/proxmox/updates/check`, { method: "POST" });
    const d = await res.json();
    alert(d.result || "Fleet apt check queued across all containers! It runs in the background over SSH.");
    setTimeout(refreshProxmoxOverwatch, 3000);
  } catch (err) {
    alert(`Failed to trigger fleet check: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "🔄 Check Fleet Updates (Apt)";
    }
  }
}

async function refreshProxmoxOverwatch() {
  try {
    const res = await fetch(`${API_BASE}/api/proxmox/overwatch`);
    if (!res.ok) return;
    const data = await res.json();
    renderProxmoxOverwatch(data);
  } catch (err) {
    console.error("Proxmox overwatch refresh error:", err);
  }
}

/* -----------------------------------------------------------
 * 9. TABLET APPS DRAWER & NATIVE ANDROID LAUNCHER
 * ----------------------------------------------------------- */
async function openTabletAppsDrawer() {
  const modal = document.getElementById("tablet-apps-modal");
  if (!modal) return;
  modal.style.display = "flex";
  loadInstalledTabletApps();
}

function closeTabletAppsDrawer() {
  const modal = document.getElementById("tablet-apps-modal");
  if (modal) modal.style.display = "none";
}

async function loadInstalledTabletApps() {
  const grid = document.getElementById("tablet-apps-grid");
  if (!grid) return;

  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.TvApps) {
    try {
      const res = await window.Capacitor.Plugins.TvApps.listApps();
      const apps = res.apps || [];
      if (apps.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 30px;">No third-party apps discovered. Use the quick actions above.</div>';
        return;
      }
      grid.innerHTML = "";
      apps.forEach(app => {
        const item = document.createElement("div");
        item.style.cssText = "display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; cursor: pointer; text-align: center; transition: all 0.2s;";
        item.onmouseenter = () => { item.style.background = "rgba(20,184,166,0.12)"; item.style.borderColor = "var(--teal)"; };
        item.onmouseleave = () => { item.style.background = "rgba(255,255,255,0.03)"; item.style.borderColor = "rgba(255,255,255,0.06)"; };
        item.onclick = () => launchNativeApp(app.packageName);

        const iconImg = app.icon ? `<img src="${app.icon}" style="width: 44px; height: 44px; border-radius: 10px; margin-bottom: 8px; object-fit: contain;">` : `<div style="width: 44px; height: 44px; border-radius: 10px; margin-bottom: 8px; background: #1e293b; display: flex; align-items: center; justify-content: center; font-size: 18px; color: var(--teal); font-weight: 700;">${app.label ? app.label.charAt(0) : '📱'}</div>`;
        
        item.innerHTML = `
          ${iconImg}
          <span style="font-size: 11px; color: #fff; font-weight: 600; line-height: 1.2; word-break: break-word;">${app.label || app.packageName}</span>
        `;
        grid.appendChild(item);
      });
    } catch (err) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 20px;">Could not list apps via native bridge: ${err.message}</div>`;
    }
  } else {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 25px;">
        <p style="margin: 0 0 10px 0; font-size: 13px; color: #e2e8f0;">Viewing from Web / Desktop Client</p>
        <p style="margin: 0; font-size: 11px;">The native App Drawer is available when running directly on the Cali Tablet OS shell.</p>
      </div>
    `;
  }
}

async function launchNativeApp(pkg) {
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.TvApps) {
    try {
      if (pkg === 'com.android.settings') {
        await window.Capacitor.Plugins.TvApps.openSettings();
      } else {
        await window.Capacitor.Plugins.TvApps.launchApp({ packageName: pkg });
      }
      closeTabletAppsDrawer();
    } catch (err) {
      alert(`Could not launch ${pkg}: ${err.message}`);
    }
  } else {
    alert(`Native launch for ${pkg} requires the Android tablet shell.`);
  }
}
