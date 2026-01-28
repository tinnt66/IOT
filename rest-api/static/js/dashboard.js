/**
 * Dashboard JavaScript - Optimized for High Frequency Raw Data
 * Notes:
 * - ADXL batch format: samples[i][0]=Z1, samples[i][1]=Z2, samples[i][2]=Z3
 * - Fixed Y axis: -2048..2048 for vibration charts
 */

const socket = io({ transports: ['websocket', 'polling'] });

// Global state
const MAX_SAMPLES = 1500;
const MAX_ENV_SAMPLES = 50;
let adxlDataHistory = [];
let envHistory = [];
let lastVibrationUpdate = 0;

// Chart instances
let chartTempHum = null;
let chartWindSpeed = null;
let chartZ1 = null;
let chartZ2 = null;
let chartZ3 = null;

// DOM Elements - Status
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const rs485Count = document.getElementById('rs485-count');
const lastUpdate = document.getElementById('last-update');

// ADXL Value Elements
const adxl1Value = document.getElementById('adxl1-value');
const adxl2Value = document.getElementById('adxl2-value');
const adxl3Value = document.getElementById('adxl3-value');

// RS485 Elements
const tempValue = document.getElementById('temp-value');
const humidityValue = document.getElementById('humidity-value');
const windDirValue = document.getElementById('wind-dir-value');
const windDirDeg = document.getElementById('wind-dir-deg');
const windSpeedValue = document.getElementById('wind-speed-value');

// ADXL Info Elements
const adxlChunk = document.getElementById('adxl-chunk');
const adxlSamples = document.getElementById('adxl-samples');
const adxlFreq = document.getElementById('adxl-freq');

// Charts / UI
const vibrationRow = document.getElementById('vibration-charts-row');
const btnToggleVibration = document.getElementById('btn-toggle-vibration');

// Nav / Views
const navRealtime = document.getElementById('nav-realtime');
const navDatabase = document.getElementById('nav-database');
const viewRealtime = document.getElementById('view-realtime');
const viewDatabase = document.getElementById('view-database');

// Database UI
const btnDbRefresh = document.getElementById('btn-db-refresh');
const dbTabRs485 = document.getElementById('db-tab-rs485');
const dbTabAdxl = document.getElementById('db-tab-adxl');
const dbPanelRs485 = document.getElementById('db-panel-rs485');
const dbPanelAdxl = document.getElementById('db-panel-adxl');
const rs485Start = document.getElementById('rs485-start');
const rs485End = document.getElementById('rs485-end');
const adxlStart = document.getElementById('adxl-start');
const adxlEnd = document.getElementById('adxl-end');
const btnRs485Apply = document.getElementById('btn-rs485-apply');
const btnAdxlApply = document.getElementById('btn-adxl-apply');
const btnRs485Csv = document.getElementById('btn-rs485-csv');
const btnRs485Xlsx = document.getElementById('btn-rs485-xlsx');
const btnAdxlCsv = document.getElementById('btn-adxl-csv');
const btnAdxlXlsx = document.getElementById('btn-adxl-xlsx');
const rs485TableBody = document.getElementById('rs485-table-body');
const adxlTableBody = document.getElementById('adxl-table-body');

initializeCharts();
setupEventListeners();
updateLastUpdate();

// Connection Events
socket.on('connect', () => {
  statusIndicator.classList.add('connected');
  statusText.textContent = 'Connected';
  socket.emit('request_stats');
});

socket.on('disconnect', () => {
  statusIndicator.classList.remove('connected');
  statusText.textContent = 'Disconnected';
});

socket.on('stats_update', (data) => {
  rs485Count.textContent = data.rs485_count?.toLocaleString?.() ?? '-';
  updateLastUpdate();
});

socket.on('rs485_data', (payload) => {
  const sample = payload?.data ?? {};

  if (sample.temp_c !== null && sample.temp_c !== undefined) {
    tempValue.textContent = Number(sample.temp_c).toFixed(1);
  }
  if (sample.hum_pct !== null && sample.hum_pct !== undefined) {
    humidityValue.textContent = Number(sample.hum_pct).toFixed(1);
  }
  if (sample.wind_dir_txt) windDirValue.textContent = sample.wind_dir_txt;
  if (sample.wind_dir_deg !== null && sample.wind_dir_deg !== undefined) {
    windDirDeg.textContent = `${sample.wind_dir_deg}°`;
  }
  if (sample.wind_spd_ms !== null && sample.wind_spd_ms !== undefined) {
    windSpeedValue.textContent = Number(sample.wind_spd_ms).toFixed(1);
  }

  pushEnvSample(payload);
  updateEnvCharts();
  updateLastUpdate();
});

