/* D1-1 canvas path panel (design 53/55).
 *
 * Self-contained: creates its own <section> inside <main>, calls the read-only
 * GET /browse/path endpoint, renders tables first and a tiny SVG (<= 12 nodes)
 * only as a supplement. No changes to browse.js / app.js are required.
 */
(function () {
  "use strict";

  var MAX_SVG_NODES = 12;
  var EMPTY_REASONS = {
    E_PATH_NOT_FOUND: "在跳数上限内没有找到路径（不是错误，可放宽 maxHops 或换起点）",
    E_CANVAS_TRUNCATED: "达到节点/边上限后仍无路径，结果是截断的",
    E_CANVAS_TBOX_EMPTY: "当前 T-Box 没有声明可用谓词，多跳图不可用",
    E_CANVAS_NO_GRAPH: "当前没有可读命名图（T-Box/推断/ABox 均为空）"
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

  function local(value) {
    return value && value.label ? value.label : short(value && value.iri);
  }

  function mount() {
    var main = document.querySelector("main");
    if (!main || document.getElementById("canvas-path")) return;

    var panel = document.createElement("section");
    panel.className = "panel";
    panel.id = "canvas-path";
    panel.innerHTML =
      '<h2>多跳路径 <span class="sub">只读 · simple 实现 · 1–3 跳</span></h2>' +
      '<form id="canvas-path-form" style="display:flex;gap:8px;flex-wrap:wrap;align-items:end">' +
      '<label class="hint" style="flex:1 1 260px">起点 IRI<br>' +
      '<input id="canvas-path-from" required style="width:100%"></label>' +
      '<label class="hint" style="flex:1 1 260px">终点 IRI（留空=邻域）<br>' +
      '<input id="canvas-path-to" style="width:100%"></label>' +
      '<label class="hint">maxHops<br>' +
      '<select id="canvas-path-hops"><option>1</option><option>2</option>' +
      '<option selected>3</option></select></label>' +
      '<button class="primary" type="submit">查路径</button>' +
      "</form>" +
      '<p class="hint" id="canvas-path-status">输入 urn:platform: 或 http(s) IRI；结果只读，不写图。</p>' +
      '<div id="canvas-path-body"></div>';

    main.appendChild(panel);

    var params = new URLSearchParams(window.location.search);
    if (params.get("from")) panel.querySelector("#canvas-path-from").value = params.get("from");
    if (params.get("to")) panel.querySelector("#canvas-path-to").value = params.get("to");
    panel.querySelector("#canvas-path-form").addEventListener("submit", run);
  }

  function setStatus(text, bad) {
    var status = document.getElementById("canvas-path-status");
    status.textContent = text;
    status.style.color = bad ? "var(--bad)" : "var(--muted)";
  }

  function run(event) {
    event.preventDefault();
    var from = document.getElementById("canvas-path-from").value.trim();
    var to = document.getElementById("canvas-path-to").value.trim();
    var hops = document.getElementById("canvas-path-hops").value;
    var url = "/browse/path?from=" + encodeURIComponent(from) + "&maxHops=" + hops;
    if (to) url += "&to=" + encodeURIComponent(to);

    setStatus("查询中…", false);
    document.getElementById("canvas-path-body").innerHTML = "";
    fetch(url)
      .then(function (response) {
        return response.json().then(function (payload) {
          return { ok: response.ok, status: response.status, payload: payload };
        });
      })
      .then(render)
      .catch(function (error) {
        setStatus("请求失败：" + error.message, true);
      });
  }

  function render(answer) {
    var payload = answer.payload || {};
    if (!answer.ok) {
      var err = payload.error || {};
      setStatus(
        "不可用：HTTP " + answer.status + " · " + (err.code || "E_UNKNOWN") +
          (err.providerCode ? " · " + err.providerCode : ""),
        true
      );
      return;
    }
    var stats = payload.stats || {};
    var parts = [
      payload.provider + "/" + payload.mode,
      stats.nodes + " 节点",
      stats.edges + " 边",
      stats.paths + " 路径",
      (stats.elapsedMs || 0) + "ms"
    ];
    if (payload.truncated) parts.push("已截断");
    setStatus(parts.join(" · "), false);

    var body = document.getElementById("canvas-path-body");
    if (payload.emptyReason) {
      body.appendChild(
        note(
          EMPTY_REASONS[payload.emptyReason] || ("无结果：" + payload.emptyReason),
          "warn"
        )
      );
    }
    body.appendChild(pathsTable(payload.paths || []));
    body.appendChild(edgesTable(payload.edges || []));
    if ((payload.nodes || []).length <= MAX_SVG_NODES && (payload.edges || []).length) {
      body.appendChild(svg(payload.nodes, payload.edges));
    }
  }

  function note(text, tone) {
    var div = document.createElement("div");
    div.className = "hint";
    div.style.margin = "10px 0";
    if (tone) div.style.color = "var(--warn)";
    div.textContent = text;
    return div;
  }

  function pathsTable(paths) {
    var wrap = document.createElement("div");
    if (!paths.length) {
      wrap.appendChild(note("没有返回路径。", ""));
      return wrap;
    }
    var rows = paths
      .map(function (path) {
        var nodes = (path.nodes || []).map(short).join(" → ");
        var edges = (path.edges || []).map(function (edge) {
          return short(edge.p);
        }).join(", ");
        return (
          "<tr><td>" + path.length + " 跳</td><td class=\"mono truncate\" title=\"" +
          esc((path.nodes || []).join(" → ")) + "\">" + esc(nodes) + "</td><td>" +
          esc(edges) + "</td></tr>"
        );
      })
      .join("");
    wrap.innerHTML =
      "<table><thead><tr><th>长度</th><th>节点序列</th><th>谓词</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    return wrap;
  }

  function edgesTable(edges) {
    var wrap = document.createElement("div");
    wrap.style.marginTop = "12px";
    if (!edges.length) return wrap;
    var rows = edges
      .map(function (edge) {
        var graph = (edge.source && edge.source.graph) || "";
        return (
          "<tr><td class=\"mono truncate\">" + esc(short(edge.s)) +
          "</td><td class=\"mono\">" + esc(short(edge.p)) +
          "</td><td class=\"mono truncate\">" + esc(short(edge.o)) +
          "</td><td>" + esc(edge.dir) + "</td><td class=\"mono truncate\">" +
          esc(short(graph)) + "</td></tr>"
        );
      })
      .join("");
    wrap.innerHTML =
      "<table><thead><tr><th>主体</th><th>谓词</th><th>客体</th><th>方向</th>" +
      "<th>命名图</th></tr></thead><tbody>" + rows + "</tbody></table>";
    return wrap;
  }

  function svg(nodes, edges) {
    var wrap = document.createElement("div");
    wrap.style.marginTop = "12px";
    var width = 720;
    var height = 320;
    var centerX = width / 2;
    var centerY = height / 2;
    var radius = Math.min(width, height) / 2 - 46;
    var point = {};
    nodes.forEach(function (node, index) {
      var angle = (2 * Math.PI * index) / nodes.length - Math.PI / 2;
      point[node.iri] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });
    var lines = edges
      .filter(function (edge) {
        return point[edge.s] && point[edge.o];
      })
      .map(function (edge) {
        var a = point[edge.s];
        var b = point[edge.o];
        return (
          '<line x1="' + a.x.toFixed(1) + '" y1="' + a.y.toFixed(1) +
          '" x2="' + b.x.toFixed(1) + '" y2="' + b.y.toFixed(1) +
          '" stroke="#9fb3c8" stroke-width="1.5"></line>'
        );
      })
      .join("");
    var circles = nodes
      .map(function (node) {
        var at = point[node.iri];
        return (
          '<g><circle cx="' + at.x.toFixed(1) + '" cy="' + at.y.toFixed(1) +
          '" r="14" fill="#eaf2fb" stroke="#3b76b8"></circle>' +
          '<text x="' + at.x.toFixed(1) + '" y="' + (at.y + 26) +
          '" font-size="11" text-anchor="middle" fill="#334">' +
          esc(local(node)) + "</text>" +
          '<title>' + esc(node.iri) + "</title></g>"
        );
      })
      .join("");
    wrap.innerHTML =
      '<svg viewBox="0 0 ' + width + " " + height +
      '" width="100%" height="' + height +
      '" role="img" aria-label="路径示意"><g>' + lines + "</g><g>" + circles + "</g></svg>" +
      '<p class="hint">示意布局，仅用于确认连通关系；节点超过 ' + MAX_SVG_NODES + " 个时不绘制。</p>";
    return wrap;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
