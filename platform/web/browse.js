(function () {
  'use strict';

  function el(id) { return document.getElementById(id); }

  // Same rule as app.js: served by the platform -> relative paths; opened from
  // disk (file://) -> talk to the default stack on 127.0.0.1:8080.
  const API_BASE = location.protocol === 'file:' ? 'http://127.0.0.1:8080' : '';

  async function getJson(url) {
    const response = await fetch(API_BASE + url, { headers: { Accept: 'application/json' } });
    let body = null;
    try { body = await response.json(); } catch (err) { body = null; }
    if (!response.ok) {
      const message = body && body.error ? body.error.message : 'HTTP ' + response.status;
      throw new Error(message);
    }
    return body;
  }

  function showEmpty(node, message) {
    node.classList.add('empty');
    node.textContent = message;
  }

  function renderError(node, err) {
    node.classList.add('empty');
    node.textContent = '加载失败：' + err.message;
  }

  // ---- tabs ---------------------------------------------------------------
  const loaded = { ontology: false, metrics: false, terms: false };
  const tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      tabs.forEach(function (item) { item.classList.toggle('active', item === tab); });
      ['ontology', 'metrics', 'terms'].forEach(function (name) {
        el('view-' + name).hidden = (name !== tab.dataset.view);
      });
      const view = tab.dataset.view;
      if (!loaded[view]) { loaded[view] = true; loadView(view); }
    });
  });

  function loadView(view) {
    if (view === 'ontology') return loadOntology();
    if (view === 'metrics') return loadMetrics();
    if (view === 'terms') return loadTerms();
    return null;
  }

  // ---- ontology -----------------------------------------------------------
  const instanceState = { classIri: null, className: '', limit: 20, offset: 0, total: 0 };

  function classNode(node) {
    const li = document.createElement('li');
    const link = document.createElement('a');
    link.href = '#';
    link.className = 'class-link';
    link.textContent = node.label || node.iri;
    link.title = node.iri;
    link.addEventListener('click', function (event) {
      event.preventDefault();
      selectClass(node);
    });
    li.appendChild(link);
    if (node.children && node.children.length) {
      const ul = document.createElement('ul');
      node.children.forEach(function (child) { ul.appendChild(classNode(child)); });
      li.appendChild(ul);
    }
    return li;
  }

  function selectClass(node) {
    instanceState.classIri = node.iri;
    instanceState.className = node.label || node.iri;
    instanceState.offset = 0;
    el('instance-head').textContent = instanceState.className + ' · ' + node.iri;
    loadInstances();
  }

  async function loadInstances() {
    const list = el('instance-list');
    if (!instanceState.classIri) {
      showEmpty(list, '尚未选择类型');
      el('instance-total').textContent = '';
      el('instance-page').textContent = '';
      el('instance-prev').disabled = true;
      el('instance-next').disabled = true;
      return;
    }
    list.classList.add('empty');
    list.textContent = '加载中…';
    try {
      const url = '/browse/ontology/instances?class=' + encodeURIComponent(instanceState.classIri) +
        '&limit=' + instanceState.limit + '&offset=' + instanceState.offset;
      const data = await getJson(url);
      instanceState.total = data.total || 0;
      el('instance-total').textContent = '共 ' + instanceState.total + ' 条';
      const page = Math.floor(instanceState.offset / instanceState.limit) + 1;
      const pages = Math.max(1, Math.ceil(instanceState.total / instanceState.limit));
      el('instance-page').textContent = '第 ' + page + ' / ' + pages + ' 页';
      el('instance-prev').disabled = instanceState.offset <= 0;
      el('instance-next').disabled = instanceState.offset + instanceState.limit >= instanceState.total;
      if (!data.items || data.items.length === 0) {
        showEmpty(list, '该类下没有实例（接口返回 0 条）。');
        return;
      }
      list.classList.remove('empty');
      list.innerHTML = '';
      const table = document.createElement('table');
      table.className = 'data-table';
      const thead = document.createElement('thead');
      thead.innerHTML = '<tr><th>实例</th><th>label</th><th>命名图</th></tr>';
      table.appendChild(thead);
      const tbody = document.createElement('tbody');
      data.items.forEach(function (item) {
        const tr = document.createElement('tr');
        [item.iri, item.label, item.graph].forEach(function (value) {
          const td = document.createElement('td');
          td.textContent = value == null ? '—' : value;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      list.appendChild(table);
    } catch (err) {
      renderError(list, err);
    }
  }

  el('instance-prev').addEventListener('click', function () {
    instanceState.offset = Math.max(0, instanceState.offset - instanceState.limit);
    loadInstances();
  });
  el('instance-next').addEventListener('click', function () {
    instanceState.offset += instanceState.limit;
    loadInstances();
  });

  async function loadOntology() {
    const treeBox = el('ontology-tree');
    const propBox = el('ontology-properties');
    treeBox.textContent = '加载中…';
    propBox.textContent = '加载中…';
    try {
      const data = await getJson('/browse/ontology/tree');
      el('tree-count').textContent = (data.counts && data.counts.classes != null)
        ? ('· ' + data.counts.classes + ' 类') : '';
      el('prop-count').textContent = (data.counts && data.counts.properties != null)
        ? ('· ' + data.counts.properties + ' 个') : '';
      if (!data.tree || data.tree.length === 0) {
        showEmpty(treeBox, '当前没有 T-Box 指针或类（接口返回 0 条）。');
      } else {
        treeBox.classList.remove('empty');
        treeBox.innerHTML = '';
        const root = document.createElement('ul');
        root.className = 'tree';
        data.tree.forEach(function (node) { root.appendChild(classNode(node)); });
        treeBox.appendChild(root);
      }
      if (!data.properties || data.properties.length === 0) {
        showEmpty(propBox, '当前没有属性（接口返回 0 条）。');
      } else {
        propBox.classList.remove('empty');
        propBox.innerHTML = '';
        const list = document.createElement('ul');
        list.className = 'prop-list';
        data.properties.forEach(function (prop) {
          const li = document.createElement('li');
          const label = document.createElement('strong');
          label.textContent = prop.label || prop.iri;
          const kind = document.createElement('span');
          kind.className = 'badge';
          kind.textContent = prop.kind || 'property';
          li.appendChild(label);
          li.appendChild(document.createTextNode(' '));
          li.appendChild(kind);
          li.title = prop.iri;
          list.appendChild(li);
        });
        propBox.appendChild(list);
      }
    } catch (err) {
      renderError(treeBox, err);
      renderError(propBox, err);
    }
  }

  // ---- metrics ------------------------------------------------------------
  function filters() {
    return {
      domain: el('filter-domain').value,
      basis: el('filter-basis').value,
      publishable: el('filter-publishable').value,
    };
  }

  async function loadMetrics() {
    const table = el('metrics-table');
    const empty = el('metrics-empty');
    const detail = el('metric-detail');
    table.hidden = true;
    empty.hidden = true;
    detail.className = 'detail empty';
    detail.textContent = '点击任一指标查看口径详情';
    const params = new URLSearchParams();
    const current = filters();
    if (current.domain) { params.set('domain', current.domain); }
    if (current.basis) { params.set('evidenceBasis', current.basis); }
    if (current.publishable) { params.set('publishable', current.publishable); }
    el('metrics-count').textContent = '加载中…';
    try {
      const data = await getJson('/browse/metrics' + (params.toString() ? '?' + params.toString() : ''));
      el('metrics-count').textContent = '· 共 ' + data.count + ' 条（source=' + data.source + '）';
      if (!data.items || data.items.length === 0) {
        empty.hidden = false;
        return;
      }
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      data.items.forEach(function (item) {
        const tr = document.createElement('tr');
        tr.className = 'clickable';
        const cells = [
          item.metricId,
          item.nameZh,
          item.domain,
          item.evidenceBasis,
          String(item.publishable),
          String(item.inference),
          String(item.formulaDisabled),
          item.definitionVersion,
        ];
        cells.forEach(function (value) {
          const td = document.createElement('td');
          td.textContent = value == null ? '—' : value;
          tr.appendChild(td);
        });
        tr.addEventListener('click', function () { loadMetricDetail(item.metricId); });
        tbody.appendChild(tr);
      });
      table.hidden = false;
    } catch (err) {
      el('metrics-count').textContent = '';
      empty.hidden = false;
      empty.textContent = '加载失败：' + err.message;
    }
  }

  function field(label, value) {
    const row = document.createElement('div');
    row.className = 'field';
    const name = document.createElement('span');
    name.className = 'field-name';
    name.textContent = label;
    const content = document.createElement('span');
    content.className = 'field-value';
    content.textContent = value == null || value === '' ? '口径未给出' : String(value);
    row.appendChild(name);
    row.appendChild(content);
    return row;
  }

  async function loadMetricDetail(metricId) {
    const box = el('metric-detail');
    box.className = 'detail';
    box.textContent = '加载中…';
    try {
      const data = await getJson('/browse/metrics/' + encodeURIComponent(metricId));
      const m = data.metric;
      box.innerHTML = '';
      const title = document.createElement('h3');
      title.textContent = m.metricId + ' · ' + (m.nameZh || '');
      box.appendChild(title);
      box.appendChild(field('域', m.domain));
      box.appendChild(field('metricKind', m.metricKind));
      box.appendChild(field('公式', m.formula));
      box.appendChild(field('分母', m.denominator));
      box.appendChild(field('分子聚合', m.numeratorAgg));
      box.appendChild(field('观察期', m.observationPeriod
        ? (m.observationPeriod.kind + ' · 最小窗口 ' + m.observationPeriod.minWindowDays + ' 天')
        : null));
      box.appendChild(field('粒度', m.grain));
      box.appendChild(field('单位', m.unit));
      box.appendChild(field('evidenceBasis', m.evidenceBasis));
      box.appendChild(field('definitionStatus', m.definitionStatus));
      box.appendChild(field('definitionVersion', m.definitionVersion));
      box.appendChild(field('inference', m.inference));
      box.appendChild(field('formulaDisabled', m.formulaDisabled));
      box.appendChild(field('missing', m.missing));
      box.appendChild(field('note', m.note));
    } catch (err) {
      box.className = 'detail empty';
      box.textContent = '加载失败：' + err.message;
    }
  }

  el('metrics-refresh').addEventListener('click', loadMetrics);
  ['filter-domain', 'filter-basis', 'filter-publishable'].forEach(function (id) {
    el(id).addEventListener('change', loadMetrics);
  });

  // ---- terms --------------------------------------------------------------
  async function loadTerms() {
    const classesBox = el('terms-classes');
    const table = el('terms-table');
    const empty = el('terms-empty');
    classesBox.textContent = '加载中…';
    table.hidden = true;
    empty.hidden = true;
    try {
      const data = await getJson('/browse/terms');
      const counts = data.counts || {};
      el('terms-counts').textContent =
        '锚点类 ' + (counts.anchorClasses || 0) +
        ' · 别名 ' + (counts.altLabels || 0) +
        ' · evidenced ' + (counts.evidenced || 0) +
        ' · inferred ' + (counts.inferred || 0);
      el('terms-class-count').textContent = '· ' + (counts.anchorClasses || 0) + ' 类';
      if (!data.classes || data.classes.length === 0) {
        showEmpty(classesBox, '当前没有锚点类（接口返回 0 条）。');
      } else {
        classesBox.classList.remove('empty');
        classesBox.innerHTML = '';
        const list = document.createElement('ul');
        list.className = 'class-alias-list';
        data.classes.forEach(function (group) {
          const li = document.createElement('li');
          const strong = document.createElement('strong');
          strong.textContent = group.label || group.iri;
          li.appendChild(strong);
          const aliases = document.createElement('span');
          aliases.className = 'sub';
          aliases.textContent = ' · ' + (group.aliases || []).join(' / ');
          li.appendChild(aliases);
          li.title = group.iri;
          list.appendChild(li);
        });
        classesBox.appendChild(list);
      }
      if (!data.entries || data.entries.length === 0) {
        empty.hidden = false;
        return;
      }
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      data.entries.forEach(function (entry) {
        const tr = document.createElement('tr');
        const values = [
          entry.classLabel,
          entry.label,
          entry.status,
          entry.confidence || '—',
          entry.guardRegex || '—',
          (entry.canonicalFor || []).join(' / ') || '—',
          (entry.suppressedSurface || []).join(' / ') || '—',
        ];
        values.forEach(function (value) {
          const td = document.createElement('td');
          td.textContent = value == null ? '—' : value;
          if (value === entry.guardRegex) { td.className = 'mono'; }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.hidden = false;
    } catch (err) {
      el('terms-counts').textContent = '';
      renderError(classesBox, err);
      empty.hidden = false;
      empty.textContent = '加载失败：' + err.message;
    }
  }

  // First paint only loads the read-only ontology view; metrics/terms load on
  // first tab activation so the initial page never runs a heavy job.
  loaded.ontology = true;
  loadOntology();
})();
