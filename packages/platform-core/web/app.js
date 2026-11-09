/* S7 UI: native JS only. No framework, no build step.
 * Opened from file:// it talks to the platform on 127.0.0.1:8080; when served
 * by the platform itself (same origin) it uses relative paths.
 */
'use strict';

const API_BASE = location.protocol === 'file:' ? 'http://127.0.0.1:8080' : '';

async function api(path, options) {
  const response = await fetch(API_BASE + path, options);
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch (_err) { body = { raw: text }; }
  if (!response.ok) {
    const detail = (body && body.error) || {};
    const message = detail.message || `HTTP ${response.status}`;
    const code = detail.providerCode || detail.code || '';
    throw new Error(`${message}${code ? ' [' + code + ']' : ''}`);
  }
  return body;
}

function esc(value) {
  return String(value === undefined || value === null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function localName(iri) {
  const parts = String(iri || '').split(/[#/]/);
  return parts[parts.length - 1] || iri;
}

function badge(text, kind) {
  return `<span class="badge ${kind || ''}">${esc(text)}</span>`;
}

function showError(target, error) {
  if (!target) return;
  target.innerHTML = `<div class="error">${esc(error && error.message ? error.message : error)}</div>`;
}

function empty(text) {
  return `<div class="empty">${esc(text)}</div>`;
}

function configureNav() {
  const page = document.body.getAttribute('data-page');
  document.querySelectorAll('header.top nav a').forEach((link) => {
    if (link.getAttribute('data-nav') === page) link.classList.add('active');
  });
}

function setBusy(button, busy, label) {
  if (!button) return;
  button.disabled = busy;
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = label || '处理中…';
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
}

async function loadOverview() {
  const root = document.getElementById('overview');
  try {
    const data = await api('/ui/api/overview');
    const pointer = data.ontology.pointer || {};
    const latest = data.ontology.latest || {};
    const services = (data.services || []).map((item) =>
      `<div>${badge(item.name, item.ok ? 'ok' : 'bad')}</div>`).join('');
    const graphs = (data.graphs || []).map((item) =>
      `<tr><td class="mono">${esc(item.iri)}</td><td>${esc(item.triples)}</td></tr>`).join('')
      || '<tr><td colspan="2" class="empty">暂无命名图</td></tr>';
    const degraded = (data.degraded || []).length
      ? `<div class="warnbox">降级：${esc(data.degraded.join(' / '))}</div>` : '';
    const counts = data.counts || {};
    root.innerHTML = `
      ${degraded}
      <div class="grid two">
        <div class="kpi">
          <div><b>${esc(counts.documents ?? '-')}</b><span>文档</span></div>
          <div><b>${esc(counts.chunks ?? '-')}</b><span>片段</span></div>
          <div><b>${esc(counts.embeddings ?? '-')}</b><span>向量</span></div>
          <div><b>${esc(counts.candidatesPending ?? '-')}</b><span>待审批</span></div>
        </div>
        <div class="chips">${services}</div>
      </div>
      <table style="margin-top:14px">
        <tr><th>版本指针</th><td class="mono">${esc(pointer.versionId || '未发布')}</td></tr>
        <tr><th>T-Box 图</th><td class="mono">${esc(pointer.graph || '-')}</td></tr>
        <tr><th>已发布版本</th><td>${esc(data.ontology.versions ?? 0)}</td></tr>
        <tr><th>最新版本</th><td class="mono">${esc(latest.id || '-')} ${esc(latest.status || '')}</td></tr>
        <tr><th>推理指针</th><td class="mono">${esc((data.reasoning || {}).pointer ? data.reasoning.pointer.targetGraph : '未物化')}</td></tr>
        <tr><th>推理模式</th><td>${esc(data.mode || '-')}</td></tr>
        <tr><th>LLM provider</th><td class="mono">${esc((data.llm || {}).provider || '-')}</td></tr>
        <tr><th>LLM model</th><td class="mono">${esc((data.llm || {}).model || '未配置')} ${(data.llm || {}).configured ? '' : '<span class="badge bad">未配置</span>'}</td></tr>
      </table>
      <h2 style="margin-top:18px;font-size:13px">命名图三元组数</h2>
      <table><tr><th>图</th><th>三元组</th></tr>${graphs}</table>`;
  } catch (error) {
    showError(root, error);
  }
}

async function loadOntology() {
  const root = document.getElementById('ontology');
  try {
    const data = await api('/ui/api/ontology');
    document.getElementById('graphs-info').textContent = `图：${(data.graphs || []).join('  ')}`;
    document.getElementById('classes').innerHTML = (data.classes || []).length
      ? `<table><tr><th>类</th><th>label</th><th>父类</th></tr>${data.classes.map((item) =>
          `<tr><td class="mono">${esc(item.iri)}</td><td>${esc(item.label)}</td>
           <td class="mono">${esc(item.parents.map(localName).join(', ') || '-')}</td></tr>`).join('')}</table>`
      : empty('暂无类声明（先导入并发布本体）');
    document.getElementById('properties').innerHTML = (data.properties || []).length
      ? `<table><tr><th>属性</th><th>类型</th><th>domain / range</th></tr>${data.properties.map((item) =>
          `<tr><td class="mono">${esc(item.iri)}</td><td>${esc(item.kind)}</td>
           <td class="mono">${esc(item.domain.map(localName).join(', ') || '-')} / ${esc(item.range.map(localName).join(', ') || '-')}</td></tr>`).join('')}</table>`
      : empty('暂无属性声明');
  } catch (error) {
    showError(root, error);
  }
}

async function searchEntities() {
  const query = document.getElementById('entity-q').value.trim();
  const target = document.getElementById('entity-results');
  try {
    const data = await api(`/ui/api/entities?q=${encodeURIComponent(query)}&limit=30`);
    target.innerHTML = (data.items || []).length
      ? `<table><tr><th>实体</th><th>label</th><th>类型</th></tr>${data.items.map((item) =>
          `<tr><td><a href="entity.html?iri=${encodeURIComponent(item.iri)}" class="mono">${esc(item.iri)}</a>
           · <a href="#" data-iri="${esc(item.iri)}" class="entity-link">邻居</a></td>
           <td>${esc(item.label)}</td><td class="mono">${esc(item.types.map(localName).join(', ') || '-')}</td></tr>`).join('')}</table>`
      : empty('无匹配实体');
    target.querySelectorAll('.entity-link').forEach((link) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        loadNeighbors(link.getAttribute('data-iri'));
      });
    });
  } catch (error) {
    showError(target, error);
  }
}

async function loadNeighbors(iri) {
  const target = document.getElementById('neighbors');
  try {
    const data = await api(`/ui/api/neighbors?iri=${encodeURIComponent(iri)}&limit=80`);
    const nodes = `<div class="chips">${(data.nodes || []).map((node) =>
      `<span class="chip" title="${esc(node.iri)}">${esc(node.label)}</span>`).join('')}</div>`;
    const edges = (data.edges || []).length
      ? `<table><tr><th>s</th><th>p</th><th>o</th></tr>${data.edges.map((edge) =>
          `<tr><td class="mono">${esc(edge.s)}</td><td class="mono">${esc(edge.p)}</td><td class="mono">${esc(edge.o)}</td></tr>`).join('')}</table>`
      : empty('没有邻居三元组');
    target.innerHTML = `<div class="sub mono">${esc(iri)}</div>${nodes}<div style="margin-top:10px">${edges}</div>`;
  } catch (error) {
    showError(target, error);
  }
}

async function loadImports() {
  const target = document.getElementById('import-progress');
  if (!target) { return; }
  try {
    const data = await api('/imports/batches?limit=5');
    const batches = data.batches || [];
    const failures = data.failures || [];
    const table = batches.length
      ? `<table><tr><th>批次</th><th>目录</th><th>状态</th><th>已完成/总数</th><th>失败</th><th>更新时间</th></tr>${batches.map((batch) => {
          const id = batch.batchId || '';
          const short = id.length > 8 ? `${id.slice(0, 8)}…` : id;
          return `<tr><td class="mono" title="${esc(id)}">${esc(short)}</td>
            <td class="mono">${esc(batch.root || '-')}</td>
            <td>${esc(batch.status || '-')}</td>
            <td>${esc(batch.completed ?? 0)} / ${esc(batch.total ?? 0)}</td>
            <td>${esc(batch.failed ?? 0)}</td>
            <td class="mono">${esc(batch.updatedAt || '-')}</td></tr>`;
        }).join('')}</table>`
      : empty('还没有批量导入批次；在容器内运行 platform import <dir>');
    const failedBlock = failures.length
      ? `<div class="hint">最近失败 ${failures.length} 项</div><table><tr><th>文件</th><th>错误码</th><th>原因</th></tr>${failures.map((item) =>
          `<tr><td class="mono">${esc(item.relPath || '-')}</td><td class="mono">${esc(item.code || '-')}</td><td>${esc(item.message || '-')}</td></tr>`
        ).join('')}</table>`
      : '';
    target.innerHTML = table + failedBlock;
  } catch (error) {
    showError(target, error);
  }
}

async function loadDocuments() {
  const target = document.getElementById('documents');
  try {
    const data = await api('/documents?limit=50');
    const items = data.items || data.documents || [];
    target.innerHTML = items.length
      ? `<table><tr><th>文档</th><th>文件名</th><th>分块</th><th>创建时间</th><th>操作</th></tr>${items.map((item) => {
          const id = item.documentId || item.document_id || item.id;
          return `<tr><td><a href="#" data-doc="${esc(id)}" class="doc-link mono">${esc(id)}</a></td>
            <td>${esc(item.filename || item.name || '-')}</td>
            <td>${esc(item.chunks ?? item.chunkCount ?? '-')}</td>
            <td class="mono">${esc(item.createdAt || item.created_at || '-')}</td>
            <td>
              <button data-index="${esc(id)}">解析</button>
              <button data-extract="${esc(id)}">抽取</button>
            </td></tr>`;
        }).join('')}</table>`
      : empty('还没有文档，先上传或运行 scripts/seed.ps1');
    target.querySelectorAll('.doc-link').forEach((link) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        loadChunks(link.getAttribute('data-doc'));
      });
    });
    target.querySelectorAll('button[data-index]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '解析中…');
        try {
          const result = await api(`/documents/${encodeURIComponent(button.dataset.index)}/index`, { method: 'POST' });
          document.getElementById('doc-status').innerHTML =
            `<div class="hint">解析完成：chunks=${esc(result.chunks)} embedded=${esc(result.embedded)} degraded=${esc(result.degraded)}</div>`;
          loadDocuments();
        } catch (error) { showError(document.getElementById('doc-status'), error); }
        finally { setBusy(button, false); }
      });
    });
    target.querySelectorAll('button[data-extract]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '抽取中…');
        try {
          const result = await api(`/documents/${encodeURIComponent(button.dataset.extract)}/extract`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'auto' })
          });
          document.getElementById('doc-status').innerHTML =
            `<div class="hint">抽取完成：inserted=${esc(result.inserted ?? 0)} mode=${esc(result.mode || 'auto')} degraded=${esc(result.degraded)}</div>`;
        } catch (error) { showError(document.getElementById('doc-status'), error); }
        finally { setBusy(button, false); }
      });
    });
  } catch (error) {
    showError(target, error);
  }
}

