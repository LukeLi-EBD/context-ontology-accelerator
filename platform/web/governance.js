'use strict';

/*
 * Governance console. Every write goes through /governance/* which reuses the
 * ontology service (same gates as the CLI). The UI never hides a failed gate:
 * structured blockers and provider codes are rendered verbatim.
 */

const gov = { proposals: [], versions: [], pointer: null, lastPlan: null, lastInspect: null };

function govActor() {
  const input = document.getElementById('actor');
  return input ? (input.value || '').trim() : '';
}

function govBody(extra) {
  return Object.assign({ actor: govActor() }, extra || {});
}

function govPost(path, extra) {
  return api(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(govBody(extra)),
  });
}

function govVersionLabel(version) {
  const tag = version.id === (gov.pointer || {}).versionId ? ' · 当前' : '';
  return `${version.id} · ${version.semver} · ${version.status}${tag}`;
}

function govVersionOptions() {
  return gov.versions.slice().reverse()
    .map((version) => `<option value="${esc(version.id)}">${esc(govVersionLabel(version))}</option>`)
    .join('');
}

function govStatusBadge(status) {
  const kind = status === 'published' ? 'ok'
    : status === 'rejected' ? 'bad'
      : status === 'approved' ? 'ok' : 'warn';
  return badge(status || '-', kind);
}

function confirmTwice(first, second) {
  if (!window.confirm(first)) return false;
  return window.confirm(second);
}

function impactText(impact) {
  const data = impact || {};
  return [
    `新增三元组 ${data.addedTriples || 0}`,
    `删除三元组 ${data.removedTriples || 0}`,
    `breaking 项 ${data.breakingItems || 0}`,
    `受影响实例 ${data.removedClassInstances || 0}`,
    `类变更 ${(data.addedClasses || 0) + (data.removedClasses || 0)}`,
    `属性变更 ${(data.addedProperties || 0) + (data.removedProperties || 0)}`,
  ].join('，');
}

function gateTable(gates) {
  const entries = Object.entries(gates || {});
  if (!entries.length) return empty('没有 gate 结果');
  const rows = entries.map(([name, gate]) => {
    const detail = gate.code
      ? `${esc(gate.code)} ${esc(gate.message || '')}`
      : esc(JSON.stringify(gate));
    return `<tr>
      <td class="mono">${esc(name)}</td>
      <td>${gate.ok ? badge('PASS', 'ok') : badge('FAIL', 'bad')}</td>
      <td class="mono">${detail}</td>
    </tr>`;
  }).join('');
  return `<table><thead><tr><th>gate</th><th>结果</th><th>原始信息</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function blockerTable(blockers) {
  if (!blockers || !blockers.length) return '';
  const rows = blockers.map((blocker) => `<tr>
      <td class="mono">${esc(blocker.gate)}</td>
      <td class="mono">${esc(blocker.code)}</td>
      <td>${esc(blocker.message)}</td>
    </tr>`).join('');
  return `<h3>阻断项（原样透出）</h3>
    <table><thead><tr><th>gate</th><th>错误码</th><th>消息</th></tr></thead><tbody>${rows}</tbody></table>`;
}

/* ---- shared data ------------------------------------------------------- */

async function loadGovernanceVersions() {
  const data = await api('/ontology/versions');
  gov.versions = data.items || [];
  gov.pointer = data.pointer || {};
  const options = govVersionOptions();
  ['publish-version', 'rollback-version'].forEach((id) => {
    const select = document.getElementById(id);
    if (select) select.innerHTML = options;
  });
}

async function loadProposals() {
  const target = document.getElementById('proposal-list');
  try {
    const data = await api('/governance/proposals?limit=30');
    gov.proposals = data.items || [];
    gov.pointer = data.current || gov.pointer;
    if (!gov.proposals.length) {
      target.innerHTML = empty('暂无提案');
      return;
    }
    const rows = gov.proposals.map((item) => `<tr>
        <td class="mono">${esc(item.proposalId)}</td>
        <td class="mono">${esc(item.versionId)}</td>
        <td>${govStatusBadge(item.status)}</td>
        <td>${govStatusBadge(item.versionStatus || '-')}</td>
        <td>${item.breaking ? badge('breaking', 'bad') : badge('non-breaking', 'ok')}</td>
        <td>${esc(item.changeSummary || '')}</td>
        <td><button type="button" data-detail="${esc(item.proposalId)}">详情</button></td>
      </tr>`).join('');
    target.innerHTML = `<p class="sub">共 ${data.count} 条，显示最近 ${data.returned} 条</p>
      <table><thead><tr><th>proposal</th><th>version</th><th>提案状态</th><th>版本状态</th><th>breaking</th><th>说明</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
    target.querySelectorAll('[data-detail]').forEach((button) => {
      button.addEventListener('click', () => showProposalDetail(button.dataset.detail));
    });
  } catch (error) {
    showError(target, error);
  }
}

