/* G4 retrieval UI (R-01..R-04). Standalone file: no edits to browse.js/entity.js.
 * Loaded by answer_panel.html and, via one script line, by index/search/browse/entity.
 */
(function () {
  'use strict';

  var API_BASE = location.protocol === 'file:' ? 'http://127.0.0.1:8080' : '';

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function pct(value) {
    if (value == null || Number.isNaN(Number(value))) { return '—'; }
    return (Number(value) * 100).toFixed(2) + '%';
  }

  function num(value) {
    return value == null ? '—' : String(value);
  }

  async function getJson(path) {
    var response = await fetch(API_BASE + path, { headers: { Accept: 'application/json' } });
    var body = null;
    try { body = await response.json(); } catch (_err) { body = null; }
    if (!response.ok) {
      var detail = (body && body.error) || { code: response.status, message: response.statusText };
      throw detail;
    }
    return body;
  }

  function emptyBox(target, message) {
    target.classList.remove('empty');
    target.innerHTML = '<div class="g4-empty">' + esc(message) + '</div>';
  }

  function errorBox(target, error) {
    target.classList.remove('empty');
    var code = (error && (error.providerCode || error.code)) || 'ERROR';
    var message = (error && error.message) || String(error);
    target.innerHTML = '<div class="error">' + esc(code) + ' · ' + esc(message) + '</div>';
  }

  function reasonText(reason) {
    var labels = {
      no_queries_matched_filters: '当前筛选条件下没有查询（接口返回 0 条）',
      no_query_set: '查询集为空',
      runtime_unavailable: '运行时不可用：本体版本/图库未就绪，面板无法出数',
      no_golden_cases: 'golden set 为空',
      no_fields: '该实体没有可展示的字段（privacy/空实体）'
    };
    return labels[reason] || ('无数据：' + (reason || '未知原因'));
  }

  function table(headers, rows, cls) {
    if (!rows.length) { return ''; }
    var head = headers.map(function (item) { return '<th>' + esc(item) + '</th>'; }).join('');
    var body = rows.map(function (row) { return '<tr>' + row + '</tr>'; }).join('');
    return '<table class="data-table ' + (cls || '') + '"><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
  }

  function badge(state, label) {
    return '<span class="g4-badge g4-badge-' + esc(state) + '">' + esc(label) + '</span>';
  }

  /* ---------------- R-01 coverage panel ---------------- */

  function coverageFilters() {
    return '<div class="g4-toolbar">'
      + '<label>问题类型<select id="g4-intent">'
      + '<option value="all">全部</option><option value="value">value</option><option value="definition">definition</option>'
      + '</select></label>'
      + '<label>查询组<select id="g4-group">'
      + '<option value="all">全部</option><option value="A">A</option><option value="B">B</option><option value="C">C</option>'
      + '</select></label>'
      + '<label>层<select id="g4-layer">'
      + '<option value="all">全部</option><option value="ontology">ontology</option><option value="terms">terms</option>'
      + '<option value="metrics">metrics</option><option value="facts">facts</option>'
      + '</select></label>'
      + '<button id="g4-refresh">刷新</button>'
      + '<span id="g4-panel-meta" class="sub"></span>'
      + '</div>';
  }

  async function renderCoverage(target, force) {
    if (!target) { return; }
    if (!target.dataset.mounted) {
      target.dataset.mounted = '1';
      target.classList.remove('empty');
      target.innerHTML = coverageFilters() + '<div id="g4-coverage-body" class="empty">加载中…</div>';
      document.getElementById('g4-refresh').addEventListener('click', function () { renderCoverage(target, true); });
      ['g4-intent', 'g4-group', 'g4-layer'].forEach(function (id) {
        document.getElementById(id).addEventListener('change', function () { renderCoverage(target, true); });
      });
    }
    var body = document.getElementById('g4-coverage-body');
    var intent = document.getElementById('g4-intent').value;
    var group = document.getElementById('g4-group').value;
    var layer = document.getElementById('g4-layer').value;
    var path = '/answerable/panel?intent=' + encodeURIComponent(intent)
      + '&group=' + encodeURIComponent(group)
      + '&layer=' + encodeURIComponent(layer)
      + '&limit=24';
    try {
      var data = await getJson(path);
      document.getElementById('g4-panel-meta').textContent =
        '评估 ' + num(data.querySet && data.querySet.evaluated) + ' / ' + num(data.querySet && data.querySet.count)
        + ' · ' + (data.generatedAt || '');
      if (data.empty) {
        emptyBox(body, reasonText(data.emptyReason));
        return;
      }
      data.__force = force;
      renderCoverageBody(body, data);
    } catch (error) {
      errorBox(body, error);
    }
  }

  function renderCoverageBody(target, data) {
    target.classList.remove('empty');
    var html = '';

    html += '<div class="g4-kpis">';
    (data.layers || []).forEach(function (item) {
      html += '<div class="g4-kpi"><b>' + num(item.covered) + ' / ' + num(item.evaluated) + '</b>'
        + '<span>' + esc(item.layer) + ' · covered ' + num(item.covered)
        + ' · partial ' + num(item.partial) + ' · missing ' + num(item.missing)
        + ' · 覆盖 ' + pct(item.coverageRate) + '</span></div>';
    });
    html += '<div class="g4-kpi"><b>' + num((data.misjudgments || {}).count) + '</b>'
      + '<span>误判 ' + pct((data.misjudgments || {}).rate) + ' / ' + num((data.misjudgments || {}).evaluated)
      + ' · 术语扩展 ' + pct((data.termExpansion || {}).rate) + '</span></div>';
    html += '</div>';

    var term = data.termExpansion || {};
    html += '<h3>术语扩展误判（24 条查询集）</h3>';
    if (term.status === 'ok') {
      html += '<div class="hint">expanded ' + num(term.evaluated) + ' · wrong ' + num(term.misjudged)
        + ' · 误判率 ' + pct(term.rate) + '（当前基线 9.09%）</div>';
      if (term.items && term.items.length) {
        html += '<table class="data-table"><thead><tr><th>ID</th><th>查询</th><th>扩展命中</th><th>期望类</th><th>误判命中</th></tr></thead><tbody>';
        term.items.forEach(function (item) {
          html += '<tr><td>' + esc(item.id) + '</td><td>' + esc(item.query) + '</td><td>'
            + esc((item.expanded || []).map(localName).join(', ')) + '</td><td>'
            + esc((item.expected || []).map(localName).join(', ')) + '</td><td class="g4-fail">'
            + esc((item.wrong || []).map(localName).join(', ')) + '</td></tr>';
        });
        html += '</tbody></table>';
      } else {
        html += '<div class="hint">本次评估没有误判命中。</div>';
      }
    } else {
      html += '<div class="g4-empty">不可算：' + esc(term.reason || 'termlex 不可用') + '</div>';
    }

    html += '<h3>missing 分布 <span class="sub">共 ' + num((data.missing || {}).total) + ' 条</span></h3>';
    var byCode = (data.missing || {}).byCode || [];
    html += byCode.length
      ? table(['层', 'code', '次数'], byCode.map(function (item) {
        return '<td>' + esc(item.layer) + '</td><td>' + esc(item.code) + '</td><td>' + num(item.count) + '</td>';
      }))
      : '<div class="hint">无 missing 记录（全部覆盖或均为 not_applicable）。</div>';

    html += '<h3>candidates <span class="sub">去重 ' + num((data.candidates || {}).total) + '</span></h3>';
    var candidates = (data.candidates || {}).items || [];
    html += candidates.length
      ? table(['层', 'ID', '标签', '命中次数', '示例查询'], candidates.slice(0, 20).map(function (item) {
        return '<td>' + esc(item.layer) + '</td><td>' + esc(localName(item.id)) + '</td><td>' + esc(item.label || '—')
          + '</td><td>' + num(item.count) + '</td><td>' + esc((item.queries || []).join(' / ')) + '</td>';
      }))
      : '<div class="hint">没有 candidates。</div>';

    html += '<h3>趋势（按查询组 / 问题类型）</h3>';
    var byGroup = (data.trend || {}).byGroup || [];
    html += byGroup.length
      ? table(['组', '评估', 'answerable', 'ontology', 'terms', 'metrics', 'facts'], byGroup.map(function (item) {
        function cell(name) {
          var value = (item.layers || {})[name] || {};
          return num(value.covered) + '/' + num(value.denominator) + ' (' + pct(value.rate) + ')';
        }
        return '<td>' + esc(item.bucket) + '</td><td>' + num(item.evaluated) + '</td><td>' + num(item.answerable)
          + '</td><td>' + cell('ontology') + '</td><td>' + cell('terms') + '</td><td>' + cell('metrics')
          + '</td><td>' + cell('facts') + '</td>';
      }))
      : '<div class="hint">趋势无数据。</div>';

    html += '<h3>误判下钻 <span class="sub">点击行展开 layerStatuses / missingCodes</span></h3>';
    var mis = (data.misjudgments || {}).items || [];
    if (mis.length) {
      html += '<table class="data-table"><thead><tr><th>ID</th><th>查询</th><th>组</th><th>判定</th><th>answerable</th><th>reason</th></tr></thead><tbody>';
      mis.forEach(function (item, index) {
        var detail = JSON.stringify({
          layerStatuses: item.layerStatuses || {},
          missingCodes: item.missingCodes || [],
          drillDownUrl: item.drillDownUrl
        });
        html += '<tr class="g4-drill" data-detail="' + esc(detail) + '" data-row="' + index + '">'
          + '<td>' + esc(item.id) + '</td><td>' + esc(item.query) + '</td><td>' + esc(item.group) + '</td>'
          + '<td class="' + (item.verdict === 'ok' ? 'g4-pass' : 'g4-fail') + '">' + esc(item.verdict)
          + '</td><td>' + (item.answerable ? 'true' : 'false') + '</td><td>' + esc(item.reasonCode || '—') + '</td></tr>';
        html += '<tr class="g4-drill-detail" data-detail-row="' + index + '" hidden><td colspan="6">'
          + '<code>' + esc(detail) + '</code> · <a href="' + esc(API_BASE + (item.drillDownUrl || '')) + '">打开原始 panel</a>'
          + '</td></tr>';
      });
      html += '</tbody></table>';
    } else {
      html += '<div class="hint">没有误判（overclaim/underclaim 均为 0）。</div>';
    }

    if (data.errors && data.errors.length) {
      html += '<h3>评估错误</h3>' + table(['ID', '查询', '错误'], data.errors.map(function (item) {
        return '<td>' + esc(item.queryId) + '</td><td>' + esc(item.query) + '</td><td>' + esc(item.error) + ' · ' + esc(item.message) + '</td>';
      }));
    }

    target.innerHTML = html;
    target.querySelectorAll('.g4-drill').forEach(function (row) {
      row.addEventListener('click', function () {
        var detail = document.querySelector('[data-detail-row="' + row.dataset.row + '"]');
        if (detail) { detail.hidden = !detail.hidden; }
      });
    });
  }

  function localName(iri) {
    var text = String(iri == null ? '' : iri);
    var cut = Math.max(text.lastIndexOf('#'), text.lastIndexOf('/'));
    return cut >= 0 ? text.slice(cut + 1) : text;
  }

  /* ---------------- R-02 answer quality ---------------- */

  async function renderQuality(target) {
    if (!target) { return; }
    if (!target.dataset.mounted) {
      target.dataset.mounted = '1';
      target.classList.remove('empty');
      target.innerHTML = '<div class="g4-toolbar">'
        + '<label>策略<select id="g4-strategy"><option value="lexical">lexical</option>'
        + '<option value="vector">vector</option><option value="hybrid">hybrid</option></select></label>'
        + '<button id="g4-quality-refresh">运行 golden set</button>'
        + '<span id="g4-quality-meta" class="sub"></span></div>'
        + '<div id="g4-quality-body" class="empty">加载中…</div>';
      document.getElementById('g4-quality-refresh').addEventListener('click', function () { renderQuality(target); });
      document.getElementById('g4-strategy').addEventListener('change', function () { renderQuality(target); });
    }
    var body = document.getElementById('g4-quality-body');
    var strategy = document.getElementById('g4-strategy').value;
    try {
      var data = await getJson('/answer/quality?strategy=' + encodeURIComponent(strategy) + '&limit=10');
      var summary = data.summary || {};
      document.getElementById('g4-quality-meta').textContent =
        'pass ' + num(summary.passed) + '/' + num(summary.cases) + ' · brokenLinkRate ' + pct(summary.brokenLinkRate);
      if (data.empty) {
        emptyBox(body, reasonText(data.emptyReason));
        return;
      }
      var html = '<div class="g4-kpis">'
        + '<div class="g4-kpi"><b>' + num(summary.passed) + ' / ' + num(summary.cases) + '</b><span>golden pass · ' + pct(summary.passRate) + '</span></div>'
        + '<div class="g4-kpi"><b>' + pct(summary.citationCoverageRate) + '</b><span>citation 覆盖率 · ' + num(summary.casesWithCitations) + '/' + num(summary.cases) + '</span></div>'
        + '<div class="g4-kpi"><b>' + pct(summary.citationResolvableRate) + '</b><span>citation 可解析 · ' + num(summary.resolvableCitations) + '/' + num(summary.citations) + '</span></div>'
        + '<div class="g4-kpi"><b>' + pct(summary.brokenLinkRate) + '</b><span>断链率 · 基线 ' + pct(summary.baselineBrokenLinkRate) + ' · 退化 ' + (summary.regression ? '是' : '否') + '</span></div>'
        + '<div class="g4-kpi"><b>' + num((data.refusalsWithoutLayers || []).length) + '</b><span>拒答缺层违规</span></div>'
        + '</div>';

      html += '<h3>10 例 golden set</h3>';
      html += table(['ID', '查询', '类型', '期望拒答', '实际拒答', 'answerType', 'citation', '结果', '失败原因'], (data.cases || []).map(function (item) {
        var actual = item.actual || {};
        return '<td>' + esc(item.id) + '</td><td>' + esc(item.query) + '</td><td>' + esc(item.type) + '</td><td>'
          + (item.expectRefused ? 'true' : 'false') + '</td><td>' + (actual.refused ? 'true' : 'false') + '</td><td>'
          + esc(actual.answerType || '—') + '</td><td>' + num((actual.citations || []).length) + '</td><td class="'
          + (item.pass ? 'g4-pass' : 'g4-fail') + '">' + (item.pass ? 'PASS' : 'FAIL') + '</td><td>'
          + esc((item.failures || []).join('; ') || '—') + '</td>';
      }));

      html += '<h3>citation 覆盖率（按类型）</h3>' + table(['类型', 'cases', 'withCitations', 'citations', 'resolvable', '覆盖率', '可解析率'], (data.citationCoverageByType || []).map(function (item) {
        return '<td>' + esc(item.type) + '</td><td>' + num(item.cases) + '</td><td>' + num(item.withCitations)
          + '</td><td>' + num(item.citations) + '</td><td>' + num(item.resolvable) + '</td><td>'
          + pct(item.citationCoverageRate) + '</td><td>' + pct(item.resolvableRate) + '</td>';
      }));

      html += '<h3>拒答原因（按类型）</h3>' + table(['类型', 'reasonCode', '次数'], (data.refusalsByReason || []).map(function (item) {
        return '<td>' + esc(item.type) + '</td><td>' + esc(item.reasonCode) + '</td><td>' + num(item.count) + '</td>';
      }));

      html += '<h3>拒答缺层违规 <span class="sub">拒答必须带缺层</span></h3>';
      html += (data.refusalsWithoutLayers || []).length
        ? table(['ID', '查询', '类型'], data.refusalsWithoutLayers.map(function (item) {
          return '<td class="g4-fail">' + esc(item.id) + '</td><td>' + esc(item.query) + '</td><td>' + esc(item.type) + '</td>';
        }))
        : '<div class="hint">0 条违规：所有拒答均带缺层。</div>';

      html += '<h3>断链明细 <span class="sub">当前断链率 ' + pct(summary.brokenLinkRate) + '</span></h3>';
      html += (data.brokenLinks || []).length
        ? table(['ID', '查询', 'citation'], data.brokenLinks.map(function (item) {
          return '<td>' + esc(item.id) + '</td><td>' + esc(item.query) + '</td><td>' + esc(JSON.stringify(item.citation)) + '</td>';
        }))
        : '<div class="hint">0 断链：全部 citation 可解析。</div>';

      body.classList.remove('empty');
      target.querySelector('#g4-quality-body').innerHTML = html;
    } catch (error) {
      errorBox(body, error);
    }
  }

  /* ---------------- R-03 entity provenance ---------------- */

  async function renderProvenance(target, iri) {
    if (!target) { return; }
    if (!iri) { emptyBox(target, '请输入实体 IRI'); return; }
    target.classList.add('empty');
    target.textContent = '加载中…';
    try {
      var data = await getJson('/entity/provenance?iri=' + encodeURIComponent(iri));
      var summary = data.summary || {};
      var meta = document.getElementById('g4-prov-summary');
      if (meta) {
        meta.textContent = '字段 ' + num(summary.total) + ' · 有溯源 ' + num(summary.evidenced)
          + ' · 仅推理 ' + num(summary.inferred) + ' · 无 ' + num(summary.none)
          + ' · 覆盖率 ' + pct(summary.coverageRate);
      }
      if (data.empty) {
        emptyBox(target, reasonText(data.emptyReason));
        return;
      }
      var html = '<div class="hint">' + esc(data.note || '') + '</div>';
      html += table(['字段', '取值', '徽标', '依据', '链接'], (data.fields || []).map(function (item) {
        var state = (item.badge || {}).state || 'none';
        var label = (item.badge || {}).label || '无';
        var links = (item.links || []).map(function (link) {
          return '<a href="' + esc(API_BASE + link.url) + '">' + esc(link.kind) + '</a>';
        }).join(' ');
        var value = item.valueText || (item.values || []).map(function (term) {
          return term && term.value != null ? term.value : localName(term && term.iri);
        }).join(', ');
        return '<td>' + esc(item.label || localName(item.property)) + '</td><td>' + esc(value || '—')
          + '</td><td>' + badge(state, label) + '</td><td>' + esc((item.badge || {}).basis || '') + '</td><td>'
          + (links || '—') + '</td>';
      }));
      html += '<h3>实体级来源 <span class="sub">sourceRef / PROV</span></h3>';
      html += (data.entitySources || []).length
        ? table(['kind', 'ref', '文本', '链接'], data.entitySources.map(function (item) {
          return '<td>' + esc(item.kind || '—') + '</td><td>' + esc(item.ref || '—') + '</td><td>'
            + esc((item.text || '').slice(0, 120)) + '</td><td>'
            + (item.resolveUrl ? '<a href="' + esc(API_BASE + item.resolveUrl) + '">打开</a>' : '—') + '</td>';
        }))
        : '<div class="hint">无实体级 sourceRef / PROV；字段徽标已显式标注「无」。</div>';
      target.classList.remove('empty');
      target.innerHTML = html;
    } catch (error) {
      errorBox(target, error);
    }
  }

  function mountProvenanceSection(target, iri, summaryTarget) {
    if (!target) { return; }
    var html = '<div class="g4-toolbar">'
      + '<label>实体 IRI<input id="g4-prov-iri-inline" type="text" size="60" value="' + esc(iri || '') + '"></label>'
      + '<button id="g4-prov-run-inline">查询溯源</button>'
      + (summaryTarget ? '<span id="' + summaryTarget + '" class="sub"></span>' : '')
      + '</div><div id="g4-prov-body-inline" class="empty">' + (iri ? '加载中…' : '输入实体 IRI 后查询') + '</div>';
    target.innerHTML = html;
    var input = target.querySelector('#g4-prov-iri-inline');
    target.querySelector('#g4-prov-run-inline').addEventListener('click', function () {
      renderProvenance(target.querySelector('#g4-prov-body-inline'), input.value.trim());
      var meta = summaryTarget ? document.getElementById(summaryTarget) : null;
      if (meta) { meta.setAttribute('data-note', ''); }
    });
  }

  /* ---------------- R-04 browse links ---------------- */

  function renderCrossLinks(target) {
    if (!target) { return; }
    target.classList.remove('empty');
    var rows = [
      { id: 'triples-to-entity', label: '三元组 → 实体页', placeholder: '实体 IRI', param: 'iri' },
      { id: 'metrics-to-definition', label: '口径卡 → 口径定义', placeholder: 'metricId（如 FIN-...）', param: 'metricId' },
      { id: 'tree-to-entity', label: '类树 → 实体页', placeholder: '类/实例 IRI', param: 'classIri' },
      { id: 'entity-to-tab', label: '实体页 → 浏览 tab', placeholder: '实体 IRI', param: 'entity' }
    ];
    var html = '<div class="hint">四条路径均为 GET、URL 稳定、不新增写操作。</div><div class="g4-links">';
    rows.forEach(function (row) {
      html += '<div class="g4-link-row" data-path="' + esc(row.id) + '">'
        + '<strong>' + esc(row.label) + '</strong>'
        + '<input type="text" data-param="' + esc(row.param) + '" placeholder="' + esc(row.placeholder) + '">'
        + '<button data-open="' + esc(row.id) + '">打开</button>'
        + '<code data-template="' + esc(row.id) + '"></code></div>';
    });
    html += '</div>';
    target.innerHTML = html;
    getJson('/browse/links').then(function (data) {
      (data.paths || []).forEach(function (item) {
        var row = target.querySelector('[data-path="' + item.id + '"]');
        if (row) { row.querySelector('[data-template]').textContent = item.template; }
      });
    }).catch(function () { /* templates stay empty; buttons still build URLs */ });

    target.querySelectorAll('[data-open]').forEach(function (button) {
      button.addEventListener('click', function () {
        var pathId = button.dataset.open;
        var row = button.closest('.g4-link-row');
        var value = row.querySelector('input').value.trim();
        var url;
        if (pathId === 'triples-to-entity') {
          url = '/ui/entity.html?iri=' + encodeURIComponent(value);
        } else if (pathId === 'metrics-to-definition') {
          url = '/ui/browse.html?tab=metrics&metricId=' + encodeURIComponent(value);
        } else if (pathId === 'tree-to-entity') {
          url = '/ui/entity.html?iri=' + encodeURIComponent(value);
        } else {
          url = '/ui/browse.html?tab=ontology&entity=' + encodeURIComponent(value);
        }
        location.href = API_BASE + url;
      });
    });
  }

  /* ---------------- mounts ---------------- */

  function mountSearchPage() {
    var main = document.querySelector('main');
    if (!main || document.getElementById('g4-coverage')) { return; }
    var coverage = document.createElement('section');
    coverage.className = 'panel';
    coverage.innerHTML = '<h2>R-01 分层覆盖度 <span class="sub">24 条查询集 · 只读</span></h2><div id="g4-coverage" class="empty">加载中…</div>';
    var quality = document.createElement('section');
    quality.className = 'panel';
    quality.innerHTML = '<h2>R-02 引用与拒答质量 <span class="sub">10 例 golden set · 只读</span></h2><div id="g4-quality" class="empty">加载中…</div>';
    main.insertBefore(quality, main.firstChild);
    main.insertBefore(coverage, main.firstChild);
    renderCoverage(document.getElementById('g4-coverage'));
    renderQuality(document.getElementById('g4-quality'));
  }

  function mountBrowsePage() {
    var main = document.querySelector('main');
    if (!main) { return; }
    var params = new URLSearchParams(location.search);
    var tab = params.get('tab');
    var metricId = params.get('metricId');
    var entity = params.get('entity');
    if (tab) {
      setTimeout(function () {
        var button = document.querySelector('.tab[data-view="' + tab + '"]');
        if (button) { button.click(); }
        if (metricId) {
          var inputs = document.querySelectorAll('input');
          inputs.forEach(function (input) {
            if (input.value === metricId) { input.dispatchEvent(new Event('change', { bubbles: true })); }
          });
        }
      }, 0);
    }
    if (entity) {
      var banner = document.createElement('div');
      banner.className = 'panel';
      banner.innerHTML = '<div class="hint">来自实体页：<a href="' + esc(API_BASE + '/ui/entity.html?iri=' + encodeURIComponent(entity)) + '">'
        + esc(entity) + '</a></div>';
      main.insertBefore(banner, main.firstChild);
    }
    var section = document.createElement('section');
    section.className = 'panel';
    section.innerHTML = '<h2>R-04 交叉跳转 <span class="sub">triples→entity · metrics→definition · tree→entity · entity→tab</span></h2><div id="g4-crosslinks"></div>';
    main.insertBefore(section, main.firstChild);
    renderCrossLinks(document.getElementById('g4-crosslinks'));
  }

  function mountEntityPage() {
    var main = document.querySelector('main');
    if (!main || document.getElementById('g4-entity-prov-panel')) { return; }
    var section = document.createElement('section');
    section.className = 'panel';
    section.id = 'g4-entity-prov-panel';
    section.innerHTML = '<h2>R-03 字段溯源徽标 <span class="sub">有 sourceRef / PROV = 有溯源；无 = 显式「无」</span></h2>'
      + '<div id="g4-entity-prov" class="empty">加载中…</div>';
    main.appendChild(section);
    var params = new URLSearchParams(location.search);
    var iri = params.get('iri');
    mountProvenanceSection(document.getElementById('g4-entity-prov'), iri, null);
    if (iri) { renderProvenance(document.getElementById('g4-prov-body-inline'), iri); }
    var form = document.getElementById('entity-form');
    if (form) {
      form.addEventListener('submit', function () {
        var input = document.getElementById('entity-iri');
        setTimeout(function () {
          var current = input ? input.value.trim() : '';
          var inline = document.getElementById('g4-prov-iri-inline');
          if (inline) { inline.value = current; }
          renderProvenance(document.getElementById('g4-prov-body-inline'), current);
        }, 700);
      });
    }
    var link = document.createElement('div');
    link.className = 'hint';
    link.innerHTML = '多 tab 跳转：'
      + '<a href="' + esc(API_BASE + '/ui/browse.html?tab=ontology' + (iri ? '&entity=' + encodeURIComponent(iri) : '')) + '">本体上下文</a> · '
      + '<a href="' + esc(API_BASE + '/ui/browse.html?tab=metrics' + (iri ? '&entity=' + encodeURIComponent(iri) : '')) + '">相关口径</a> · '
      + '<a href="' + esc(API_BASE + '/ui/browse.html?tab=triples' + (iri ? '&entity=' + encodeURIComponent(iri) : '')) + '">三元组</a>';
    section.appendChild(link);
  }

  function mountOverviewLink() {
    var nav = document.querySelector('nav');
    if (!nav || nav.querySelector('[data-nav="answer-panel"]')) { return; }
    var link = document.createElement('a');
    link.href = 'answer_panel.html';
    link.dataset.nav = 'answer-panel';
    link.textContent = '检索问答质量';
    nav.appendChild(link);
  }

  function mountPanelPage() {
    var prov = document.getElementById('g4-provenance');
    var iri = new URLSearchParams(location.search).get('iri') || '';
    prov.classList.remove('empty');
    prov.innerHTML = '<div id="g4-prov-body-main" class="empty">' + (iri ? '加载中…' : '输入实体 IRI 后查询') + '</div>';
    var run = function () {
      renderProvenance(document.getElementById('g4-prov-body-main'),
        document.getElementById('g4-prov-iri').value.trim());
    };
    document.getElementById('g4-prov-run').addEventListener('click', run);
    document.getElementById('g4-prov-iri').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') { run(); }
    });
    if (iri) { renderProvenance(document.getElementById('g4-prov-body-main'), iri); }
    renderCoverage(document.getElementById('g4-coverage'));
    renderQuality(document.getElementById('g4-quality'));
    renderCrossLinks(document.getElementById('g4-crosslinks'));
  }

  function init() {
    var page = document.body.dataset.page;
    if (page === 'overview') { mountOverviewLink(); }
    if (page === 'search') { mountSearchPage(); }
    if (page === 'browse') { mountBrowsePage(); }
    if (page === 'entity') { mountEntityPage(); }
    if (page === 'answer-panel') { mountPanelPage(); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
