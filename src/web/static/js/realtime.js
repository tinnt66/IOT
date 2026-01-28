/* global Chart, jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};
  var utils = window.WebDashboard.utils;

  var MAX_ENV_SAMPLES = 50;
  var MAX_VIB_SAMPLES = 1500;
  var VIB_CHART_MIN_UPDATE_MS = 100;

  var envHistory = [];
  var adxlHistory = [];
  var lastVibrationUpdateMs = 0;

  var chartTempHum = null;
  var chartWindSpeed = null;
  var chartZ1 = null;
  var chartZ2 = null;
  var chartZ3 = null;

  function isDark() {
    return document.documentElement.classList.contains('dark');
  }

  function chartTheme() {
    if (isDark()) {
      return {
        tick: '#9ca3af',
        grid: '#374151',
        legend: '#e5e7eb'
      };
    }
    return {
      tick: '#6b7280',
      grid: '#e5e7eb',
      legend: '#111827'
    };
  }

  function hasRealtimeDom() {
    return $('#legacy-realtime').length || $('#temp-value').length || $('#tempValue').length;
  }

  function extractTimeLabel(ts) {
    if (!ts) return utils.nowLocalTime();
    var d = new Date(ts);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    return utils.nowLocalTime();
  }

  function setLastUpdate(ts) {
    var label = extractTimeLabel(ts);
    $('#lastUpdateText').text(label);
    $('#last-update').text(label);
  }

  function trimHistory(arr, maxLen) {
    var extra = arr.length - maxLen;
    if (extra > 0) arr.splice(0, extra);
  }

  function pushEnvSample(payload) {
    var sample = (payload && payload.data) ? payload.data : {};
    envHistory.push({
      label: extractTimeLabel(payload ? payload.timestamp : null),
      temp: sample.temp_c,
      hum: sample.hum_pct,
      wind: sample.wind_spd_ms
    });
    trimHistory(envHistory, MAX_ENV_SAMPLES);
  }

  function updateEnvCharts() {
    if (!envHistory.length) return;

    var labels = $.map(envHistory, function (d) { return d.label; });

    if (chartTempHum) {
      chartTempHum.data.labels = labels;
      chartTempHum.data.datasets[0].data = $.map(envHistory, function (d) { return d.temp; });
      chartTempHum.data.datasets[1].data = $.map(envHistory, function (d) { return d.hum; });
      chartTempHum.update('none');
    }

    if (chartWindSpeed) {
      chartWindSpeed.data.labels = labels;
      chartWindSpeed.data.datasets[0].data = $.map(envHistory, function (d) { return d.wind; });
      chartWindSpeed.update('none');
    }
  }

  function createRawWaveformOptions(color, title) {
    var theme = chartTheme();
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      parsing: false,
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
      plugins: {
        legend: { display: false },
        title: { display: false, text: title },
        tooltip: { enabled: false }
      },
      scales: {
        x: {
          type: 'linear',
          display: true,
          title: { display: false, text: 'Sample index', color: theme.tick },
          ticks: { color: theme.tick, maxRotation: 0 },
          grid: { color: theme.grid }
        },
        y: {
          display: true,
          title: { display: false, text: 'Counts (Raw)', color: theme.tick },
          ticks: { color: theme.tick },
          grid: { color: theme.grid },
          min: -2048,
          max: 2048
        }
      },
      elements: { point: { radius: 0 }, line: { borderWidth: 1, tension: 0 } }
    };
  }

  function destroyCharts() {
    if (chartTempHum) { chartTempHum.destroy(); chartTempHum = null; }
    if (chartWindSpeed) { chartWindSpeed.destroy(); chartWindSpeed = null; }
    if (chartZ1) { chartZ1.destroy(); chartZ1 = null; }
    if (chartZ2) { chartZ2.destroy(); chartZ2 = null; }
    if (chartZ3) { chartZ3.destroy(); chartZ3 = null; }
  }

  function initCharts() {
    if (typeof Chart === 'undefined') return;

    var tempHumCanvas = $('#chart-temp-hum')[0];
    var windCanvas = $('#chart-wind-speed')[0];
    var z1Canvas = $('#chart-z1')[0];
    var z2Canvas = $('#chart-z2')[0];
    var z3Canvas = $('#chart-z3')[0];

    var theme = chartTheme();

    if (tempHumCanvas) {
      chartTempHum = new Chart(tempHumCanvas, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            { label: 'Temp', data: [], borderColor: '#059669', backgroundColor: 'rgba(5,150,105,0.10)', tension: 0.4, yAxisID: 'y-temp' },
            { label: 'Hum', data: [], borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.10)', tension: 0.4, yAxisID: 'y-hum' }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          scales: {
            'y-temp': { type: 'linear', position: 'left', min: 0, max: 100, ticks: { color: theme.tick }, grid: { color: theme.grid } },
            'y-hum': { type: 'linear', position: 'right', min: 0, max: 100, ticks: { color: theme.tick }, grid: { drawOnChartArea: false } },
            x: { ticks: { color: theme.tick, maxRotation: 0 }, grid: { color: theme.grid } }
          },
          plugins: { legend: { display: true, labels: { color: theme.legend } } }
        }
      });
    }

    if (windCanvas) {
      chartWindSpeed = new Chart(windCanvas, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Wind', data: [], borderColor: '#d97706', backgroundColor: 'rgba(217,119,6,0.10)', tension: 0.4, fill: true }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          scales: {
            y: { beginAtZero: true, ticks: { color: theme.tick }, grid: { color: theme.grid } },
            x: { ticks: { color: theme.tick, maxRotation: 0 }, grid: { color: theme.grid } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    if (z1Canvas) {
      chartZ1 = new Chart(z1Canvas, {
        type: 'line',
        data: { datasets: [{ data: [], borderColor: '#ef4444', borderWidth: 1 }] },
        options: createRawWaveformOptions('#ef4444', 'Z1 Raw Signal')
      });
    }
    if (z2Canvas) {
      chartZ2 = new Chart(z2Canvas, {
        type: 'line',
        data: { datasets: [{ data: [], borderColor: '#14b8a6', borderWidth: 1 }] },
        options: createRawWaveformOptions('#14b8a6', 'Z2 Raw Signal')
      });
    }
    if (z3Canvas) {
      chartZ3 = new Chart(z3Canvas, {
        type: 'line',
        data: { datasets: [{ data: [], borderColor: '#a855f7', borderWidth: 1 }] },
        options: createRawWaveformOptions('#a855f7', 'Z3 Raw Signal')
      });
    }
  }

  function rebuildCharts() {
    if (!$('#chart-temp-hum').length) return;
    destroyCharts();
    initCharts();
    updateEnvCharts();
    updateVibrationCharts();
  }

  function maybeUpdateVibrationCharts() {
    var $row = $('#vibration-charts-row');
    if (!$row.length || $row.is(':hidden')) return;

    var nowMs = Date.now();
    if (nowMs - lastVibrationUpdateMs < VIB_CHART_MIN_UPDATE_MS) return;
    lastVibrationUpdateMs = nowMs;

    updateVibrationCharts();
  }

  function updateVibrationCharts() {
    if (!adxlHistory.length) return;

    var z1Data = new Array(adxlHistory.length);
    var z2Data = new Array(adxlHistory.length);
    var z3Data = new Array(adxlHistory.length);

    for (var i = 0; i < adxlHistory.length; i++) {
      var row = adxlHistory[i];
      z1Data[i] = { x: i, y: row.z1 };
      z2Data[i] = { x: i, y: row.z2 };
      z3Data[i] = { x: i, y: row.z3 };
    }

    if (chartZ1) {
      chartZ1.data.datasets[0].data = z1Data;
      chartZ1.update('none');
    }
    if (chartZ2) {
      chartZ2.data.datasets[0].data = z2Data;
      chartZ2.update('none');
    }
    if (chartZ3) {
      chartZ3.data.datasets[0].data = z3Data;
      chartZ3.update('none');
    }
  }

  function setLegacyConnection(state) {
    var $dot = $('#status-indicator');
    var $txt = $('#status-text');

    $dot.removeClass('bg-gray-300 bg-emerald-500 bg-red-500');
    $txt.removeClass(
      'text-notion-muted text-emerald-700 text-red-700 ' +
      'dark:text-gray-400 dark:text-emerald-300 dark:text-red-300'
    );

    if (state === true) {
      $dot.addClass('bg-emerald-500');
      $txt.addClass('text-emerald-700 dark:text-emerald-300').text('Connected');
      return;
    }
    if (state === false) {
      $dot.addClass('bg-red-500');
      $txt.addClass('text-red-700 dark:text-red-300').text('Disconnected');
      return;
    }

    $dot.addClass('bg-gray-300');
    $txt.addClass('text-notion-muted dark:text-gray-400').text('Connecting...');
  }

  function updateStats(data) {
    $('#rs485-count').text(utils.fmtInt(data.rs485_count));
    $('#adxl-count').text(utils.fmtInt(data.adxl_count));
    $('#rs485Count').text(utils.fmtInt(data.rs485_count));
    $('#adxlCount').text(utils.fmtInt(data.adxl_count));
    setLastUpdate(data.timestamp);
  }

  function updateRs485(payload) {
    var sample = (payload && payload.data) ? payload.data : {};

    var temp = utils.fmtFixed(sample.temp_c, 1);
    var hum = utils.fmtFixed(sample.hum_pct, 1);
    var windTxt = sample.wind_dir_txt || '-';
    var windDeg = (sample.wind_dir_deg !== undefined && sample.wind_dir_deg !== null) ? (String(sample.wind_dir_deg) + '°') : '-';
    var windSpd = utils.fmtFixed(sample.wind_spd_ms, 1);

    $('#temp-value').text(temp);
    $('#tempValue').text(temp);
    $('#humidity-value').text(hum);
    $('#humValue').text(hum);
    $('#wind-dir-value').text(windTxt);
    $('#windDirTxt').text(windTxt);
    $('#wind-dir-deg').text(windDeg);
    $('#windDirDeg').text(windDeg);
    $('#wind-speed-value').text(windSpd);
    $('#windSpd').text(windSpd);

    pushEnvSample(payload);
    updateEnvCharts();
    setLastUpdate(payload ? payload.timestamp : null);
  }

  function updateAdxl(payload) {
    var z1 = payload && payload.adxl1 !== undefined && payload.adxl1 !== null ? utils.fmtInt(payload.adxl1) : '-';
    var z2 = payload && payload.adxl2 !== undefined && payload.adxl2 !== null ? utils.fmtInt(payload.adxl2) : '-';
    var z3 = payload && payload.adxl3 !== undefined && payload.adxl3 !== null ? utils.fmtInt(payload.adxl3) : '-';

    $('#adxl1-value').text(z1);
    $('#adxl2-value').text(z2);
    $('#adxl3-value').text(z3);
    $('#adxlZ1').text(z1);
    $('#adxlZ2').text(z2);
    $('#adxlZ3').text(z3);

    var chunk = payload && payload.chunk_start_us !== undefined && payload.chunk_start_us !== null ? utils.fmtInt(payload.chunk_start_us) : '-';
    var count = payload && payload.sample_count !== undefined && payload.sample_count !== null ? utils.fmtInt(payload.sample_count) : '-';
    var fs = payload && payload.fs_hz !== undefined && payload.fs_hz !== null ? (utils.fmtInt(payload.fs_hz) + ' Hz') : '-';

    $('#adxl-chunk').text(chunk);
    $('#adxl-samples').text(count);
    $('#adxl-freq').text(fs);
    $('#adxlChunkStart').text(chunk);
    $('#adxlSampleCount').text(count);
    $('#adxlFs').text(payload && payload.fs_hz !== undefined && payload.fs_hz !== null ? utils.fmtInt(payload.fs_hz) : '-');

    var samples = payload && Array.isArray(payload.samples) ? payload.samples : null;
    if (samples) {
      for (var i = 0; i < samples.length; i++) {
        var row = samples[i];
        if (!Array.isArray(row) || row.length < 3) continue;
        var r1 = Number(row[0]);
        var r2 = Number(row[1]);
        var r3 = Number(row[2]);
        if (!Number.isFinite(r1) || !Number.isFinite(r2) || !Number.isFinite(r3)) continue;
        adxlHistory.push({ z1: r1, z2: r2, z3: r3 });
      }
      trimHistory(adxlHistory, MAX_VIB_SAMPLES);
    }

    setLastUpdate(payload ? payload.timestamp : null);
    maybeUpdateVibrationCharts();
  }

  function setupUi() {
    $('#btn-toggle-vibration').on('click', function () {
      var $row = $('#vibration-charts-row');
      if (!$row.length) return;

      var willShow = $row.hasClass('hidden');
      $row.toggleClass('hidden', !willShow);
      $('#btn-toggle-vibration').text(willShow ? 'Hide Vibration Charts' : 'Show Vibration Charts');

      if (willShow) {
        setTimeout(function () {
          if (chartZ1) chartZ1.resize();
          if (chartZ2) chartZ2.resize();
          if (chartZ3) chartZ3.resize();
          updateVibrationCharts();
        }, 50);
      }
    });
  }

  window.WebDashboard.realtime = {
    init: function () {
      if (!hasRealtimeDom()) return;

      initCharts();
      setupUi();

      $(document).on('ws:connect', function () { setLegacyConnection(true); });
      $(document).on('ws:disconnect', function () { setLegacyConnection(false); });
      $(document).on('ws:rs485', function (_e, payload) { updateRs485(payload); });
      $(document).on('ws:adxl', function (_e, payload) { updateAdxl(payload); });
      $(document).on('ws:stats', function (_e, data) { updateStats(data || {}); });

      // Default state while connecting.
      setLegacyConnection(null);
      setLastUpdate(null);

      $(document).on('theme:changed', function () {
        rebuildCharts();
      });
    }
  };
})(window, jQuery);
