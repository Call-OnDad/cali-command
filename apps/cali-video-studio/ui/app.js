// Cali Video & Media Studio Pro - NLE Controller

let projectState = {
  title: "Cali Operations Showcase",
  format: "9:16",
  voice: "cali",
  speed: 1.0,
  include_bumper: true,
  subtitle_preset: "yellow",
  activeSceneIndex: 0,
  pixelsPerSecond: 45,
  scenes: [
    { text: "Welcome to the new Cali operations hub.", prompt: "Futuristic dark tech control room with glowing screens", duration: 4.0 },
    { text: "Every department now runs in its own native suite, powered by local GPU acceleration.", prompt: "High tech server cluster with blue data streams", duration: 5.0 },
    { text: "Faster video creation with local Piper voice synthesis and instant render dispatch.", prompt: "Modern video editing timeline with glowing waveforms", duration: 4.5 }
  ]
};

let allPacks = [];
let isPlaying = false;
let playheadTime = 0.0;
let renderPollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  initTimelineResizer();
  renderScriptBlocks();
  renderTimeline();
  loadPacks();
  loadAuditionsVault();
  bindPlayerEvents();
  updateInspector();

  // Spacebar Play/Pause
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "INPUT") {
      e.preventDefault();
      togglePlay();
    }
  });
});

let allAuditionFiles = [];

/* 0b. VOICE VAULT & CLONE AUDITION ROOM */
let auditionRetryCount = 0;

async function loadAuditionsVault() {
  try {
    const res = await fetch("/api/voice-auditions");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    allAuditionFiles = Array.isArray(data) ? data : [];
    renderAuditions(allAuditionFiles);
    auditionRetryCount = 0;
  } catch (e) {
    console.warn("Auditions initial load attempt failed, retrying in 1.5s...", e);
    const container = document.getElementById("auditions-list");
    if (auditionRetryCount < 5) {
      auditionRetryCount++;
      if (container) {
        container.innerHTML = `<div style="color: var(--teal); font-size: 11px; padding: 10px;">
          Connecting to local voice server (attempt ${auditionRetryCount}/5)...
        </div>`;
      }
      setTimeout(loadAuditionsVault, 1500);
    } else {
      if (container) {
        container.innerHTML = `<div style="color: var(--text-muted); font-size: 11px; padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 4px; border: 1px solid var(--border);">
          <strong>Server Not Responding:</strong> Please ensure <code>Launch-Studio.cmd</code> is running in the background, then <a href="javascript:loadAuditionsVault()" style="color: var(--cyan); text-decoration: underline;">Click Here to Retry</a>.
        </div>`;
      }
    }
  }
}

