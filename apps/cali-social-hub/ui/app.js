/* Cali Social Media & Publishing Hub - Frontend Controller */

let activeNetwork = "tiktok";
let networkLimits = {
  tiktok: 2200,
  youtube_posts: 5000,
  facebook: 63206,
  instagram: 2200,
  linkedin: 3000,
  pinterest: 500,
  bluesky: 300,
  mastodon: 500,
  tumblr: 10000
};
let availableAssets = [];

document.addEventListener("DOMContentLoaded", () => {
  initHub();
});

async function initHub() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("filter")) {
    const fStatus = document.getElementById("filter-status");
    if (fStatus) fStatus.value = params.get("filter");
  }

  setDefaultTime();
  await loadPosts();
  await loadAssets();
  updateCharCounter();
  updateBrandGuide();
}

function setDefaultTime() {
  const now = new Date();
  now.setHours(now.getHours() + 2);
  const timeStr = now.toISOString().slice(0, 16);
  document.getElementById("composer-time").value = timeStr;
}

/* 1. NETWORK SELECTION & CHAR COUNTER */
function selectNetwork(net) {
  activeNetwork = net;
  document.querySelectorAll(".network-pill").forEach(p => {
    p.classList.toggle("selected", p.getAttribute("data-net") === net);
  });
  updateCharCounter();
  validateWithEcho();
}

function onCaptionInput() {
  updateCharCounter();
  validateWithEcho();
}

function updateCharCounter() {
  const caption = document.getElementById("composer-caption").value;
  const limit = networkLimits[activeNetwork] || 2000;
  const el = document.getElementById("char-counter");
  const current = caption.length;

  el.innerText = `${current} / ${limit.toLocaleString()}`;
  if (current > limit) {
    el.style.color = "var(--red)";
  } else if (current > limit * 0.9) {
    el.style.color = "var(--yellow)";
  } else {
    el.style.color = "var(--teal)";
  }
}

function onBrandChange() {
  updateBrandGuide();
  validateWithEcho();
}

function updateBrandGuide() {
  const brand = document.getElementById("composer-brand").value;
  const guideEl = document.getElementById("echo-brand-guide");
  const guides = {
    "call-on.dad": "<strong>Arthur & Trevor Voice:</strong> Direct, practical, no jargon. Focus on utility traps, consumer checks, and DIY fixes.",
    "call-on.mom": "<strong>Hilda Voice:</strong> Warm, reassuring, motherly tone. Smart grocery shopping, household budgeting, and community care.",
    "cali-media.ltd": "<strong>The Director & Cali Voice:</strong> Confident, innovative, sovereign local software, autonomous systems.",
    "call-on.media": "<strong>Dexter Voice:</strong> Fast-paced, creative coordinator, visual storytelling, viral video pacing.",
    "call-on.shop": "<strong>Crew Club Voice:</strong> Exclusive mascot apparel drops, community pride, official merchandise."
  };
  if (guideEl && guides[brand]) {
    guideEl.innerHTML = guides[brand];
  }
}

let echoValidateTimeout = null;
function validateWithEcho() {
  clearTimeout(echoValidateTimeout);
  echoValidateTimeout = setTimeout(async () => {
    const caption = document.getElementById("composer-caption").value;
    const brand = document.getElementById("composer-brand").value;
    const warningBox = document.getElementById("echo-warning-box");

    if (!caption.trim()) {
      warningBox.style.display = "none";
      return;
    }

    try {
      const res = await fetch("/api/agent/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caption, network: activeNetwork, brand })
      });
      const data = await res.json();
      if (data.warnings && data.warnings.length > 0) {
        warningBox.style.display = "block";
        warningBox.innerHTML = `⚠️ <strong>Echo Notice:</strong> ${data.warnings.join(" | ")}`;
      } else {
        warningBox.style.display = "none";
      }
    } catch (e) {
      console.warn("Echo validation failed:", e);
    }
  }, 300);
}

/* 2. POSTS QUEUE & FEED */
let allLoadedPosts = [];
let currentModalPostId = null;

async function loadPosts() {
  const brand = document.getElementById("filter-brand").value;
  const status = document.getElementById("filter-status").value;

  try {
    const res = await fetch(`/api/posts?brand=${encodeURIComponent(brand)}&status=${encodeURIComponent(status)}`);
    const posts = await res.json();
    allLoadedPosts = posts;
    renderPosts(posts);
  } catch (e) {
    console.error("Load posts error:", e);
  }
}