async function loadChunks(documentId) {
  const target = document.getElementById('chunks');
  try {
    const data = await api(`/documents/${encodeURIComponent(documentId)}/chunks?limit=100`);
    const items = data.items || data.chunks || [];
    target.innerHTML = items.length
      ? `<table><tr><th>#</th><th>chunk</th><th>页</th><th>原文片段</th></tr>${items.map((chunk) =>
          `<tr><td>${esc(chunk.seq)}</td><td class="mono">${esc(chunk.chunkId || chunk.chunk_id)}</td>
           <td>${esc(chunk.pageFrom || chunk.page_from || '-')}–${esc(chunk.pageTo || chunk.page_to || '-')}</td>
           <td><pre class="snippet">${esc(chunk.text)}</pre></td></tr>`).join('')}</table>`
      : empty('该文档没有分块');
  } catch (error) {
    showError(target, error);
  }
}

async function uploadDocument(event) {
  event.preventDefault();
  const form = event.target;
  const status = document.getElementById('upload-status');
  const button = form.querySelector('button[type="submit"]');
  setBusy(button, true, '上传中…');
  try {
    const body = new FormData();
    body.append('file', form.elements.file.files[0]);
    const result = await api('/documents', { method: 'POST', body });
    status.innerHTML = `<div class="hint">上传完成：${esc(result.documentId || result.id || 'ok')}，下一步点“解析”。</div>`;
    loadDocuments();
  } catch (error) {
    showError(status, error);
  } finally {
    setBusy(button, false);
  }
}

