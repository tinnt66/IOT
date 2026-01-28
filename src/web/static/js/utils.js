/* global jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};

  window.WebDashboard.utils = {
    nowLocalTime: function () {
      var d = new Date();
      return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },
    fmtFixed: function (v, digits) {
      if (v === null || v === undefined) return '-';
      var n = Number(v);
      if (!Number.isFinite(n)) return '-';
      return n.toFixed(digits);
    },
    fmtInt: function (v) {
      if (v === null || v === undefined) return '-';
      var n = Number(v);
      if (!Number.isFinite(n)) return '-';
      return Math.trunc(n).toLocaleString();
    },
    normalizeDatetimeLocal: function (value) {
      if (!value) return '';
      return value.length === 16 ? value + ':00' : value;
    },
    buildRangeParams: function (startValue, endValue) {
      var params = {};
      var start = window.WebDashboard.utils.normalizeDatetimeLocal(startValue);
      var end = window.WebDashboard.utils.normalizeDatetimeLocal(endValue);
      if (start) params.start = start;
      if (end) params.end = end;
      return params;
    }
  };
})(window, jQuery);