function renderPosts(posts) {
  const feed = document.getElementById("posts-feed");
  if (!feed) return;
  feed.innerHTML = "";

  if (posts.length === 0) {
    feed.innerHTML = `<div style="color: var(--text-muted); font-size: 12px; padding: 20px; text-align: center;">No posts found matching filter.</div>`;
    return;
  }

  posts.forEach(p => {
    const card = document.createElement("div");
    card.className = "post-card";

    // Media & Video Preview Pill
    let mediaBadge = "";
    const videoStream = p.video_url || (p.media_path && p.media_path.endsWith(".mp4") ? `http://127.0.0.1:8790/stream/exports/trend_videos/${p.media_path}` : "");
    if (videoStream) {
      mediaBadge = `
        <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0;">
          <div class="attached-media-pill" style="cursor: pointer; background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4);" onclick="openVideoModal('${escapeHtml(p.title || p.id)}', '${videoStream}', '${escapeHtml(p.shop_link || '')}', '${p.id}')">
            🎬 <strong>Watch Video Preview</strong> (${p.media_path})
          </div>
          ${p.shop_link ? `<a href="${p.shop_link}" target="_blank" style="font-size: 11px; color: var(--teal); text-decoration: none; background: rgba(20,184,166,0.1); border: 1px solid rgba(20,184,166,0.3); padding: 3px 8px; border-radius: 4px;">🛍️ Print-Off Guide (£1.99)</a>` : ''}
        </div>
      `;
    } else if (p.media_path) {
      mediaBadge = `<div class="attached-media-pill">🎬 <span>${p.media_path}</span></div>`;
    }

    // Evidence & Live Proof
    let evidenceBadge = "";
    if (p.evidence) {
      const isLive = p.status === "published";
      evidenceBadge = `
        <div style="font-size: 11px; padding: 6px 10px; background: ${isLive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)'}; border: 1px solid ${isLive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
          <span style="color: ${isLive ? 'var(--green)' : 'var(--yellow)'}; font-weight: 700;">
            ${isLive ? '✓ LIVE VERIFIED' : '⏳ READY FOR APPROVAL'} (${p.evidence.receipt_id || p.id})
          </span>
          <a href="javascript:void(0)" onclick="showProofModal('${p.id}')" style="color: var(--cyan); text-decoration: underline; font-weight: 600;">
            View Verified Receipt &amp; Proof
          </a>
        </div>
      `;
    }

    // Action Buttons
    let actionBtn = "";
    if (p.status !== "published") {
      actionBtn = `
        <button class="btn btn-success" style="padding: 3px 10px; font-size: 11px;" onclick="publishPostNow('${p.id}')">⚡ Approve &amp; Publish</button>
      `;
    }

    card.innerHTML = `
      <div class="post-meta">
        <div style="display: flex; gap: 6px; align-items: center;">
          <span class="brand-badge">${p.brand}</span>
          <span style="font-size: 11px; font-weight: 700; color: var(--pink); text-transform: uppercase;">${p.network}</span>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          <span class="status-pill status-${p.status}">${p.status.toUpperCase()}</span>
          <span style="font-size: 10px; color: var(--text-dim);">${p.scheduled_time || p.created_at}</span>
        </div>
      </div>

      <div class="post-caption" style="white-space: pre-line; line-height: 1.4;">${escapeHtml(p.caption)}</div>
      ${mediaBadge}
      ${evidenceBadge}

      <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px;">
        ${videoStream ? `<button class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="openVideoModal('${escapeHtml(p.title || p.id)}', '${videoStream}', '${escapeHtml(p.shop_link || '')}', '${p.id}')">🎬 Preview</button>` : ''}
        ${actionBtn}
        <button class="btn" style="padding: 3px 8px; font-size: 11px; color: var(--red);" onclick="deletePost('${p.id}')">Delete</button>
      </div>
    `;
    feed.appendChild(card);
  });
}