async function showProposalDetail(proposalId) {
  const target = document.getElementById('proposal-detail');
  target.className = '';
  try {
    const data = await api(`/governance/proposals/${encodeURIComponent(proposalId)}`);
    target.innerHTML = `
      <h3>${esc(proposalId)} · 版本 ${esc(data.proposal.versionId)}（${esc(data.versionStatus)}）</h3>
      <p>${esc(data.proposal.changeSummary || '')}</p>
      <p class="sub">impact：${esc(impactText(data.impact))}</p>
      <table><thead><tr><th>字段</th><th>值</th></tr></thead><tbody>
        <tr><td>breaking</td><td>${data.proposal.breaking ? badge('true', 'bad') : badge('false', 'ok')}</td></tr>
        <tr><td>against</td><td class="mono">${esc(data.proposal.againstVersion || '')}</td></tr>
        <tr><td>approvedBy</td><td class="mono">${esc(data.proposal.approvedBy || '')}</td></tr>
        <tr><td>当前指针</td><td class="mono">${esc((data.current || {}).versionId || '')}</td></tr>
      </tbody></table>
      <h3>diff</h3>
      ${data.diff && Object.keys(data.diff).length ? `<pre class="mono">${esc(JSON.stringify(data.diff, null, 2))}</pre>` : empty('diff 为空')}`;
  } catch (error) {
    showError(target, error);
  }
}

async function loadApprovals() {
  const target = document.getElementById('approval-list');
  try {
    const data = await api('/governance/proposals?status=proposed&limit=30');
    const pending = (data.items || []).filter((item) => item.versionStatus !== 'rejected');
    if (!pending.length) {
      target.innerHTML = empty('没有待审批提案');
      return;
    }
    const rows = pending.map((item) => `<tr>
        <td class="mono">${esc(item.proposalId)}</td>
        <td class="mono">${esc(item.versionId)}</td>
        <td>${item.breaking ? badge('breaking', 'bad') : badge('non-breaking', 'ok')}</td>
        <td>${esc(item.changeSummary || '')}</td>
        <td>
          <button type="button" data-approve="${esc(item.proposalId)}">approve</button>
          <button type="button" class="danger" data-reject="${esc(item.proposalId)}">reject</button>
        </td>
      </tr>`).join('');
    target.innerHTML = `<table><thead><tr><th>proposal</th><th>version</th><th>breaking</th><th>说明</th><th>操作（理由必填）</th></tr></thead><tbody>${rows}</tbody></table>`;
    target.querySelectorAll('[data-approve]').forEach((button) => {
      button.addEventListener('click', () => approveProposal(button.dataset.approve));
    });
    target.querySelectorAll('[data-reject]').forEach((button) => {
      button.addEventListener('click', () => rejectProposal(button.dataset.reject));
    });
  } catch (error) {
    showError(target, error);
  }
}

async function approveProposal(proposalId) {
  const reason = window.prompt(`审批通过 ${proposalId} 的理由（必填）`);
  if (reason === null) return;
  if (!reason.trim()) {
    showError(document.getElementById('approval-list'), 'E_GOVERNANCE_REASON_REQUIRED：理由必填');
    return;
  }
  try {
    const result = await govPost(`/governance/proposals/${encodeURIComponent(proposalId)}/approve`, { reason });
    await loadProposals();
    await loadApprovals();
    await loadGovernanceVersions();
    document.getElementById('proposal-detail').className = '';
    document.getElementById('proposal-detail').innerHTML =
      `<div class="ok-box">approved ${esc(proposalId)} by ${esc(result.approvedBy || govActor())}</div>`;
  } catch (error) {
    showError(document.getElementById('approval-list'), error);
  }
}