async function runSearch(event) {
  event.preventDefault();
  const target = document.getElementById('search-result');
  const button = event.target.querySelector('button[type="submit"]');
  setBusy(button, true, '检索中…');
  try {
    const q = document.getElementById('q').value;
    const strategy = document.getElementById('strategy').value;
    const topK = document.getElementById('topK').value;
    const tokenBudget = document.getElementById('tokenBudget').value;
    const data = await api(`/ui/api/search?q=${encodeURIComponent(q)}&strategy=${strategy}&topK=${topK}&tokenBudget=${tokenBudget}`);
    const flags = [];
    if (data.truncated) flags.push(badge('truncated=true', 'warn'));
    if (data.degraded) flags.push(badge('degraded=true', 'warn'));
    if (!data.degraded) flags.push(badge('degraded=false', 'ok'));
    const reasons = (data.warnings || data.reasons || []).map((reason) => badge(reason, 'warn')).join('');
    const chunks = (data.chunks || []).map((chunk) => {
      const cite = (data.citations || []).find((item) => item.kind === 'chunk' && item.id === chunk.chunkId) || {};
      return `<tr><td>${esc(chunk.chunkId)}</td><td class="mono">${esc(chunk.documentId || cite.documentId || '-')}</td>
        <td>${esc(chunk.pageFrom)}–${esc(chunk.pageTo)}</td><td><pre class="snippet">${esc(chunk.text)}</pre></td></tr>`;
    }).join('');
    const facts = (data.facts || []).map((fact) =>
      `<tr><td class="mono">${esc(fact.s)}</td><td class="mono">${esc(fact.p)}</td><td class="mono">${esc(fact.o)}</td>
       <td class="mono">${esc(fact.graph || '-')}</td></tr>`).join('');
    target.innerHTML = `
      <div class="chips" style="margin-bottom:10px">${flags.join('')}${reasons}</div>
      ${data.truncated ? '<div class="warnbox">结果因 token 预算被截断（truncated=true）：仅保留可容纳的片段，其余在 omitted 中计数。</div>' : ''}
      ${data.degraded ? '<div class="warnbox">存在降级（degraded=true）：部分通路不可用，结果不完整，原因见上方徽标。</div>' : ''}
      <h2 style="font-size:13px">片段 <span class="sub">${esc((data.chunks || []).length)}</span></h2>
      ${chunks ? `<table><tr><th>chunk</th><th>文档</th><th>页</th><th>原文</th></tr>${chunks}</table>` : empty('没有片段命中')}
      <h2 style="font-size:13px;margin-top:16px">事实 <span class="sub">${esc((data.facts || []).length)}</span></h2>
      ${facts ? `<table><tr><th>s</th><th>p</th><th>o</th><th>图</th></tr>${facts}</table>` : empty('没有事实三元组')}
      <p class="hint">citations=${esc(JSON.stringify(data.citations || []).slice(0, 600))}${(data.citations || []).length > 6 ? ' …' : ''}</p>`;
  } catch (error) {
    showError(target, error);
  } finally {
    setBusy(button, false);
  }
}