function renderAuditions(files) {
  const container = document.getElementById("auditions-list");
  if (!container) return;
  container.innerHTML = "";

  if (!Array.isArray(files) || files.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">No voice files found matching filter.</div>';
    return;
  }

  files.forEach(f => {
    const card = document.createElement("div");
    card.style.background = "var(--bg-track)";
    card.style.border = "1px solid var(--border)";
    card.style.borderRadius = "6px";
    card.style.padding = "10px 12px";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 12px; font-weight: 700; color: var(--cyan);">${f.character}</span>
        <span style="font-size: 10px; padding: 2px 6px; background: rgba(16, 185, 129, 0.15); color: #34d399; border-radius: 3px; font-weight: 600;">🔒 LOCKED CANONICAL</span>
      </div>
      <div style="font-size: 11px; color: var(--text-main); font-weight: 500; margin-bottom: 2px;">${f.name}</div>
      <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">${f.desc || ''} (${f.size_kb} KB)</div>
      <audio controls preload="metadata" style="width: 100%; height: 32px; margin-bottom: 4px;" src="${f.stream_url}"></audio>
    `;
    container.appendChild(card);
  });
}

function filterAuditions() {
  const sel = document.getElementById("voice-filter").value;
  if (sel === "ALL") {
    renderAuditions(allAuditionFiles);
  } else {
    renderAuditions(allAuditionFiles.filter(f => f.character.toLowerCase().includes(sel.toLowerCase())));
  }
}

/* 0c. AUTONOMOUS TREND-TO-VIDEO ENGINE (Apify + Google Trends + Flow + Cast) */
let currentTrendScript = null;

async function loadLiveTrends() {
  const box = document.getElementById("live-trends-box");
  if (!box) return;
  box.innerHTML = `<div style="font-size: 10px; color: var(--cyan); text-align: center; padding: 6px;">📡 Scouting live UK trends (Apify & Google Trends)...</div>`;

  try {
    const res = await fetch("/api/trends/live");
    const trends = await res.json();
    if (!trends || !trends.length) {
      box.innerHTML = `<div style="font-size: 10px; color: var(--text-dim); text-align: center; padding: 6px;">No trends returned. Using baseline topics.</div>`;
      return;
    }

    box.innerHTML = "";
    trends.forEach(t => {
      const item = document.createElement("div");
      item.style.cssText = "background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; padding: 6px 8px; cursor: pointer; transition: 0.15s; display: flex; flex-direction: column; gap: 2px;";
      item.onmouseover = () => { item.style.borderColor = "var(--cyan)"; item.style.background = "rgba(56, 189, 248, 0.08)"; };
      item.onmouseout = () => { item.style.borderColor = "rgba(255,255,255,0.08)"; item.style.background = "rgba(255,255,255,0.04)"; };
      
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 9px; color: var(--cyan); font-weight: 700; text-transform: uppercase;">${t.source}</span>
          <span style="font-size: 8px; background: rgba(56,189,248,0.2); color: #fff; padding: 1px 4px; border-radius: 3px;">${t.velocity || 'Active'}</span>
        </div>
        <div style="font-size: 11px; font-weight: 600; color: var(--text-main); line-height: 1.3;">${t.topic}</div>
        <div style="font-size: 9px; color: var(--text-dim);">${t.category}</div>
      `;

      item.onclick = () => selectTrend(t.topic, t.category, t.source);
      box.appendChild(item);
    });
  } catch (e) {
    box.innerHTML = `<div style="font-size: 10px; color: var(--red); text-align: center; padding: 6px;">Failed to fetch live trends: ${e.message}</div>`;
  }
}

async function selectTrend(topic, category, source) {
  const inputEl = document.getElementById("auto-input");
  if (inputEl) inputEl.value = topic;

  // Auto-fetch script preview & matched cast
  try {
    const res = await fetch("/api/trends/script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic })
    });
    const scriptData = await res.json();
    currentTrendScript = scriptData;

    // Auto set persona selector
    const charSelect = document.getElementById("auto-char");
    if (charSelect && scriptData.character_id) {
      charSelect.value = scriptData.character_id;
    }

    // Display dispatch card
    const card = document.getElementById("trend-dispatch-card");
    const title = document.getElementById("disp-char-title");
    const snippet = document.getElementById("disp-script-snippet");
    if (card && title && snippet) {
      card.style.display = "block";
      title.innerHTML = `🎭 Matched: <strong>${scriptData.character_name}</strong> (${scriptData.role}) &bull; ${scriptData.estimated_duration_sec}s 9:16 Short`;
      snippet.innerText = `"${scriptData.hook}"`;
    }
  } catch (e) {
    console.warn("Script preview failed:", e);
  }
}

