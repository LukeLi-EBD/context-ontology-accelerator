// M-03: /browse 口径卡 tab 的族索引指引与变体选择。
// 本文件为独立增量脚本：不修改 browse.js，只在既有 DOM 上追加 G3 区块。
// 跨 tab / 深链 URL 一律经 BrowseUrls（browse_urls.js）生成。
(function () {
  'use strict';

  var G3 = {
    selectedMetricId: null,
    familyCache: { items: null, promise: null },
    detailTimers: {},
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
      '.g3-link{font-size:12px}'
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

  function clearG3(box) {
    Array.prototype.slice.call(box.querySelectorAll('[data-g3]')).forEach(function (node) {
      node.parentNode.removeChild(node);
    });
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
    clearG3(box);
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
    familyIndex().then(function (families) {
      var family = familyFor(families, metricId);
      if (family && family.variants && family.variants.length) {
        renderFamilyBox(box, family, metricId);
      }
    }).catch(function () { /* 族信息不可用时不影响既有详情 */ });
  }

  function wire() {
    injectStyle();

    document.addEventListener('click', function (event) {
      var target = event.target;
      var row = target && target.closest && target.closest('#metrics-table tbody tr');
      if (!row || !row.cells || !row.cells[0]) { return; }
      var metricId = row.cells[0].textContent.trim();
      if (metricId) { watchDetail(metricId); }
    }, true);

    var params = new URLSearchParams(window.location.search);
    var tab = params.get(window.BrowseUrls.VIEW_PARAM);
    var metricId = params.get(window.BrowseUrls.METRIC_PARAM);
    if (tab === 'metrics' || metricId) {
      var tabButton = document.querySelector('.tab[data-view="metrics"]');
      if (tabButton && !document.querySelector('#view-metrics').hidden) {
        if (metricId) { watchDetail(metricId); }
      } else if (tabButton) {
        tabButton.click();
      }
      if (metricId && !findMetricRow(metricId)) {
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
