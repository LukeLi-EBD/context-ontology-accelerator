(function () {
  'use strict';

  function el(id) { return document.getElementById(id); }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function show(value) {
    if (value === null || value === undefined) { return '<span class="badge bad">不可算</span>'; }
    return esc(value);
  }

  function pct(value) {
    if (value === null || value === undefined) { return '不可算'; }
    return (Number(value) * 100).toFixed(1) + '%';
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
      throw (body && body.error) || { code: response.status, message: response.statusText };
    }
    return body;
  }

  function errorNote(error) {
    return error ? '<div class="hint">error：' + esc(error) + '</div>' : '';
  }

  function renderSummary(data) {
    const target = el('health-summary');
    target.classList.remove('empty');
    const ready = (data.readyz || {});
    const readyBadge = ready.status === 'ok'
      ? '<span class="badge ok">ok</span>' : '<span class="badge bad">degraded</span>';
    const tbox = data.tbox || {};
    const migration = data.migration || {};
    const migrateBadge = migration.consistent === true
      ? '<span class="badge ok">一致</span>'
      : (migration.consistent === false ? '<span class="badge bad">不一致</span>' : '<span class="badge bad">不可算</span>');
    target.innerHTML = '<div class="kpi">'
      + '<div><b>' + readyBadge + '</b><span>readyz</span></div>'
      + '<div><b class="mono" style="font-size:15px">' + esc(tbox.versionId || '—') + '</b><span>tbox/current ' + esc(tbox.semver || '') + '</span></div>'
      + '<div><b>' + migrateBadge + '</b><span>schema</span></div>'
      + '<div><b style="font-size:15px">' + esc(data.sampledAt || '—') + '</b><span>采样时间</span></div>'
      + '</div>'
      + '<div style="margin-top:10px">' + (ready.checks ? '<table><tr><th>检查</th><th>状态</th><th>详情</th></tr>'
        + Object.keys(ready.checks).map(function (name) {
          const item = ready.checks[name] || {};
          return '<tr><td>' + esc(name) + '</td><td>'
            + (item.status === 'ok' ? '<span class="badge ok">ok</span>' : '<span class="badge bad">fail</span>')
            + '</td><td>' + esc(item.detail || (item.disk_free_pct != null ? ('磁盘可用 ' + item.disk_free_pct + '%') : '—'))
            + '</td></tr>';
        }).join('') + '</table>' : '') + '</div>';
  }

  function renderCoverage(data) {
    const target = el('health-coverage');
    const coverage = data.coverage || {};
    const classes = coverage.classes || {};
    const properties = coverage.properties || {};
    const instances = coverage.instances || {};
    target.classList.remove('empty');
    target.innerHTML = '<table>'
      + '<tr><th>维度</th><th>总量</th><th>已使用</th><th>覆盖率</th><th>备注</th></tr>'
      + '<tr><td>类（有实例 / 总类）</td><td>' + show(classes.total) + '</td><td>'
      + show(classes.withInstances) + '</td><td>' + pct(classes.ratio) + '</td><td>'
      + '无标签类：' + show(classes.unlabeled) + errorNote(classes.error) + '</td></tr>'
      + '<tr><td>属性（有取值 / 总属性）</td><td>' + show(properties.total) + '</td><td>'
      + show(properties.withValues) + '</td><td>' + pct(properties.ratio) + '</td><td>'
      + errorNote(properties.error) + '</td></tr>'
      + '<tr><td>实例总数</td><td>' + show(instances.total) + '</td><td>—</td><td>—</td><td>'
      + esc((instances.graphs || []).join(', ') || '—') + errorNote(instances.error) + '</td></tr>'
      + '</table>'
      + '<div class="hint">' + esc(coverage.source || '') + '</div>';
  }

  function renderQuality(data) {
    const target = el('health-quality');
    const shacl = data.shaclViolations || {};
    const inference = data.inferenceFailures || {};
    const orphan = data.orphanInstances || {};
    target.classList.remove('empty');
    target.innerHTML = '<table>'
      + '<tr><th>指标</th><th>值</th><th>来源 / 说明</th></tr>'
      + '<tr><td>SHACL 违规数</td><td>' + show(shacl.count) + '</td><td>'
      + esc(shacl.source || '') + (shacl.sampledAt ? (' · 采样 ' + esc(shacl.sampledAt)) : '')
      + (shacl.conforms === false ? ' · <span class="badge bad">conforms=false</span>' : '')
      + errorNote(shacl.error) + (shacl.note ? '<div class="hint">' + esc(shacl.note) + '</div>' : '')
      + '</td></tr>'
      + '<tr><td>推理失败数</td><td>' + show(inference.count) + '</td><td>'
      + esc(inference.source || '')
      + (inference.lastJob ? (' · 最近作业 ' + esc(inference.lastJob.state || '—')) : '')
      + errorNote(inference.error) + '</td></tr>'
      + '<tr><td>孤实例数</td><td>' + show(orphan.count) + '</td><td>'
      + esc(orphan.source || '') + errorNote(orphan.error) + '</td></tr>'
      + '</table>';
  }

  function renderMigration(data) {
    const target = el('health-migration');
    const migration = data.migration || {};
    target.classList.remove('empty');
    target.innerHTML = '<div class="kpi">'
      + '<div><b>' + show(migration.codeVersion) + '</b><span>代码 schema 版本</span></div>'
      + '<div><b>' + show(migration.dbVersion) + '</b><span>数据库 MAX(version)</span></div>'
      + '<div><b>' + (migration.consistent === true
        ? '<span class="badge ok">一致</span>'
        : (migration.consistent === false ? '<span class="badge bad">不一致</span>' : '<span class="badge bad">不可算</span>'))
      + '</b><span>一致性</span></div>'
      + '</div><div class="hint">' + esc(migration.source || '') + errorNote(migration.error) + '</div>';
  }

  function renderSource(data) {
    const source = data.dataSource || {};
    el('health-source').innerHTML =
      '端点：' + esc((source.endpoints || []).join('；') || '—')
      + '<br>采样时间：' + esc(source.sampledAt || data.sampledAt || '—')
      + '<br>' + esc(source.note || '');
  }

  async function loadDashboard() {
    try {
      const data = await getJson('/health/dashboard');
      renderSummary(data);
      renderCoverage(data);
      renderQuality(data);
      renderMigration(data);
      renderSource(data);
    } catch (error) {
      showError(el('health-summary'), error);
    }
  }

  function renderTerm(term) {
    if (!term) { return '—'; }
    return esc(term.value == null ? '—' : term.value);
  }

  function renderExampleList(items, triple) {
    if (!(items || []).length) { return '<div class="empty">无示例</div>'; }
    if (triple) {
      return '<table><tr><th>s</th><th>p</th><th>o</th></tr>'
        + items.map(function (item) {
          return '<tr><td class="mono">' + renderTerm(item.s) + '</td><td class="mono">'
            + renderTerm(item.p) + '</td><td class="mono">' + renderTerm(item.o) + '</td></tr>';
        }).join('') + '</table>';
    }
    return '<div class="chips">' + items.map(function (item) {
      return '<span class="chip mono">' + esc(item) + '</span>';
    }).join('') + '</div>';
  }

  function renderDiff(data) {
    const counts = data.counts || {};
    const examples = data.examples || {};
    const rows = [
      ['类', counts.addedClasses, counts.removedClasses, 'addedClasses', 'removedClasses'],
      ['属性', counts.addedProperties, counts.removedProperties, 'addedProperties', 'removedProperties'],
      ['三元组', counts.addedTriples, counts.removedTriples, 'addedTriples', 'removedTriples'],
    ].map(function (row) {
      return '<tr><td>' + row[0] + '</td><td>' + esc(row[1] == null ? '不可算' : row[1])
        + '</td><td>' + esc(row[2] == null ? '不可算' : row[2]) + '</td></tr>';
    }).join('');
    el('diff-result').classList.remove('empty');
    el('diff-result').innerHTML =
      '<div class="sub">from ' + esc(data.from) + ' (' + esc((data.resolved.from || {}).semver || '—')
      + ') → to ' + esc(data.to) + ' (' + esc((data.resolved.to || {}).semver || '—')
      + ') · breaking=' + (data.breaking ? 'true' : 'false') + '</div>'
      + '<table><tr><th>类别</th><th>新增</th><th>删除</th></tr>' + rows + '</table>'
      + '<h3 style="font-size:13px">新增类示例</h3>' + renderExampleList(examples.addedClasses)
      + '<h3 style="font-size:13px">删除类示例</h3>' + renderExampleList(examples.removedClasses)
      + '<h3 style="font-size:13px">新增属性示例</h3>' + renderExampleList(examples.addedProperties)
      + '<h3 style="font-size:13px">删除属性示例</h3>' + renderExampleList(examples.removedProperties)
      + '<h3 style="font-size:13px">新增三元组示例</h3>' + renderExampleList(examples.addedTriples, true)
      + '<h3 style="font-size:13px">删除三元组示例</h3>' + renderExampleList(examples.removedTriples, true)
      + '<div class="hint">端点 ' + esc(data.source || '') + ' · 采样 ' + esc(data.sampledAt || '—')
      + ' · 示例上限 ' + esc(data.exampleLimit) + '</div>';
  }

  document.getElementById('diff-form').addEventListener('submit', async function (event) {
    event.preventDefault();
    const from = el('diff-from').value.trim();
    const to = el('diff-to').value.trim();
    const params = new URLSearchParams();
    if (from) { params.set('from', from); }
    if (to) { params.set('to', to); }
    el('diff-state').textContent = '加载中…';
    try {
      const query = params.toString();
      const data = await getJson('/health/ontology-diff' + (query ? ('?' + query) : ''));
      el('diff-state').textContent = '';
      renderDiff(data);
    } catch (error) {
      el('diff-state').textContent = '';
      showError(el('diff-result'), error);
    }
  });

  document.getElementById('refresh').addEventListener('click', loadDashboard);
  loadDashboard();
})();