async function runAutoVideoGenerator() {
  const input = document.getElementById("auto-input").value.trim();
  const char = document.getElementById("auto-char").value;
  const count = parseInt(document.getElementById("auto-scenes-count").value || "4");

  if (!input) {
    alert("Please scout live trends or enter a topic first!");
    return;
  }

  const badge = document.getElementById("render-status-badge");
  badge.innerText = "Status: Auto-Generating...";
  badge.style.color = "var(--cyan)";

  try {
    const res = await fetch("/api/trends/script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: input,
        character_id: char === "auto" ? null : char
      })
    });
    const scriptData = await res.json();
    currentTrendScript = scriptData;

    const charName = scriptData.character_name;
    const scenes = [];

    // Scene 1: Hook
    scenes.push({
      text: scriptData.hook,
      prompt: `${charName} looking directly into lens with urgent visual graphic for ${input.slice(0, 30)}`,
      duration: 6.0
    });

    // Scene 2 & 3: Body & Actionable Solution
    const bodyWords = scriptData.body.split(". ");
    if (bodyWords.length > 1 && count >= 4) {
      scenes.push({
        text: bodyWords[0] + ".",
        prompt: `Close-up diagnostic view, technical verification documents, or kitchen audit demonstration`,
        duration: 7.0
      });
      scenes.push({
        text: bodyWords.slice(1).join(". "),
        prompt: `${charName} demonstrating practical sovereign checklist with green checkmarks and safety tips`,
        duration: 8.0
      });
    } else {
      scenes.push({
        text: scriptData.body,
        prompt: `${charName} demonstrating practical sovereign checklist with green checkmarks`,
        duration: 10.0
      });
    }

    // Scene 4: CTA
    scenes.push({
      text: scriptData.cta,
      prompt: `Clean Call-On brand card with ${scriptData.brand_target} domain and official cast badge`,
      duration: 5.5
    });

    // Apply to project state
    projectState.title = `${charName} - ${input.slice(0, 32)}`;
    projectState.voice = scriptData.character_id;
    projectState.scenes = scenes;
    projectState.activeSceneIndex = 0;

    document.getElementById("project-title").value = projectState.title;
    const voiceSelect = document.getElementById("char-voice");
    if (voiceSelect) {
      voiceSelect.value = scriptData.character_id;
      if (typeof onVoiceProfileChange === "function") onVoiceProfileChange();
    }

    renderScriptBlocks();
    renderTimeline();
    switchLeftTab("pane-script");

    // Show dispatch card
    const card = document.getElementById("trend-dispatch-card");
    const title = document.getElementById("disp-char-title");
    const snippet = document.getElementById("disp-script-snippet");
    if (card && title && snippet) {
      card.style.display = "block";
      title.innerHTML = `🎭 Ready: <strong>${scriptData.character_name}</strong> (${scriptData.role}) &bull; ${scriptData.estimated_duration_sec}s 9:16 Short`;
      snippet.innerText = `"${scriptData.hook}"`;
    }

    badge.innerText = "Status: Storyboard Ready";
    badge.style.color = "var(--teal)";
  } catch (e) {
    alert("Auto-generation error: " + e.message);
    badge.innerText = "Status: Error";
    badge.style.color = "var(--red)";
  }
}

async function dispatchToFlowAndSocial() {
  const input = document.getElementById("auto-input").value.trim();
  const char = document.getElementById("auto-char").value;

  if (!input) {
    alert("Please select a trending topic first!");
    return;
  }

  const badge = document.getElementById("render-status-badge");
  badge.innerText = "Status: Dispatching to Flow & Social...";
  badge.style.color = "var(--cyan)";

  try {
    const res = await fetch("/api/trends/dispatch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: input,
        character_id: char === "auto" ? null : char
      })
    });
    const result = await res.json();
    if (result.success) {
      badge.innerText = "Status: Queued in Flow & Social Hub";
      badge.style.color = "var(--teal)";
      alert(`🚀 Trend Video Dispatched!\n\nProject ID: ${result.project_id}\nPresenter: ${result.character}\nTopic: ${result.topic}\n\nStaged in:\n- Flow Video Manifest (${result.flow_engine})\n- Cali Social Hub Queue (${result.staged_in_social_hub ? 'Active' : 'Offline'})\n\nAntony can review or trigger render in Video Studio or Social Hub (:8793).`);
    } else {
      alert("Dispatch failed: " + (result.error || "Unknown error"));
    }
  } catch (e) {
    alert("Dispatch error: " + e.message);
    badge.innerText = "Status: Error";
    badge.style.color = "var(--red)";
  }
}

