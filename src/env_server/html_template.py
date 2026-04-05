DASHBOARD = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Env Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 16px; }
  h1 { font-size: 1.4em; margin-bottom: 12px; color: #e94560; }
  .cards { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .card { background: #16213e; border-radius: 10px; padding: 16px; flex: 1; min-width: 120px; text-align: center; }
  .card .value { font-size: 2em; font-weight: bold; }
  .card.temp .value { color: #ff6b6b; }
  .card.humi .value { color: #4ecdc4; }
  .card.pres .value { color: #ffe66d; }
  .card .label { font-size: 0.8em; color: #aaa; margin-top: 4px; }
  .chart-box { background: #16213e; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
  .controls { margin-bottom: 12px; }
  .controls button { background: #e94560; color: #fff; border: none; padding: 8px 16px;
    border-radius: 6px; margin-right: 8px; cursor: pointer; font-size: 0.9em; }
  .controls button.active { background: #0f3460; }
  .info { font-size: 0.75em; color: #666; margin-top: 8px; }
</style>
</head>
<body>
<h1>Env Monitor - Pico W</h1>

<div class="cards">
  <div class="card temp"><div class="value" id="cur-temp">--</div><div class="label">Temperature (C)</div></div>
  <div class="card humi"><div class="value" id="cur-humi">--</div><div class="label">Humidity (%)</div></div>
  <div class="card pres"><div class="value" id="cur-pres">--</div><div class="label">Pressure (hPa)</div></div>
</div>

<div class="controls">
  <button onclick="loadHistory('10m')" id="btn-10m">10min</button>
  <button onclick="loadHistory('1h')" id="btn-1h">1h</button>
  <button onclick="loadHistory('24h')" id="btn-24h" class="active">24h</button>
</div>

<div class="chart-box"><canvas id="tempChart" height="120"></canvas></div>
<div class="chart-box"><canvas id="humiChart" height="120"></canvas></div>
<div class="chart-box"><canvas id="presChart" height="120"></canvas></div>
<div class="info" id="info"></div>

<script>
const chartOpts = (label, color) => ({
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#aaa', maxTicksLimit: 12 }, grid: { color: '#333' } },
    y: { ticks: { color: '#aaa' }, grid: { color: '#333' },
         title: { display: true, text: label, color: '#aaa' } }
  }
});

const tempChart = new Chart(document.getElementById('tempChart'), {
  type: 'line', data: { labels: [], datasets: [{ data: [], borderColor: '#ff6b6b', borderWidth: 2, pointRadius: 0, tension: 0.3 }] },
  options: chartOpts('Temperature (C)', '#ff6b6b')
});
const humiChart = new Chart(document.getElementById('humiChart'), {
  type: 'line', data: { labels: [], datasets: [{ data: [], borderColor: '#4ecdc4', borderWidth: 2, pointRadius: 0, tension: 0.3 }] },
  options: chartOpts('Humidity (%)', '#4ecdc4')
});
const presChart = new Chart(document.getElementById('presChart'), {
  type: 'line', data: { labels: [], datasets: [{ data: [], borderColor: '#ffe66d', borderWidth: 2, pointRadius: 0, tension: 0.3 }] },
  options: chartOpts('Pressure (hPa)', '#ffe66d')
});

function updateCharts(data) {
  const labels = data.map(d => d[0]);
  [tempChart, humiChart, presChart].forEach((chart, i) => {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data.map(d => d[i + 1]);
    chart.update();
  });
}

function fetchCurrent() {
  fetch('/api/current').then(r => r.json()).then(d => {
    document.getElementById('cur-temp').textContent = d.temp.toFixed(1);
    document.getElementById('cur-humi').textContent = d.humi.toFixed(1);
    document.getElementById('cur-pres').textContent = d.pres.toFixed(1);
  }).catch(() => {});
}

let currentRange = '24h';
function loadHistory(range) {
  currentRange = range;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-' + range).classList.add('active');
  fetch('/api/history?range=' + range).then(r => r.json()).then(d => {
    updateCharts(d.data);
    document.getElementById('info').textContent = 'Records: ' + d.data.length + ' | Source: ' + d.source;
  }).catch(() => {});
}

fetchCurrent();
loadHistory('24h');
setInterval(fetchCurrent, 5000);
setInterval(() => loadHistory(currentRange), 30000);
</script>
</body>
</html>"""
