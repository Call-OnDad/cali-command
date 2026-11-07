/**
 * vision.js - Sovereign Live Vision & Continuous Audio/Video Session for Cali
 * Connects camera + microphone to Cali (Gemini Live via CT130 vision bridge).
 */

(function() {
  let LV = null;
  let camFacing = 'user';

  function getBaseUrl() {
    if (typeof API_BASE !== 'undefined' && API_BASE) return API_BASE;
    if (window.location.protocol === 'tauri:' || window.location.hostname === 'tauri.localhost') {
      return 'http://192.168.0.60:8800';
    }
    return '';
  }

  function showToast(msg) {
    console.log('[Live Vision]', msg);
    const existing = document.getElementById('lv-toast');
    if (existing) existing.remove();
    const t = document.createElement('div');
    t.id = 'lv-toast';
    t.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#1e293b;color:#38bdf8;padding:10px 20px;border-radius:8px;border:1px solid rgba(56,189,248,0.4);z-index:9999999;box-shadow:0 10px 25px rgba(0,0,0,0.5);font-size:13px;font-weight:600;';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => { if (t.parentNode) t.remove(); }, 3500);
  }

  function overlay() {
    let o = document.getElementById('lv-overlay');
    if (o) return o;
    o = document.createElement('div');
    o.id = 'lv-overlay';
    o.className = 'lv-overlay';
    o.innerHTML = `
      <div class="lv-stage">
        <div class="lv-video" id="lv-video"></div>
        <div class="lv-reply" id="lv-reply"></div>
        <div class="lv-bar">
          <button class="lv-btn" id="lv-mic" title="Mute microphone">🎙️</button>
          <button class="lv-btn" id="lv-flip" title="Switch camera">🔄</button>
          <button class="lv-btn" id="lv-snap" title="Snapshot: analyze with Cali Vision">📸</button>
          <button class="lv-btn lv-end" id="lv-end" title="End Session">✕ End</button>
        </div>
      </div>`;
    document.body.appendChild(o);
    o.querySelector('#lv-end').onclick = closeLiveVision;
    o.querySelector('#lv-flip').onclick = flipCamera;
    o.querySelector('#lv-mic').onclick = toggleMic;
    o.querySelector('#lv-snap').onclick = snapshotFrame;
    return o;
  }

  function reply(who, body, thinking) {
    const el = document.getElementById('lv-reply');
    if (!el) return;
    el.classList.add('show');
    el.innerHTML = '';
    const q = document.createElement('div');
    q.className = 'lv-q';
    q.textContent = who;
    el.appendChild(q);
    const b = document.createElement('div');
    b.className = thinking ? 'lv-thinking' : '';
    b.textContent = body;
    el.appendChild(b);
  }

  async function openLiveVision() {
    if (LV) return;
    if (!window.GeminiLiveAPI || !window.VideoStreamer) {
      showToast('Live Vision streaming libraries not ready.');
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showToast('This device has no accessible camera or microphone.');
      return;
    }
    const o = overlay();
    o.classList.add('open');
    reply('Cali', 'Connecting to Sovereign Vision…', true);

    try {
      const wrap = document.getElementById('lv-video');
      wrap.innerHTML = '';
      const video = new window.VideoStreamer(null);
      const audio = new window.AudioStreamer(null);

      const apiBase = getBaseUrl();
      const tokRes = await fetch(`${apiBase}/api/vision/token`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const tok = await tokRes.json();
      if (tok.error) throw new Error(tok.error);

      await Promise.all([
        video.start({ fps: 1, facingMode: camFacing, width: 640, height: 360, quality: 0.65, container: wrap }),
        audio.start()
      ]);

      const client = new window.GeminiLiveAPI(tok.ws_url);
      video.client = client;
      audio.client = client;
      if (client.setVoice) client.setVoice('Kore');

      client.setSystemInstructions("You are Cali, Antony Brown's Sovereign Executive AI Chief of Staff, now seeing and hearing him live through his device camera. Be concise, executive, and conversational. Describe what is relevant, answer what he asks about what you see. UK English, sharp, warm, executive.");
      client.setResponseModalities(['AUDIO']);
      client.setInputAudioTranscription(true);
      client.setOutputAudioTranscription(true);

      const player = new window.AudioPlayer();
      let inT = '', outT = '';

      client.onOpen = () => reply('Cali', 'Watching and listening live…', true);
      client.onClose = () => {
        if (LV) {
          closeLiveVision();
          showToast('Live Vision session ended.');
        }
      };
      client.onError = m => reply('Cali', 'Connection notice: ' + m, false);
      client.onReceiveResponse = r => {
        if (r.type === 'AUDIO') {
          player.play(r.data).catch(() => {});
        } else if (r.type === 'INPUT_TRANSCRIPTION') {
          inT = r.data.text;
          reply('Antony', inT, !r.data.finished);
        } else if (r.type === 'OUTPUT_TRANSCRIPTION') {
          outT = r.data.text;
          reply('Cali', outT, !r.data.finished);
        } else if (r.type === 'INTERRUPTED') {
          player.interrupt();
        } else if (r.type === 'TURN_COMPLETE' && LV) {
          LV.turns++;
          if (inT.trim()) LV.transcript.push({ role: 'user', text: inT.trim() });
          if (outT.trim()) LV.transcript.push({ role: 'assistant', text: outT.trim() });
          inT = '';
          outT = '';
        }
      };

      client.connect();
      LV = { client, audio, video, player, started: Date.now(), turns: 0, transcript: [] };
    } catch (e) {
      reply('Cali', 'Live Vision unavailable: ' + e.message, false);
      showToast('Live Vision error: ' + e.message);
      setTimeout(closeLiveVision, 3000);
    }
  }

  async function snapshotFrame() {
    if (!LV || !LV.video || !LV.video.takeSnapshot) {
      showToast('No camera frame ready yet.');
      return;
    }
    const btn = document.getElementById('lv-snap');
    const was = btn.textContent;
    btn.textContent = '…';
    btn.disabled = true;
    try {
      const dataUrl = LV.video.takeSnapshot();
      const blob = await (await fetch(dataUrl)).blob();
      const fd = new FormData();
      fd.append('file', blob, `snapshot-${Date.now()}.jpg`);
      const apiBase = getBaseUrl();
      const r = await (await fetch(`${apiBase}/api/vision/snapshot`, { method: 'POST', body: fd })).json();
      showToast(r.description || r.vendor || 'Frame captured and analyzed by Cali Vision.');
    } catch (e) {
      showToast('Snapshot failed: ' + e.message);
    } finally {
      btn.textContent = was;
      btn.disabled = false;
    }
  }

  function closeLiveVision() {
    if (LV) {
      const { client, audio, video, player, started, turns, transcript } = LV;
      try { audio.stop(); } catch {}
      try { video.stop(); } catch {}
      try { player.destroy(); } catch {}
      try { client.disconnect(); } catch {}
      const apiBase = getBaseUrl();
      fetch(`${apiBase}/api/vision/session-log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'ui-' + started,
          started_at: new Date(started).toISOString(),
          ended_at: new Date().toISOString(),
          query_count: turns,
          summary: 'Executive live vision session'
        })
      }).catch(() => {});
      if (transcript && transcript.length) {
        fetch(`${apiBase}/api/vision/save-transcript`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transcript })
        }).catch(() => {});
      }
      LV = null;
    }
    const o = document.getElementById('lv-overlay');
    if (o) o.classList.remove('open');
    const w = document.getElementById('lv-video');
    if (w) w.innerHTML = '';
  }

  async function flipCamera() {
    if (!LV) return;
    camFacing = camFacing === 'user' ? 'environment' : 'user';
    LV.video.stop();
    const wrap = document.getElementById('lv-video');
    wrap.innerHTML = '';
    await LV.video.start({ fps: 1, facingMode: camFacing, width: 640, height: 360, quality: 0.65, container: wrap });
  }

  function toggleMic() {
    if (!LV) return;
    const btn = document.getElementById('lv-mic');
    if (LV.audio.isStreaming) {
      LV.audio.stop();
      btn.classList.add('active');
      btn.textContent = '🔇';
      btn.title = 'Unmute microphone';
    } else {
      LV.audio.start();
      btn.classList.remove('active');
      btn.textContent = '🎙️';
      btn.title = 'Mute microphone';
    }
  }

  // Export globally
  window.openLiveVision = openLiveVision;
  window.closeLiveVision = closeLiveVision;
})();