/* 0. DRAGGABLE TIMELINE RESIZER */
function initTimelineResizer() {
  const resizer = document.getElementById("timeline-resizer");
  const dock = document.getElementById("timeline-dock");
  if (!resizer || !dock) return;

  // Restore saved height
  const savedHeight = localStorage.getItem("cali_timeline_height");
  if (savedHeight) {
    dock.style.height = savedHeight + "px";
  }

  let isDragging = false;
  let startY = 0;
  let startHeight = 0;

  resizer.addEventListener("mousedown", (e) => {
    isDragging = true;
    startY = e.clientY;
    startHeight = dock.offsetHeight;
    resizer.classList.add("dragging");
    document.body.style.cursor = "ns-resize";
    e.preventDefault();
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const dy = startY - e.clientY; // Dragging UP increases height
    const newHeight = Math.max(120, Math.min(550, startHeight + dy));
    dock.style.height = newHeight + "px";
  });

  window.addEventListener("mouseup", () => {
    if (isDragging) {
      isDragging = false;
      resizer.classList.remove("dragging");
      document.body.style.cursor = "default";
      localStorage.setItem("cali_timeline_height", dock.offsetHeight);
    }
  });
}

function onVoiceProfileChange() {
  const sel = document.getElementById("char-voice");
  const val = sel.value;
  projectState.voice = val;

  const descriptions = {
    arthur: "Arthur Auditor (Consumer Protection · Locked: arthur-natural 0.93x)",
    hilda: "Hilda (Family & Home Advice · Locked: Antony's late mum reference voice)",
    the_director: "The Director (Antony Leadership · Locked: Antony cloned voice master)",
    trevor: "Trevor (Handyman & DIY Guides · Locked: 02-trevor audition master)",
    dexter: "Dexter (Creative Director & Production · Locked: 03-dexter audition master)",
    odin: "Odin (Chief Security Officer · Locked: odin-michael approved master)",
    cali: "Cali (Platform Command · Locked: Jenny 1.0x neural model)"
  };

  const descEl = document.getElementById("voice-desc");
  if (descEl && descriptions[val]) {
    descEl.innerText = descriptions[val];
  }

  renderTimeline();
}

