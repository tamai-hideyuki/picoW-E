DASHBOARD = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Altitude Meter</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee;
    padding: 16px; padding: max(16px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right)) max(16px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left)); }
  h1 { font-size: 1.4em; margin-bottom: 12px; color: #e94560; }

  .alt-display { background: #16213e; border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 16px; }
  .alt-value { font-size: 3em; font-weight: bold; color: #4fc3f7; }
  .alt-unit { font-size: 1em; color: #aaa; }
  .alt-label { font-size: 0.8em; color: #888; margin-top: 4px; }

  .cards { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
  .card { background: #16213e; border-radius: 10px; padding: 14px 10px; flex: 1; min-width: 80px; text-align: center; }
  .card .value { font-size: 1.6em; font-weight: bold; }
  .card.temp .value { color: #ff6b6b; }
  .card.humi .value { color: #4ecdc4; }
  .card.pres .value { color: #ffe66d; }
  .card .label { font-size: 0.7em; color: #aaa; margin-top: 4px; }

  .pressure-setting { background: #16213e; border-radius: 10px; padding: 14px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .pressure-setting label { font-size: 0.85em; color: #aaa; }
  .pressure-setting input { background: #0f3460; color: #eee; border: 1px solid #444;
    border-radius: 6px; padding: 8px 10px; width: 120px; font-size: 1em; }
  .pressure-setting button { background: #e94560; color: #fff; border: none; padding: 8px 16px;
    border-radius: 6px; cursor: pointer; font-size: 0.9em; position: relative; z-index: 10; }
  .pressure-setting button.jma { background: #0f3460; }
  .pressure-setting .jma-status { font-size: 0.75em; color: #4ecdc4; width: 100%; }

  .calibration { background: #16213e; border-radius: 10px; padding: 14px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .calibration label { font-size: 0.85em; color: #aaa; }
  .calibration input { background: #0f3460; color: #eee; border: 1px solid #444;
    border-radius: 6px; padding: 8px 10px; width: 100px; font-size: 1em; }
  .calibration button { background: #4ecdc4; color: #1a1a2e; border: none; padding: 8px 16px;
    border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: bold;
    position: relative; z-index: 10; }
  .calibration .cal-status { font-size: 0.75em; color: #ffe66d; width: 100%; }
  .calibration .offset-display { font-size: 0.8em; color: #aaa; }

  .chart-box { background: #16213e; border-radius: 10px; padding: 12px; margin-bottom: 12px; }
  .info { font-size: 0.75em; color: #666; margin-top: 8px; }

  @media (max-width: 480px) {
    .alt-value { font-size: 2.4em; }
    .card .value { font-size: 1.3em; }
    .chart-box { padding: 8px; }
  }
</style>
</head>
<body>
<h1>Altitude Meter - Pico W</h1>

<div class="alt-display">
  <div><span class="alt-value" id="cur-alt">--</span> <span class="alt-unit">m</span></div>
  <div class="alt-label">Estimated Altitude</div>
</div>

<div class="cards">
  <div class="card temp"><div class="value" id="cur-temp">--</div><div class="label">Temp (C)</div></div>
  <div class="card humi"><div class="value" id="cur-humi">--</div><div class="label">Humidity (%)</div></div>
  <div class="card pres"><div class="value" id="cur-pres">--</div><div class="label">Pressure (hPa)</div></div>
</div>

<div class="pressure-setting">
  <label>Sea Level Pressure (hPa):</label>
  <input type="number" id="slp-input" step="0.01" value="1013.25">
  <button onclick="setSeaLevelPressure()">Set</button>
  <button class="jma" onclick="fetchJmaSeaLevelPressure()">JMA Auto</button>
  <div class="jma-status" id="jma-status"></div>
</div>

<div class="calibration">
  <label>Reference Alt (m):</label>
  <input type="number" id="ref-alt-input" step="0.1" value="73.0">
  <button onclick="runCalibration()">Calibrate</button>
  <span class="offset-display">Offset: <span id="cur-offset">0.0</span> hPa</span>
  <div class="cal-status" id="cal-status"></div>
</div>

<div class="chart-box"><canvas id="altChart" height="140"></canvas></div>
<div class="info" id="info"></div>

<script>
const altChart = new Chart(document.getElementById('altChart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      data: [],
      borderColor: '#4fc3f7',
      backgroundColor: 'rgba(79,195,247,0.1)',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: true
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#aaa', maxTicksLimit: 10 }, grid: { color: '#333' } },
      y: { ticks: { color: '#aaa' }, grid: { color: '#333' },
           title: { display: true, text: 'Altitude (m)', color: '#aaa' } }
    }
  }
});

function fetchCurrent() {
  fetch('/api/current').then(function(r) { return r.json(); }).then(function(d) {
    document.getElementById('cur-alt').textContent = d.alt.toFixed(1);
    document.getElementById('cur-temp').textContent = d.temp.toFixed(1);
    document.getElementById('cur-humi').textContent = d.humi.toFixed(1);
    document.getElementById('cur-pres').textContent = d.pres.toFixed(1);
    document.getElementById('slp-input').value = d.sea_level_pressure;
    document.getElementById('cur-offset').textContent = d.pressure_offset;
    document.getElementById('ref-alt-input').value = d.reference_altitude;
  }).catch(function() {});
}

function loadHistory() {
  fetch('/api/history').then(function(r) { return r.json(); }).then(function(d) {
    var records = d.data;
    var labels = records.map(function(r, i) {
      var elapsed = (records.length - 1 - i) * 2;
      return elapsed >= 60 ? Math.floor(elapsed / 60) + 'm' : elapsed + 's';
    });
    altChart.data.labels = labels;
    altChart.data.datasets[0].data = records.map(function(r) { return r[4]; });
    altChart.update();
    document.getElementById('info').textContent = 'Buffer: ' + records.length + ' records';
  }).catch(function() {});
}

function setSeaLevelPressure() {
  var val = document.getElementById('slp-input').value;
  fetch('/api/set_pressure?value=' + val).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      fetchCurrent();
      loadHistory();
    }
  }).catch(function() {});
}

function fetchJmaSeaLevelPressure() {
  var status = document.getElementById('jma-status');
  status.textContent = 'Fetching from JMA...';

  fetch('https://www.jma.go.jp/bosai/amedas/data/latest_time.txt')
    .then(function(r) { return r.text(); })
    .then(function(text) {
      var lt = new Date(text.trim());
      var y = lt.getFullYear();
      var m = String(lt.getMonth() + 1).padStart(2, '0');
      var d = String(lt.getDate()).padStart(2, '0');
      var h = String(Math.floor(lt.getHours() / 3) * 3).padStart(2, '0');
      var url = 'https://www.jma.go.jp/bosai/amedas/data/point/46106/'
        + y + m + d + '_' + h + '.json';
      return fetch(url);
    })
    .then(function(r) {
      if (!r.ok) {
        status.textContent = 'JMA: data not available (HTTP ' + r.status + ')';
        return;
      }
      r.json().then(function(data) {
        var keys = Object.keys(data).sort();
        var lastKey = keys[keys.length - 1];
        var latest = data[lastKey];
        if (latest && latest.normalPressure) {
          var slp = latest.normalPressure[0];
          document.getElementById('slp-input').value = slp;
          setSeaLevelPressure();
          var timeStr = lastKey.slice(8,10) + ':' + lastKey.slice(10,12);
          status.textContent = 'JMA Yokohama ' + timeStr + ' JST: ' + slp + ' hPa';
        } else {
          status.textContent = 'No pressure data in response';
        }
      });
    })
    .catch(function(e) {
      status.textContent = 'JMA fetch failed: ' + e.message;
    });
}

function runCalibration() {
  var calStatus = document.getElementById('cal-status');
  var refAlt = document.getElementById('ref-alt-input').value;
  calStatus.textContent = 'Calibrating...';
  fetch('/api/set_ref_alt?value=' + refAlt).then(function(r) { return r.json(); }).then(function() {
    return fetch('/api/calibrate');
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      calStatus.textContent = 'Calibrated: ' + d.before + 'm -> ' + d.after + 'm (offset: ' + d.pressure_offset + ' hPa)';
      document.getElementById('cur-offset').textContent = d.pressure_offset;
      fetchCurrent();
      loadHistory();
    }
  }).catch(function(e) {
    calStatus.textContent = 'Calibration failed: ' + e.message;
  });
}

fetchCurrent();
loadHistory();
fetchJmaSeaLevelPressure();
setInterval(fetchCurrent, 2000);
setInterval(loadHistory, 10000);
setInterval(fetchJmaSeaLevelPressure, 600000);
</script>
</body>
</html>"""