async function loadCandidates() {
  const target = document.getElementById('candidates');
  try {
    const data = await api('/ui/api/candidates?state=pending&limit=50');
    const items = data.candidates || [];
    target.innerHTML = items.length
      ? `<table><tr><th>候选三元组</th><th>置信度</th><th>来源片段</th><th>操作</th></tr>${items.map((item) => `
          <tr>
            <td class="mono">${esc(localName(item.subject))} ${esc(localName(item.predicate))} ${esc(item.object)}</td>
            <td>${esc(item.confidence)}</td>
            <td><pre class="snippet">${esc((item.evidence || {}).text || '（来源片段不可用）')}</pre>
              <div class="hint">chunk=${esc(item.chunkId)} page=${esc((item.evidence || {}).pageFrom ?? '-')}</div></td>
            <td>
              <button class="primary" data-approve="${esc(item.candidateId)}">通过</button>
              <button class="danger" data-reject="${esc(item.candidateId)}">拒绝</button>
            </td>
          </tr>`).join('')}</table>`
      : empty('没有待审批候选；上传→解析→抽取后会出现在这里');
    target.querySelectorAll('button[data-approve]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '写入中…');
        try {
          await api(`/candidates/${encodeURIComponent(button.dataset.approve)}/approve`, { method: 'POST' });
          loadCandidates();
          loadFacts();
        } catch (error) { showError(document.getElementById('decision-status'), error); }
        finally { setBusy(button, false); }
      });
    });
    target.querySelectorAll('button[data-reject]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '拒绝中…');
        try {
          await api(`/candidates/${encodeURIComponent(button.dataset.reject)}/reject`, { method: 'POST' });
          loadCandidates();
        } catch (error) { showError(document.getElementById('decision-status'), error); }
        finally { setBusy(button, false); }
      });
    });
  } catch (error) {
    showError(target, error);
  }
}