/* 1. LEFT PANEL TABS */
function switchLeftTab(tabId) {
  document.querySelectorAll(".panel-left .tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".panel-tabs .panel-tab-btn").forEach(el => el.classList.remove("active"));

  document.getElementById(tabId).classList.add("active");
  const activeBtn = Array.from(document.querySelectorAll(".panel-tabs .panel-tab-btn")).find(b => b.getAttribute("onclick").includes(tabId));
  if (activeBtn) activeBtn.classList.add("active");
}

/* 2. SCRIPT EDITOR (DESCRIPT STYLE) */
function renderScriptBlocks() {
  const container = document.getElementById("script-blocks-container");
  container.innerHTML = "";

  let cumulativeTime = projectState.include_bumper ? 3.0 : 0.0;

  projectState.scenes.forEach((scene, idx) => {
    const block = document.createElement("div");
    block.className = `script-sentence-block ${idx === projectState.activeSceneIndex ? 'active' : ''}`;
    block.onclick = () => selectScene(idx);

    const startTime = cumulativeTime;
    const endTime = startTime + scene.duration;
    cumulativeTime = endTime;

    block.innerHTML = `
      <div class="script-sentence-header">
        <span>SCENE ${idx + 1} (${startTime.toFixed(1)}s - ${endTime.toFixed(1)}s)</span>
        <button style="background: none; border: none; color: var(--text-dim); cursor: pointer;" onclick="event.stopPropagation(); removeScene(${idx})">✕</button>
      </div>
      <textarea style="margin-bottom: 0; min-height: 54px; font-size: 13px;" onchange="updateSceneText(${idx}, this.value)">${scene.text}</textarea>
    `;
    container.appendChild(block);
  });
}

function selectScene(idx) {
  projectState.activeSceneIndex = idx;
  renderScriptBlocks();
  updateInspector();
  highlightActiveClipOnTimeline();

  // Jump playhead to scene start
  let t = projectState.include_bumper ? 3.0 : 0.0;
  for (let i = 0; i < idx; i++) {
    t += projectState.scenes[i].duration;
  }
  setPlayheadTime(t);
}

function updateSceneText(idx, val) {
  projectState.scenes[idx].text = val;
  renderTimeline();
}

function updateActiveSceneDuration(val) {
  const dur = parseFloat(val);
  projectState.scenes[projectState.activeSceneIndex].duration = dur;
  document.getElementById("scene-duration-val").innerText = dur.toFixed(1) + "s";
  renderTimeline();
  renderScriptBlocks();
}

function updateActiveScenePrompt(val) {
  projectState.scenes[projectState.activeSceneIndex].prompt = val;
}

function addScene() {
  projectState.scenes.push({
    text: "Enter next narration sentence for this scene...",
    prompt: "Scene visual asset description",
    duration: 4.0
  });
  renderScriptBlocks();
  renderTimeline();
}

function removeScene(idx) {
  if (projectState.scenes.length <= 1) return;
  projectState.scenes.splice(idx, 1);
  if (projectState.activeSceneIndex >= projectState.scenes.length) {
    projectState.activeSceneIndex = projectState.scenes.length - 1;
  }
  renderScriptBlocks();
  renderTimeline();
  updateInspector();
}

function applyCharacter(charName) {
  const active = projectState.scenes[projectState.activeSceneIndex];
  active.prompt = `${charName} presenting: ` + active.prompt;
  document.getElementById("scene-prompt").value = active.prompt;

  // Sync voice selector
  const charKey = charName.toLowerCase().replace(" ", "_");
  const sel = document.getElementById("char-voice");
  if (sel) {
    for (let opt of sel.options) {
      if (opt.value === charKey || opt.value.includes(charKey)) {
        sel.value = opt.value;
        onVoiceProfileChange();
        break;
      }
    }
  }

  alert(`Applied ${charName} to Scene ${projectState.activeSceneIndex + 1} and synced voice!`);
}

/* 3. MULTI-TRACK TIMELINE RENDERING */
function renderTimeline() {
  const pps = projectState.pixelsPerSecond;
  const totalDuration = calculateTotalDuration();

  // 1. Render Ruler Bar
  const ruler = document.getElementById("ruler-bar");
  ruler.innerHTML = "";
  const totalSeconds = Math.ceil(totalDuration) + 5;
  ruler.style.width = (totalSeconds * pps) + "px";

  for (let s = 0; s <= totalSeconds; s++) {
    const tick = document.createElement("div");
    tick.className = "ruler-tick";
    tick.style.left = (s * pps) + "px";
    tick.innerText = `${s}s`;
    ruler.appendChild(tick);
  }

  // 2. Render Tracks
  const subTrack = document.getElementById("track-sub");
  const videoTrack = document.getElementById("track-video");
  const audioTrack = document.getElementById("track-audio");

  subTrack.innerHTML = "";
  videoTrack.innerHTML = "";
  audioTrack.innerHTML = "";

  let offset = 0;

  // Bumper clip if enabled
  if (projectState.include_bumper) {
    const bumperW = 3.0 * pps;

    const bumperSub = document.createElement("div");
    bumperSub.className = "timeline-clip clip-sub";
    bumperSub.style.left = "0px";
    bumperSub.style.width = bumperW + "px";
    bumperSub.innerText = "CALI MEDIA (Opener)";
    subTrack.appendChild(bumperSub);

    const bumperVid = document.createElement("div");
    bumperVid.className = "timeline-clip clip-video";
    bumperVid.style.left = "0px";
    bumperVid.style.width = bumperW + "px";
    bumperVid.innerText = "🎬 Cali 3s Bumper";
    videoTrack.appendChild(bumperVid);

    const bumperAud = document.createElement("div");
    bumperAud.className = "timeline-clip clip-audio";
    bumperAud.style.left = "0px";
    bumperAud.style.width = bumperW + "px";
    bumperAud.innerText = "🔔 Brand Audio";
    audioTrack.appendChild(bumperAud);

    offset += bumperW;
  }

  // Render scenes
  projectState.scenes.forEach((scene, idx) => {
    const clipW = scene.duration * pps;

    // Subtitle Clip
    const subClip = document.createElement("div");
    subClip.className = `timeline-clip clip-sub ${idx === projectState.activeSceneIndex ? 'selected' : ''}`;
    subClip.style.left = offset + "px";
    subClip.style.width = clipW + "px";
    subClip.innerText = scene.text.slice(0, 30) + "...";
    subClip.onclick = (e) => { e.stopPropagation(); selectScene(idx); };
    subTrack.appendChild(subClip);

    // Video Scene Clip
    const vidClip = document.createElement("div");
    vidClip.className = `timeline-clip clip-video ${idx === projectState.activeSceneIndex ? 'selected' : ''}`;
    vidClip.style.left = offset + "px";
    vidClip.style.width = clipW + "px";
    vidClip.innerText = `Scene ${idx + 1}: ${scene.prompt.slice(0, 24)}`;
    vidClip.onclick = (e) => { e.stopPropagation(); selectScene(idx); };
    videoTrack.appendChild(vidClip);

    // Audio Voice Clip
    const audClip = document.createElement("div");
    audClip.className = `timeline-clip clip-audio ${idx === projectState.activeSceneIndex ? 'selected' : ''}`;
    audClip.style.left = offset + "px";
    audClip.style.width = clipW + "px";
    audClip.innerText = `🗣️ ${projectState.voice} (${scene.duration.toFixed(1)}s)`;
    audClip.onclick = (e) => { e.stopPropagation(); selectScene(idx); };
    audioTrack.appendChild(audClip);

    offset += clipW;
  });

  document.getElementById("tracks-container").style.width = Math.max(offset + 100, 800) + "px";
}

function calculateTotalDuration() {
  let dur = projectState.include_bumper ? 3.0 : 0.0;
  projectState.scenes.forEach(s => dur += s.duration);
  return dur;
}

function highlightActiveClipOnTimeline() {
  renderTimeline();
}

function onTimelineZoom(val) {
  projectState.pixelsPerSecond = parseInt(val);
  renderTimeline();
  updatePlayheadVisual();
}

function onTimelineClick(event) {
  const rect = document.getElementById("tracks-container").getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const time = Math.max(0, clickX / projectState.pixelsPerSecond);
  setPlayheadTime(time);
}

function setPlayheadTime(time) {
  playheadTime = Math.min(time, calculateTotalDuration());
  updatePlayheadVisual();

  const player = document.getElementById("main-player");
  if (player.duration) {
    player.currentTime = playheadTime;
  }
}

function updatePlayheadVisual() {
  const playhead = document.getElementById("timeline-playhead");
  const x = playheadTime * projectState.pixelsPerSecond;
  playhead.style.left = x + "px";

  // Update timecode display
  const totalMs = Math.round(playheadTime * 1000);
  const mins = Math.floor(totalMs / 60000);
  const secs = Math.floor((totalMs % 60000) / 1000);
  const frames = Math.floor(((totalMs % 1000) / 1000) * 30);
  document.getElementById("timecode-readout").innerText = `00:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}:${String(frames).padStart(2,'0')}`;
  document.getElementById("playback-time").innerText = `${playheadTime.toFixed(1)}s / ${calculateTotalDuration().toFixed(1)}s`;
}

/* 4. PLAYER & TRANSPORT */
function bindPlayerEvents() {
  const player = document.getElementById("main-player");
  player.ontimeupdate = () => {
    if (isPlaying) {
      playheadTime = player.currentTime;
      updatePlayheadVisual();
    }
  };
  player.onended = () => {
    isPlaying = false;
    document.getElementById("play-pause-btn").innerText = "▶";
  };
}

function togglePlay() {
  const player = document.getElementById("main-player");
  if (!player.src) return;

  if (isPlaying) {
    player.pause();
    isPlaying = false;
    document.getElementById("play-pause-btn").innerText = "▶";
  } else {
    player.play();
    isPlaying = true;
    document.getElementById("play-pause-btn").innerText = "⏸";
  }
}

function stepFrame(seconds) {
  setPlayheadTime(playheadTime + seconds);
}

function onAspectChange() {
  const fmt = document.getElementById("canvas-aspect").value;
  projectState.format = fmt;
  const wrapper = document.getElementById("video-wrapper");
  wrapper.className = `video-frame-wrapper aspect-${fmt.replace(':', '-')}`;
}

/* 5. INSPECTOR UPDATES */
function updateInspector() {
  const active = projectState.scenes[projectState.activeSceneIndex];
  if (!active) return;

  document.getElementById("scene-duration").value = active.duration;
  document.getElementById("scene-duration-val").innerText = active.duration.toFixed(1) + "s";
  document.getElementById("scene-prompt").value = active.prompt;
}

/* 6. PRODUCTION PACKS BROWSER */
async function loadPacks() {
  try {
    const res = await fetch("/api/collections");
    allPacks = await res.json();
    const sel = document.getElementById("pack-selector");
    sel.innerHTML = '<option value="">-- Select Active Pack --</option>';

    allPacks.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.path;
      opt.innerText = `${p.name} (${p.count} cuts)`;
      sel.appendChild(opt);
    });
  } catch (e) {
    console.error("Pack load error:", e);
  }
}

