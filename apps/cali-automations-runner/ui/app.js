// app.js - Cali Daily Briefing & Automations Runner Client Script

let currentBriefing = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchBriefing();
  fetchJobs();
  fetchLogs();

  // Auto-refresh logs and briefing every 30 seconds
  setInterval(() => {
    fetchLogs(true);
  }, 30000);
});

function switchTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  const btn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  const pane = document.getElementById(tabId);
  if (btn) btn.classList.add('active');
  if (pane) pane.classList.add('active');

  if (tabId === 'tab-jobs') {
    fetchJobs();
  } else if (tabId === 'tab-logs') {
    fetchLogs();
  }
}

// -------------------------------------------------------------
// 1. Daily Executive Briefing
// -------------------------------------------------------------
async function fetchBriefing() {
  try {
    const res = await fetch('/api/briefings/latest');
    const data = await res.json();
    currentBriefing = data;

    document.getElementById('briefingHeadline').textContent = data.headline || 'Executive Morning Briefing';
    document.getElementById('briefingSubtitle').textContent = `Cross-departmental telemetry compiled for Antony Brown &bull; ${data.date || 'Today'}`;
    document.getElementById('briefingContent').innerHTML = data.summary_html || '<div class="empty-state">No briefing content available.</div>';
    document.getElementById('ttsScriptContent').textContent = data.tts_script || 'No TTS script generated.';

    document.getElementById('kpiBriefingDate').textContent = data.date || 'Today';
    document.getElementById('kpiBriefingTime').textContent = `Compiled at ${new Date(data.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

    fetchArchiveList();
  } catch (err) {
    console.error('Error fetching briefing:', err);
    document.getElementById('briefingContent').innerHTML = `<div class="empty-state" style="color:var(--rose)">Failed to load briefing: ${err.message}</div>`;
  }
}

async function compileBriefing() {
  const btn = document.getElementById('generateBtn');
  btn.innerHTML = '<span>⚡ Compiling Briefing...</span>';
  btn.disabled = true;

  try {
    const res = await fetch('/api/briefings/generate', { method: 'POST' });
    const data = await res.json();
    showToast(`Compiled fresh briefing for ${data.date}!`, 'success');
    fetchBriefing();
    fetchLogs();
  } catch (err) {
    showToast(`Compilation failed: ${err.message}`, 'error');
  } finally {
    btn.innerHTML = '<span class="icon">⚡</span> Compile Fresh Briefing';
    btn.disabled = false;
  }
}

async function fetchArchiveList() {
  try {
    const res = await fetch('/api/briefings');
    const data = await res.json();
    const container = document.getElementById('briefingArchiveList');
    const briefings = data.briefings || [];

    if (briefings.length === 0) {
      container.innerHTML = '<div class="empty-state">No historical briefings found.</div>';
      return;
    }

    container.innerHTML = briefings.map(b => `
      <div class="archive-item" onclick="loadArchivedBriefing('${escapeHtml(b.date_str)}')">
        <div class="archive-date">${escapeHtml(b.date_str)}</div>
        <div class="archive-title">${escapeHtml(b.headline)}</div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error fetching archive:', err);
  }
}

function copyBriefingText() {
  if (currentBriefing && currentBriefing.summary_text) {
    navigator.clipboard.writeText(currentBriefing.summary_text);
    showToast('Briefing text copied to clipboard!', 'success');
  }
}

function copyTtsScript() {
  if (currentBriefing && currentBriefing.tts_script) {
    navigator.clipboard.writeText(currentBriefing.tts_script);
    showToast('Piper TTS voice script copied!', 'success');
  }
}

