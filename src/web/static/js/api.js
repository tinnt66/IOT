/* global jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};
  var utils = window.WebDashboard.utils;

  function getJson(url, params) {
    return $.ajax({
      url: url,
      method: 'GET',
      data: params || {},
      dataType: 'json',
      cache: false
    });
  }

  window.WebDashboard.api = {
    dbRs485: function (params) {
      return getJson('/api/db/rs485', params);
    },
    dbAdxl: function (params) {
      return getJson('/api/db/adxl', params);
    },
    exportUrl: function (kind, fmt, startValue, endValue) {
      var params = utils.buildRangeParams(startValue, endValue);
      var q = $.param(params);
      var base = '/api/export/' + kind + '.' + fmt;
      return q ? base + '?' + q : base;
    }
  };
})(window, jQuery);