async function loadFacts() {
  const target = document.getElementById('facts');
  try {
    const data = await api('/facts?state=all&limit=100');
    const items = data.items || [];
    target.innerHTML = items.length
      ? `<table><tr><th>事实</th><th>来源</th><th>状态</th><th>治理</th><th>操作</th></tr>${items.map((item) => `
          <tr>
            <td class="mono">${esc(localName(item.subject))} ${esc(localName(item.predicate))} ${esc(item.object.value || item.object.iri)}</td>
            <td>${esc((item.source || {}).kind || '-')}
              <div class="hint">${esc((item.source || {}).documentId || (item.source || {}).runId || '-')}</div></td>
            <td>${esc(item.state)}</td>
            <td>${item.conflict ? `<span class="badge warn">conflict</span><div class="hint">${esc((item.conflictValues || []).join(' | '))}</div>` : '-'}</td>
            <td>
              ${item.state === 'active'
                ? `<button class="danger" data-retract="${esc(item.factId)}">撤回</button>`
                : item.state === 'retracted'
                  ? `<button data-restore="${esc(item.factId)}">恢复</button>`
                  : '-'}
              ${(item.source || {}).documentId
                ? `<button data-source="${esc(item.source.documentId)}">按来源撤回</button>`
                : ''}
            </td>
          </tr>`).join('')}</table>`
      : empty('还没有事实；审批通过候选后会出现在这里');
    target.querySelectorAll('button[data-retract]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '撤回中…');
        try {
          await api(`/facts/${encodeURIComponent(button.dataset.retract)}/retract`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: 'ui' })
          });
          loadFacts();
        } catch (error) { showError(document.getElementById('facts-status'), error); }
        finally { setBusy(button, false); }
      });
    });
    target.querySelectorAll('button[data-restore]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '恢复中…');
        try {
          await api(`/facts/${encodeURIComponent(button.dataset.restore)}/restore`, { method: 'POST' });
          loadFacts();
        } catch (error) { showError(document.getElementById('facts-status'), error); }
        finally { setBusy(button, false); }
      });
    });
    target.querySelectorAll('button[data-source]').forEach((button) => {
      button.addEventListener('click', async () => {
        setBusy(button, true, '批量撤回中…');
        try {
          const result = await api('/facts/retract', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sourceDocumentId: button.dataset.source, reason: 'ui-batch' })
          });
          document.getElementById('facts-status').innerHTML =
            `<span class="badge ok">已撤回 ${esc(result.retracted)} 条（batch=${esc(result.batchId)}）</span>`;
          loadFacts();
        } catch (error) { showError(document.getElementById('facts-status'), error); }
        finally { setBusy(button, false); }
      });
    });
  } catch (error) {
    showError(target, error);
  }
}

async function loadConflicts() {
  const target = document.getElementById('conflicts');
  try {
    const data = await api('/facts/conflicts');
    const items = data.conflicts || [];
    target.innerHTML = items.length
      ? `<table><tr><th>(s, p)</th><th>多值 / 来源片段</th><th>裁决</th></tr>${items.map((item) => `
          <tr>
            <td class="mono">${esc(localName(item.subject))} ${esc(localName(item.predicate))}</td>
            <td>${(item.facts || []).map((fact) => `
              <div><span class="mono">${esc(fact.object)}</span>
                <span class="hint">${esc((fact.source || {}).kind || '-')} ${esc((fact.source || {}).documentId || '')}</span>
                ${fact.evidence ? `<div class="hint">${esc(fact.evidence.text)}</div>` : ''}
                <button data-keep="${esc(fact.object)}" data-subject="${esc(item.subject)}" data-predicate="${esc(item.predicate)}">保留此值</button>
              </div>`).join('')}
              ${item.accepted ? '<span class="badge warn">accepted_conflict</span>' : ''}</td>
            <td>
              <button data-keepboth="${esc(item.subject)}|${esc(item.predicate)}">两者都保留</button>
              <button class="danger" data-merge="${esc(item.subject)}|${esc(item.predicate)}">合并…</button>
            </td>
          </tr>`).join('')}</table>`
      : empty('没有冲突；同一 (s,p) 出现多个 active 值时会出现在这里');

    const resolve = async (body, button, label) => {
      setBusy(button, true, label);
      try {
        await api('/facts/conflicts/resolve', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...body, actor: 'operator', reason: 'ui' })
        });
        document.getElementById('conflicts-status').innerHTML = '<span class="badge ok">裁决已记录</span>';
        loadConflicts();
        loadFacts();
      } catch (error) { showError(document.getElementById('conflicts-status'), error); }
      finally { setBusy(button, false); }
    };
    target.querySelectorAll('button[data-keep]').forEach((button) => {
      button.addEventListener('click', () => resolve({
        subject: button.dataset.subject, predicate: button.dataset.predicate,
        action: 'keep', keep: button.dataset.keep
      }, button, '保留中…'));
    });
    target.querySelectorAll('button[data-keepboth]').forEach((button) => {
      button.addEventListener('click', () => {
        const [subject, predicate] = button.dataset.keepboth.split('|');
        resolve({ subject, predicate, action: 'keep_both' }, button, '记录中…');
      });
    });
    target.querySelectorAll('button[data-merge]').forEach((button) => {
      button.addEventListener('click', () => {
        const [subject, predicate] = button.dataset.merge.split('|');
        const merged = window.prompt('合并后的目标值（IRI 或字面量）', '');
        if (!merged) { return; }
        resolve({ subject, predicate, action: 'merge', mergedObject: merged }, button, '合并中…');
      });
    });
  } catch (error) {
    showError(target, error);
  }
}

