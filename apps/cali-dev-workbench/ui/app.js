// app.js - Cali Dev & Code Release Workbench Client Script

let activeFile = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchDevData();
  scanSecrets();
  fetchPatches();
  fetchReceipts();
  
  // Auto-refresh every 20 seconds
  setInterval(() => {
    fetchDevData(true);
  }, 20000);
});

function switchTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  const btn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  const pane = document.getElementById(tabId);
  if (btn) btn.classList.add('active');
  if (pane) pane.classList.add('active');

  if (tabId === 'tab-shield') {
    scanSecrets();
  } else if (tabId === 'tab-patches') {
    fetchPatches();
  } else if (tabId === 'tab-receipts') {
    fetchReceipts();
  }
}

// -------------------------------------------------------------
// 1. Fetch Git Data (Working Tree, Status, Commits)
// -------------------------------------------------------------
async function fetchDevData(silent = false) {
  const refreshBtn = document.getElementById('refreshBtn');
  if (!silent && refreshBtn) refreshBtn.classList.add('loading');

  try {
    const res = await fetch('/api/dev/git');
    const data = await res.json();

    // Branch & Status
    document.getElementById('branchName').textContent = data.branch || 'master';
    const statusPill = document.getElementById('repoStatusPill');
    const statusText = document.getElementById('repoStatusText');

    if (data.is_clean) {
      statusPill.className = 'status-pill status-clean';
      statusText.textContent = 'Working Tree Clean';
    } else {
      statusPill.className = 'status-pill status-dirty';
      statusText.textContent = `${data.modified_count} Modified Files`;
    }

    // KPIs
    document.getElementById('kpiModified').textContent = data.modified_count || 0;
    document.getElementById('kpiUntracked').textContent = `${data.untracked_count || 0} untracked files`;
    document.getElementById('modifiedCountBadge').textContent = `${data.modified_count} changed`;

    // Render Modified & Untracked Files List
    renderFileList(data.modified_files || [], data.untracked_files || []);

    // Render Recent Commits
    renderRecentCommits(data.recent_commits || []);

    // If no active file diff loaded yet and files exist, load first file
    if (!activeFile && data.modified_files && data.modified_files.length > 0) {
      loadDiff(data.modified_files[0].file);
    } else if (!activeFile) {
      loadDiff(null);
    }

  } catch (err) {
    console.error('Error fetching git status:', err);
    if (!silent) showToast('Failed to connect to Dev Workbench server', 'error');
  } finally {
    if (!silent && refreshBtn) refreshBtn.classList.remove('loading');
  }
}