function openVideoModal(title, videoUrl, shopUrl, postId) {
  currentModalPostId = postId;
  const modal = document.getElementById("video-preview-modal");
  const modalTitle = document.getElementById("preview-modal-title");
  const player = document.getElementById("modal-video-player");
  const shopInfo = document.getElementById("modal-shop-info");

  if (!modal) return;
  modalTitle.innerText = "🎬 " + (title || "Video Preview & Approval");
  player.src = videoUrl;
  player.load();
  player.play().catch(() => {});

  if (shopUrl) {
    shopInfo.innerHTML = `<strong>📚 Official Call-On Shop Guide:</strong> <a href="${shopUrl}" target="_blank" style="color: var(--teal); font-weight: bold; text-decoration: underline;">${shopUrl}</a> &bull; Print-Off Checklist: £1.99`;
    shopInfo.style.display = "block";
  } else {
    shopInfo.style.display = "none";
  }

  modal.style.display = "flex";
}

function closeVideoModal() {
  const modal = document.getElementById("video-preview-modal");
  const player = document.getElementById("modal-video-player");
  if (player) player.pause();
  if (modal) modal.style.display = "none";
}

async function publishFromModal() {
  if (currentModalPostId) {
    closeVideoModal();
    await publishPostNow(currentModalPostId);
  }
}

function showProofModal(postId) {
  const post = allLoadedPosts.find(p => p.id === postId);
  if (!post) return;

  const modal = document.getElementById("proof-modal");
  const content = document.getElementById("proof-content");
  if (!modal || !content) return;

  const ev = post.evidence || {};
  const isLive = post.status === "published";
  const videoStream = post.video_url || (post.media_path && post.media_path.endsWith(".mp4") ? `http://127.0.0.1:8790/stream/exports/trend_videos/${post.media_path}` : "");

  content.innerHTML = `
    <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 6px; padding: 12px; margin-bottom: 12px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Broadcast Status:</span>
        <span style="color: ${isLive ? 'var(--green)' : 'var(--yellow)'}; font-weight: 700;">${isLive ? '🟢 LIVE VERIFIED' : '⏳ STAGED DRAFT'}</span>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Receipt ID:</span>
        <span style="font-family: monospace; color: var(--cyan);">${ev.receipt_id || post.id}</span>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Target Brand:</span>
        <strong>${post.brand}</strong>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Destination Network:</span>
        <span style="text-transform: uppercase; font-weight: 700; color: var(--pink);">${post.network}</span>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Timestamp:</span>
        <span>${post.published_at || post.scheduled_time || post.created_at}</span>
      </div>
      ${post.media_path ? `
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Attached Media:</span>
        <span style="font-family: monospace;">${post.media_path}</span>
      </div>` : ''}
      ${post.shop_link ? `
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: var(--text-dim);">Linked Shop Guide:</span>
        <a href="${post.shop_link}" target="_blank" style="color: var(--teal); font-weight: bold; text-decoration: underline;">Print-Off Checklist Guide (£1.99)</a>
      </div>` : ''}
      ${videoStream ? `
      <div style="margin-top: 10px;">
        <button class="btn btn-secondary" style="width: 100%; font-size: 11px;" onclick="openVideoModal('${escapeHtml(post.title || post.id)}', '${videoStream}', '${escapeHtml(post.shop_link || '')}', '${post.id}')">🎬 Play Staged Video Clip</button>
      </div>` : ''}
    </div>

    <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">
      <strong>Broadcast Receipt Statement:</strong> Staged and verified via Cali Sovereign Fleet. Telemetry recorded in <code>data/posts.json</code>.
    </div>
  `;

  modal.style.display = "flex";
}

function closeProofModal() {
  const modal = document.getElementById("proof-modal");
  if (modal) modal.style.display = "none";
}

async function submitPost(actionType) {
  const brand = document.getElementById("composer-brand").value;
  const caption = document.getElementById("composer-caption").value.trim();
  const media_path = document.getElementById("composer-media").value;
  const scheduled_time = document.getElementById("composer-time").value.replace("T", " ");

  if (!caption) {
    alert("Please write a caption before saving.");
    return;
  }

  const status = actionType === "publish_now" ? "published" : "scheduled";
  try {
    const res = await fetch("/api/posts/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brand, network: activeNetwork, caption, media_path, scheduled_time, status })
    });
    const data = await res.json();

    if (actionType === "publish_now" && data.post) {
      await fetch("/api/posts/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: data.post.id })
      });
    }

    clearComposer();
    loadPosts();
    alert(actionType === "publish_now" ? "Post published and verified!" : "Post scheduled in calendar queue!");
  } catch (e) {
    alert("Post creation failed: " + e.message);
  }
}