async function onPackSelect() {
  const path = document.getElementById("pack-selector").value;
  if (!path) return;

  try {
    const res = await fetch(`/api/library?collection=${encodeURIComponent(path)}`);
    const videos = await res.json();
    const list = document.getElementById("pack-videos-list");
    list.innerHTML = "";

    videos.forEach(v => {
      const row = document.createElement("div");
      row.className = "btn btn-secondary";
      row.style.justifyContent = "space-between";
      row.style.fontSize = "11px";
      row.style.padding = "6px 8px";
      row.onclick = () => loadVideoToMonitor(v.rel_path);
      row.innerHTML = `
        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px;">📹 ${v.name}</span>
        <span style="color: var(--text-dim);">${v.size_mb}M</span>
      `;
      list.appendChild(row);
    });
  } catch (e) {
    console.error("Fetch pack videos error:", e);
  }
}

function loadVideoToMonitor(relPath) {
  const player = document.getElementById("main-player");
  const placeholder = document.getElementById("monitor-placeholder");
  player.src = "/stream/" + relPath;
  placeholder.style.display = "none";
  player.load();
  player.play();
  isPlaying = true;
  document.getElementById("play-pause-btn").innerText = "⏸";
}

/* 7. RENDERING & PIPER AUDITION */
async function auditionActiveScene() {
  const text = projectState.scenes[projectState.activeSceneIndex].text;
  const voice = document.getElementById("char-voice").value;
  const speed = parseFloat(document.getElementById("speech-speed").value);

  try {
    const res = await fetch("/api/tts/audition", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice, speed })
    });
    const data = await res.json();
    if (data.stream_url) {
      const audio = new Audio(data.stream_url);
      audio.play();
      alert(`Audition playing: ${data.duration.toFixed(1)}s (-16 LUFS normalized)`);
    }
  } catch (e) {
    alert("Audition error: " + e.message);
  }
}

