/*
 * cali-sidekick.js - Universal Embedded Executive Assistant for All Cali Modules.
 * Provides a floating "Ask Cali" assistant inside any department module without
 * needing to switch back to the main Executive Chat on port 8800.
 */

(function () {
  const HUB_HOST = window.location.hostname || "127.0.0.1";
  const HUB_PROTO = window.location.protocol || "http:";
  const isHttpsRoot = HUB_PROTO === "https:" && (!window.location.port || window.location.port === "443");
  const HUB_API = isHttpsRoot ? "/api/cali/chat" : `${HUB_PROTO}//${HUB_HOST}:8800/api/cali/chat`;
  const HUB_URL = isHttpsRoot ? "/" : `${HUB_PROTO}//${HUB_HOST}:8800`;
  let CURRENT_PORT = window.location.port || "80";
  if (window.location.pathname.startsWith('/proxy/')) {
    const parts = window.location.pathname.split('/');
    if (parts.length >= 3 && parts[2]) {
      CURRENT_PORT = parts[2];
    }
  }

  // Module identification
  const MODULE_MAP = {
    "8789": { name: "Website Studio", icon: "🌐", chips: ["✦ Switch to Bento Grid", "🚨 Emergency Trades Layout", "🎨 Change Color to Emerald", "📋 Rewrite Sales Pitch"] },
    "8790": { name: "Video Studio", icon: "🎬", chips: ["🎤 Set Voice to Arthur", "🔲 Render Faceless Short", "💰 Set Guide to £1.99", "⚡ Dispatch Today's Trend"] },
    "8793": { name: "Social Hub", icon: "📢", chips: ["📢 Approve All Staged Drafts", "📊 Umami Traffic Today", "🚀 Check Social Queue", "📝 Draft TikTok Script"] },
    "8791": { name: "SEO Radar", icon: "📈", chips: ["🔍 Check Google Rankings", "📊 Domain Audit", "🎯 Keyword Opportunities"] },
    "8792": { name: "Dev Workbench", icon: "⚡", chips: ["⚡ Git Branch Status", "🔒 Scan Secret Leaks", "📦 Proxmox Fleet Updates"] },
    "8796": { name: "Health Checker", icon: "🏥", chips: ["🔍 Deep Dive Website Scan", "🌐 Check 5 Domains SSL", "⚡ Uptime Kuma Status"] },
    "8797": { name: "Security Radar", icon: "🛡️", chips: ["🛡️ CrowdSec Ban List", "⚡ T3MP3ST Pentest Status", "🔒 TLS & SSL Health"] },
    "8798": { name: "Docs & Reports", icon: "📄", chips: ["📄 Generate Weekly Summary", "📊 Revenue vs Overhead", "📋 PDF Export"] },
    "8799": { name: "Finance Ledger", icon: "💳", chips: ["💰 Gross Revenue YTD", "📉 Overhead Runrate", "⚖️ Corporation Tax Reserve"] }
  };

  const modInfo = MODULE_MAP[CURRENT_PORT] || { name: `Module :${CURRENT_PORT}`, icon: "⚡", chips: ["📊 Operations Status", "🚀 Proxmox Fleet", "💰 Financial Ledger"] };

  // Inject DOM
  function initSidekick() {
    if (document.getElementById("cali-sidekick-root")) return;

    const root = document.createElement("div");
    root.id = "cali-sidekick-root";
    root.innerHTML = `
      <!-- FLOATING TRIGGER PILL -->
      <button id="cali-sidekick-trigger" class="sidekick-trigger" title="Ask Cali for instant tweaks or changes">
        <span class="sidekick-trigger-avatar">👩‍💼</span>
        <span class="sidekick-trigger-label">Ask Cali</span>
        <span class="sidekick-trigger-badge">:${CURRENT_PORT}</span>
      </button>

      <!-- COLLAPSIBLE CHAT DRAWER -->
      <div id="cali-sidekick-panel" class="sidekick-panel hidden">
        <div class="sidekick-header">
          <div class="sidekick-header-info">
            <span class="sidekick-avatar">👩‍💼</span>
            <div>
              <div class="sidekick-title">Cali <span class="sidekick-sub">Chief of Staff</span></div>
              <div class="sidekick-context">${modInfo.icon} In ${modInfo.name} (: ${CURRENT_PORT})</div>
            </div>
          </div>
          <div class="sidekick-header-actions">
            <a href="${HUB_URL}" class="sidekick-btn-icon" title="Open Main Central Hub">↗</a>
            <button id="cali-sidekick-close" class="sidekick-btn-icon" title="Close Assistant">✕</button>
          </div>
        </div>

        <!-- QUICK PROMPT CHIPS -->
        <div class="sidekick-chips-row">
          ${modInfo.chips.map(chip => `<button class="sidekick-chip" data-prompt="${chip}">${chip}</button>`).join("")}
        </div>

        <!-- CHAT MESSAGES CONTAINER -->
        <div id="cali-sidekick-messages" class="sidekick-messages">
          <div class="sidekick-msg cali">
            <div class="sidekick-bubble">
              Hi Antony! I'm active inside <strong>${modInfo.name}</strong>. Let me know any changes, tweaks, or actions you'd like me to make here.
            </div>
          </div>
        </div>

        <!-- INPUT BOX -->
        <form id="cali-sidekick-form" class="sidekick-form">
          <input type="text" id="cali-sidekick-input" class="sidekick-input" placeholder="Ask Cali to change anything on this page..." autocomplete="off">
          <button type="submit" id="cali-sidekick-submit" class="sidekick-send-btn" title="Send request">➤</button>
        </form>
      </div>
    `;

    document.body.appendChild(root);
    setupEvents();
  }

  function setupEvents() {
    const trigger = document.getElementById("cali-sidekick-trigger");
    const panel = document.getElementById("cali-sidekick-panel");
    const closeBtn = document.getElementById("cali-sidekick-close");
    const form = document.getElementById("cali-sidekick-form");
    const input = document.getElementById("cali-sidekick-input");

    trigger.addEventListener("click", () => {
      panel.classList.toggle("hidden");
      if (!panel.classList.contains("hidden")) {
        input.focus();
      }
    });

    closeBtn.addEventListener("click", () => {
      panel.classList.add("hidden");
    });

    // Chips
    document.querySelectorAll(".sidekick-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        const prompt = btn.getAttribute("data-prompt");
        submitMessage(prompt);
      });
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const msg = input.value.trim();
      if (!msg) return;
      input.value = "";
      submitMessage(msg);
    });
  }

  async function submitMessage(userText) {
    const messagesBox = document.getElementById("cali-sidekick-messages");

    // 1. Render User Message
    const userMsgEl = document.createElement("div");
    userMsgEl.className = "sidekick-msg user";
    userMsgEl.innerHTML = `<div class="sidekick-bubble user">${escapeHtml(userText)}</div>`;
    messagesBox.appendChild(userMsgEl);
    messagesBox.scrollTop = messagesBox.scrollHeight;

    // 2. Render Typing Indicator
    const typingEl = document.createElement("div");
    typingEl.className = "sidekick-msg cali typing";
    typingEl.innerHTML = `<div class="sidekick-bubble cali"><span class="pulse-dots">Executing...</span></div>`;
    messagesBox.appendChild(typingEl);
    messagesBox.scrollTop = messagesBox.scrollHeight;

    // 3. Inspect in-page contextual state if available
    let pageContext = `[Context: User is currently inside ${modInfo.name} on Port :${CURRENT_PORT}]`;
    if (CURRENT_PORT === "8789") {
      const bName = document.getElementById("field-business-name")?.value || "";
      const arch = document.getElementById("field-archetype")?.value || "";
      const theme = document.getElementById("field-theme")?.value || "";
      pageContext += ` [Active Mockup: "${bName}", Archetype: "${arch}", Theme: "${theme}"]`;
    }

    // 4. Send to Cali Brain on Port 8800
    try {
      const res = await fetch(HUB_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `${pageContext}\nUser Request: ${userText}` })
      });

      const data = await res.json();
      typingEl.remove();

      const caliReply = data.reply || data.response || "Task executed successfully.";
      const caliMsgEl = document.createElement("div");
      caliMsgEl.className = "sidekick-msg cali";
      caliMsgEl.innerHTML = `<div class="sidekick-bubble cali">${formatMarkdown(caliReply)}</div>`;
      messagesBox.appendChild(caliMsgEl);
      messagesBox.scrollTop = messagesBox.scrollHeight;

      // 5. In-Page Live Tweak Dispatcher for Website Creator (:8789)
      handleInPageTweaks(userText, caliReply);

    } catch (err) {
      typingEl.remove();
      const errEl = document.createElement("div");
      errEl.className = "sidekick-msg cali";
      errEl.innerHTML = `<div class="sidekick-bubble cali error">Unable to connect to Cali Mission Control (:8800). Please ensure Central Hub is running.</div>`;
      messagesBox.appendChild(errEl);
      messagesBox.scrollTop = messagesBox.scrollHeight;
    }
  }

  function handleInPageTweaks(userText, reply) {
    if (CURRENT_PORT !== "8789") return;
    const lower = userText.toLowerCase();

    // Check if user asked to change archetype
    if (lower.includes("bento")) {
      const archEl = document.getElementById("field-archetype");
      if (archEl) archEl.value = "bento-modern-saas";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("trades") || lower.includes("emergency")) {
      const archEl = document.getElementById("field-archetype");
      if (archEl) archEl.value = "high-trust-trades";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("advocacy") || lower.includes("call-on dad")) {
      const archEl = document.getElementById("field-archetype");
      if (archEl) archEl.value = "advocacy-fintech";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("luxury") || lower.includes("boutique")) {
      const archEl = document.getElementById("field-archetype");
      if (archEl) archEl.value = "luxury-boutique";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("health") || lower.includes("dental")) {
      const archEl = document.getElementById("field-archetype");
      if (archEl) archEl.value = "vitality-health";
      if (typeof generateAndPreview === "function") generateAndPreview();
    }

    // Check if user asked to change theme color
    if (lower.includes("emerald") || lower.includes("green")) {
      const t = document.getElementById("field-theme");
      if (t) t.value = "emerald";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("cyan") || lower.includes("electric")) {
      const t = document.getElementById("field-theme");
      if (t) t.value = "electric-cyan";
      if (typeof generateAndPreview === "function") generateAndPreview();
    } else if (lower.includes("amber") || lower.includes("gold")) {
      const t = document.getElementById("field-theme");
      if (t) t.value = "luxury-gold";
      if (typeof generateAndPreview === "function") generateAndPreview();
    }
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function formatMarkdown(str) {
    let html = escapeHtml(str);
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Code
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    // Linebreaks
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  // Auto-init on load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidekick);
  } else {
    initSidekick();
  }
})();