async function undoLastResolution() {
  const status = document.getElementById('conflicts-status');
  const subject = window.prompt('撤销哪个 (s,p) 的裁决？subject IRI', '');
  if (!subject) { return; }
  const predicate = window.prompt('predicate IRI', '');
  if (!predicate) { return; }
  try {
    const preview = await api('/facts/conflicts/undo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, predicate, actor: 'operator', dryRun: true })
    });
    const text = `将恢复 ${(preview.restoredFactIds || []).length} 条、撤回 ${(preview.retiredFactIds || []).length} 条，`
      + `共影响 ${preview.affected} 条（${preview.undoOf}）。继续？`;
    if (!window.confirm(text)) { return; }
    const result = await api('/facts/conflicts/undo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, predicate, actor: 'operator', reason: 'ui undo', dryRun: false })
    });
    status.innerHTML = `<span class="badge ok">已撤销 ${esc(result.undoOf)}，追加审计事件 ${esc(String(result.undoOfEventId || '-'))}</span>`;
    loadConflicts();
    loadFacts();
  } catch (error) { showError(status, error); }
}

async function batchKeep() {
  const status = document.getElementById('conflicts-status');
  const predicate = window.prompt('按谓词批量：predicate IRI', '');
  if (!predicate) { return; }
  const keep = window.prompt('要保留的值（IRI 或字面量）', '');
  if (!keep) { return; }
  try {
    const preview = await api('/facts/conflicts/batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ predicate, keep, actor: 'operator', dryRun: true })
    });
    const text = `按谓词匹配 ${preview.matched} 组冲突：将保留 ${preview.kept} 组、跳过 ${preview.skipped} 组，`
      + `影响 ${preview.affectedFacts} 条断言。继续？`;
    if (!window.confirm(text)) { return; }
    const result = await api('/facts/conflicts/batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ predicate, keep, actor: 'operator', reason: 'ui batch', dryRun: false })
    });
    const skipped = (result.results || []).filter((item) => item.status === 'skipped');
    status.innerHTML = `<span class="badge ok">批量完成 matched=${result.matched} kept=${result.kept} skipped=${result.skipped}</span>`
      + (skipped.length ? `<div class="hint">跳过：${esc(skipped.map((item) => `${localName(item.subject)}=${item.reason}`).join('; '))}</div>` : '');
    loadConflicts();
    loadFacts();
  } catch (error) { showError(status, error); }
}

async function runMaterialize() {
  const target = document.getElementById('materialize-result');
  const button = document.getElementById('materialize-btn');
  setBusy(button, true, '物化中…');
  try {
    const result = await api('/reasoning/materialize', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({})
    });
    const stages = result.stages || {};
    const stageRows = Object.keys(stages).map((name) =>
      `<tr><td>${esc(name)}</td><td class="mono">${esc(JSON.stringify(stages[name]))}</td></tr>`).join('');
    target.innerHTML = `
      <div class="chips">
        ${badge(result.skipped ? 'skipped=true' : 'skipped=false', result.skipped ? 'warn' : 'ok')}
        ${badge('mode=' + (result.mode || '-'))}
        ${badge('inferred=' + (result.inferred ?? 0))}
      </div>
      <p class="hint mono">${esc(result.targetGraph || '')}</p>
      ${stageRows ? `<table><tr><th>阶段</th><th>结果</th></tr>${stageRows}</table>` : ''}`;
  } catch (error) {
    showError(target, error);
  } finally {
    setBusy(button, false);
  }
}

let ontoSelection = null;