async function rejectProposal(proposalId) {
  const reason = window.prompt(`驳回 ${proposalId} 的理由（必填）`);
  if (reason === null) return;
  if (!reason.trim()) {
    showError(document.getElementById('approval-list'), 'E_GOVERNANCE_REASON_REQUIRED：理由必填');
    return;
  }
  try {
    const result = await govPost(`/governance/proposals/${encodeURIComponent(proposalId)}/reject`, { reason });
    await loadProposals();
    await loadApprovals();
    await loadGovernanceVersions();
    document.getElementById('proposal-detail').className = '';
    document.getElementById('proposal-detail').innerHTML =
      `<div class="warn-box">rejected ${esc(proposalId)}：版本 ${esc(result.versionId)} → ${esc(result.versionStatus)}</div>`;
  } catch (error) {
    showError(document.getElementById('approval-list'), error);
  }
}

/* ---- publish ---------------------------------------------------------- */

async function loadPublishProposals() {
  const select = document.getElementById('publish-proposal');
  const versionId = document.getElementById('publish-version').value;
  select.innerHTML = '<option value="">（不指定提案，走隐式发布）</option>';
  if (!versionId) return;
  try {
    const data = await api(`/governance/proposals?versionId=${encodeURIComponent(versionId)}&limit=30`);
    const usable = (data.items || []).filter((item) => item.status === 'approved');
    select.innerHTML = '<option value="">（不指定提案）</option>' + usable
      .map((item) => `<option value="${esc(item.proposalId)}">${esc(item.proposalId)} · ${esc(item.status)}</option>`)
      .join('');
  } catch (error) {
    select.innerHTML = `<option value="">加载提案失败：${esc(error.message)}</option>`;
  }
}

function publishPayload(dryRun) {
  return {
    versionId: document.getElementById('publish-version').value,
    proposalId: document.getElementById('publish-proposal').value || undefined,
    acknowledgeBreaking: document.getElementById('publish-ack').checked,
    publishExisting: document.getElementById('publish-existing').checked,
    dryRun,
  };
}

async function publishDryRun() {
  const target = document.getElementById('publish-gates');
  const button = document.getElementById('publish-dryrun');
  setBusy(button, true, '检查中…');
  try {
    const result = await govPost('/governance/publish', publishPayload(true));
    target.className = '';
    target.innerHTML = `
      <div class="toolbar">
        <span>dryRun ${badge(result.wouldPublish ? '可发布' : '被阻断', result.wouldPublish ? 'ok' : 'bad')}</span>
        <span class="sub">governed=${esc(result.governed)} implicit=${esc(result.implicit)} breaking=${esc(result.breaking)}</span>
      </div>
      <p class="sub">impact：${esc(impactText(result.impact))}</p>
      ${gateTable(result.gates)}
      ${blockerTable(result.blockers)}`;
    return result;
  } catch (error) {
    showError(target, error);
    return null;
  } finally {
    setBusy(button, false);
  }
}

async function publishReal() {
  const target = document.getElementById('publish-result');
  const button = document.getElementById('publish-run');
  const preview = await publishDryRun();
  if (!preview) {
    showError(target, 'dry-run 失败，未执行发布');
    return;
  }
  if (!preview.wouldPublish) {
    target.className = '';
    target.innerHTML = `<div class="error">gates 未通过，发布被阻止（错误码见上方阻断项）</div>`;
    return;
  }
  const versionId = document.getElementById('publish-version').value;
  const impact = impactText(preview.impact);
  if (!confirmTwice(
    `确认发布 ${versionId}？\n将影响：${impact}\n当前指针：${(gov.pointer || {}).versionId || '无'}`,
    `再次确认：发布 ${versionId} 会切换本体指针并写审计链，继续？`,
  )) {
    target.className = '';
    target.innerHTML = empty('已取消发布');
    return;
  }
  setBusy(button, true, '发布中…');
  try {
    const result = await govPost('/governance/publish', publishPayload(false));
    target.className = '';
    target.innerHTML = `
      <div class="ok-box">发布成功：${esc(result.versionId || versionId)} · ${esc(result.status || 'published')}</div>
      <p class="sub">替换指针：${esc((gov.pointer || {}).versionId || '无')} → ${esc(result.versionId || versionId)}</p>
      ${gateTable(result.gates)}
      <pre class="mono">${esc(JSON.stringify(result, null, 2))}</pre>`;
    await loadGovernanceVersions();
    await loadProposals();
    await loadApprovals();
  } catch (error) {
    showError(target, error);
  } finally {
    setBusy(button, false);
  }
}