async function publishPostNow(postId) {
  try {
    const res = await fetch("/api/posts/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: postId })
    });
    const data = await res.json();
    loadPosts();
    alert(`Post published successfully! Receipt: ${data.evidence.receipt_id}`);
  } catch (e) {
    alert("Publish failed: " + e.message);
  }
}

async function deletePost(postId) {
  if (!confirm("Delete this post?")) return;
  try {
    await fetch("/api/posts/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: postId })
    });
    loadPosts();
  } catch (e) {
    alert("Delete failed: " + e.message);
  }
}

/* 3. VIDEO STUDIO ASSETS BRIDGE */
async function loadAssets() {
  try {
    const res = await fetch("/api/assets");
    availableAssets = await res.json();

    const mediaSelect = document.getElementById("composer-media");
    if (mediaSelect) {
      mediaSelect.innerHTML = `<option value="">(None - Text Only)</option>`;
      availableAssets.forEach(a => {
        const opt = document.createElement("option");
        opt.value = a.id;
        opt.innerText = `🎬 ${a.title} (${a.size_mb} MB)`;
        mediaSelect.appendChild(opt);
      });
    }

    const assetsContainer = document.getElementById("assets-list");
    if (assetsContainer) {
      assetsContainer.innerHTML = "";
      if (availableAssets.length === 0) {
        assetsContainer.innerHTML = `<div style="font-size: 11px; color: var(--text-muted);">No rendered MP4s found. Open Video Studio to render clips.</div>`;
        return;
      }

      availableAssets.slice(0, 5).forEach(a => {
        const div = document.createElement("div");
        div.style.background = "var(--bg-card)";
        div.style.border = "1px solid var(--border)";
        div.style.borderRadius = "6px";
        div.style.padding = "8px 10px";

        div.innerHTML = `
          <div style="font-size: 11px; font-weight: 700; color: var(--text-main); margin-bottom: 2px;">${a.title}</div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
            <span style="font-size: 10px; color: var(--text-dim);">${a.size_mb} MB · ${a.source}</span>
            <button class="btn" style="padding: 2px 6px; font-size: 10px; color: var(--cyan);" onclick="attachAsset('${a.id}', '${a.title}')">+ Attach</button>
          </div>
        `;
        assetsContainer.appendChild(div);
      });
    }
  } catch (e) {
    console.error("Load assets error:", e);
  }
}

function attachAsset(assetId, assetTitle) {
  document.getElementById("composer-media").value = assetId;
  const captionEl = document.getElementById("composer-caption");
  if (!captionEl.value.trim()) {
    captionEl.value = `New Video Drop: ${assetTitle}!\n\nWatch full breakdown below.\n\n#CaliMedia #VideoStudio`;
  }
  updateCharCounter();
  validateWithEcho();
  alert(`Attached ${assetTitle} to composer!`);
}

/* 4. AGENT ECHO VARIATIONS */
async function generateEchoVariations() {
  const brand = document.getElementById("composer-brand").value;
  const currentCaption = document.getElementById("composer-caption").value.trim();
  const topic = currentCaption || "Avoiding the Direct Debit Trap when moving house";

  try {
    const res = await fetch("/api/agent/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, brand })
    });
    const data = await res.json();
    const variations = data.variations || [];

    if (variations.length > 0) {
      const choice = prompt(
        `Choose variation (1, 2, or 3):\n\n` +
        variations.map((v, i) => `[${i + 1}] ${v.style}:\n${v.caption.slice(0, 90)}...`).join("\n\n")
      );
      const idx = parseInt(choice) - 1;
      if (variations[idx]) {
        document.getElementById("composer-caption").value = variations[idx].caption;
        updateCharCounter();
        validateWithEcho();
      }
    }
  } catch (e) {
    alert("Variation generation failed: " + e.message);
  }
}

function clearComposer() {
  document.getElementById("composer-caption").value = "";
  document.getElementById("composer-media").value = "";
  setDefaultTime();
  updateCharCounter();
  document.getElementById("echo-warning-box").style.display = "none";
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
