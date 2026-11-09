// 跨 tab / 深链 URL 集中常量。
// R-04 的跨 tab 跳转 URL 约定尚未冻结：这里先写占位实现，业务代码统一经本文件生成 URL，
// 不得在 browse_metrics.js 等处散落硬编码。
// TODO(R-04): 约定冻结后只改本文件；届时同步更新 metrics/triples 的 tab 参数名与参数编码。
(function () {
  function metricPath(metricId) {
    return '/browse/metrics/' + encodeURIComponent(String(metricId));
  }

  window.BrowseUrls = {
    // 占位约定：browse.html?tab=<view>&metric=<metricId>
    VIEW_PARAM: 'tab',
    METRIC_PARAM: 'metric',
    GRAPH_PARAM: 'graph',
    SUBJECT_PARAM: 'subject',
    PROV_GRAPH: 'urn:platform:prov',

    metricsTab: function (metricId) {
      if (!metricId) { return 'browse.html?tab=metrics'; }
      return 'browse.html?tab=metrics&metric=' + encodeURIComponent(String(metricId));
    },
    metricsView: function () { return 'browse.html?tab=metrics'; },
    provTriplesTab: function () {
      return 'browse.html?tab=triples&graph=' + encodeURIComponent(window.BrowseUrls.PROV_GRAPH);
    },
    provDecisions: function (metricId, limit) {
      return '/prov/decisions?metricId=' + encodeURIComponent(String(metricId))
        + '&limit=' + encodeURIComponent(String(limit || 20));
    },
    provVerify: function () { return '/prov/verify'; },
    metricCard: function (metricId) {
      return metricPath(metricId) + '/card';
    },
    metricOutput: function (metricId) {
      return '/metrics/' + encodeURIComponent(String(metricId)) + '/output';
    },
    families: function () { return '/metrics/report/families'; },
    family: function (familyId) {
      return '/metrics/report/families/' + encodeURIComponent(String(familyId));
    },
    manifest: function (scope) {
      return '/metrics/report/manifest?scope=' + encodeURIComponent(scope || 'all');
    },
    manifestCsv: function (scope) {
      return '/metrics/report/manifest.csv?scope=' + encodeURIComponent(scope || 'all');
    }
  };
}());