async function startRender() {
  const title = document.getElementById("project-title").value;
  const badge = document.getElementById("render-status-badge");
  badge.innerText = "Status: Rendering...";
  badge.style.color = "var(--cyan)";

  const projectData = {
    title,
    format: projectState.format,
    voice: document.getElementById("char-voice").value,
    speed: parseFloat(document.getElementById("speech-speed").value),
    include_bumper: document.getElementById("include-bumper").checked,
    scenes: projectState.scenes
  };

  try {
    const res = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: projectData })
    });
    const data = await res.json();
    if (data.job_id) {
      pollJob(data.job_id);
    }
  } catch (e) {
    badge.innerText = "Status: Render Failed";
    badge.style.color = "var(--red)";
    alert("Render error: " + e.message);
  }
}

function pollJob(jobId) {
  const badge = document.getElementById("render-status-badge");
  if (renderPollInterval) clearInterval(renderPollInterval);

  renderPollInterval = setInterval(async () => {
    try {
      const res = await fetch("/api/job/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId })
      });
      const data = await res.json();

      if (data.status === "completed") {
        clearInterval(renderPollInterval);
        badge.innerText = "Status: Completed (Ready)";
        badge.style.color = "var(--teal)";

        loadVideoToMonitor(data.stream_url.replace('/stream/', ''));
        const dlBtn = document.getElementById("download-btn");
        dlBtn.style.display = "block";
        dlBtn.setAttribute("data-url", data.stream_url);
      } else if (data.status === "failed") {
        clearInterval(renderPollInterval);
        badge.innerText = "Status: Render Failed";
        badge.style.color = "var(--red)";
        alert("Render failed: " + data.error);
      }
    } catch (e) {
      clearInterval(renderPollInterval);
    }
  }, 1500);
}

