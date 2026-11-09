/* O-01 dictionary views: missing comments / unbound / mappable-unbound.
 * Independent read-only panel; browse.js is not modified. */
(function () {
  'use strict';

  var VIEWS = [
    { id: 'all', label: '全部' },
    { id: 'missing_comment', label: '缺注释列' },
    { id: 'unbound', label: '未绑定列' },
    { id: 'mappable_unbound', label: '可映射未绑定' }
  ];
  var state = { view: 'mappable_unbound', limit: 20, offset: 0, total: 0 };

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

  function cell(value) {
    var td = document.createElement('td');
    td.textContent = value == null || value === '' ? '—' : String(value);
    return td;
  }

  function viewUrl() {
    var params = new URLSearchParams();
    params.set('limit', String(state.limit));
    params.set('offset', String(state.offset));
    var table = (el('dictx-table').value || '').trim();
    if (table) params.set('table', table);
    return '/catalog/dictionaries/views/' + state.view + '?' + params.toString();
  }

  function syncButtons() {
    var buttons = document.querySelectorAll('#dictx-views button[data-view]');
    buttons.forEach(function (button) {
      if (button.getAttribute('data-view') === state.view) {
        button.classList.add('primary');
      } else {
        button.classList.remove('primary');
      }
    });
  }

  function renderPager() {
    var page = Math.floor(state.offset / state.limit) + 1;
    var pages = Math.max(1, Math.ceil(state.total / state.limit));
    el('dictx-page').textContent = '第 ' + page + ' / ' + pages + ' 页';
    el('dictx-prev').disabled = state.offset <= 0;
    el('dictx-next').disabled = state.offset + state.limit >= state.total;
  }

  async function load() {
    var table = el('dictx-table');
    var empty = el('dictx-empty');
    var status = el('dictx-status');
    var view = el('dictx-table-view');
    table.setAttribute('disabled', 'disabled');
    view.hidden = true;
    empty.hidden = true;
    status.textContent = '加载中…';
    try {
      var data = await getJson(viewUrl());
      state.total = data.total || 0;
      status.textContent = '· ' + state.total + ' 行';
      var items = data.items || [];
      if (!items.length) {
        empty.hidden = false;
        renderPager();
        return;
      }
      var tbody = view.querySelector('tbody');
      tbody.innerHTML = '';
      items.forEach(function (item) {
        var tr = document.createElement('tr');
        tr.appendChild(cell(item.table));
        tr.appendChild(cell(item.column));
        tr.appendChild(cell(item.dataType));
        tr.appendChild(cell(item.comment));
        tr.appendChild(cell(item.bindingMethod));
        tr.appendChild(cell(item.propertyIri));
        tr.appendChild(cell(item.bindingNote));
        tbody.appendChild(tr);
      });
      view.hidden = false;
      renderPager();
    } catch (err) {
      status.textContent = '';
      empty.textContent = '加载失败：' + err.message;
      empty.hidden = false;
    } finally {
      table.removeAttribute('disabled');
    }
  }

  function selectView(view) {
    state.view = view;
    state.offset = 0;
    syncButtons();
    load();
  }

  function build() {
    var host = el('view-dictionaries');
    if (!host || el('dictx-panel')) return;

    var panel = document.createElement('section');
    panel.id = 'dictx-panel';
    panel.innerHTML =
      '<h3>字典筛选视图 <span class="sub">GET /catalog/dictionaries/views/{view}</span></h3>' +
      '<div class="filters" id="dictx-views">' +
      '<label>表名 <input type="text" id="dictx-table" placeholder="留空为全部，如 bank_loan_account"></label>' +
      '<span id="dictx-status" class="sub"></span>' +
      '</div>' +
      '<div class="hint">只读视图：缺注释列为 comment 空值；未绑定列为 binding_method=none；' +
      '可映射未绑定列仅统计本体确有字面值属性、但尚未写入绑定的列。' +
      '可映射口径不把数值度量、对象属性（hasStatus/hasCurrency 等）计入，未绑定不等于可绑定。</div>' +
      '<div id="dictx-empty" class="empty" hidden>当前视图没有字典行。</div>' +
      '<table id="dictx-table-view" class="data-table" hidden>' +
      '<thead><tr><th>表</th><th>列</th><th>类型</th><th>注释</th>' +
      '<th>绑定方法</th><th>绑定属性</th><th>说明</th></tr></thead>' +
      '<tbody></tbody></table>' +
      '<div class="pager">' +
      '<button id="dictx-prev" disabled>上一页</button>' +
      '<span id="dictx-page" class="sub"></span>' +
      '<button id="dictx-next" disabled>下一页</button>' +
      '</div>';
    host.appendChild(panel);

    var toolbar = el('dictx-views');
    VIEWS.forEach(function (item) {
      var button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('data-view', item.id);
      button.textContent = item.label;
      button.addEventListener('click', function () {
        selectView(item.id);
      });
      toolbar.appendChild(button);
    });
    el('dictx-table').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        state.offset = 0;
        load();
      }
    });
    el('dictx-prev').addEventListener('click', function () {
      state.offset = Math.max(0, state.offset - state.limit);
      load();
    });
    el('dictx-next').addEventListener('click', function () {
      state.offset += state.limit;
      load();
    });

    syncButtons();
    load();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
