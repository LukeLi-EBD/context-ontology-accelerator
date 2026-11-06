(function () {
  'use strict';

  function el(id) { return document.getElementById(id); }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function localName(iri) {
    if (!iri) { return '—'; }
    const text = String(iri);
    const cut = Math.max(text.lastIndexOf('#'), text.lastIndexOf('/'));
    return cut >= 0 ? text.slice(cut + 1) : text;
  }

  function termText(term) {
    if (!term) { return '—'; }
    return term.value == null ? '—' : String(term.value);
  }

  function empty(target, message) {
    target.classList.add('empty');
    target.textContent = message;
  }

  function showError(target, error) {
    target.classList.remove('empty');
    const code = (error && (error.providerCode || error.code)) || 'ERROR';
    const message = (error && error.message) || String(error);
    target.innerHTML = '<div class="error">' + esc(code) + ' · ' + esc(message) + '</div>';
  }

  async function getJson(url) {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    let body = null;
    try { body = await response.json(); } catch (err) { body = null; }
    if (!response.ok) {
      const error = (body && body.error) || { code: response.status, message: response.statusText };
      throw error;
    }
    return body;
  }

  function badgeHtml(badge) {
    if (!badge) { return ''; }
    const cls = badge.state === 'evidenced' ? 'ok' : (badge.state === 'inferred' ? 'warn' : 'bad');
    const detail = [badge.basis, badge.judge ? ('判定人：' + badge.judge) : null]
      .filter(Boolean).join(' · ');
    return '<span class="badge ' + cls + '" title="' + esc(detail) + '">'
      + esc(badge.label || badge.state) + '</span>';
  }

  function renderSummary(data) {
    const target = el('entity-summary');
    target.classList.remove('empty');
    const types = (data.classes || []).map(function (item) { return esc(item.label); }).join(' / ') || '—';
    const tbox = data.tbox || {};
    target.innerHTML =
      '<div class="kpi">'
      + '<div><b>' + badgeHtml(data.evidenceBadge) + '</b><span>溯源徽标</span></div>'
      + '<div><b>' + esc(data.instanceCount) + '</b><span>本类实例数</span></div>'
      + '<div><b>' + esc(data.sources.length) + '</b><span>可解析来源</span></div>'
      + '<div><b>' + esc((data.relatedMetrics.items || []).length) + '</b><span>相关指标</span></div>'
      + '</div>'
      + '<div class="mono" style="margin-top:10px;word-break:break-all">' + esc(data.iri) + '</div>'
      + '<div class="sub" style="margin-top:4px">' + esc(data.label) + ' · ' + types
      + ' · T-Box ' + esc(tbox.semver || '—') + ' (' + esc(tbox.versionId || '—') + ')</div>';
  }

  function renderClasses(data) {
    const target = el('entity-classes');
    const items = data.classes || [];
    el('class-count').textContent = '· ' + items.length + ' 类';
    if (!items.length) { empty(target, '未找到 rdf:type 类归属。'); return; }
    target.classList.remove('empty');
    const rows = items.map(function (item) {
      const chain = (item.chain || []).map(function (node) { return esc(node.label); }).join(' → ');
      const inferred = item.inferredOnly
        ? '<span class="badge warn">仅推理</span>' : '<span class="badge ok">断言</span>';
      return '<tr><td><span class="mono">' + esc(item.iri) + '</span><br><span class="sub">'
        + esc(item.label) + '</span></td><td>' + chain + '</td><td>' + esc(item.instanceCount)
        + '</td><td>' + inferred + '</td></tr>';
    }).join('');
    target.innerHTML = '<table><tr><th>类</th><th>父类链</th><th>实例数</th><th>来源图</th></tr>'
      + rows + '</table>';
  }

  function renderRequired(data) {
    const target = el('entity-required');
    const items = data.requiredProperties || [];
    el('required-count').textContent = '· ' + (data.requiredStatus === 'no-restrictions'
      ? 'T-Box 无 minCardinality 约束' : (items.length + ' 项'));
    if (!items.length) { empty(target, '当前类及父类没有 owl:minCardinality 约束。'); return; }
    target.classList.remove('empty');
    const rows = items.map(function (item) {
      const values = (item.values || []).map(function (term) {
        return '<span class="chip">' + esc(termText(term)) + '</span>';
      }).join(' ') || '—';
      const state = item.satisfied
        ? '<span class="badge ok">已满足</span>' : '<span class="badge bad">缺失</span>';
      return '<tr><td><span class="mono">' + esc(item.property) + '</span><br><span class="sub">'
        + esc(item.label) + '</span></td><td>' + esc(item.minCount) + '</td><td>' + values
        + '</td><td>' + esc(item.valueCount) + '</td><td>' + state + '</td></tr>';
    }).join('');
    target.innerHTML = '<table><tr><th>属性</th><th>minCount</th><th>取值</th><th>取值数</th><th>状态</th></tr>'
      + rows + '</table>';
  }

  function renderProperties(data) {
    const target = el('entity-properties');
    const items = data.properties || [];
    if (!items.length) { empty(target, '没有可展示的断言/推理属性取值。'); return; }
    target.classList.remove('empty');
    const rows = items.map(function (item) {
      return '<tr><td><span class="mono">' + esc(item.property) + '</span><br><span class="sub">'
        + esc(item.label) + '</span></td><td><div class="chips">'
        + (item.values || []).map(function (term) {
          return '<span class="chip" title="' + esc(term.kind) + '">' + esc(termText(term)) + '</span>';
        }).join('') + '</div></td></tr>';
    }).join('');
    target.innerHTML = '<table><tr><th>属性</th><th>取值</th></tr>' + rows + '</table>';
  }

  function renderNeighbors(data) {
    const target = el('entity-neighbors');
    const neighbors = data.neighbors || {};
    el('neighbor-count').textContent = '· ' + (neighbors.edges || []).length + ' 条边';
    const nodes = (neighbors.nodes || []).map(function (node) {
      return '<span class="chip" title="' + esc(node.iri) + '">' + esc(node.label)
        + (node.inferred ? ' · 推理' : '') + '</span>';
    }).join(' ');
    const edges = (neighbors.edges || []).map(function (edge) {
      return '<tr><td class="mono">' + esc(edge.s) + '</td><td class="mono">' + esc(edge.p)
        + '</td><td class="mono">' + esc(edge.o) + '</td><td>'
        + (edge.inferred ? '<span class="badge warn">推理</span>' : '<span class="badge ok">断言</span>')
        + '</td></tr>';
    }).join('');
    target.classList.remove('empty');
    target.innerHTML = '<div class="chips">' + (nodes || '—') + '</div>'
      + '<div style="margin-top:10px">' + (edges
        ? '<table><tr><th>s</th><th>p</th><th>o</th><th>图</th></tr>' + edges + '</table>'
        : '<div class="empty">没有邻居三元组。</div>') + '</div>'
      + (neighbors.truncated ? '<div class="hint">已截断，仅显示前若干条。</div>' : '');
  }

  function renderMetrics(data) {
    const target = el('entity-metrics');
    const payload = data.relatedMetrics || {};
    if (payload.status !== 'bound' || !(payload.items || []).length) {
      target.classList.remove('empty');
      target.innerHTML = '<div class="warn-box">未绑定（unbound）：'
        + esc(payload.reason || 'metric_field_binding 无匹配行')
        + '。弱匹配依据：' + esc((payload.matchBasis || []).join('；') || '类名未命中别名表')
        + '</div>';
      return;
    }
    target.classList.remove('empty');
    const rows = payload.items.map(function (item) {
      const bindings = (item.bindings || []).map(function (binding) {
        return esc((binding.factTable || '') + ' . ' + (binding.entityColumn || ''))
          + (binding.role ? (' (' + esc(binding.role) + ')') : '');
      }).join('<br>');
      return '<tr><td class="mono">' + esc(item.metricId) + '</td><td>' + esc(item.nameZh || '—')
        + '</td><td>' + esc(item.grain || '—') + '</td><td>'
        + ((item.publishable ? '<span class="badge ok">可发布</span>' : '<span class="badge warn">不可发布</span>'))
        + '</td><td class="mono">' + bindings + '</td><td class="mono">'
        + esc((item.matchBasis || []).join('；')) + '</td></tr>';
    }).join('');
    target.innerHTML = '<table><tr><th>指标</th><th>名称</th><th>grain</th><th>发布</th>'
      + '<th>binding（表·字段）</th><th>命中依据</th></tr>' + rows + '</table>'
      + '<div class="hint">弱匹配依据：' + esc((payload.matchBasis || []).join('；'))
      + '</div>';
  }

  function renderSources(data) {
    const target = el('entity-sources');
    const items = data.sources || [];
    if (!items.length) {
      target.classList.remove('empty');
      target.innerHTML = '<div class="warn-box">无可解析 sourceRef；徽标 = '
        + esc((data.evidenceBadge || {}).state || 'no-source')
        + '。依据：' + esc((data.evidenceBadge || {}).basis || '—') + '</div>';
      return;
    }
    target.classList.remove('empty');
    target.innerHTML = '<table><tr><th>类型</th><th>sourceRef</th><th>跳转</th><th>原文</th></tr>'
      + items.map(function (item) {
        return '<tr><td>' + esc(item.kind) + '</td><td class="mono">'
          + '<a href="' + esc(item.resolveUrl) + '" target="_blank" rel="noopener">'
          + esc(item.ref) + '</a></td><td><a href="' + esc(item.href)
          + '" target="_blank" rel="noopener">打开</a></td><td>'
          + esc(item.text || '—') + '</td></tr>';
      }).join('') + '</table>';
  }

  function renderSourceNote(data) {
    el('entity-source-note').textContent = '端点 ' + (data.source || 'GET /ui/api/entity')
      + ' · 采样时间 ' + (data.sampledAt || '—')
      + ' · T-Box ' + ((data.tbox || {}).versionId || '—')
      + ' · readOnly=' + (data.readOnly ? 'true' : 'false');
  }

  async function loadEntity(iri) {
    const state = el('entity-state');
    state.textContent = '加载中…';
    try {
      const data = await getJson('/ui/api/entity?iri=' + encodeURIComponent(iri));
      state.textContent = '';
      renderSummary(data);
      renderClasses(data);
      renderRequired(data);
      renderProperties(data);
      renderNeighbors(data);
      renderMetrics(data);
      renderSources(data);
      renderSourceNote(data);
    } catch (error) {
      state.textContent = '';
      showError(el('entity-summary'), error);
    }
  }

  document.getElementById('entity-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const iri = el('entity-iri').value.trim();
    if (!iri) { return; }
    const url = new URL(location.href);
    url.searchParams.set('iri', iri);
    history.replaceState(null, '', url);
    loadEntity(iri);
  });

  const initial = new URLSearchParams(location.search).get('iri');
  if (initial) {
    el('entity-iri').value = initial;
    loadEntity(initial);
  }
})();