function downloadRender() {
  const url = document.getElementById("download-btn").getAttribute("data-url");
  if (url) window.open(url, "_blank");
}

async function exportToColab() {
  const title = document.getElementById("project-title").value;
  try {
    const res = await fetch("/api/export-colab", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: { title, scenes: projectState.scenes } })
    });
    const data = await res.json();
    alert(`Staged Colab GPU Batch Job:\n${data.colab_staging_path}`);
  } catch (e) {
    alert("Colab export failed: " + e.message);
  }
}

async function saveProject() {
  const title = document.getElementById("project-title").value;
  try {
    await fetch("/api/project/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        format: projectState.format,
        scenes: projectState.scenes
      })
    });
    alert("Project spec saved successfully!");
  } catch (e) {
    alert("Save failed: " + e.message);
  }
}

/* 10. FACELESS SHORTS & REELS GENERATOR */
function setFacelessTopic(topic, theme) {
  const topEl = document.getElementById("faceless-topic");
  const thmEl = document.getElementById("faceless-theme");
  if (topEl) topEl.value = topic;
  if (thmEl && theme) thmEl.value = theme;
}

async function generateFacelessShort() {
  const topic = document.getElementById("faceless-topic")?.value.trim() || "Boiler Pressure Dropping in Sub-Zero Weather";
  const theme = document.getElementById("faceless-theme")?.value || "diy_trades";
  const btn = document.getElementById("btn-generate-faceless");
  const resCard = document.getElementById("faceless-result-card");
  const resTopic = document.getElementById("faceless-res-topic");
  const prevLink = document.getElementById("faceless-preview-link");
  const guideLink = document.getElementById("faceless-guide-link");

  if (btn) {
    btn.disabled = true;
    btn.innerText = "⏳ Generating Faceless Short & B-Roll...";
  }

  try {
    const res = await fetch("/api/faceless/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, theme })
    });
    const data = await res.json();

    if (data.ok) {
      if (resCard) resCard.style.display = "block";
      if (resTopic) resTopic.innerHTML = `<strong>Topic:</strong> ${escapeHtml(data.topic)}<br><strong>Theme:</strong> ${escapeHtml(data.theme)} &bull; £1.99 Print-Off Guide`;
      if (prevLink) prevLink.href = data.video_stream_url || `http://127.0.0.1:8790/stream/exports/trend_videos/${data.project_id}.mp4`;
      if (guideLink) guideLink.href = data.shop_url || "https://call-on.shop";

      // Also load video in center monitor
      const player = document.getElementById("main-player");
      const placeholder = document.getElementById("monitor-placeholder");
      if (player && data.video_stream_url) {
        player.src = data.video_stream_url;
        player.style.display = "block";
        if (placeholder) placeholder.style.display = "none";
        player.play().catch(() => {});
      }
    } else {
      alert("Notice: " + (data.error || "Generation complete. Check Social Hub."));
    }
  } catch (e) {
    alert("Faceless generation error: " + e.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "⚡ Generate Faceless Short & Guide";
    }
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