socket.on('adxl_data', (payload) => {
  // Cards (latest values)
  if (payload?.adxl1 !== null && payload?.adxl1 !== undefined) adxl1Value.textContent = payload.adxl1.toLocaleString();
  if (payload?.adxl2 !== null && payload?.adxl2 !== undefined) adxl2Value.textContent = payload.adxl2.toLocaleString();
  if (payload?.adxl3 !== null && payload?.adxl3 !== undefined) adxl3Value.textContent = payload.adxl3.toLocaleString();

  // Batch info
  if (payload?.chunk_start_us !== null && payload?.chunk_start_us !== undefined) adxlChunk.textContent = payload.chunk_start_us.toLocaleString();
  if (payload?.sample_count !== null && payload?.sample_count !== undefined) adxlSamples.textContent = payload.sample_count.toLocaleString();
  if (payload?.fs_hz !== null && payload?.fs_hz !== undefined) adxlFreq.textContent = `${payload.fs_hz} Hz`;

  // Samples history (batch format)
  const samples = Array.isArray(payload?.samples) ? payload.samples : null;
  if (samples) {
    for (let i = 0; i < samples.length; i++) {
      const row = samples[i];
      if (!Array.isArray(row) || row.length < 3) continue;
      const z1 = Number(row[0]);
      const z2 = Number(row[1]);
      const z3 = Number(row[2]);
      if (!Number.isFinite(z1) || !Number.isFinite(z2) || !Number.isFinite(z3)) continue;
      adxlDataHistory.push({ z1, z2, z3 });
    }
    trimHistory(adxlDataHistory, MAX_SAMPLES);
  }

  updateLastUpdate();
  maybeUpdateVibrationCharts();
});

socket.on('error', (data) => {
  void data;
});

function setupEventListeners() {
  if (navRealtime && navDatabase && viewRealtime && viewDatabase) {
    navRealtime.addEventListener('click', () => showView('realtime'));
    navDatabase.addEventListener('click', () => showView('database'));
  }

  if (btnToggleVibration && vibrationRow) {
    btnToggleVibration.addEventListener('click', () => {
      const isCurrentlyHidden = vibrationRow.style.display === 'none' || vibrationRow.style.display === '';
      vibrationRow.style.display = isCurrentlyHidden ? 'flex' : 'none';
      btnToggleVibration.textContent = isCurrentlyHidden ? 'Hide Vibration Charts' : 'Show Vibration Charts';

      if (isCurrentlyHidden) {
        setTimeout(() => {
          chartZ1?.resize();
          chartZ2?.resize();
          chartZ3?.resize();
          updateVibrationCharts();
        }, 50);
      }
    });
  }

  if (dbTabRs485 && dbTabAdxl) {
    dbTabRs485.addEventListener('click', () => showDbTab('rs485'));
    dbTabAdxl.addEventListener('click', () => showDbTab('adxl'));
  }

  btnDbRefresh?.addEventListener('click', () => {
    if (dbPanelAdxl && dbPanelAdxl.style.display !== 'none') {
      void loadAdxlTable();
    } else {
      void loadRs485Table();
    }
  });

  btnRs485Apply?.addEventListener('click', () => void loadRs485Table());
  btnAdxlApply?.addEventListener('click', () => void loadAdxlTable());

  btnRs485Csv?.addEventListener('click', () => {
    window.location.href = `/api/export/rs485.csv${buildRangeQuery(rs485Start, rs485End)}`;
  });
  btnRs485Xlsx?.addEventListener('click', () => {
    window.location.href = `/api/export/rs485.xlsx${buildRangeQuery(rs485Start, rs485End)}`;
  });
  btnAdxlCsv?.addEventListener('click', () => {
    window.location.href = `/api/export/adxl.csv${buildRangeQuery(adxlStart, adxlEnd)}`;
  });
  btnAdxlXlsx?.addEventListener('click', () => {
    window.location.href = `/api/export/adxl.xlsx${buildRangeQuery(adxlStart, adxlEnd)}`;
  });
}