function renderFileList(modified, untracked) {
  const container = document.getElementById('modifiedFileList');
  if (modified.length === 0 && untracked.length === 0) {
    container.innerHTML = '<div class="empty-state">No changes in working tree</div>';
    return;
  }

  let html = '';
  modified.forEach(item => {
    const isActive = activeFile === item.file ? 'active' : '';
    html += `
      <div class="file-item ${isActive}" onclick="loadDiff('${escapeHtml(item.file)}')">
        <span>${escapeHtml(item.file)}</span>
        <span class="file-status-tag tag-m">${escapeHtml(item.status || 'M')}</span>
      </div>
    `;
  });

  untracked.forEach(file => {
    const isActive = activeFile === file ? 'active' : '';
    html += `
      <div class="file-item ${isActive}" onclick="loadDiff('${escapeHtml(file)}')">
        <span>${escapeHtml(file)}</span>
        <span class="file-status-tag tag-untracked">??</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderRecentCommits(commits) {
  const container = document.getElementById('recentCommitList');
  if (!commits || commits.length === 0) {
    container.innerHTML = '<div class="empty-state">No recent commits</div>';
    return;
  }

  container.innerHTML = commits.map(c => `
    <div class="commit-item">
      <div class="commit-head">
        <span class="commit-hash">${escapeHtml(c.hash)}</span>
        <span class="commit-time">${escapeHtml(c.relative_time)}</span>
      </div>
      <div class="commit-msg" title="${escapeHtml(c.subject)}">${escapeHtml(c.subject)}</div>
    </div>
  `).join('');
}

// -------------------------------------------------------------
// 2. Diff Viewer
// -------------------------------------------------------------
async function loadDiff(filePath) {
  activeFile = filePath;

  // Highlight in file list
  document.querySelectorAll('.file-item').forEach(el => {
    el.classList.remove('active');
  });

  const diffTitle = document.getElementById('currentDiffTitle');
  const diffFile = document.getElementById('currentDiffFile');
  const diffContent = document.getElementById('diffContent');

  if (filePath) {
    diffTitle.textContent = `File Diff: ${filePath.split('/').pop()}`;
    diffFile.textContent = filePath;
  } else {
    diffTitle.textContent = `Full Tree Working Diff`;
    diffFile.textContent = `All uncommitted changes in D:/The Cali Project`;
  }

  diffContent.innerHTML = '<code>Loading diff...</code>';

  try {
    const url = filePath ? `/api/dev/diff?file=${encodeURIComponent(filePath)}` : '/api/dev/diff';
    const res = await fetch(url);
    const data = await res.json();

    const rawDiff = data.diff || '(No uncommitted diff)';
    diffContent.innerHTML = formatDiffSyntax(rawDiff);

  } catch (err) {
    diffContent.innerHTML = `<code style="color:var(--rose)">Failed to fetch diff: ${err.message}</code>`;
  }
}

function formatDiffSyntax(diffText) {
  const lines = diffText.split('\n');
  return lines.map(line => {
    const escaped = escapeHtml(line);
    if (line.startsWith('+++') || line.startsWith('---')) {
      return `<span style="color: var(--cyan); font-weight: bold;">${escaped}</span>`;
    } else if (line.startsWith('+')) {
      return `<span class="diff-line-add">${escaped}</span>`;
    } else if (line.startsWith('-')) {
      return `<span class="diff-line-del">${escaped}</span>`;
    } else if (line.startsWith('@@')) {
      return `<span class="diff-line-hunk">${escaped}</span>`;
    }
    return `<span>${escaped}</span>`;
  }).join('\n');
}

// -------------------------------------------------------------
// 3. Secret & Credential Leak Shield
// -------------------------------------------------------------
async function scanSecrets() {
  try {
    const res = await fetch('/api/dev/security');
    const data = await res.json();

    const kpiLeaks = document.getElementById('kpiLeaks');
    const kpiCard = document.getElementById('kpiLeakCard');
    const kpiStatus = document.getElementById('kpiLeakStatus');
    const shieldBox = document.getElementById('shieldStatusBox');
    const shieldIcon = document.getElementById('shieldIcon');
    const shieldHeading = document.getElementById('shieldHeading');
    const shieldDetail = document.getElementById('shieldDetail');
    const tbody = document.getElementById('leakTableBody');

    kpiLeaks.textContent = data.total_leaks;

    if (data.clean) {
      kpiLeaks.className = 'kpi-value value-emerald';
      kpiStatus.textContent = `Live Shield Active (0 Leaks / ${data.files_scanned} files)`;
      shieldBox.className = 'shield-status-box';
      shieldIcon.textContent = '🛡️';
      shieldHeading.textContent = 'Source Tree 100% Clean';
      shieldDetail.textContent = `Scanned ${data.files_scanned} modified and staged files. No live API tokens, Stripe keys, or private keys detected.`;
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No credential leaks detected. Safe for commits and staging.</td></tr>';
    } else {
      kpiLeaks.className = 'kpi-value value-rose';
      kpiStatus.textContent = `CRITICAL: ${data.total_leaks} Secret Leaks Flagged!`;
      shieldBox.className = 'shield-status-box has-leaks';
      shieldIcon.textContent = '🚨';
      shieldHeading.textContent = `CRITICAL ALERT: ${data.total_leaks} Credential Leaks Found!`;
      shieldDetail.textContent = `Immediate remediation required. Hardcoded credentials detected in working files before commit.`;

      tbody.innerHTML = data.leaks.map(leak => `
        <tr>
          <td><span class="file-status-tag tag-m" style="background: rgba(248, 113, 113, 0.2); color: var(--rose);">FLAGGED</span></td>
          <td>${escapeHtml(leak.file)}</td>
          <td>${leak.line}</td>
          <td><strong style="color: var(--amber);">${escapeHtml(leak.leak_type)}</strong></td>
          <td><code>${escapeHtml(leak.preview)}</code></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error scanning secrets:', err);
  }
}

// -------------------------------------------------------------
// 4. Safe Patch Proposal & Review Queue
// -------------------------------------------------------------
async function fetchPatches() {
  try {
    const res = await fetch('/api/dev/patches');
    const data = await res.json();
    const patches = data.patches || [];

    const pending = patches.filter(p => p.status === 'pending');
    document.getElementById('kpiPatches').textContent = patches.length;
    document.getElementById('kpiPendingPatches').textContent = `${pending.length} pending review`;
    document.getElementById('tabPatchBadge').textContent = pending.length;

    renderPatches(patches);
  } catch (err) {
    console.error('Error fetching patches:', err);
  }
}

function renderPatches(patches) {
  const container = document.getElementById('patchesContainer');
  if (patches.length === 0) {
    container.innerHTML = '<div class="empty-state">No patch proposals in queue. Click "+ New Patch Proposal" to create one.</div>';
    return;
  }

  container.innerHTML = patches.map(p => {
    const isPending = p.status === 'pending';
    const statusClass = p.status;
    const dateStr = new Date(p.created_at * 1000).toLocaleString('en-GB');

    return `
      <div class="patch-card ${statusClass}">
        <div class="patch-header">
          <div>
            <div class="patch-title">#${p.id} - ${escapeHtml(p.description)}</div>
            <div class="patch-meta">
              Target: <strong>${escapeHtml(p.file_path)}</strong> &bull; Author: ${escapeHtml(p.author)} &bull; Created: ${dateStr}
            </div>
          </div>
          <div>
            <span class="file-status-tag ${p.status === 'pending' ? 'tag-m' : (p.status === 'applied' ? 'status-clean' : 'tag-untracked')}">
              ${p.status.toUpperCase()}
            </span>
          </div>
        </div>

        <div class="patch-diff-preview">
          <div class="diff-block">
            <h5>Existing Code (Target)</h5>
            <code>${escapeHtml(p.old_text)}</code>
          </div>
          <div class="diff-block" style="border-color: rgba(52, 211, 153, 0.4);">
            <h5 style="color: var(--emerald);">Replacement Code</h5>
            <code>${escapeHtml(p.new_text)}</code>
          </div>
        </div>

        ${isPending ? `
          <div class="patch-actions">
            <button class="btn btn-emerald btn-sm" onclick="applyPatch(${p.id})">
              <span>✓ Approve &amp; Apply Live</span>
            </button>
            <button class="btn btn-secondary btn-sm" onclick="rejectPatch(${p.id})">
              <span>✕ Reject</span>
            </button>
          </div>
        ` : `
          <div class="patch-meta">
            ${p.status === 'applied' ? `Applied at: ${new Date(p.applied_at * 1000).toLocaleString('en-GB')}` : 'Proposal rejected.'}
          </div>
        `}
      </div>
    `;
  }).join('');
}

async function applyPatch(id) {
  if (!confirm(`Are you sure you want to apply Patch #${id} directly to disk?`)) return;

  try {
    const res = await fetch('/api/dev/patches/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(data.message, 'success');
      fetchPatches();
      fetchDevData();
      fetchReceipts();
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed to apply patch: ${err.message}`, 'error');
  }
}

async function rejectPatch(id) {
  try {
    const res = await fetch('/api/dev/patches/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    showToast(data.message, 'success');
    fetchPatches();
  } catch (err) {
    showToast(`Failed to reject patch: ${err.message}`, 'error');
  }
}

function openNewPatchModal() {
  document.getElementById('patchModal').style.display = 'flex';
  if (activeFile) {
    document.getElementById('patchFilePath').value = activeFile;
  }
}

function closeNewPatchModal() {
  document.getElementById('patchModal').style.display = 'none';
  document.getElementById('patchForm').reset();
}

async function submitPatchProposal(event) {
  event.preventDefault();
  const filePath = document.getElementById('patchFilePath').value.trim();
  const description = document.getElementById('patchDescription').value.trim();
  const oldText = document.getElementById('patchOldText').value;
  const newText = document.getElementById('patchNewText').value;

  try {
    const res = await fetch('/api/dev/patches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: filePath,
        description,
        old_text: oldText,
        new_text: newText,
        author: 'Antony Brown'
      })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(data.message, 'success');
      closeNewPatchModal();
      fetchPatches();
      switchTab('tab-patches');
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed to create proposal: ${err.message}`, 'error');
  }
}

// -------------------------------------------------------------
// 5. Deployment Receipts
// -------------------------------------------------------------
async function fetchReceipts() {
  try {
    const res = await fetch('/api/dev/receipts');
    const data = await res.json();
    const receipts = data.receipts || [];

    document.getElementById('kpiReceipts').textContent = receipts.length;
    if (receipts.length > 0) {
      document.getElementById('kpiLastReceipt').textContent = `Last: ${receipts[0].release_tag}`;
    }

    const tbody = document.getElementById('receiptsTableBody');
    if (receipts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No deployment receipts recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = receipts.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td><strong style="color: var(--cyan);">${escapeHtml(r.release_tag)}</strong></td>
        <td>${escapeHtml(r.action)}</td>
        <td><code>${escapeHtml(r.file_path)}</code></td>
        <td><span class="file-status-tag status-clean">${escapeHtml(r.status)}</span></td>
        <td>${escapeHtml(r.details || '-')}</td>
        <td>${new Date(r.timestamp * 1000).toLocaleString('en-GB')}</td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Error fetching receipts:', err);
  }
}

// -------------------------------------------------------------
// Utility Functions
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
  }, 4000);
}