async function loadOntologyGovernance() {
  const target = document.getElementById('onto-versions');
  try {
    const data = await api('/ontology/versions');
    const versions = data.items || [];
    const proposals = await api('/ontology/proposals');
    const latest = {};
    (proposals.items || []).forEach((item) => {
      if (!latest[item.versionId]) latest[item.versionId] = item;
    });
    const pointerId = (data.pointer || {}).versionId || null;
    if (!ontoSelection || !versions.some((item) => item.id === ontoSelection)) {
      ontoSelection = pointerId || (versions.length ? versions[versions.length - 1].id : null);
    }
    document.getElementById('onto-governance-status').textContent =
      `当前指针：${pointerId || '未发布'} · 选中：${ontoSelection || '-'}`;
    if (!versions.length) {
      target.innerHTML = empty('还没有版本；先通过 CLI 导入 TTL');
      return;
    }
    const rows = versions.slice().reverse().map((item) => {
      const proposal = latest[item.id];
      const actions = [];
      if (item.status === 'draft' || item.status === 'proposed') {
        actions.push(`<button data-propose="${esc(item.id)}">提案</button>`);
      }
      if (proposal && proposal.status === 'proposed') {
        actions.push(`<button data-approve="${esc(proposal.proposalId)}">审批</button>`);
      }
      actions.push(`<button data-diff="${esc(item.id)}">diff</button>`);
      if (proposal && proposal.status === 'approved') {
        actions.push(`<button class="primary" data-publish="${esc(item.id)}">发布</button>`);
      }
      if (item.status === 'published' || item.status === 'superseded') {
        actions.push(`<button class="danger" data-rollback="${esc(item.id)}">回滚</button>`);
      }
      actions.push(`<button data-select="${esc(item.id)}">选中</button>`);
      const summary = proposal
        ? `${badge(proposal.status, proposal.breaking ? 'warn' : 'ok')} ${esc(proposal.changeSummary)}`
        : '-';
      return `<tr>
        <td class="mono">${esc(item.id)}</td>
        <td>${esc(item.semver)}</td>
        <td>${badge(item.status, item.status === 'published' ? 'ok' : '')}</td>
        <td>${esc(item.label || '-')}</td>
        <td>${esc(item.createdAt || '-')}</td>
        <td>${summary}</td>
        <td>${actions.join(' ')}</td>
      </tr>`;
    }).join('');
    target.innerHTML = `<table><tr><th>版本</th><th>semver</th><th>状态</th><th>说明</th>
      <th>创建</th><th>提案</th><th>操作</th></tr>${rows}</table>`;

    target.querySelectorAll('button[data-select]').forEach((button) => {
      button.addEventListener('click', () => {
        ontoSelection = button.dataset.select;
        document.getElementById('onto-governance-status').textContent =
          `选中：${ontoSelection}`;
      });
    });
    target.querySelectorAll('button[data-propose]').forEach((button) => {
      button.addEventListener('click', () => {
        document.getElementById('onto-proposal-version').value = button.dataset.propose;
        document.getElementById('onto-proposal-note').focus();
      });
    });
    target.querySelectorAll('button[data-approve]').forEach((button) => {
      button.addEventListener('click', () => approveOntologyProposal(button.dataset.approve, button));
    });
    target.querySelectorAll('button[data-diff]').forEach((button) => {
      button.addEventListener('click', () => previewOntologyDiff(button.dataset.diff));
    });
    target.querySelectorAll('button[data-publish]').forEach((button) => {
      button.addEventListener('click', () => publishOntologyVersion(button.dataset.publish, button));
    });
    target.querySelectorAll('button[data-rollback]').forEach((button) => {
      button.addEventListener('click', () => rollbackOntologyVersion(button.dataset.rollback, button));
    });
  } catch (error) {
    showError(target, error);
  }
}

async function proposeOntologyVersion(event) {
  event.preventDefault();
  const status = document.getElementById('onto-governance-status');
  const versionId = document.getElementById('onto-proposal-version').value.trim();
  const note = document.getElementById('onto-proposal-note').value.trim();
  const actor = document.getElementById('onto-proposal-actor').value.trim() || 'operator';
  if (!versionId || !note) { showError(status, '版本 ID 与变更说明必填'); return; }
  try {
    const result = await api(`/ontology/versions/${encodeURIComponent(versionId)}/propose`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ changeSummary: note, actor })
    });
    status.innerHTML = `<span class="badge ${result.breaking ? 'bad' : 'ok'}">提案 ${esc(result.proposalId)}（breaking=${esc(result.breaking)}）</span>`;
    ontoSelection = versionId;
    document.getElementById('onto-diff-preview-box').innerHTML =
      `<pre class="snippet">${esc(result.diff.markdown || '')}</pre>`;
    loadOntologyGovernance();
  } catch (error) { showError(status, error); }
}

async function approveOntologyProposal(proposalId, button) {
  setBusy(button, true, '审批中…');
  try {
    await api(`/ontology/proposals/${encodeURIComponent(proposalId)}/approve`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actor: 'operator', reason: 'ui approve' })
    });
    loadOntologyGovernance();
  } catch (error) { showError(document.getElementById('onto-governance-status'), error); }
  finally { setBusy(button, false); }
}

