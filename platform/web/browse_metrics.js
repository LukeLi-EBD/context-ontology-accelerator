// M-03: /browse 口径卡 tab 的族索引指引与变体选择。
// 本文件为独立增量脚本：不修改 browse.js，只在既有 DOM 上追加 G3 区块。
// 跨 tab / 深链 URL 一律经 BrowseUrls（browse_urls.js）生成。
(function () {
  'use strict';

  var G3 = {
    selectedMetricId: null,
    familyCache: { items: null, promise: null },
    manifestCache: { byId: null, meta: null, promise: null },
    detailTimers: {},
    rowObserver: null,
    injected: false
  };

  function el(id) { return document.getElementById(id); }

  function getJson(url) {
    return fetch(url, { headers: { Accept: 'application/json' } }).then(function (response) {
      return response.text().then(function (text) {
        var data;
        try {
          data = JSON.parse(text);
        } catch (err) {
          throw new Error('HTTP ' + response.status + '：响应不是 JSON');
        }
        if (!response.ok) {
          var error = new Error(
            (data && data.error && data.error.message) || ('HTTP ' + response.status)
          );
          error.providerCode = data && data.error && data.error.providerCode;
          error.payload = data;
          throw error;
        }
        return data;
      });
    });
  }

  function injectStyle() {
    if (G3.injected) { return; }
    G3.injected = true;
    var style = document.createElement('style');
    style.textContent = [
      '.g3-box{border-top:1px dashed #c8d0da;margin-top:12px;padding-top:10px}',
      '.g3-box h4{margin:0 0 6px;font-size:14px}',
      '.g3-badges{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}',
      '.g3-badge{display:inline-block;border:1px solid #c8d0da;border-radius:10px;padding:1px 8px;font-size:12px}',
      '.g3-badge.ok{border-color:#2f855a;color:#2f855a}',
      '.g3-badge.warn{border-color:#b7791f;color:#b7791f}',
      '.g3-badge.bad{border-color:#c53030;color:#c53030}',
      '.g3-badge.muted{color:#718096}',
      '.g3-note{font-size:12px;color:#4a5568;margin:4px 0}',
      '.g3-warn{background:#fffaf0;border:1px solid #f6ad55;border-radius:4px;padding:8px;margin:8px 0;font-size:13px}',
      '.g3-variants{width:100%;border-collapse:collapse;font-size:12px}',
      '.g3-variants th,.g3-variants td{border:1px solid #dde3ea;padding:4px 6px;vertical-align:top;text-align:left}',
      '.g3-variants tr.selected{background:#ebf8ff}',
      '.g3-variants td.g3-mono{font-family:monospace}',
      '.g3-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}',
      '.g3-link{font-size:12px;margin-right:10px}',
      '.g3-field{display:flex;gap:8px;font-size:12px;margin:3px 0}',
      '.g3-field-name{min-width:64px;color:#4a5568;flex:0 0 auto}',
      '.g3-field-value{white-space:pre-wrap;word-break:break-word}',
      '.g3-card-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function familyIndex() {
    if (G3.familyCache.items) { return Promise.resolve(G3.familyCache.items); }
    if (!G3.familyCache.promise) {
      G3.familyCache.promise = getJson(window.BrowseUrls.families())
        .then(function (data) {
          G3.familyCache.items = data.families || [];
          return G3.familyCache.items;
        })
        .catch(function (err) {
          G3.familyCache.promise = null;
          throw err;
        });
    }
    return G3.familyCache.promise;
  }

  function familyFor(families, metricId) {
    return families.filter(function (family) {
      if (family.familyId === metricId || family.indexMetricId === metricId) { return true; }
      return (family.variants || []).some(function (variant) {
        return variant.metricId === metricId;
      });
    })[0] || null;
  }

  function manifestIndex() {
    if (G3.manifestCache.byId) { return Promise.resolve(G3.manifestCache.byId); }
    if (!G3.manifestCache.promise) {
      G3.manifestCache.promise = getJson(window.BrowseUrls.manifest('all'))
        .then(function (data) {
          var byId = {};
          (data.items || []).forEach(function (item) { byId[item.metricId] = item; });
          G3.manifestCache.byId = byId;
          G3.manifestCache.meta = data.meta || {};
          return byId;
        })
        .catch(function (err) {
          G3.manifestCache.promise = null;
          throw err;
        });
    }
    return G3.manifestCache.promise;
  }

  function badge(text, tone) {
    var span = document.createElement('span');
    span.className = 'g3-badge ' + (tone || 'muted');
    span.textContent = text;
    return span;
  }

  function link(href, text, title, sameTab) {
    var anchor = document.createElement('a');
    anchor.className = 'g3-link';
    anchor.href = href;
    anchor.textContent = text;
    if (title) { anchor.title = title; }
    if (!sameTab) {
      anchor.target = '_blank';
      anchor.rel = 'noopener';
    }
    return anchor;
  }

  function externalTone(status) {
    if (status === 'external_candidate') { return 'ok'; }
    if (status === 'internal_baseline') { return 'warn'; }
    return 'bad';
  }

  function tableCell(text, tone) {
    var td = document.createElement('td');
    if (tone) {
      td.appendChild(badge(text, tone));
    } else {
      td.textContent = text;
    }
    return td;
  }

  function ensureHeader(table) {
    if (!table || !table.tHead || !table.tHead.rows.length) { return; }
    if (table.getAttribute('data-g3-header') === '1') { return; }
    var headRow = table.tHead.rows[0];
    ['口径卡', '可算性', '对外状态'].forEach(function (label) {
      var th = document.createElement('th');
      th.textContent = label;
      headRow.appendChild(th);
    });
    table.setAttribute('data-g3-header', '1');
  }

  function enhanceRows(table, byId) {
    if (!table) { return; }
    var tbody = table.querySelector('tbody');
    if (!tbody) { return; }
    Array.prototype.slice.call(tbody.querySelectorAll('tr')).forEach(function (row) {
      if (row.getAttribute('data-g3-row') === '1') { return; }
      if (!row.cells || !row.cells[0]) { return; }
      var metricId = row.cells[0].textContent.trim();
      var item = byId[metricId];
      if (!item) { return; }
      row.appendChild(tableCell(
        item.variantOf ? '未建卡' : '已建卡',
        item.variantOf ? 'warn' : 'ok'
      ));
      row.appendChild(tableCell(
        item.computabilityLabel,
        item.computabilityTone || 'muted'
      ));
      row.appendChild(tableCell(
        externalStatusText(item),
        externalStatusTone(item)
      ));
      row.setAttribute('data-g3-row', '1');
    });
  }

  // 候选资格 ≠ 当前真能算出数：对外状态列同时给出执行路径与不可用原因。
  function executionText(item) {
    if (item.executionPath === 'compute') { return '可 compute'; }
    if (item.executionPath === 'rule_set') { return '仅 rules API'; }
    return '当前不可算：' + (item.executionReason || item.executionReasonCode || '未知原因');
  }

  function externalStatusText(item) {
    if (!item.externalEligible) { return item.externalLabel; }
    return item.externalLabel + '｜' + executionText(item);
  }

  function externalStatusTone(item) {
    if (!item.externalEligible) { return externalTone(item.externalStatus); }
    return item.executable ? 'ok' : 'warn';
  }

  function startRowObserver() {
    var table = el('metrics-table');
    if (!table) { return; }
    manifestIndex().then(function (byId) {
      ensureHeader(table);
      enhanceRows(table, byId);
      if (G3.rowObserver || !window.MutationObserver) { return; }
      var tbody = table.querySelector('tbody');
      if (!tbody) { return; }
      G3.rowObserver = new MutationObserver(function () {
        manifestIndex()
          .then(function (map) {
            ensureHeader(table);
            enhanceRows(table, map);
          })
          .catch(function () { /* 清单不可用时保持 browse.js 原表 */ });
      });
      G3.rowObserver.observe(tbody, { childList: true });
    }).catch(function () { /* 清单不可用时保持 browse.js 原表 */ });
  }

  function clearG3(box, scope) {
    Array.prototype.slice.call(
      box.querySelectorAll(scope ? '[data-g3="' + scope + '"]' : '[data-g3]')
    ).forEach(function (node) {
      node.parentNode.removeChild(node);
    });
  }

  function renderCardBox(box, card) {
    clearG3(box, 'card');
    var wrap = document.createElement('div');
    wrap.className = 'g3-box';
    wrap.setAttribute('data-g3', 'card');

    var head = document.createElement('div');
    head.className = 'g3-card-head';
    var title = document.createElement('h4');
    title.textContent = '口径卡 · ' + card.metricId;
    head.appendChild(title);
    head.appendChild(badge(
      card.cardStateLabel,
      card.cardExists ? 'ok' : 'warn'
    ));
    wrap.appendChild(head);

    if (!card.cardExists) {
      var notBuilt = document.createElement('div');
      notBuilt.className = 'g3-warn';
      notBuilt.textContent = '未建卡：该指标为族变体，没有独立口径卡；'
        + '请先在族索引中选择变体并回填 metric_id。以下展示的是库内口径字段，不是独立卡。';
      wrap.appendChild(notBuilt);
    } else if (card.docPath) {
      var source = document.createElement('div');
      source.className = 'g3-note';
      source.textContent = '卡源：' + card.docPath;
      wrap.appendChild(source);
    }

    var badges = document.createElement('div');
    badges.className = 'g3-badges';
    (card.badges || []).forEach(function (item) {
      badges.appendChild(badge(item.label, item.tone));
    });
    wrap.appendChild(badges);

    (card.sections || []).forEach(function (section) {
      var row = document.createElement('div');
      row.className = 'g3-field';
      var name = document.createElement('span');
      name.className = 'g3-field-name';
      name.textContent = section.title;
      var value = document.createElement('span');
      value.className = 'g3-field-value';
      value.textContent = section.text;
      if (section.key === 'formula') {
        value.appendChild(document.createTextNode(' '));
        value.appendChild(link(
          card.links.output,
          '查看输出端点',
          '/metrics/' + card.metricId + '/output（后端可能返回 E_METRIC_VARIANT_REQUIRED 等结构化错误）'
        ));
      }
      if (section.key === 'evidence') {
        value.appendChild(document.createTextNode(' '));
        value.appendChild(link(
          card.links.detailApi,
          '查看证据详情',
          '只读 /browse/metrics/' + card.metricId
        ));
      }
      row.appendChild(name);
      row.appendChild(value);
      wrap.appendChild(row);
    });

    var provWrap = document.createElement('div');
    provWrap.className = 'g3-box';
    var provTitle = document.createElement('h4');
    provTitle.textContent = 'PROV 判定链';
    provWrap.appendChild(provTitle);
    var provNote = document.createElement('div');
    provNote.className = 'g3-note';
    provNote.textContent = card.prov.decisionLabel
      + ' · 图 ' + card.prov.graph;
    provWrap.appendChild(provNote);
    var provLinks = document.createElement('div');
    provLinks.className = 'g3-actions';
    provLinks.appendChild(link(
      card.prov.decisionsUrl,
      'PROV 判定记录'
        + (card.prov.decisionCount == null ? '' : '（' + card.prov.decisionCount + '）'),
      '只读 /prov/decisions'
    ));
    provLinks.appendChild(link(card.prov.verifyUrl, 'PROV 图校验', '只读 /prov/verify'));
    // 跨 tab 跳转：URL 由 BrowseUrls 集中生成（R-04 约定未定，见 browse_urls.js TODO）。
    provLinks.appendChild(link(
      window.BrowseUrls.provTriplesTab(),
      '在三元组 tab 查看 PROV 图',
      '跨 tab 跳转占位约定',
      true
    ));
    provWrap.appendChild(provLinks);
    wrap.appendChild(provWrap);

    box.appendChild(wrap);
  }

  function selectVariant(family, metricId) {
    G3.selectedMetricId = metricId;
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', window.BrowseUrls.metricsTab(metricId));
    }
    var row = findMetricRow(metricId);
    if (row) {
      row.click();
      return;
    }
    var box = el('metric-detail');
    if (box) { renderFamilyBox(box, family, metricId); }
  }

  function findMetricRow(metricId) {
    var tbody = el('metrics-table') && el('metrics-table').querySelector('tbody');
    if (!tbody) { return null; }
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    for (var i = 0; i < rows.length; i += 1) {
      var cell = rows[i].cells[0];
      if (cell && cell.textContent.trim() === metricId) { return rows[i]; }
    }
    return null;
  }

  function renderFamilyBox(box, family, selectedId) {
    clearG3(box, 'family');
    var wrap = document.createElement('div');
    wrap.className = 'g3-box';
    wrap.setAttribute('data-g3', 'family');

    var title = document.createElement('h4');
    title.textContent = '口径族索引 · ' + family.familyId;
    wrap.appendChild(title);

    var warn = document.createElement('div');
    warn.className = 'g3-warn';
    var guidance = family.guidance || {};
    var text = document.createElement('div');
    text.textContent = (guidance.code || 'E_METRIC_VARIANT_REQUIRED') + '：'
      + (guidance.message || '该指标是口径族索引，不直接出数；请先选择变体并回填 metric_id。');
    warn.appendChild(text);
    (guidance.howTo || []).forEach(function (step) {
      var line = document.createElement('div');
      line.className = 'g3-note';
      line.textContent = '· ' + step;
      warn.appendChild(line);
    });
    wrap.appendChild(warn);

    var diffLine = document.createElement('div');
    diffLine.className = 'g3-note';
    diffLine.textContent = '差异：' + (family.diffs || []).map(function (diff) {
      return diff.label + (diff.different ? '（不同）' : '（相同）');
    }).join('｜');
    wrap.appendChild(diffLine);

    var table = document.createElement('table');
    table.className = 'g3-variants';
    var thead = document.createElement('thead');
    var headRow = document.createElement('tr');
    ['变体 metric_id', '观察窗口', '分母', '粒度', 'publishable', '操作'].forEach(function (label) {
      var th = document.createElement('th');
      th.textContent = label;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var activeId = selectedId || G3.selectedMetricId;
    var tbody = document.createElement('tbody');
    (family.variants || []).forEach(function (variant) {
      var tr = document.createElement('tr');
      if (variant.metricId === activeId) { tr.className = 'selected'; }
      var nameCell = document.createElement('td');
      nameCell.className = 'g3-mono';
      nameCell.textContent = variant.metricId;
      var name = document.createElement('div');
      name.className = 'g3-note';
      name.textContent = variant.nameZh || '';
      nameCell.appendChild(name);
      tr.appendChild(nameCell);
      [variant.window.text + '（' + (variant.window.minWindowDays || 0) + ' 天）',
        variant.denominator,
        variant.grain,
        String(variant.publishable)].forEach(function (value) {
        var td = document.createElement('td');
        td.textContent = value == null || value === '' ? '口径未给出' : String(value);
        tr.appendChild(td);
      });
      var action = document.createElement('td');
      var button = document.createElement('button');
      button.textContent = variant.metricId === activeId ? '已选择' : '选择此变体';
      button.disabled = variant.metricId === activeId;
      button.addEventListener('click', function (event) {
        event.stopPropagation();
        selectVariant(family, variant.metricId);
      });
      action.appendChild(button);
      tr.appendChild(action);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);

    var status = document.createElement('div');
    status.className = 'g3-note';
    status.textContent = activeId
      ? '已回填 metric_id：' + activeId
      : '尚未选择变体；直接以族索引出数会返回 E_METRIC_VARIANT_REQUIRED。';
    wrap.appendChild(status);

    box.appendChild(wrap);
  }

  function watchDetail(metricId) {
    if (G3.detailTimers[metricId]) { clearInterval(G3.detailTimers[metricId]); }
    var tries = 0;
    G3.detailTimers[metricId] = setInterval(function () {
      tries += 1;
      var box = el('metric-detail');
      var title = box && box.querySelector('h3');
      if (box && title && title.textContent.indexOf(metricId + ' · ') === 0) {
        clearInterval(G3.detailTimers[metricId]);
        delete G3.detailTimers[metricId];
        enhanceDetail(box, metricId);
      } else if (tries > 50) {
        clearInterval(G3.detailTimers[metricId]);
        delete G3.detailTimers[metricId];
      }
    }, 100);
  }

  function enhanceDetail(box, metricId) {
    clearG3(box);
    getJson(window.BrowseUrls.metricCard(metricId)).then(function (card) {
      var title = box.querySelector('h3');
      if (title && title.textContent.indexOf(metricId + ' · ') === 0) {
        renderCardBox(box, card);
      }
    }).catch(function () { /* 卡不可用不影响既有详情 */ });

    familyIndex().then(function (families) {
      var family = familyFor(families, metricId);
      if (family && family.variants && family.variants.length) {
        renderFamilyBox(box, family, metricId);
      }
    }).catch(function () { /* 族信息不可用时不影响既有详情 */ });
  }

  function wire() {
    injectStyle();
    startRowObserver();

    document.addEventListener('click', function (event) {
      var target = event.target;
      var row = target && target.closest && target.closest('#metrics-table tbody tr');
      if (!row || !row.cells || !row.cells[0]) { return; }
      var metricId = row.cells[0].textContent.trim();
      if (metricId) { watchDetail(metricId); }
    }, true);

    // 深链占位约定：browse.html?tab=<view>&metric=<metricId>（R-04 未定，见 browse_urls.js）。
    var params = new URLSearchParams(window.location.search);
    var tab = params.get(window.BrowseUrls.VIEW_PARAM);
    var metricId = params.get(window.BrowseUrls.METRIC_PARAM);
    var desired = metricId ? 'metrics' : tab;
    if (desired && /^[a-z-]+$/.test(desired)) {
      var tabButton = document.querySelector('.tab[data-view="' + desired + '"]');
      var view = el('view-' + desired);
      if (tabButton && view && view.hidden) { tabButton.click(); }
    }
    if (metricId) {
      watchDetail(metricId);
      if (!findMetricRow(metricId)) {
        var tries = 0;
        var timer = setInterval(function () {
          tries += 1;
          var row = findMetricRow(metricId);
          if (row) {
            clearInterval(timer);
            row.click();
          } else if (tries > 50) {
            clearInterval(timer);
          }
        }, 100);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
}());