function updateLastUpdate() {
  const now = new Date();
  lastUpdate.textContent = now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function showView(view) {
  const isRealtime = view === 'realtime';
  if (!viewRealtime || !viewDatabase || !navRealtime || !navDatabase) return;

  viewRealtime.style.display = isRealtime ? '' : 'none';
  viewDatabase.style.display = isRealtime ? 'none' : '';
  navRealtime.classList.toggle('active', isRealtime);
  navDatabase.classList.toggle('active', !isRealtime);

  if (isRealtime) {
    setTimeout(() => {
      chartTempHum?.resize();
      chartWindSpeed?.resize();
      if (vibrationRow?.style.display !== 'none') {
        chartZ1?.resize();
        chartZ2?.resize();
        chartZ3?.resize();
        updateVibrationCharts();
      }
    }, 50);
  } else {
    const wantsAdxl = dbPanelAdxl && dbPanelAdxl.style.display !== 'none';
    showDbTab(wantsAdxl ? 'adxl' : 'rs485');
    void (wantsAdxl ? loadAdxlTable() : loadRs485Table());
  }
}

function showDbTab(tab) {
  if (!dbTabRs485 || !dbTabAdxl || !dbPanelRs485 || !dbPanelAdxl) return;
  const isRs = tab === 'rs485';
  dbTabRs485.classList.toggle('active', isRs);
  dbTabAdxl.classList.toggle('active', !isRs);
  dbPanelRs485.style.display = isRs ? '' : 'none';
  dbPanelAdxl.style.display = isRs ? 'none' : '';
}

function normalizeDatetimeLocal(value) {
  if (!value) return '';
  // datetime-local usually returns YYYY-MM-DDTHH:mm (no seconds)
  return value.length === 16 ? `${value}:00` : value;
}

function buildRangeQuery(startEl, endEl) {
  const start = normalizeDatetimeLocal(startEl?.value);
  const end = normalizeDatetimeLocal(endEl?.value);
  const params = new URLSearchParams();
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

function setTableLoading(tbody, colspan) {
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="${colspan}" class="muted">Loading...</td></tr>`;
}

function setTableEmpty(tbody, colspan, message) {
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="${colspan}" class="muted">${message}</td></tr>`;
}

async function loadRs485Table() {
  setTableLoading(rs485TableBody, 7);
  try {
    const res = await fetch(`/api/db/rs485${buildRangeQuery(rs485Start, rs485End)}`);
    if (!res.ok) {
      setTableEmpty(rs485TableBody, 7, 'Failed to load data');
      return;
    }
    const json = await res.json();
    const items = Array.isArray(json?.items) ? json.items : [];
    if (!items.length) {
      setTableEmpty(rs485TableBody, 7, 'No data');
      return;
    }

    rs485TableBody.innerHTML = items.map((d) => {
      const windDir = (d.wind_dir_txt ?? '-') + (d.wind_dir_deg !== null && d.wind_dir_deg !== undefined ? ` (${d.wind_dir_deg}°)` : '');
      return `<tr>
        <td>${d.id ?? ''}</td>
        <td>${d.time_local ?? ''}</td>
        <td>${d.temp_c ?? ''}</td>
        <td>${d.hum_pct ?? ''}</td>
        <td>${windDir}</td>
        <td>${d.wind_spd_ms ?? ''}</td>
        <td>${d.created_at ?? ''}</td>
      </tr>`;
    }).join('');
  } catch {
    setTableEmpty(rs485TableBody, 7, 'Failed to load data');
  }
}

async function loadAdxlTable() {
  setTableLoading(adxlTableBody, 5);
  try {
    const res = await fetch(`/api/db/adxl${buildRangeQuery(adxlStart, adxlEnd)}`);
    if (!res.ok) {
      setTableEmpty(adxlTableBody, 5, 'Failed to load data');
      return;
    }
    const json = await res.json();
    const items = Array.isArray(json?.items) ? json.items : [];
    if (!items.length) {
      setTableEmpty(adxlTableBody, 5, 'No data');
      return;
    }

    adxlTableBody.innerHTML = items.map((d) => {
      return `<tr>
        <td>${d.id ?? ''}</td>
        <td>${d.chunk_start_us ?? ''}</td>
        <td>${d.fs_hz ?? ''}</td>
        <td>${d.sample_count ?? ''}</td>
        <td>${d.created_at ?? ''}</td>
      </tr>`;
    }).join('');
  } catch {
    setTableEmpty(adxlTableBody, 5, 'Failed to load data');
  }
}

function trimHistory(arr, maxLen) {
  const extra = arr.length - maxLen;
  if (extra > 0) arr.splice(0, extra);
}

function extractTimeLabel(ts) {
  if (!ts) {
    return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  const d = new Date(ts);
  if (!Number.isNaN(d.getTime())) {
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  const parts = String(ts).split(' ');
  return parts.length > 1 ? parts[1] : String(ts);
}

function pushEnvSample(payload) {
  const sample = payload?.data ?? {};
  envHistory.push({
    label: extractTimeLabel(payload?.timestamp),
    temp: sample.temp_c,
    hum: sample.hum_pct,
    wind: sample.wind_spd_ms
  });
  trimHistory(envHistory, MAX_ENV_SAMPLES);
}

function createRawWaveformOptions(color, title) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    interaction: { mode: 'nearest', axis: 'x', intersect: false },
    plugins: {
      legend: { display: false },
      title: { display: true, text: title, color: color, font: { size: 14 } },
      tooltip: { enabled: false }
    },
    scales: {
      x: {
        type: 'linear',
        display: true,
        title: { display: true, text: 'Sample index', color: '#888' },
        ticks: { color: '#bbbbbb', maxRotation: 0 },
        grid: { color: '#333333' }
      },
      y: {
        display: true,
        title: { display: true, text: 'Counts (Raw)', color: '#888' },
        ticks: { color: color },
        grid: { color: '#333333' },
        min: -2048,
        max: 2048
      }
    },
    elements: { point: { radius: 0 }, line: { borderWidth: 1, tension: 0 } }
  };
}

function initializeCharts() {
  const ctxTempHum = document.getElementById('chart-temp-hum');
  const ctxWindSpeed = document.getElementById('chart-wind-speed');

  if (ctxTempHum) {
    chartTempHum = new Chart(ctxTempHum, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          { label: 'Temp', data: [], borderColor: '#00cc66', backgroundColor: 'rgba(0,204,102,0.1)', tension: 0.4, yAxisID: 'y-temp' },
          { label: 'Hum', data: [], borderColor: '#4da6ff', backgroundColor: 'rgba(77,166,255,0.1)', tension: 0.4, yAxisID: 'y-hum' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          'y-temp': { type: 'linear', position: 'left', min: 0, max: 100, ticks: { color: '#00cc66' }, grid: { color: '#333333' } },
          'y-hum': { type: 'linear', position: 'right', min: 0, max: 100, ticks: { color: '#4da6ff' }, grid: { drawOnChartArea: false } },
          x: { ticks: { color: '#bbbbbb', maxRotation: 0 }, grid: { color: '#333333' } }
        },
        plugins: { legend: { display: true, labels: { color: '#bbbbbb' } } }
      }
    });
  }

  if (ctxWindSpeed) {
    chartWindSpeed = new Chart(ctxWindSpeed, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Wind', data: [], borderColor: '#ffcc00', backgroundColor: 'rgba(255,204,0,0.1)', tension: 0.4, fill: true }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          y: { beginAtZero: true, ticks: { color: '#ffcc00' }, grid: { color: '#333333' } },
          x: { ticks: { color: '#bbbbbb', maxRotation: 0 }, grid: { color: '#333333' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  const z1Canvas = document.getElementById('chart-z1');
  const z2Canvas = document.getElementById('chart-z2');
  const z3Canvas = document.getElementById('chart-z3');

  if (z1Canvas) {
    chartZ1 = new Chart(z1Canvas, {
      type: 'line',
      data: { datasets: [{ data: [], borderColor: '#ff6b6b', borderWidth: 1 }] },
      options: createRawWaveformOptions('#ff6b6b', 'Z1 Raw Signal')
    });
  }
  if (z2Canvas) {
    chartZ2 = new Chart(z2Canvas, {
      type: 'line',
      data: { datasets: [{ data: [], borderColor: '#4ecdc4', borderWidth: 1 }] },
      options: createRawWaveformOptions('#4ecdc4', 'Z2 Raw Signal')
    });
  }
  if (z3Canvas) {
    chartZ3 = new Chart(z3Canvas, {
      type: 'line',
      data: { datasets: [{ data: [], borderColor: '#95e1d3', borderWidth: 1 }] },
      options: createRawWaveformOptions('#95e1d3', 'Z3 Raw Signal')
    });
  }
}

function updateEnvCharts() {
  if (!envHistory.length) return;
  const labels = envHistory.map(d => d.label);

  if (chartTempHum) {
    chartTempHum.data.labels = labels;
    chartTempHum.data.datasets[0].data = envHistory.map(d => d.temp);
    chartTempHum.data.datasets[1].data = envHistory.map(d => d.hum);
    chartTempHum.update('none');
  }

  if (chartWindSpeed) {
    chartWindSpeed.data.labels = labels;
    chartWindSpeed.data.datasets[0].data = envHistory.map(d => d.wind);
    chartWindSpeed.update('none');
  }
}

function maybeUpdateVibrationCharts() {
  if (!vibrationRow || vibrationRow.style.display === 'none') return;
  const now = Date.now();
  if (now - lastVibrationUpdate < 100) return;
  lastVibrationUpdate = now;
  updateVibrationCharts();
}

function updateVibrationCharts() {
  if (!adxlDataHistory.length) return;

  const z1Data = new Array(adxlDataHistory.length);
  const z2Data = new Array(adxlDataHistory.length);
  const z3Data = new Array(adxlDataHistory.length);

  for (let i = 0; i < adxlDataHistory.length; i++) {
    const row = adxlDataHistory[i];
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

// Request stats every 10 seconds
setInterval(() => {
  if (socket.connected) socket.emit('request_stats');
}, 10000);

void 0;
