/* O-01b dictionary comment coverage: read-only pg_description coverage panel.
 * Independent file; browse.js and browse_dict.js are not modified. */
(function () {
  'use strict';

  function el(id) {
    return document.getElementById(id);
  }

  async function getJson(url) {
    var response = await fetch(url, { headers: { Accept: 'application/json' } });
    var data = await response.json().catch(function () { return {}; });
    if (!response.ok) {
      var message = data.message || data.detail || ('HTTP ' + response.status);
      throw new Error(message);
    }
    return data;
  }

  function cell(value, className) {
    var td = document.createElement('td');
    td.textContent = value == null || value === '' ? '—' : String(value);
    if (className) td.className = className;
    return td;
  }

  function percent(item) {
    return item.ratePercent == null ? '—' : String(item.ratePercent) + '%';
  }

  function render(data) {
    var totals = data.totals || {};
    var summary = el('dictcov-summary');
    var table = el('dictcov-table');
    var tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    (data.items || []).forEach(function (item) {
      var tr = document.createElement('tr');
      tr.appendChild(cell(item.table));
      tr.appendChild(cell(item.columns));
      tr.appendChild(cell(item.commented));
      tr.appendChild(cell(item.missing));
      tr.appendChild(cell(percent(item)));
      tbody.appendChild(tr);
    });
    var complete = data.complete === true;
    summary.textContent = complete
      ? '覆盖 ' + totals.commented + ' / ' + totals.columns + ' 列（100%）'
      : '覆盖 ' + totals.commented + ' / ' + totals.columns + ' 列（' + percent(totals) + '）';
    summary.className = complete ? 'sub dictcov-ok' : 'sub dictcov-gap';
    table.hidden = false;
  }

  async function load() {
    var summary = el('dictcov-summary');
    var empty = el('dictcov-empty');
    summary.textContent = '加载中…';
    empty.hidden = true;
    try {
      render(await getJson('/catalog/dictionaries/comment-coverage'));
    } catch (err) {
      summary.textContent = '';
      empty.textContent = '注释覆盖率暂不可用：' + err.message;
      empty.hidden = false;
    }
  }

  function build() {
    var host = el('view-dictionaries');
    if (!host || el('dictcov-panel')) return;

    var panel = document.createElement('section');
    panel.id = 'dictcov-panel';
    panel.innerHTML =
      '<h3>注释覆盖率 <span class="sub">GET /catalog/dictionaries/comment-coverage</span></h3>' +
      '<div class="hint">只读统计：直接读取 pg_description，不经字典快照，也不写入任何数据。' +
      '覆盖率 100% 表示 28 张事实表全部物理列都有业务含义注释。</div>' +
      '<div id="dictcov-summary" class="sub">加载中…</div>' +
      '<div id="dictcov-empty" class="empty" hidden></div>' +
      '<table id="dictcov-table" class="data-table" hidden>' +
      '<thead><tr><th>表</th><th>列数</th><th>已注释</th><th>缺注释</th><th>覆盖率</th></tr></thead>' +
      '<tbody></tbody></table>';
    host.appendChild(panel);
    load();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