async function previewOntologyDiff(versionId) {
  const box = document.getElementById('onto-diff-preview-box');
  ontoSelection = versionId;
  try {
    const data = await api(`/ontology/versions/${encodeURIComponent(versionId)}/diff`);
    box.innerHTML = `
      <div class="chips">${badge(data.breaking ? 'breaking=true' : 'breaking=false', data.breaking ? 'bad' : 'ok')}</div>
      <pre class="snippet">${esc(data.markdown || '')}</pre>`;
  } catch (error) { showError(box, error); }
}

async function publishOntologyVersion(versionId, button) {
  const status = document.getElementById('onto-governance-status');
  setBusy(button, true, '发布中…');
  try {
    const proposals = await api(`/ontology/proposals?versionId=${encodeURIComponent(versionId)}`);
    const proposal = (proposals.items || []).find((item) => item.status === 'approved');
    if (!proposal) { throw new Error('该版本没有已审批的提案，无法发布'); }
    let ack = false;
    if (proposal.breaking) {
      ack = window.confirm('该提案包含 breaking 变更，确认要发布吗？');
      if (!ack) { throw new Error('已取消发布（breaking 未确认）'); }
    }
    const result = await api('/ontology/publish', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        versionId, proposalId: proposal.proposalId, acknowledgeBreaking: ack,
        actor: 'operator', reason: 'ui publish'
      })
    });
    status.innerHTML = `<span class="badge ok">已发布 ${esc(result.id)}</span>`;
    loadOntologyGovernance();
  } catch (error) { showError(status, error); }
  finally { setBusy(button, false); }
}

async function rollbackOntologyVersion(versionId, button) {
  const status = document.getElementById('onto-governance-status');
  if (!window.confirm(`回滚指针到 ${versionId}？当前版本会转为 superseded，两个图都保留。`)) {
    return;
  }
  setBusy(button, true, '回滚中…');
  try {
    const result = await api('/ontology/rollback', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ versionId, actor: 'operator', reason: 'ui rollback' })
    });
    status.innerHTML = `<span class="badge ok">已回滚到 ${esc(result.id)}</span>`;
    loadOntologyGovernance();
  } catch (error) { showError(status, error); }
  finally { setBusy(button, false); }
}

document.addEventListener('DOMContentLoaded', () => {
  configureNav();
  const page = document.body.getAttribute('data-page');
  if (page === 'overview') {
    document.getElementById('refresh').addEventListener('click', loadOverview);
    loadOverview();
  }
  if (page === 'ontology') {
    loadOntology();
    loadOntologyGovernance();
    document.getElementById('onto-proposal-form').addEventListener('submit', proposeOntologyVersion);
    document.getElementById('onto-diff-preview').addEventListener('click', () => {
      if (ontoSelection) { previewOntologyDiff(ontoSelection); }
    });
    document.getElementById('onto-publish').addEventListener('click', () => {
      if (ontoSelection) { publishOntologyVersion(ontoSelection, document.getElementById('onto-publish')); }
    });
    document.getElementById('onto-rollback').addEventListener('click', () => {
      if (ontoSelection) { rollbackOntologyVersion(ontoSelection, document.getElementById('onto-rollback')); }
    });
    document.getElementById('entity-form').addEventListener('submit', (event) => {
      event.preventDefault();
      searchEntities();
    });
    document.getElementById('entity-q').addEventListener('keydown', (event) => {
      if (event.key === 'Enter') { event.preventDefault(); searchEntities(); }
    });
    // 支持 ontology.html?entity=<IRI> 深链：直接展示该实体的邻居子图。
    const entityIri = new URLSearchParams(location.search).get('entity');
    if (entityIri) {
      document.getElementById('entity-q').value = entityIri;
      loadNeighbors(entityIri);
    }
  }
  if (page === 'documents') {
    document.getElementById('upload-form').addEventListener('submit', uploadDocument);
    document.getElementById('import-refresh').addEventListener('click', loadImports);
    loadDocuments();
    loadImports();
  }
  if (page === 'search') {
    document.getElementById('search-form').addEventListener('submit', runSearch);
  }
  if (page === 'approvals') {
    document.getElementById('materialize-btn').addEventListener('click', runMaterialize);
    document.getElementById('facts-refresh').addEventListener('click', loadFacts);
    document.getElementById('conflicts-refresh').addEventListener('click', loadConflicts);
    document.getElementById('conflict-undo').addEventListener('click', undoLastResolution);
    document.getElementById('conflict-batch').addEventListener('click', batchKeep);
    loadCandidates();
    loadConflicts();
    loadFacts();
  }
});
