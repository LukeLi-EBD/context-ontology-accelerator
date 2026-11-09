/* D1-2 full canvas panel (design 53/55/62).
 *
 * Standalone: mounts its own <section> only when GET /browse/canvas/manifest
 * reports provider=full. Under simple/off it does nothing, so the existing
 * browse_path.js panel keeps working and no page has to be changed. In full
 * mode the older panel is hidden to avoid two competing canvases.
 *
 * Rendering strategy: server-side aggregation + cursor pages. Each page adds
 * at most pageSize nodes/edges; the drawing never exceeds 300 nodes. Provenance
 * badges come straight from source.hasRef/resolveUrl (no client guessing).
 */
(function () {
  "use strict";

  var MAX_DRAW_NODES = 300;
  var MAX_TABLE_ROWS = 400;
  var CLUSTER_COLORS = [
    "#3b76b8", "#2f9e7a", "#b86b3b", "#7b5bb8", "#b83b6b",
    "#5a8f2f", "#b8a13b", "#3bb3b8"
  ];
  var TRUNC_REASONS = {
    E_CANVAS_NODES_TRUNCATED: "节点数达到上限，结果已截断",
    E_CANVAS_EDGES_TRUNCATED: "边数达到上限，结果已截断",
    E_CANVAS_PATHS_TRUNCATED: "路径数达到上限，只保留较短/较轻的路径",
    E_CANVAS_TIMEOUT: "超出请求预算，结果已中止"
  };

  var state = {
    nodes: [],
    edges: [],
    paths: [],
    degree: {},
    cluster: {},
    stats: null,
    page: null,
    request: 0,
    lastQuery: null
  };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function short(iri) {
    var text = String(iri || "");
    var cut = Math.max(text.lastIndexOf("#"), text.lastIndexOf("/"));
    return cut >= 0 ? text.slice(cut + 1) : text;
  }

  function pct(ratio) {
    var number = Number(ratio || 0);
    return (number * 100).toFixed(number === 0 || number === 1 ? 0 : 1) + "%";
  }

  function setStatus(text, bad) {
    var node = document.getElementById("cf-status");
    if (!node) return;
    node.textContent = text;
    node.style.color = bad ? "var(--bad)" : "var(--muted)";
  }

  function mount() {
    var main = document.querySelector("main");
    if (!main || document.getElementById("canvas-full")) return;

    var old = document.getElementById("canvas-path");
    if (old) old.hidden = true;

    var panel = document.createElement("section");
    panel.className = "panel";
    panel.id = "canvas-full";
    panel.innerHTML =
      '<h2>全画布 <span class="sub">只读 · full 实现 · 1–6 跳 · 服务端聚合 + 游标分页</span></h2>' +
      '<form id="cf-form" class="cf-filters">' +
      '<label>起点 IRI<input id="cf-from" type="text" required style="min-width:260px"></label>' +
      '<label>终点 IRI（留空=邻域）<input id="cf-to" type="text" style="min-width:260px"></label>' +
      '<label>maxHops<select id="cf-hops">' +
      '<option>1</option><option>2</option><option selected>3</option>' +
      '<option>4</option><option>5</option><option>6</option></select></label>' +
      '<label>maxNodes<select id="cf-nodes">' +
      '<option>100</option><option>200</option><option>400</option>' +
      '<option>800</option><option>1000</option></select></label>' +
      '<label>maxEdges<select id="cf-edges">' +
      '<option>200</option><option selected>400</option><option>800</option>' +
      '<option>1200</option><option>1500</option></select></label>' +
      '<label>maxPaths<select id="cf-paths">' +
      '<option>10</option><option selected>20</option><option>50</option></select></label>' +
      '<label>pageSize<select id="cf-page">' +
      '<option>50</option><option selected>100</option><option>200</option></select></label>' +
      '<div class="cf-checks" id="cf-kinds">' +
      '<label><input type="checkbox" value="object" checked> object</label>' +
      '<label><input type="checkbox" value="datatype"> datatype</label>' +
      '<label><input type="checkbox" value="annotation"> annotation</label>' +
      '<label><input type="checkbox" value="rdf"> rdf</label>' +
      '</div>' +
      '<button class="primary" type="submit">查询全画布</button>' +
      '<button type="button" id="cf-clear">清空</button>' +
      '</form>' +
      '<p class="hint" id="cf-status">输入 IRI；服务端聚合、分页下拉，结果只读不写图。</p>' +
      '<div id="cf-warnings"></div>' +
      '<div class="cf-grid">' +
      '<div class="cf-canvas-wrap"><canvas id="cf-canvas" width="760" height="460"></canvas></div>' +
      '<div class="cf-side" id="cf-side"></div>' +
      '</div>' +
      '<div class="cf-tables" id="cf-tables"></div>' +
      '<div class="toolbar" style="margin-top:10px">' +
      '<button type="button" id="cf-more" hidden>加载下一页</button>' +
      '<span class="hint" id="cf-page-note"></span>' +
      '</div>';

    main.appendChild(panel);

    var params = new URLSearchParams(window.location.search);
    if (params.get("from")) panel.querySelector("#cf-from").value = params.get("from");
    if (params.get("to")) panel.querySelector("#cf-to").value = params.get("to");
    panel.querySelector("#cf-form").addEventListener("submit", function (event) {
      event.preventDefault();
      run(true);
    });
    panel.querySelector("#cf-clear").addEventListener("click", clear);
    panel.querySelector("#cf-more").addEventListener("click", function () {
      run(false);
    });
    draw();
  }

  function clear() {
    state.nodes = [];
    state.edges = [];
    state.paths = [];
    state.degree = {};
    state.cluster = {};
    state.stats = null;
    state.page = null;
    state.lastQuery = null;
    document.getElementById("cf-warnings").innerHTML = "";
    document.getElementById("cf-side").innerHTML = "";
    document.getElementById("cf-tables").innerHTML = "";
    document.getElementById("cf-more").hidden = true;
    document.getElementById("cf-page-note").textContent = "";
    setStatus("已清空。", false);
    draw();
  }

  function kinds() {
    var boxes = Array.prototype.slice.call(
      document.querySelectorAll("#cf-kinds input[type=checkbox]")
    );
    var selected = boxes.filter(function (box) { return box.checked; })
      .map(function (box) { return box.value; });
    if (selected.length === boxes.length) return null;
    return selected;
  }

  function queryParams(cursor) {
    var params = new URLSearchParams();
    params.set("from", document.getElementById("cf-from").value.trim());
    var to = document.getElementById("cf-to").value.trim();
    if (to) params.set("to", to);
    params.set("maxHops", document.getElementById("cf-hops").value);
    params.set("maxNodes", document.getElementById("cf-nodes").value);
    params.set("maxEdges", document.getElementById("cf-edges").value);
    params.set("maxPaths", document.getElementById("cf-paths").value);
    params.set("pageSize", document.getElementById("cf-page").value);
    var selected = kinds();
    if (selected) params.set("predicateTypes", selected.join(","));
    if (cursor) params.set("cursor", cursor);
    return params;
  }

  function run(reset) {
    var from = document.getElementById("cf-from").value.trim();
    if (!from) return;
    if (reset) {
      state.nodes = [];
      state.edges = [];
      state.paths = [];
      state.degree = {};
      state.cluster = {};
      state.stats = null;
      state.page = null;
      document.getElementById("cf-warnings").innerHTML = "";
      document.getElementById("cf-tables").innerHTML = "";
    }
    var cursor = reset ? null : (state.page && state.page.nextCursor);
    if (!reset && !cursor) return;
    var params = queryParams(cursor);
    state.lastQuery = params.toString();
    var token = ++state.request;
    document.getElementById("cf-more").disabled = true;
    setStatus(reset ? "查询中…" : "加载下一页…", false);

    fetch("/browse/canvas/full?" + params.toString())
      .then(function (response) {
        return response.json().then(function (payload) {
          return { ok: response.ok, status: response.status, payload: payload };
        });
      })
      .then(function (answer) {
        if (token !== state.request) return;
        document.getElementById("cf-more").disabled = false;
        if (!answer.ok) {
          var err = (answer.payload || {}).error || {};
          setStatus(
            "不可用：HTTP " + answer.status + " · " + (err.code || "E_UNKNOWN") +
              (err.providerCode ? " · " + err.providerCode : "") +
              (err.message ? " · " + err.message : ""),
            true
          );
          return;
        }
        append(answer.payload);
        render();
      })
      .catch(function (error) {
        if (token !== state.request) return;
        document.getElementById("cf-more").disabled = false;
        setStatus("请求失败：" + error.message, true);
      });
  }

  function append(payload) {
    var nodes = payload.nodes || [];
    var edges = payload.edges || [];
    var known = {};
    state.nodes.forEach(function (node) { known[node.iri] = true; });
    nodes.forEach(function (node) {
      if (!known[node.iri]) {
        known[node.iri] = true;
        state.nodes.push(node);
      }
    });
    var knownEdges = {};
    state.edges.forEach(function (edge) {
      knownEdges[edge.s + "|" + edge.p + "|" + edge.o + "|" + edge.dir] = true;
    });
    edges.forEach(function (edge) {
      var key = edge.s + "|" + edge.p + "|" + edge.o + "|" + edge.dir;
      if (!knownEdges[key]) {
        knownEdges[key] = true;
        state.edges.push(edge);
      }
    });
    state.paths = payload.paths || state.paths;
    state.stats = payload.stats || state.stats;
    state.page = payload.page || state.page;
    var aggregates = payload.aggregates || {};
    (aggregates.nodeDegree || []).forEach(function (item) {
      state.degree[item.iri] = Math.max(state.degree[item.iri] || 0, item.total);
    });
    var layout = payload.layout || {};
    (layout.nodes || []).forEach(function (item) {
      state.cluster[item.iri] = item.cluster;
      if (item.degree != null) {
        state.degree[item.iri] = Math.max(state.degree[item.iri] || 0, item.degree);
      }
    });
  }

  function render() {
    var stats = state.stats || {};
    var page = state.page || {};
    var coverage = stats.refCoverage || {};
    var truncation = stats.truncation || {};
    var parts = [
      "full/" + (state.paths.length ? "path" : "subgraph"),
      (stats.totalNodes != null ? stats.totalNodes : state.nodes.length) + " 节点",
      (stats.totalEdges != null ? stats.totalEdges : state.edges.length) + " 边",
      state.paths.length + " 路径",
      (stats.elapsedMs || 0) + "ms"
    ];
    if (truncation.truncated) parts.push("已截断");
    setStatus(parts.join(" · "), false);

    renderWarnings(truncation, coverage);
    renderSide(stats, page, coverage, truncation);
    renderTables();
    document.getElementById("cf-page-note").textContent =
      "累计 " + state.nodes.length + "/" + (page.totalNodes || 0) + " 节点 · " +
      state.edges.length + "/" + (page.totalEdges || 0) + " 边（图最多绘制 " +
      MAX_DRAW_NODES + " 个节点）";
    document.getElementById("cf-more").hidden = !(page.nextCursor);
    draw();
  }

  function renderWarnings(truncation, coverage) {
    var box = document.getElementById("cf-warnings");
    box.innerHTML = "";
    (truncation.reasons || []).forEach(function (code) {
      var div = document.createElement("div");
      div.className = "cf-warn";
      div.textContent = "截断原因：" + code + " — " + (TRUNC_REASONS[code] || "达到上限");
      box.appendChild(div);
    });
    if (coverage.error) {
      var note = document.createElement("div");
      note.className = "cf-warn";
      note.textContent = "溯源查询降级：" + coverage.error + "（hasRef=false 仅代表未取到引用）";
      box.appendChild(note);
    }
  }

  function renderSide(stats, page, coverage, truncation) {
    var side = document.getElementById("cf-side");
    var timings = stats.timings || {};
    var timingRows = Object.keys(timings).map(function (key) {
      return "<dt>" + esc(key) + "</dt><dd>" + esc(timings[key]) + "ms</dd>";
    }).join("");
    side.innerHTML =
      "<h3 style=\"margin-top:0\">运行统计</h3>" +
      "<dl class=\"cf-kv\">" +
      "<dt>provider</dt><dd>full</dd>" +
      "<dt>总耗时</dt><dd>" + esc(stats.elapsedMs || 0) + "ms</dd>" +
      "<dt>本页节点/边</dt><dd>" + esc(stats.nodes || 0) + " / " + esc(stats.edges || 0) + "</dd>" +
      "<dt>总节点/边</dt><dd>" + esc(page.totalNodes || 0) + " / " + esc(page.totalEdges || 0) + "</dd>" +
      "<dt>hasRef 节点</dt><dd>" + esc(coverage.nodesWithRef || 0) + " / " + esc(coverage.nodes || 0) + " (" + pct(coverage.nodeRatio) + ")</dd>" +
      "<dt>hasRef 边</dt><dd>" + esc(coverage.edgesWithRef || 0) + " / " + esc(coverage.edges || 0) + " (" + pct(coverage.edgeRatio) + ")</dd>" +
      "<dt>截断</dt><dd>" + (truncation.truncated ? "是" : "否") + "</dd>" +
      timingRows +
      "</dl>" +
      "<p class=\"hint\" style=\"margin:8px 0 0\">hasRef 只来自已通过的抽取候选（文档块）与 PROV src:// 引用；没有可解析引用时保持 false。</p>";
  }

  function refCell(source) {
    if (source && source.hasRef && source.ref) {
      var url = source.resolveUrl || ("/source/resolve?ref=" + encodeURIComponent(source.ref));
      return '<a class="cf-ref" href="' + esc(url) + '" target="_blank" rel="noopener" title="' +
        esc(source.ref) + '">src</a>';
    }
    return '<span class="cf-ref missing" title="没有可解析的 source key">无</span>';
  }

  function renderTables() {
    var box = document.getElementById("cf-tables");
    box.innerHTML = "";
    if (state.paths.length) {
      var pathRows = state.paths.map(function (path) {
        return "<tr><td>" + esc(path.length) + " 跳</td><td class=\"cf-truncate mono\" title=\"" +
          esc((path.nodes || []).join(" → ")) + "\">" +
          esc((path.nodes || []).map(short).join(" → ")) + "</td><td>" +
          esc((path.edges || []).map(function (edge) { return short(edge.p); }).join(", ")) +
          "</td></tr>";
      }).join("");
      box.appendChild(table("路径 " + state.paths.length,
        "<th>长度</th><th>节点序列</th><th>谓词</th>", pathRows));
    }

    var nodes = state.nodes.slice(0, MAX_TABLE_ROWS);
    var nodeRows = nodes.map(function (node) {
      return "<tr><td class=\"cf-truncate mono\" title=\"" + esc(node.iri) + "\">" +
        esc(short(node.iri)) + "</td><td>" + esc(node.label || "") +
        "</td><td>" + esc((node.types || []).map(short).join(", ")) +
        "</td><td>" + esc(state.degree[node.iri] || 0) +
        "</td><td>" + refCell(node.source) + "</td></tr>";
    }).join("");
    box.appendChild(table("节点 " + state.nodes.length + (state.nodes.length > nodes.length ? "（显示前 " + MAX_TABLE_ROWS + "）" : ""),
      "<th>IRI</th><th>标签</th><th>类型</th><th>度数</th><th>溯源</th>", nodeRows));

    var edges = state.edges.slice(0, MAX_TABLE_ROWS);
    var edgeRows = edges.map(function (edge) {
      return "<tr><td class=\"cf-truncate mono\" title=\"" + esc(edge.s) + "\">" +
        esc(short(edge.s)) + "</td><td class=\"mono\">" + esc(short(edge.p)) +
        "</td><td class=\"cf-truncate mono\" title=\"" + esc(edge.o) + "\">" + esc(short(edge.o)) +
        "</td><td>" + esc(edge.dir) + "</td><td>" + refCell(edge.source) + "</td></tr>";
    }).join("");
    box.appendChild(table("边 " + state.edges.length + (state.edges.length > edges.length ? "（显示前 " + MAX_TABLE_ROWS + "）" : ""),
      "<th>主体</th><th>谓词</th><th>客体</th><th>方向</th><th>溯源</th>", edgeRows));
  }

  function table(title, head, rows) {
    var wrap = document.createElement("div");
    wrap.innerHTML = "<h3>" + esc(title) + "</h3>" +
      '<div class="cf-table-wrap"><table><thead><tr>' + head +
      "</tr></thead><tbody>" + (rows || "<tr><td colspan=\"5\" class=\"hint\">无</td></tr>") +
      "</tbody></table></div>";
    return wrap;
  }

  function draw() {
    var canvas = document.getElementById("cf-canvas");
    if (!canvas) return;
    var ratio = window.devicePixelRatio || 1;
    var width = canvas.clientWidth || 760;
    var height = 460;
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
    }
    var ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);

    var drawn = state.nodes.slice(0, MAX_DRAW_NODES);
    var iris = {};
    drawn.forEach(function (node) { iris[node.iri] = true; });
    var positions = layout(drawn, width, height);
    var edges = state.edges.filter(function (edge) {
      return iris[edge.s] && iris[edge.o];
    });

    ctx.lineWidth = 1;
    edges.forEach(function (edge) {
      var a = positions[edge.s];
      var b = positions[edge.o];
      if (!a || !b) return;
      ctx.strokeStyle = edge.source && edge.source.hasRef ? "#d69a2d" : "#c2ccd8";
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    });

    drawn.forEach(function (node) {
      var at = positions[node.iri];
      if (!at) return;
      var degree = state.degree[node.iri] || 0;
      var radius = 3.5 + Math.min(9, Math.sqrt(degree) * 1.8);
      var cluster = Number(state.cluster[node.iri]);
      ctx.fillStyle = CLUSTER_COLORS[
        (cluster >= 0 ? cluster : 0) % CLUSTER_COLORS.length
      ];
      ctx.beginPath();
      ctx.arc(at.x, at.y, radius, 0, Math.PI * 2);
      ctx.fill();
      if (node.source && node.source.hasRef) {
        ctx.strokeStyle = "#d69a2d";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(at.x, at.y, radius + 2.5, 0, Math.PI * 2);
        ctx.stroke();
      }
    });

    if (drawn.length > 80) return;
    ctx.font = "10px system-ui, sans-serif";
    ctx.fillStyle = "#334";
    ctx.textAlign = "center";
    drawn.forEach(function (node) {
      var at = positions[node.iri];
      if (!at) return;
      var label = node.label || short(node.iri);
      ctx.fillText(label.length > 22 ? label.slice(0, 21) + "…" : label, at.x, at.y + 16);
    });
  }

  function layout(nodes, width, height) {
    var positions = {};
    var count = Math.max(1, nodes.length);
    var cx = width / 2;
    var cy = height / 2;
    nodes.forEach(function (node, index) {
      var cluster = Number(state.cluster[node.iri]);
      var ring = cluster >= 0 ? cluster : Math.floor(index / 60);
      var radius = Math.min(width, height) * 0.36 / (1 + ring * 0.6);
      var angle = (2 * Math.PI * index) / count + ring * 0.9;
      positions[node.iri] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle)
      };
    });
    if (nodes.length <= 1) return positions;

    var drawn = {};
    nodes.forEach(function (node) { drawn[node.iri] = true; });
    var edges = state.edges.filter(function (edge) {
      return drawn[edge.s] && drawn[edge.o];
    });
    var iterations = nodes.length > 220 ? 16 : 26;
    for (var step = 0; step < iterations; step++) {
      var force = {};
      nodes.forEach(function (node) {
        force[node.iri] = { x: 0, y: 0 };
      });
      for (var i = 0; i < nodes.length; i++) {
        for (var j = i + 1; j < nodes.length; j++) {
          var a = positions[nodes[i].iri];
          var b = positions[nodes[j].iri];
          var dx = a.x - b.x;
          var dy = a.y - b.y;
          var dist2 = dx * dx + dy * dy + 0.01;
          var dist = Math.sqrt(dist2);
          var repulse = 520 / dist2;
          var fx = (dx / dist) * repulse;
          var fy = (dy / dist) * repulse;
          force[nodes[i].iri].x += fx;
          force[nodes[i].iri].y += fy;
          force[nodes[j].iri].x -= fx;
          force[nodes[j].iri].y -= fy;
        }
      }
      edges.forEach(function (edge) {
        var a = positions[edge.s];
        var b = positions[edge.o];
        var dx = b.x - a.x;
        var dy = b.y - a.y;
        var dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
        var pull = (dist - 70) * 0.035;
        var fx = (dx / dist) * pull;
        var fy = (dy / dist) * pull;
        force[edge.s].x += fx;
        force[edge.s].y += fy;
        force[edge.o].x -= fx;
        force[edge.o].y -= fy;
      });
      nodes.forEach(function (node) {
        var at = positions[node.iri];
        var f = force[node.iri];
        f.x += (cx - at.x) * 0.01;
        f.y += (cy - at.y) * 0.01;
        at.x += Math.max(-12, Math.min(12, f.x));
        at.y += Math.max(-12, Math.min(12, f.y));
        at.x = Math.max(16, Math.min(width - 16, at.x));
        at.y = Math.max(16, Math.min(height - 16, at.y));
      });
    }
    return positions;
  }

  function boot() {
    fetch("/browse/canvas/manifest")
      .then(function (response) { return response.json(); })
      .then(function (manifest) {
        if (manifest && manifest.provider === "full") mount();
      })
      .catch(function () {
        /* no manifest -> keep the simple panel untouched */
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