/* ---- rollback --------------------------------------------------------- */

async function rollbackPlan() {
  const target = document.getElementById('rollback-plan-box');
  const versionId = document.getElementById('rollback-version').value;
  try {
    const plan = await api(`/governance/rollback/plan?versionId=${encodeURIComponent(versionId)}`);
    gov.lastPlan = plan;
    target.className = '';
    target.innerHTML = `
      <table><thead><tr><th>项目</th><th>值</th></tr></thead><tbody>
        <tr><td>目标版本</td><td class="mono">${esc(plan.target.id)} · ${esc(plan.target.semver)} · ${esc(plan.target.status)}</td></tr>
        <tr><td>将被替换的版本</td><td class="mono">${esc((plan.replacedVersion || {}).versionId || '无（尚未发布）')}</td></tr>
        <tr><td>目标三元组</td><td class="mono">${esc(plan.targetTriples)}</td></tr>
        <tr><td>是否切换指针</td><td>${plan.wouldChangePointer ? badge('是', 'warn') : badge('否', 'ok')}</td></tr>
      </tbody></table>`;
    return plan;
  } catch (error) {
    showError(target, error);
    return null;
  }
}

async function runRollback(mode) {
  const target = document.getElementById('rollback-result');
  const versionId = document.getElementById('rollback-version').value;
  const plan = await rollbackPlan();
  if (!plan) {
    showError(target, '预览失败，未执行回滚');
    return;
  }
  const replaced = (plan.replacedVersion || {}).versionId || '无（尚未发布）';
  const path = mode === 'new' ? '/governance/rollback' : '/governance/rollback-to';
  const verb = mode === 'new' ? '回滚并新建版本' : '回滚指针';
  if (!confirmTwice(
    `确认${verb}到 ${versionId}？\n将被替换的版本：${replaced}\n影响对象：${plan.targetTriples} 个三元组`,
    `再次确认：${verb} ${versionId}，继续？`,
  )) {
    target.className = '';
    target.innerHTML = empty('已取消回滚');
    return;
  }
  try {
    const reason = document.getElementById('rollback-reason').value.trim();
    const result = await govPost(path, { versionId, reason: reason || undefined });
    target.className = '';
    target.innerHTML = `
      <div class="ok-box">${esc(verb)}成功：${esc(result.versionId || result.id || versionId)}</div>
      <p class="sub">替换的版本：${esc(result.replacedVersionId || replaced)}</p>
      <pre class="mono">${esc(JSON.stringify(result, null, 2))}</pre>`;
    await loadGovernanceVersions();
    await loadProposals();
  } catch (error) {
    showError(target, error);
  }
}

/* ---- migration -------------------------------------------------------- */

function renderMigration(title, payload) {
  const target = document.getElementById('migration-result');
  target.className = '';
  target.innerHTML = `<h3>${esc(title)}</h3><pre class="mono">${esc(JSON.stringify(payload, null, 2))}</pre>`;
}

async function inspectBundle(path) {
  const data = await api(`/governance/bundle/inspect?path=${encodeURIComponent(path)}`);
  const totals = data.totals || {};
  return {
    data,
    text: Object.entries(totals).map(([key, value]) => `${key}=${value}`).join('，') || '无计数',
  };
}

/* ---- audit ------------------------------------------------------------ */