// -------------------------------------------------------------
// 2. Scheduled Automations
// -------------------------------------------------------------
async function fetchJobs() {
  try {
    const res = await fetch('/api/automations/jobs');
    const data = await res.json();
    const jobs = data.jobs || [];

    const activeCount = jobs.filter(j => j.enabled).length;
    document.getElementById('kpiActiveJobs').textContent = activeCount;
    document.getElementById('jobCountBadge').textContent = jobs.length;

    const container = document.getElementById('jobsGrid');
    if (jobs.length === 0) {
      container.innerHTML = '<div class="empty-state">No scheduled jobs registered.</div>';
      return;
    }

    container.innerHTML = jobs.map(j => {
      const isEnabled = j.enabled === 1;
      const lastRunStr = j.last_run ? new Date(j.last_run * 1000).toLocaleString('en-GB') : 'Never';
      const statusClass = j.last_status === 'SUCCESS' ? 'status-active' : (j.last_status === 'READY' ? 'panel-badge' : 'tag-m');

      return `
        <div class="job-card">
          <div>
            <div class="job-header">
              <span class="job-category">${escapeHtml(j.category)}</span>
              <span class="status-pill ${statusClass}" style="font-size:0.7rem; padding: 0.15rem 0.5rem;">
                ${escapeHtml(j.last_status || 'READY')}
              </span>
            </div>
            <h4 class="job-title">${escapeHtml(j.name)}</h4>
            <div class="job-schedule">⏰ ${escapeHtml(j.schedule_human)}</div>
            <p class="job-desc">${escapeHtml(j.description)}</p>
          </div>

          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem; font-family: var(--font-mono);">
              Last Run: ${lastRunStr}
            </div>
            <div class="job-footer">
              <label class="toggle-switch">
                <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="toggleJob('${j.id}', this.checked)">
                <span>${isEnabled ? 'Enabled' : 'Paused'}</span>
              </label>

              <button class="btn btn-secondary btn-sm" onclick="runJob('${j.id}')">
                <span>▶ Run Now</span>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching jobs:', err);
  }
}

async function toggleJob(jobId, enabled) {
  try {
    const res = await fetch('/api/automations/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, enabled })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`Automation ${jobId} ${enabled ? 'enabled' : 'paused'}`, 'success');
      fetchJobs();
    }
  } catch (err) {
    showToast(`Failed to toggle: ${err.message}`, 'error');
  }
}

async function runJob(jobId) {
  showToast(`Triggering ${jobId}...`, 'info');
  try {
    const res = await fetch('/api/automations/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`Completed in ${data.execution_time_ms}ms: ${data.output}`, 'success');
      fetchJobs();
      fetchLogs();
      if (jobId === 'morning_briefing') {
        fetchBriefing();
      }
    } else {
      showToast(`Job failed: ${data.output}`, 'error');
    }
  } catch (err) {
    showToast(`Execution error: ${err.message}`, 'error');
  }
}

// -------------------------------------------------------------
// 3. Execution Logs & Receipts
// -------------------------------------------------------------
async function fetchLogs(silent = false) {
  try {
    const res = await fetch('/api/automations/logs');
    const data = await res.json();
    const logs = data.logs || [];

    const successCount = logs.filter(l => l.status === 'SUCCESS').length;
    const rate = logs.length > 0 ? Math.round((successCount / logs.length) * 100) : 100;
    document.getElementById('kpiSuccessRate').textContent = `${rate}%`;
    document.getElementById('kpiTotalRuns').textContent = `${logs.length} total runs recorded`;

    const tbody = document.getElementById('logsTableBody');
    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No execution logs recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>#${l.id}</td>
        <td><strong>${escapeHtml(l.job_name)}</strong></td>
        <td>
          <span class="status-pill ${l.status === 'SUCCESS' ? 'status-active' : 'tag-m'}" style="font-size:0.7rem; padding: 0.15rem 0.5rem;">
            ${escapeHtml(l.status)}
          </span>
        </td>
        <td>${escapeHtml(l.output)}</td>
        <td>${l.execution_time_ms} ms</td>
        <td>${new Date(l.timestamp * 1000).toLocaleString('en-GB')}</td>
      </tr>
    `).join('');

  } catch (err) {
    if (!silent) console.error('Error fetching logs:', err);
  }
}

// -------------------------------------------------------------
// Utilities
// -------------------------------------------------------------
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4500);
}

