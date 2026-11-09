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

  // 4xx 不是异常场景（例如只读端点拒绝写查询），这里保留状态码与原始 body，
  // 交给调用方原样展示；普通视图仍用上面的 getJson。
  async function requestJson(url) {
    const response = await fetch(API_BASE + url, { headers: { Accept: 'application/json' } });
    let body = null;
    try { body = await response.json(); } catch (err) { body = null; }
    return { ok: response.ok, status: response.status, body: body };
  }

  async function postJson(url, payload) {
    const response = await fetch(API_BASE + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    });
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
  const VIEWS = ['ontology', 'metrics', 'terms', 'dictionaries', 'triples', 'sparql', 'answer'];
  const loaded = { ontology: false, metrics: false, terms: false, dictionaries: false, triples: false, sparql: false, answer: false };
  const tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      tabs.forEach(function (item) { item.classList.toggle('active', item === tab); });
      VIEWS.forEach(function (name) {
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
    if (view === 'dictionaries') return loadDictionaries();
    if (view === 'triples') return loadTriples();
    if (view === 'sparql') return loadSparql();
    if (view === 'answer') return null;
    return null;
  }

  // ---- ontology -----------------------------------------------------------
  const instanceState = { classIri: null, className: '', limit: 20, offset: 0, total: 0 };
  // 支持 browse.html?class=<IRI> 深链（口径卡"查看该类实例"入口），类树加载后自动选中。
  const initialClassIri = new URLSearchParams(location.search).get('class');

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
        [item.iri, item.label, item.graph].forEach(function (value, index) {
          const td = document.createElement('td');
          if (index === 0 && value) {
            const link = document.createElement('a');
            link.href = 'entity.html?iri=' + encodeURIComponent(value);
            link.textContent = value;
            td.appendChild(link);
          } else {
            td.textContent = value == null ? '—' : value;
          }
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
      if (initialClassIri) {
        const match = findClassNode(data.tree || [], initialClassIri);
        if (match) {
          selectClass(match);
        } else {
          el('instance-head').textContent = '未找到类：' + initialClassIri;
        }
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

  function findClassNode(nodes, iri) {
    for (let i = 0; i < (nodes || []).length; i += 1) {
      if (nodes[i].iri === iri) { return nodes[i]; }
      const hit = findClassNode(nodes[i].children, iri);
      if (hit) { return hit; }
    }
    return null;
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
      // 异步补"相关实体/事实"块，不阻塞详情其余字段。
      renderMetricLinks(box, m);
    } catch (err) {
      box.className = 'detail empty';
      box.textContent = '加载失败：' + err.message;
    }
  }

  el('metrics-refresh').addEventListener('click', loadMetrics);
  ['filter-domain', 'filter-basis', 'filter-publishable'].forEach(function (id) {
    el(id).addEventListener('change', loadMetrics);
  });

  // ---- metric -> ontology deep links --------------------------------------
  // 后端 metric 详情没有实/类绑定字段（实测全部指标 0 条含 IRI），
  // 唯一可用线索是 grain 文本与当前 T-Box 类的 localName 同名。
  // 因此这里只做"弱关联"并在界面明示依据；匹配不到就显示"未绑定"，不构造链接。
  const classCache = { list: null, promise: null };

  function localNameOf(iri) {
    if (!iri) return null;
    const parts = String(iri).split(/[#/]/);
    return parts[parts.length - 1] || null;
  }

  function ontologyClassList() {
    if (classCache.list) return Promise.resolve(classCache.list);
    if (!classCache.promise) {
      classCache.promise = getJson('/browse/ontology/tree').then(function (data) {
        classCache.list = data.classes || [];
        return classCache.list;
      }).catch(function (err) {
        classCache.promise = null;
        throw err;
      });
    }
    return classCache.promise;
  }

  function makeLink(href, text, title) {
    const link = document.createElement('a');
    link.href = href;
    link.textContent = text;
    if (title) { link.title = title; }
    link.className = 'deep-link';
    return link;
  }

  function renderClassBinding(cls) {
    const row = document.createElement('div');
    row.className = 'binding';
    const label = document.createElement('strong');
    label.textContent = cls.label || localNameOf(cls.iri);
    row.appendChild(label);
    row.appendChild(document.createTextNode(' · '));
    row.appendChild(makeLink(
      'browse.html?class=' + encodeURIComponent(cls.iri), '查看该类实例', cls.iri));
    row.appendChild(document.createTextNode(' · '));
    row.appendChild(makeLink(
      'ontology.html?entity=' + encodeURIComponent(cls.iri), '本体实体页', cls.iri));
    const instanceBox = document.createElement('div');
    instanceBox.className = 'sub binding-instances';
    instanceBox.textContent = '实例加载中…';
    row.appendChild(instanceBox);
    getJson('/browse/ontology/instances?class=' + encodeURIComponent(cls.iri) + '&limit=5')
      .then(function (data) {
        const items = data.items || [];
        instanceBox.textContent = '共 ' + (data.total || 0) + ' 条实例';
        if (items.length === 0) {
          instanceBox.textContent += '（当前命名图里没有该类的个体）';
          return;
        }
        instanceBox.textContent += '，前 ' + items.length + ' 条：';
        items.forEach(function (item, index) {
          if (index > 0) { instanceBox.appendChild(document.createTextNode(' / ')); }
          instanceBox.appendChild(makeLink(
            'ontology.html?entity=' + encodeURIComponent(item.iri),
            item.label || item.iri,
            item.iri));
        });
      })
      .catch(function (err) {
        instanceBox.textContent = '实例加载失败：' + err.message;
      });
    return row;
  }

  async function renderMetricLinks(box, metric) {
    const wrap = document.createElement('div');
    wrap.className = 'metric-links';
    const head = document.createElement('h4');
    head.textContent = '相关实体/事实';
    wrap.appendChild(head);
    const body = document.createElement('div');
    body.className = 'metric-links-body empty';
    body.textContent = '正在匹配当前 T-Box…';
    wrap.appendChild(body);
    box.appendChild(wrap);

    const grain = metric.grain == null ? '' : String(metric.grain).trim();
    if (!grain) {
      showEmpty(body, '未绑定：该口径未给出 grain，无法定位到本体类或实例。');
      return;
    }
    let classes;
    try {
      classes = await ontologyClassList();
    } catch (err) {
      showEmpty(body, '未绑定：读取本体类失败（' + err.message + '）。');
      return;
    }
    const matches = classes.filter(function (item) {
      const local = localNameOf(item.iri);
      return local && local.toLowerCase() === grain.toLowerCase();
    });
    if (matches.length === 0) {
      showEmpty(body, '未绑定：grain=' + grain + '，当前 T-Box 没有同名类（按类 localName 精确同名匹配）。');
      return;
    }
    body.classList.remove('empty');
    body.textContent = '';
    const basis = document.createElement('div');
    basis.className = 'sub';
    basis.textContent = '弱关联：按 grain=' + grain + ' 与本体类 localName 同名匹配，不是口径显式声明的绑定。';
    body.appendChild(basis);
    matches.slice(0, 3).forEach(function (cls) {
      body.appendChild(renderClassBinding(cls));
    });
  }

  // ---- triples ------------------------------------------------------------
  const tripleState = { limit: 20, offset: 0 };

  function tripleFilters() {
    return {
      subject: el('triple-subject').value.trim(),
      predicate: el('triple-predicate').value.trim(),
      object: el('triple-object').value.trim(),
      graph: el('triple-graph').value.trim(),
    };
  }

  async function loadTriples(resetOffset) {
    const table = el('triples-table');
    const empty = el('triples-empty');
    if (resetOffset) { tripleState.offset = 0; }
    const current = tripleFilters();
    const params = new URLSearchParams();
    ['subject', 'predicate', 'object', 'graph'].forEach(function (name) {
      if (current[name]) { params.set(name, current[name]); }
    });
    tripleState.limit = parseInt(el('triple-limit').value, 10) || 20;
    params.set('limit', String(tripleState.limit));
    params.set('offset', String(tripleState.offset));
    table.hidden = true;
    empty.hidden = true;
    el('triples-status').textContent = '加载中…';
    try {
      const data = await getJson('/browse/triples?' + params.toString());
      const items = data.items || [];
      let status = '· 返回 ' + items.length + ' 条 · offset=' + tripleState.offset;
      if (data.truncated) { status += ' · truncated=true（服务端可能截断结果）'; }
      el('triples-status').textContent = status;
      const page = Math.floor(tripleState.offset / tripleState.limit) + 1;
      el('triples-page').textContent = '第 ' + page + ' 页';
      el('triples-prev').disabled = tripleState.offset <= 0;
      // 接口不返回 total，只有本页满页时才认为可能还有下一页。
      el('triples-next').disabled = items.length < tripleState.limit;
      if (items.length === 0) {
        showEmpty(empty, '当前条件下没有三元组（接口返回 0 条）。');
        empty.hidden = false;
        return;
      }
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      items.forEach(function (item) {
        const tr = document.createElement('tr');
        [item.graph, item.subject, item.predicate, item.object].forEach(function (value) {
          const td = document.createElement('td');
          td.className = 'mono';
          td.textContent = value == null ? '—' : String(value);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.hidden = false;
    } catch (err) {
      el('triples-status').textContent = '';
      showEmpty(empty, '加载失败：' + err.message);
      empty.hidden = false;
    }
  }

  el('triples-query').addEventListener('click', function () { loadTriples(true); });
  el('triples-reset').addEventListener('click', function () {
    ['triple-subject', 'triple-predicate', 'triple-object', 'triple-graph'].forEach(function (id) {
      el(id).value = '';
    });
    el('triple-limit').value = '20';
    loadTriples(true);
  });
  ['triple-subject', 'triple-predicate', 'triple-object', 'triple-graph'].forEach(function (id) {
    el(id).addEventListener('keydown', function (event) {
      if (event.key === 'Enter') { event.preventDefault(); loadTriples(true); }
    });
  });
  el('triples-prev').addEventListener('click', function () {
    tripleState.offset = Math.max(0, tripleState.offset - tripleState.limit);
    loadTriples(false);
  });
  el('triples-next').addEventListener('click', function () {
    tripleState.offset += tripleState.limit;
    loadTriples(false);
  });

  // ---- sparql -------------------------------------------------------------
  const DEFAULT_SPARQL = 'SELECT ?g ?s ?p ?o\nWHERE { GRAPH ?g { ?s ?p ?o } }\nLIMIT 20';

  function loadSparql() {
    if (!el('sparql-query').value) { el('sparql-query').value = DEFAULT_SPARQL; }
  }

  // 绑定 term 形状：{kind:'iri'|'literal'|'bnode', iri|value|label, datatype, lang}
  function sparqlTerm(term) {
    if (!term || typeof term !== 'object') { return '—'; }
    if (term.kind === 'iri') { return term.iri || '—'; }
    if (term.kind === 'literal') {
      let text = term.value == null ? '' : String(term.value);
      if (term.lang) { text += ' @' + term.lang; }
      else if (term.datatype) { text += ' ^^' + term.datatype; }
      return text;
    }
    if (term.kind === 'bnode') { return '_:' + (term.label || term.value || ''); }
    return JSON.stringify(term);
  }

  function renderSparqlResult(box, body) {
    box.classList.remove('empty');
    box.textContent = '';
    if (!body || !body.kind) {
      const pre = document.createElement('pre');
      pre.className = 'result-raw';
      pre.textContent = JSON.stringify(body, null, 2);
      box.appendChild(pre);
      return;
    }
    if (body.kind === 'ask') {
      const line = document.createElement('div');
      line.className = 'sub';
      line.textContent = 'ASK · boolean=' + String(body.boolean);
      box.appendChild(line);
      if (body.truncated) {
        const note = document.createElement('div');
        note.className = 'sub';
        note.textContent = 'truncated=true（服务端可能截断结果）';
        box.appendChild(note);
      }
      return;
    }
    const variables = body.variables || [];
    const bindings = body.bindings || [];
    if (variables.length === 0) {
      showEmpty(box, 'SELECT 没有返回变量（接口 variables=[]）。');
      return;
    }
    if (bindings.length === 0) {
      showEmpty(box, 'SELECT 返回 0 行（接口 bindings=[]）。');
      return;
    }
    const table = document.createElement('table');
    table.className = 'data-table';
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    variables.forEach(function (name) {
      const th = document.createElement('th');
      th.textContent = '?' + name;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    bindings.forEach(function (binding) {
      const tr = document.createElement('tr');
      const values = binding.values || {};
      variables.forEach(function (name) {
        const td = document.createElement('td');
        td.className = 'mono';
        const text = sparqlTerm(values[name]);
        td.textContent = text;
        td.title = text;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    box.appendChild(table);
    if (body.truncated) {
      const note = document.createElement('div');
      note.className = 'sub';
      note.textContent = 'truncated=true（服务端可能截断结果）';
      box.appendChild(note);
    }
  }

  function renderSparqlError(box, response) {
    box.hidden = false;
    box.textContent = '';
    const error = response.body && response.body.error ? response.body.error : null;
    const rows = [
      ['HTTP 状态', String(response.status)],
      ['providerCode', error ? (error.providerCode || '—') : '—'],
      ['code', error ? (error.code || '—') : '—'],
      ['provider', error ? (error.provider || '—') : '—'],
      ['retryable', error ? String(error.retryable) : '—'],
      ['message', error ? (error.message || '—') : '—'],
      ['details', error && error.details ? JSON.stringify(error.details) : '{}'],
    ];
    const table = document.createElement('table');
    table.className = 'error-table';
    rows.forEach(function (pair) {
      const tr = document.createElement('tr');
      const th = document.createElement('th');
      th.textContent = pair[0];
      const td = document.createElement('td');
      td.textContent = pair[1];
      tr.appendChild(th);
      tr.appendChild(td);
      table.appendChild(tr);
    });
    box.appendChild(table);
    const pre = document.createElement('pre');
    pre.className = 'result-raw';
    pre.textContent = response.body ? JSON.stringify(response.body, null, 2) : '(空响应体)';
    box.appendChild(pre);
  }

  async function runSparql() {
    const query = el('sparql-query').value.trim();
    const status = el('sparql-status');
    const errorBox = el('sparql-error');
    const result = el('sparql-result');
    errorBox.hidden = true;
    errorBox.textContent = '';
    result.className = 'empty';
    if (!query) {
      result.textContent = '请输入 SELECT 或 ASK 查询。';
      return;
    }
    result.textContent = '运行中…';
    status.textContent = '· GET /browse/sparql';
    const response = await requestJson('/browse/sparql?query=' + encodeURIComponent(query));
    if (!response.ok) {
      status.textContent = '· HTTP ' + response.status;
      result.textContent = '查询被拒绝（错误详见上方）。';
      renderSparqlError(errorBox, response);
      return;
    }
    const body = response.body || {};
    if (body.kind === 'select') {
      status.textContent = '· kind=select · ' + ((body.bindings || []).length) + ' 行';
    } else if (body.kind === 'ask') {
      status.textContent = '· kind=ask · boolean=' + String(body.boolean);
    } else {
      status.textContent = '· HTTP ' + response.status;
    }
    renderSparqlResult(result, body);
  }

  el('sparql-run').addEventListener('click', runSparql);
  el('sparql-query').addEventListener('keydown', function (event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      runSparql();
    }
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

  // ---- dictionaries -------------------------------------------------------
  const dictState = { limit: 20, offset: 0, total: 0 };

  function dictQueryUrl() {
    const params = new URLSearchParams();
    params.set('limit', String(dictState.limit));
    params.set('offset', String(dictState.offset));
    const table = el('dict-table').value.trim();
    const column = el('dict-column').value.trim();
    const source = el('dict-source').value;
    const binding = el('dict-binding').value;
    if (table) { params.set('table', table); }
    if (column) { params.set('column', column); }
    if (source) { params.set('sourceKind', source); }
    if (binding) { params.set('bindingMethod', binding); }
    return '/catalog/dictionaries?' + params.toString();
  }

  function dictCell(value, mono) {
    const td = document.createElement('td');
    td.textContent = value == null || value === '' ? '—' : value;
    if (mono) { td.className = 'mono'; }
    return td;
  }

  async function loadDictionaries() {
    const table = el('dict-table-view');
    const empty = el('dict-empty');
    const status = el('dict-status');
    table.hidden = true;
    empty.hidden = true;
    status.textContent = '加载中…';
    try {
      const data = await getJson(dictQueryUrl());
      dictState.total = data.total || 0;
      status.textContent = '· 共 ' + dictState.total + ' 行';
      const items = data.items || [];
      if (items.length === 0) {
        empty.hidden = false;
        renderDictPager();
        return;
      }
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      items.forEach(function (item) {
        const tr = document.createElement('tr');
        const tableCell = dictCell(item.table);
        const link = document.createElement('a');
        link.href = '#';
        link.className = 'class-link';
        link.textContent = item.table;
        link.title = '只看这张表';
        link.addEventListener('click', function (event) {
          event.preventDefault();
          el('dict-table').value = item.table;
          el('dict-column').value = '';
          dictState.offset = 0;
          loadDictionaries();
        });
        tableCell.textContent = '';
        tableCell.appendChild(link);
        tr.appendChild(tableCell);
        tr.appendChild(dictCell(item.column));
        tr.appendChild(dictCell(item.dataType));
        tr.appendChild(dictCell(item.isNullable ? 'YES' : 'NO'));
        tr.appendChild(dictCell(item.comment));
        tr.appendChild(dictCell(item.sourceKind));
        tr.appendChild(dictCell(item.bindingMethod));
        tr.appendChild(dictCell(item.propertyIri, true));
        tr.appendChild(dictCell(item.confidence == null ? '—' : item.confidence));
        tr.appendChild(dictCell(item.bindingNote));
        tbody.appendChild(tr);
      });
      table.hidden = false;
      renderDictPager();
    } catch (err) {
      status.textContent = '';
      renderError(empty, err);
      empty.hidden = false;
    }
  }

  function renderDictPager() {
    const page = Math.floor(dictState.offset / dictState.limit) + 1;
    const pages = Math.max(1, Math.ceil(dictState.total / dictState.limit));
    el('dict-page').textContent = '第 ' + page + ' / ' + pages + ' 页';
    el('dict-prev').disabled = dictState.offset <= 0;
    el('dict-next').disabled = dictState.offset + dictState.limit >= dictState.total;
  }

  el('dict-query').addEventListener('click', function () {
    dictState.offset = 0;
    loadDictionaries();
  });
  el('dict-table').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') { event.preventDefault(); dictState.offset = 0; loadDictionaries(); }
  });
  el('dict-column').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') { event.preventDefault(); dictState.offset = 0; loadDictionaries(); }
  });
  el('dict-prev').addEventListener('click', function () {
    dictState.offset = Math.max(0, dictState.offset - dictState.limit);
    loadDictionaries();
  });
  el('dict-next').addEventListener('click', function () {
    dictState.offset += dictState.limit;
    loadDictionaries();
  });
  el('dict-refresh').addEventListener('click', async function () {
    el('dict-status').textContent = '刷新中…';
    try {
      const result = await postJson('/catalog/dictionaries/refresh', { sources: ['pg'] });
      el('dict-status').textContent =
        '· 处理 ' + result.processed + ' 列 · 新增 ' + result.inserted +
        ' · 更新 ' + result.updated + ' · 未变 ' + result.unchanged +
        ' · 显式 ' + (result.binding || {}).explicit +
        ' · 名称匹配 ' + (result.binding || {}).name_match +
        ' · 未绑定 ' + (result.binding || {}).none;
      loaded.dictionaries = true;
      loadDictionaries();
    } catch (err) {
      el('dict-status').textContent = '刷新失败：' + err.message;
    }
  });

  // ---- answer / coverage --------------------------------------------------
  const QA_LAYER_LABELS = {
    ontology: '本体 T-Box',
    terms: 'SKOS 术语',
    metrics: '口径层',
    facts: '事实层',
  };

  function qaStatusPill(status) {
    const pill = document.createElement('span');
    pill.className = 'status-pill status-' + (status || 'missing');
    pill.textContent = status || 'missing';
    return pill;
  }

  function qaMetaText(text) {
    const node = document.createElement('div');
    node.className = 'qa-bar-meta';
    node.textContent = text;
    return node;
  }

  function renderQaCoverage(data) {
    const box = el('qa-coverage-bars');
    box.innerHTML = '';
    box.classList.remove('empty');
    (data.layers || []).forEach(function (layer) {
      const row = document.createElement('div');
      row.className = 'qa-bar';

      const head = document.createElement('div');
      head.className = 'qa-bar-head';
      const label = document.createElement('span');
      label.className = 'qa-bar-label';
      label.textContent = QA_LAYER_LABELS[layer.layer] || layer.layer;
      head.appendChild(label);
      head.appendChild(qaStatusPill(layer.status));
      row.appendChild(head);

      const track = document.createElement('div');
      track.className = 'qa-bar-track';
      const fill = document.createElement('div');
      fill.className = 'qa-bar-fill status-' + (layer.status || 'missing');
      const pct = Math.round(Number(layer.coverage || 0) * 100);
      fill.style.width = pct + '%';
      track.appendChild(fill);
      row.appendChild(track);

      // 覆盖度 meta：优先展示真实命中对象，其次展示缺失片段，最后落到状态解释。
      let metaParts = [];
      if (layer.matched && layer.matched.length) {
        metaParts.push('命中：' + layer.matched.map(function (item) {
          return item.label || item.id || item.metricId || '';
        }).filter(Boolean).slice(0, 4).join(' / '));
      }
      if (layer.missing && layer.missing.length) {
        metaParts.push('缺：' + layer.missing.slice(0, 4).join(' / '));
      }
      if (!metaParts.length) {
        metaParts.push(layer.status === 'not_applicable' ? '本问题不需要该层' : '无命中');
      }
      metaParts.push('coverage=' + pct + '%');
      row.appendChild(qaMetaText(metaParts.join(' · ')));
      box.appendChild(row);
    });
    if (!(data.layers || []).length) {
      showEmpty(box, '接口没有返回 layers。');
    }
  }

  function summarizeQaStep(step) {
    const out = step.output || {};
    if (step.step === 'retrieve') {
      return 'chunks=' + (out.chunks || 0) + ' · facts=' + (out.facts || 0) +
        (out.error ? ' · error=' + out.error : '');
    }
    if (step.step === 'terms') {
      return 'ontology=' + (out.ontologyMatched || 0) + ' · terms=' + (out.termsMatched || 0);
    }
    if (step.step === 'metric') {
      const mid = out.metricId ? out.metricId + '@' + (out.definitionVersion || '?') : 'none';
      return 'metric=' + mid;
    }
    if (step.step === 'facts') {
      return 'observations=' + (out.observationRows || 0) +
        ' · code=' + (out.code || '—') +
        (out.factFunction ? ' · fn=' + out.factFunction : '');
    }
    if (step.step === 'compute') {
      if (out.error) return 'error=' + out.error;
      if (out.reason) return 'reason=' + out.reason;
      if (out.mode === 'rule_set') return 'mode=rule_set · value=null';
      return 'value=' + (out.value == null ? 'null' : out.value) +
        (out.dataSource ? ' · dataSource=' + out.dataSource : '');
    }
    return '';
  }

  function renderQaSteps(steps) {
    const box = el('qa-steps');
    box.innerHTML = '';
    box.classList.remove('empty');
    el('qa-step-count').textContent = '· ' + steps.length + ' 步';
    steps.forEach(function (step) {
      const item = document.createElement('div');
      item.className = 'qa-step';
      const dot = document.createElement('span');
      dot.className = 'qa-step-dot status-' + (step.status || 'skipped');
      item.appendChild(dot);

      const body = document.createElement('div');
      body.className = 'qa-step-body';
      const title = document.createElement('div');
      title.className = 'qa-step-title';
      const name = document.createElement('span');
      name.className = 'qa-step-name';
      name.textContent = step.step;
      title.appendChild(name);
      title.appendChild(qaStatusPill(step.status));
      const duration = document.createElement('span');
      duration.className = 'sub';
      duration.textContent = (step.durationMs == null ? '—' : step.durationMs + ' ms');
      title.appendChild(duration);
      body.appendChild(title);

      const meta = document.createElement('div');
      meta.className = 'qa-step-meta';
      meta.textContent = summarizeQaStep(step);
      body.appendChild(meta);
      item.appendChild(body);
      box.appendChild(item);
    });
  }

  function renderQaCitations(citations) {
    const box = el('qa-citations');
    box.innerHTML = '';
    box.classList.remove('empty');
    el('qa-citation-count').textContent = '· ' + citations.length + ' 条';
    if (!citations.length) {
      showEmpty(box, '本次回答没有引用（可能被拒答）。');
      return;
    }
    citations.forEach(function (citation) {
      const chip = document.createElement('span');
      chip.className = 'qa-chip';
      chip.title = (citation.id || '') + ' -> ' + (citation.ref || '');
      const kind = document.createElement('span');
      kind.className = 'qa-chip-kind';
      kind.textContent = citation.kind || 'ref';
      chip.appendChild(kind);
      const ref = document.createElement('span');
      ref.className = 'qa-chip-ref';
      ref.textContent = citation.ref || citation.id || '';
      chip.appendChild(ref);
      if (citation.sourceRef && citation.sourceRef.resolveUrl) {
        const prov = document.createElement('a');
        prov.className = 'qa-chip-prov';
        prov.href = citation.sourceRef.resolveUrl;
        prov.target = '_blank';
        prov.rel = 'noopener';
        prov.title = (citation.sourceRef.type || 'source') + ' · ' +
          (citation.sourceRef.targetTable || '');
        prov.textContent = '溯源';
        chip.appendChild(prov);
      }
      box.appendChild(chip);
    });
  }

  function renderQaMissing(missing) {
    const box = el('qa-missing');
    box.innerHTML = '';
    box.classList.remove('empty');
    if (!missing || !missing.length) {
      showEmpty(box, '无缺口。');
      return;
    }
    const list = document.createElement('ul');
    missing.forEach(function (item) {
      const li = document.createElement('li');
      const layer = document.createElement('span');
      layer.className = 'qa-missing-layer';
      layer.textContent = item.layer || 'unknown';
      li.appendChild(layer);
      const what = document.createElement('span');
      what.textContent = item.what || item.text || item.code || '';
      li.appendChild(what);
      if (item.howToFix) {
        const fix = document.createElement('div');
        fix.className = 'qa-missing-fix';
        fix.textContent = '补法：' + item.howToFix;
        li.appendChild(fix);
      }
      list.appendChild(li);
    });
    box.appendChild(list);
  }

  function renderQaAnswer(answer) {
    const box = el('qa-answer');
    box.classList.remove('empty');
    box.classList.toggle('refused', !!answer.refused);
    box.textContent = answer.answer || '（空回答）';
    const badge = el('qa-refusal');
    badge.className = 'qa-refusal-badge ' + (answer.refused ? 'refused' : (answer.valueRefused ? 'warn' : 'ok'));
    const parts = [];
    if (answer.refused) parts.push('refused');
    else if (answer.valueRefused) parts.push('valueRefused');
    else parts.push('answered');
    if (answer.answerType) parts.push(answer.answerType);
    if (answer.reasonCode) parts.push(answer.reasonCode);
    badge.textContent = '· ' + parts.join(' · ');
    if (answer.sourceRef && answer.sourceRef.resolveUrl) {
      const prov = document.createElement('div');
      prov.className = 'qa-source-ref';
      const kind = document.createElement('span');
      kind.className = 'qa-chip-kind';
      kind.textContent = answer.sourceRef.type || 'source';
      prov.appendChild(kind);
      const link = document.createElement('a');
      link.href = answer.sourceRef.resolveUrl;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = '溯源 · ' + (answer.sourceRef.targetTable || '');
      prov.appendChild(link);
      box.appendChild(prov);
    }
  }

  async function askQuestion() {
    const question = el('qa-question').value.trim();
    const status = el('qa-status');
    if (!question) {
      status.textContent = '请输入问题。';
      return;
    }
    status.textContent = '提问中…';
    const payload = {
      query: question,
      strategy: el('qa-strategy').value,
      topK: Number(el('qa-topk').value || 5),
    };
    try {
      const results = await Promise.all([
        postJson('/answerable', payload),
        postJson('/answer', payload),
      ]);
      const coverage = results[0] || {};
      const answer = results[1] || {};
      renderQaCoverage(coverage);
      renderQaSteps(answer.steps || []);
      renderQaCitations(answer.citations || []);
      renderQaMissing(answer.missing || []);
      renderQaAnswer(answer);
      status.textContent = '· answerable=' + String(coverage.answerable) +
        ' · valueAnswerable=' + String(coverage.valueAnswerable) +
        (coverage.degraded ? ' · degraded' : '');
    } catch (err) {
      status.textContent = '';
      const box = el('qa-answer');
      box.classList.add('empty', 'refused');
      box.textContent = '提问失败：' + err.message;
      showEmpty(el('qa-coverage-bars'), '覆盖度读取失败。');
      showEmpty(el('qa-steps'), '步骤读取失败。');
      showEmpty(el('qa-citations'), '引用读取失败。');
      showEmpty(el('qa-missing'), '缺口读取失败。');
    }
  }

  el('qa-ask').addEventListener('click', askQuestion);
  el('qa-example').addEventListener('click', function () {
    el('qa-question').value = '13个月继续率是多少';
    el('qa-question').focus();
  });
  el('qa-question').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      askQuestion();
    }
  });

  // First paint only loads the read-only ontology view; metrics/terms load on
  // first tab activation so the initial page never runs a heavy job.
  loaded.ontology = true;
  loadOntology();
})();