async function loadAudit() {
  const target = document.getElementById('audit-list');
  const versionId = document.getElementById('audit-version').value.trim();
  const action = document.getElementById('audit-action').value;
  const params = new URLSearchParams({ limit: '200' });
  if (versionId) params.set('versionId', versionId);
  if (action) params.set('action', action);
  try {
    const data = await api(`/governance/events?${params.toString()}`);
    const counts = data.categories || {};
    document.getElementById('audit-counts').textContent =
      `published=${counts.published || 0} rolled_back=${counts.rolled_back || 0} superseded=${counts.superseded || 0} other=${counts.other || 0}`;
    if (!data.items.length) {
      target.innerHTML = empty('没有符合条件的事件');
      return;
    }
    const rows = data.items.map((item) => `<tr>
        <td class="mono">${esc(item.at || item.createdAt || '')}</td>
        <td class="mono">${esc(item.versionId)}</td>
        <td class="mono">${esc(item.action)}</td>
        <td>${badge(item.category, item.category === 'published' ? 'ok'
          : item.category === 'rolled_back' ? 'warn'
            : item.category === 'superseded' ? 'warn' : '')}</td>
        <td class="mono">${esc(item.actor || '')}</td>
        <td>${esc(item.reason || '')}</td>
        <td class="mono">${esc(item.proposalId || '')}</td>
      </tr>`).join('');
    target.innerHTML = `<table><thead><tr><th>时间</th><th>版本</th><th>动作</th><th>分类</th><th>actor</th><th>理由</th><th>proposal</th></tr></thead><tbody>${rows}</tbody></table>`;
  } catch (error) {
    showError(target, error);
  }
}

/* ---- wiring ----------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  configureNav();

  document.getElementById('proposal-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const target = document.getElementById('proposal-detail');
    try {
      const result = await govPost('/governance/proposals', {
        versionId: document.getElementById('proposal-version').value.trim(),
        againstVersion: document.getElementById('proposal-against').value.trim() || undefined,
        changeSummary: document.getElementById('proposal-summary').value.trim(),
      });
      target.className = '';
      target.innerHTML = `<div class="ok-box">提案已创建：${esc(result.proposalId)}（${esc(result.status)}）</div>`;
      await loadProposals();
      await loadApprovals();
    } catch (error) {
      showError(target, error);
    }
  });

  document.getElementById('proposal-refresh').addEventListener('click', loadProposals);
  document.getElementById('approval-refresh').addEventListener('click', loadApprovals);
  document.getElementById('publish-version').addEventListener('change', loadPublishProposals);
  document.getElementById('publish-dryrun').addEventListener('click', publishDryRun);
  document.getElementById('publish-run').addEventListener('click', publishReal);
  document.getElementById('rollback-plan').addEventListener('click', rollbackPlan);
  document.getElementById('rollback-to').addEventListener('click', () => runRollback('to'));
  document.getElementById('rollback-new').addEventListener('click', () => runRollback('new'));
  document.getElementById('audit-load').addEventListener('click', loadAudit);

  document.getElementById('export-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const result = await govPost('/governance/bundle/export', {
        out: document.getElementById('export-out').value.trim(),
        tag: document.getElementById('export-tag').value.trim(),
        includeBlobs: document.getElementById('export-blobs').checked,
      });
      renderMigration('export-bundle 完成', result);
    } catch (error) {
      showError(document.getElementById('migration-result'), error);
    }
  });

  document.getElementById('inspect-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const path = document.getElementById('inspect-path').value.trim();
    try {
      gov.lastInspect = await inspectBundle(path);
      renderMigration('bundle 检查结果', gov.lastInspect.data);
    } catch (error) {
      showError(document.getElementById('migration-result'), error);
    }
  });

  document.getElementById('import-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const path = document.getElementById('import-path').value.trim();
    const database = document.getElementById('import-database').value.trim();
    const target = document.getElementById('migration-result');
    try {
      let inspected;
      try {
        inspected = await inspectBundle(path);
      } catch (error) {
        showError(target, `bundle 检查失败，未执行导入：${error.message}`);
        return;
      }
      gov.lastInspect = inspected;
      if (!confirmTwice(
        `确认导入 ${path}？\n目标数据库：${database}\n将写入：${inspected.text}`,
        `再次确认：导入会创建/覆盖数据库 ${database}，继续？`,
      )) {
        target.className = '';
        target.innerHTML = empty('已取消导入');
        return;
      }
      const result = await govPost('/governance/bundle/import', {
        bundle: path,
        database,
        replace: document.getElementById('import-replace').checked,
        keepDbOnFailure: document.getElementById('import-keep').checked,
      });
      renderMigration('import-bundle 完成', result);
    } catch (error) {
      showError(target, error);
    }
  });

  loadGovernanceVersions()
    .then(() => Promise.all([loadProposals(), loadApprovals(), loadPublishProposals()]))
    .then(loadAudit)
    .catch(() => {
      showError(document.getElementById('proposal-list'), '初始化失败，请检查 /ontology/versions');
    });
});
