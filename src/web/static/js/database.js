/* global jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};
  var api = window.WebDashboard.api;
  var utils = window.WebDashboard.utils;

  function renderRs485(items) {
    var $body = $('#rs485TableBody');
    $body.empty();
    if (!items || !items.length) {
      $body.append('<tr><td colspan="7" class="px-4 py-6 text-center text-gray-500 dark:text-gray-400">No data</td></tr>');
      return;
    }

    $.each(items, function (_i, d) {
      var wind = (d.wind_dir_txt || '-') + (d.wind_dir_deg !== null && d.wind_dir_deg !== undefined ? (' ' + d.wind_dir_deg + '°') : '');
      var $tr = $('<tr/>', { class: 'hover:bg-notion-bg dark:hover:bg-gray-950' });
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.id }));
      $tr.append($('<td/>', { class: 'px-4 py-3 whitespace-nowrap text-gray-700 dark:text-gray-200', text: d.time_local || '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.temp_c !== null && d.temp_c !== undefined ? utils.fmtFixed(d.temp_c, 1) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.hum_pct !== null && d.hum_pct !== undefined ? utils.fmtFixed(d.hum_pct, 1) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 whitespace-nowrap text-gray-700 dark:text-gray-200', text: wind }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.wind_spd_ms !== null && d.wind_spd_ms !== undefined ? utils.fmtFixed(d.wind_spd_ms, 1) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 whitespace-nowrap text-gray-500 dark:text-gray-400 text-xs', text: d.created_at || '-' }));
      $body.append($tr);
    });
  }

  function renderAdxl(items) {
    var $body = $('#adxlTableBody');
    $body.empty();
    if (!items || !items.length) {
      $body.append('<tr><td colspan="5" class="px-4 py-6 text-center text-gray-500 dark:text-gray-400">No data</td></tr>');
      return;
    }

    $.each(items, function (_i, d) {
      var $tr = $('<tr/>', { class: 'hover:bg-notion-bg dark:hover:bg-gray-950' });
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.id }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.chunk_start_us !== null && d.chunk_start_us !== undefined ? utils.fmtInt(d.chunk_start_us) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.fs_hz !== null && d.fs_hz !== undefined ? utils.fmtInt(d.fs_hz) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 tabular-nums text-gray-900 dark:text-gray-100', text: d.sample_count !== null && d.sample_count !== undefined ? utils.fmtInt(d.sample_count) : '-' }));
      $tr.append($('<td/>', { class: 'px-4 py-3 whitespace-nowrap text-gray-500 dark:text-gray-400 text-xs', text: d.created_at || '-' }));
      $body.append($tr);
    });
  }

  function loadRs485() {
    var params = utils.buildRangeParams($('#rs485Start').val(), $('#rs485End').val());
    params.limit = 200;
    return api.dbRs485(params).done(function (resp) {
      renderRs485(resp.items || []);
    }).fail(function () {
      renderRs485([]);
    });
  }

  function loadAdxl() {
    var params = utils.buildRangeParams($('#adxlStart').val(), $('#adxlEnd').val());
    params.limit = 200;
    return api.dbAdxl(params).done(function (resp) {
      renderAdxl(resp.items || []);
    }).fail(function () {
      renderAdxl([]);
    });
  }

  function activeTab() {
    return $('#tab-adxl').attr('aria-selected') === 'true' ? 'adxl' : 'rs485';
  }

  function setTab(tab) {
    var isAdxl = tab === 'adxl';
    $('#tab-rs485').attr('aria-selected', isAdxl ? 'false' : 'true');
    $('#tab-adxl').attr('aria-selected', isAdxl ? 'true' : 'false');
    $('#panel-rs485').toggleClass('hidden', isAdxl);
    $('#panel-adxl').toggleClass('hidden', !isAdxl);
  }

  window.WebDashboard.database = {
    init: function () {
      if (!$('#btnDbRefresh').length) return;
      $('#tab-rs485').on('click', function () {
        setTab('rs485');
        loadRs485();
      });
      $('#tab-adxl').on('click', function () {
        setTab('adxl');
        loadAdxl();
      });
      $('#btnRs485Apply').on('click', function () { loadRs485(); });
      $('#btnAdxlApply').on('click', function () { loadAdxl(); });
      $('#btnDbRefresh').on('click', function () {
        return activeTab() === 'adxl' ? loadAdxl() : loadRs485();
      });

      $('#btnRs485Csv').on('click', function () {
        window.location.href = api.exportUrl('rs485', 'csv', $('#rs485Start').val(), $('#rs485End').val());
      });
      $('#btnRs485Xlsx').on('click', function () {
        window.location.href = api.exportUrl('rs485', 'xlsx', $('#rs485Start').val(), $('#rs485End').val());
      });
      $('#btnAdxlCsv').on('click', function () {
        window.location.href = api.exportUrl('adxl', 'csv', $('#adxlStart').val(), $('#adxlEnd').val());
      });
      $('#btnAdxlXlsx').on('click', function () {
        window.location.href = api.exportUrl('adxl', 'xlsx', $('#adxlStart').val(), $('#adxlEnd').val());
      });

      // Default tab
      setTab(activeTab());
      if (activeTab() === 'adxl') loadAdxl();
      else loadRs485();
    }
  };
})(window, jQuery);
