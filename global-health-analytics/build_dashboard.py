"""Build the self-contained dashboard HTML with embedded data."""
import json

with open("data/global_health_data.json") as f:
    data = json.load(f)

DATA_JS = json.dumps(data, separators=(",", ":"))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Health Analytics 2015–2024</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
  --bg:#06080f; --surface:#0d1117; --surface2:#161b27; --surface3:#1e2535;
  --border:rgba(255,255,255,0.07); --text:#e8edf5; --muted:#7a8499;
  --accent:#00e5cc; --accent2:#7c5cfc; --accent3:#ff6b6b; --accent4:#ffd166;
  --grid:rgba(255,255,255,0.04);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}
.orb{position:fixed;border-radius:50%;filter:blur(120px);pointer-events:none;z-index:0;opacity:.12}
.orb-1{width:600px;height:600px;background:var(--accent2);top:-200px;left:-200px}
.orb-2{width:400px;height:400px;background:var(--accent);bottom:-100px;right:-100px}
main{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:0 24px 80px}

/* Header */
header{padding:48px 0 40px;display:flex;align-items:flex-start;justify-content:space-between;gap:24px;border-bottom:1px solid var(--border);margin-bottom:40px;flex-wrap:wrap}
.tag{display:inline-flex;align-items:center;gap:6px;background:rgba(0,229,204,.1);border:1px solid rgba(0,229,204,.2);color:var(--accent);font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:500;letter-spacing:.15em;padding:4px 10px;border-radius:20px;text-transform:uppercase;margin-bottom:16px}
.tag::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
h1{font-size:clamp(28px,4vw,52px);font-weight:800;line-height:1.05;letter-spacing:-.02em}
h1 span{color:var(--accent)}
.subtitle{margin-top:10px;color:var(--muted);font-size:14px;font-family:'JetBrains Mono',monospace;font-weight:300}
.header-stats{display:flex;gap:24px;flex-wrap:wrap}
.hstat-value{font-size:32px;font-weight:800;color:var(--accent);line-height:1}
.hstat-label{font-size:11px;color:var(--muted);font-family:'JetBrains Mono',monospace;letter-spacing:.08em;text-transform:uppercase;margin-top:4px}

/* KPI */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-bottom:32px}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:20px 24px;position:relative;overflow:hidden;transition:border-color .2s,transform .2s;cursor:default}
.kpi-card:hover{border-color:rgba(255,255,255,.15);transform:translateY(-2px)}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--kpi-color,var(--accent))}
.kpi-label{font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}
.kpi-value{font-size:34px;font-weight:800;color:var(--kpi-color,var(--text));line-height:1}
.kpi-unit{font-size:15px;font-weight:400;color:var(--muted)}
.kpi-delta{margin-top:8px;font-size:12px;font-family:'JetBrains Mono',monospace}
.dp{color:#2ecc71}.dn{color:#e74c3c}

/* Section */
.section{margin-bottom:32px}
.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:12px}
.section-title{font-size:18px;font-weight:700;display:flex;align-items:center;gap:10px}
.icon{width:32px;height:32px;background:var(--surface3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px}

/* Chart cards */
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:24px;height:100%;transition:border-color .2s}
.chart-card:hover{border-color:rgba(255,255,255,.12)}
.chart-title{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;font-family:'JetBrains Mono',monospace}
.chart-subtitle{font-size:15px;font-weight:700;margin-bottom:20px}
canvas{max-width:100%}

/* Layouts */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.grid-2{grid-template-columns:1fr}}

/* Controls */
.controls{display:flex;gap:8px;flex-wrap:wrap}
.btn{padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:transparent;color:var(--muted);font-family:'JetBrains Mono',monospace;font-size:11px;cursor:pointer;transition:all .15s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.active{background:rgba(0,229,204,.12);border-color:var(--accent);color:var(--accent)}
select.btn{appearance:none;padding-right:24px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237a8499'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 8px center}

/* SDG */
.sdg-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.sdg-item{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:16px}
.sdg-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.sdg-badge{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--accent4);background:rgba(255,209,102,.1);border:1px solid rgba(255,209,102,.2);padding:3px 8px;border-radius:6px}
.sdg-name{font-size:13px;font-weight:600;flex:1;margin:0 8px}
.sdg-pct{font-size:20px;font-weight:800}
.progress-bar{height:5px;background:var(--surface3);border-radius:3px;overflow:hidden;margin-top:6px}
.progress-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent2),var(--accent));transition:width 1s cubic-bezier(.34,1.56,.64,1)}
.progress-fill.at-risk{background:linear-gradient(90deg,#c0392b,var(--accent3))}
.progress-fill.on-track{background:linear-gradient(90deg,#27ae60,#2ecc71)}

/* Findings */
.findings-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.finding-card{background:var(--surface2);border:1px solid var(--border);border-radius:16px;padding:20px;display:flex;gap:14px;align-items:flex-start;transition:border-color .2s,transform .2s}
.finding-card:hover{border-color:rgba(0,229,204,.25);transform:translateY(-2px)}
.finding-num{font-size:40px;font-weight:800;color:rgba(0,229,204,.15);line-height:1;min-width:40px}
.finding-text{font-size:14px;line-height:1.6;color:var(--muted)}
.finding-text strong{color:var(--text)}

/* Table */
.data-table{width:100%;border-collapse:collapse;font-size:13px;font-family:'JetBrains Mono',monospace}
.data-table th{text-align:left;padding:10px 12px;font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);border-bottom:1px solid var(--border);font-weight:500}
.data-table td{padding:10px 12px;border-bottom:1px solid var(--border)}
.data-table tr:last-child td{border-bottom:none}
.data-table tr:hover td{background:rgba(255,255,255,.02)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px}
.rank-badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:6px;font-size:11px;font-weight:700;background:var(--surface3);color:var(--muted)}
.rank-badge.top{background:rgba(0,229,204,.12);color:var(--accent)}
.sparkbar{display:inline-flex;align-items:flex-end;gap:2px;height:20px;vertical-align:middle;margin-left:8px}
.sparkbar span{width:3px;background:var(--accent);opacity:.6;border-radius:1px}

/* Footer */
footer{border-top:1px solid var(--border);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:40px}
.footer-text{font-size:12px;color:var(--muted);font-family:'JetBrains Mono',monospace}
.sources{display:flex;gap:8px;flex-wrap:wrap}
.source-badge{font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--muted);background:var(--surface2);border:1px solid var(--border);padding:3px 8px;border-radius:6px}
</style>
</head>
<body>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<main>

<!-- HEADER -->
<header>
  <div>
    <div class="tag">Health Analytics Platform</div>
    <h1>Global Health<br><span>Status Report</span></h1>
    <p class="subtitle">2015–2024 &nbsp;·&nbsp; 34 countries &nbsp;·&nbsp; 7 regions &nbsp;·&nbsp; 12+ indicators</p>
  </div>
  <div class="header-stats">
    <div class="hstat"><div class="hstat-value">72.9</div><div class="hstat-label">Avg Life Expectancy</div></div>
    <div class="hstat"><div class="hstat-value" style="color:var(--accent2)">340</div><div class="hstat-label">Observations</div></div>
    <div class="hstat"><div class="hstat-value" style="color:var(--accent4)">2024</div><div class="hstat-label">Latest Year</div></div>
  </div>
</header>

<!-- KPIs -->
<div class="section"><div class="kpi-row" id="kpiRow"></div></div>

<!-- TREND + COVID -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><span class="icon">📈</span> Life Expectancy Trends & COVID-19 Disruption</div>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-title">Time Series · All Regions</div>
      <div class="chart-subtitle">Life Expectancy 2015–2024</div>
      <canvas id="lineChart" height="260"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Baseline-Indexed · 2019 = 0%</div>
      <div class="chart-subtitle">COVID-19 Health System Impact</div>
      <canvas id="covidChart" height="260"></canvas>
    </div>
  </div>
</div>

<!-- DISEASE + FINANCING -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><span class="icon">🦠</span> Disease Burden & Health Financing</div>
    <div class="controls">
      <select class="btn" id="regionSelect" onchange="updateDisease()"><option value="all">All Regions</option></select>
    </div>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-title">Global Burden of Disease</div>
      <div class="chart-subtitle">DALYs per 100,000 Population</div>
      <canvas id="diseaseChart" height="290"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Health Financing Structure</div>
      <div class="chart-subtitle">Spending Mix by Region</div>
      <canvas id="financingChart" height="290"></canvas>
    </div>
  </div>
</div>

<!-- SCATTER + RADAR -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><span class="icon">🔗</span> Correlations & Multi-dimensional Benchmarking</div>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-title">Correlation · r = +0.97</div>
      <div class="chart-subtitle">UHC Index vs Life Expectancy — 2024</div>
      <canvas id="scatterChart" height="290"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Radar · Normalized 0–100</div>
      <div class="chart-subtitle">Regional Health Profile (select 3 regions shown)</div>
      <canvas id="radarChart" height="290"></canvas>
    </div>
  </div>
</div>

<!-- SDG -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><span class="icon">🎯</span> SDG 3 Progress Tracker — Target: 2030</div>
  </div>
  <div class="sdg-grid" id="sdgGrid"></div>
</div>

<!-- TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><span class="icon">🏆</span> Country Rankings — 2024</div>
    <div class="controls">
      <button class="btn active" onclick="sortTable('uhc_index',this)">UHC Index</button>
      <button class="btn" onclick="sortTable('life_expectancy',this)">Life Exp</button>
      <button class="btn" onclick="sortTable('vaccination_coverage',this)">Vaccination</button>
      <button class="btn" onclick="sortTable('u5_mortality_rate',this)">U5 Mortality</button>
    </div>
  </div>
  <div class="chart-card"><table class="data-table" id="rankTable"></table></div>
</div>

<!-- FINDINGS -->
<div class="section">
  <div class="section-header"><div class="section-title"><span class="icon">🔍</span> Key Analytical Findings</div></div>
  <div class="findings-grid" id="findingsGrid"></div>
</div>

<footer>
  <div class="footer-text">Synthetic dataset · Analytical demonstration · Generated 2024</div>
  <div class="sources">
    <span class="source-badge">WHO GHO</span>
    <span class="source-badge">World Bank</span>
    <span class="source-badge">IHME GBD</span>
    <span class="source-badge">UN SDG</span>
  </div>
</footer>

</main>
<script>
const DATA=__DATA_PLACEHOLDER__;
const RC={"Sub-Saharan Africa":"#e67e22","South Asia":"#e74c3c","East Asia & Pacific":"#3498db","Latin America":"#2ecc71","Middle East & N. Africa":"#9b59b6","Europe & Central Asia":"#1abc9c","North America":"#f39c12"};
const REGIONS=Object.keys(RC);
const YEARS=DATA.years;

function avg(a){return a.reduce((s,v)=>s+v,0)/a.length}
function rya(metric,year,region){
  let rows=DATA.timeseries.filter(r=>r.year===year);
  if(region)rows=rows.filter(r=>r.region===region);
  const v=rows.map(r=>r[metric]).filter(x=>x!=null);
  return v.length?avg(v):null;
}

const CD={
  plugins:{
    legend:{labels:{color:'#7a8499',font:{family:'JetBrains Mono',size:11},boxWidth:10,boxHeight:10,padding:14}},
    tooltip:{backgroundColor:'#0d1117',borderColor:'rgba(255,255,255,.1)',borderWidth:1,titleColor:'#e8edf5',bodyColor:'#7a8499',titleFont:{family:'Syne',weight:'600'},bodyFont:{family:'JetBrains Mono',size:11},padding:12,cornerRadius:10}
  },
  scales:{
    x:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#7a8499',font:{family:'JetBrains Mono',size:10}}},
    y:{grid:{color:'rgba(255,255,255,.04)'},ticks:{color:'#7a8499',font:{family:'JetBrains Mono',size:10}}}
  }
};

/* KPIs */
function buildKPIs(){
  const l=DATA.timeseries.filter(r=>r.year===2024);
  const p=DATA.timeseries.filter(r=>r.year===2015);
  const kpis=[
    {label:"Life Expectancy",val:avg(l.map(r=>r.life_expectancy)).toFixed(1),unit:"yrs",d:(avg(l.map(r=>r.life_expectancy))-avg(p.map(r=>r.life_expectancy))).toFixed(1),color:"#00e5cc",pos:true},
    {label:"UHC Coverage Index",val:avg(l.map(r=>r.uhc_index)).toFixed(1),unit:"/100",d:(avg(l.map(r=>r.uhc_index))-avg(p.map(r=>r.uhc_index))).toFixed(1),color:"#7c5cfc",pos:true},
    {label:"Vaccination Coverage",val:avg(l.map(r=>r.vaccination_coverage)).toFixed(1),unit:"%",d:(avg(l.map(r=>r.vaccination_coverage))-avg(p.map(r=>r.vaccination_coverage))).toFixed(1),color:"#3498db",pos:true},
    {label:"U5 Mortality Rate",val:avg(l.map(r=>r.u5_mortality_rate)).toFixed(1),unit:"/1k",d:(avg(l.map(r=>r.u5_mortality_rate))-avg(p.map(r=>r.u5_mortality_rate))).toFixed(1),color:"#2ecc71",pos:false},
    {label:"Hospital Beds",val:avg(l.map(r=>r.hospital_beds_per_1k)).toFixed(2),unit:"/1k pop",d:(avg(l.map(r=>r.hospital_beds_per_1k))-avg(p.map(r=>r.hospital_beds_per_1k))).toFixed(2),color:"#f39c12",pos:true},
    {label:"Out-of-Pocket Spend",val:avg(l.map(r=>r.out_of_pocket_pct)).toFixed(1),unit:"%",d:(avg(l.map(r=>r.out_of_pocket_pct))-avg(p.map(r=>r.out_of_pocket_pct))).toFixed(1),color:"#ff6b6b",pos:false},
  ];
  const c=document.getElementById('kpiRow');
  kpis.forEach(k=>{
    const good=k.pos?parseFloat(k.d)>=0:parseFloat(k.d)<0;
    const sign=parseFloat(k.d)>=0?'+':'';
    c.innerHTML+=`<div class="kpi-card" style="--kpi-color:${k.color}"><div class="kpi-label">${k.label}</div><div class="kpi-value">${k.val}<span class="kpi-unit"> ${k.unit}</span></div><div class="kpi-delta ${good?'dp':'dn'}">${sign}${k.d} vs 2015</div></div>`;
  });
}

/* Line chart */
function buildLine(){
  const ctx=document.getElementById('lineChart').getContext('2d');
  new Chart(ctx,{type:'line',data:{labels:YEARS,datasets:REGIONS.map(r=>({label:r,data:YEARS.map(y=>rya('life_expectancy',y,r)),borderColor:RC[r],backgroundColor:'transparent',borderWidth:2,pointRadius:3,pointHoverRadius:5,tension:.35}))},options:{...CD,responsive:true,interaction:{mode:'index'}}});
}

/* COVID chart */
function buildCovid(){
  const ctx=document.getElementById('covidChart').getContext('2d');
  const metrics=['vaccination_coverage','uhc_index','u5_mortality_rate'];
  const labels=['Vaccination Coverage','UHC Index','U5 Mortality Rate'];
  const years=[2018,2019,2020,2021,2022,2023,2024];
  const colors=['#00e5cc','#7c5cfc','#ff6b6b'];
  const datasets=metrics.map((m,i)=>({
    label:labels[i],
    data:years.map(y=>{const base=rya(m,2019);const v=rya(m,y);return base?((v-base)/base*100).toFixed(2):0;}),
    borderColor:colors[i],backgroundColor:colors[i]+'22',borderWidth:2,fill:false,tension:.3,pointRadius:4
  }));
  new Chart(ctx,{type:'line',data:{labels:years,datasets},options:{...CD,responsive:true,plugins:{...CD.plugins,tooltip:{...CD.plugins.tooltip,callbacks:{label:c=>`${c.dataset.label}: ${c.parsed.y>0?'+':''}${c.parsed.y}% vs 2019`}}},scales:{...CD.scales,y:{...CD.scales.y,title:{display:true,text:'% change vs 2019',color:'#7a8499',font:{family:'JetBrains Mono',size:10}}}}}});
}

/* Disease chart */
let dChart;
function buildDisease(region){
  const ctx=document.getElementById('diseaseChart').getContext('2d');
  if(dChart)dChart.destroy();
  let b=DATA.disease_burden;
  if(region&&region!=='all')b=b.filter(d=>d.region===region);
  const byD={};b.forEach(d=>{if(!byD[d.disease])byD[d.disease]=[];byD[d.disease].push(d.dalys_per_100k);});
  const sorted=Object.entries(byD).map(([k,v])=>({k,v:avg(v)})).sort((a,b)=>b.v-a.v);
  const colors=['#ff6b6b','#ffd166','#06d6a0','#118ab2','#7c5cfc','#f72585','#4cc9f0','#fb8500','#e63946','#2ec4b6'];
  dChart=new Chart(ctx,{type:'bar',data:{labels:sorted.map(s=>s.k),datasets:[{data:sorted.map(s=>s.v),backgroundColor:colors.map(c=>c+'cc'),borderColor:colors,borderWidth:1,borderRadius:6}]},options:{...CD,indexAxis:'y',responsive:true,plugins:{...CD.plugins,legend:{display:false}},scales:{x:{...CD.scales.x,title:{display:true,text:'DALYs per 100,000',color:'#7a8499',font:{family:'JetBrains Mono',size:10}}},y:{...CD.scales.y}}}});
}
function updateDisease(){buildDisease(document.getElementById('regionSelect').value)}

/* Financing */
function buildFinancing(){
  const ctx=document.getElementById('financingChart').getContext('2d');
  new Chart(ctx,{type:'bar',data:{labels:DATA.financing.map(f=>f.region),datasets:[
    {label:"Gov't Spending (×10% GDP)",data:DATA.financing.map(f=>f.govt_health_spending_gdp*10),backgroundColor:'#00e5cc55',borderColor:'#00e5cc',borderWidth:1,borderRadius:4},
    {label:"Private Spending (%)",data:DATA.financing.map(f=>f.private_spending_pct),backgroundColor:'#7c5cfc55',borderColor:'#7c5cfc',borderWidth:1,borderRadius:4},
    {label:"Out-of-Pocket (%)",data:DATA.financing.map(f=>f.oop_pct),backgroundColor:'#ff6b6b55',borderColor:'#ff6b6b',borderWidth:1,borderRadius:4},
  ]},options:{...CD,responsive:true,scales:{x:{...CD.scales.x,ticks:{...CD.scales.x.ticks,maxRotation:30}},y:{...CD.scales.y,title:{display:true,text:'% of Health Spend',color:'#7a8499',font:{family:'JetBrains Mono',size:10}}}}}});
}

/* Scatter */
function buildScatter(){
  const ctx=document.getElementById('scatterChart').getContext('2d');
  const latest=DATA.timeseries.filter(r=>r.year===2024);
  const datasets=REGIONS.map(r=>({label:r,data:latest.filter(d=>d.region===r).map(d=>({x:d.uhc_index,y:d.life_expectancy,country:d.country})),backgroundColor:RC[r]+'99',borderColor:RC[r],borderWidth:1.5,pointRadius:7,pointHoverRadius:9}));
  new Chart(ctx,{type:'scatter',data:{datasets},options:{...CD,responsive:true,plugins:{...CD.plugins,tooltip:{...CD.plugins.tooltip,callbacks:{label:c=>`${c.raw.country}: UHC ${c.raw.x.toFixed(1)}, LE ${c.raw.y.toFixed(1)}`}}},scales:{x:{...CD.scales.x,title:{display:true,text:'UHC Index',color:'#7a8499',font:{family:'JetBrains Mono',size:10}}},y:{...CD.scales.y,title:{display:true,text:'Life Expectancy (years)',color:'#7a8499',font:{family:'JetBrains Mono',size:10}}}}}});
}

/* Radar */
function buildRadar(){
  const ctx=document.getElementById('radarChart').getContext('2d');
  const labels=['Life Exp','UHC Index','Vaccination','Hosp Beds','Low OOP','Low U5MR'];
  const y=2024;
  function norm(vals,inv){const mn=Math.min(...vals),mx=Math.max(...vals);return vals.map(v=>{const n=(v-mn)/(mx-mn+.01)*100;return inv?100-n:n;});}
  const leN=norm(REGIONS.map(r=>rya('life_expectancy',y,r)));
  const uhcN=norm(REGIONS.map(r=>rya('uhc_index',y,r)));
  const vN=norm(REGIONS.map(r=>rya('vaccination_coverage',y,r)));
  const hN=norm(REGIONS.map(r=>rya('hospital_beds_per_1k',y,r)));
  const oN=norm(REGIONS.map(r=>rya('out_of_pocket_pct',y,r)),true);
  const u5N=norm(REGIONS.map(r=>rya('u5_mortality_rate',y,r)),true);
  const featured=['North America','Sub-Saharan Africa','South Asia'];
  const datasets=REGIONS.map((r,i)=>({label:r,data:[leN[i],uhcN[i],vN[i],hN[i],oN[i],u5N[i]],borderColor:RC[r],backgroundColor:RC[r]+'18',borderWidth:1.5,pointRadius:3,hidden:!featured.includes(r)}));
  new Chart(ctx,{type:'radar',data:{labels,datasets},options:{responsive:true,plugins:{legend:{labels:{color:'#7a8499',font:{family:'JetBrains Mono',size:10},boxWidth:8,padding:10}},tooltip:CD.plugins.tooltip},scales:{r:{min:0,max:100,grid:{color:'rgba(255,255,255,.06)'},angleLines:{color:'rgba(255,255,255,.06)'},ticks:{display:false},pointLabels:{color:'#7a8499',font:{family:'JetBrains Mono',size:9}}}}}});
}

/* SDG Grid */
function buildSDG(){
  const defs=[
    {col:'sdg_3_1_progress',id:'SDG 3.1',name:'Maternal Mortality Reduction'},
    {col:'sdg_3_2_progress',id:'SDG 3.2',name:'Child Mortality Reduction'},
    {col:'sdg_3_3_progress',id:'SDG 3.3',name:'Epidemic Control'},
    {col:'sdg_3_4_progress',id:'SDG 3.4',name:'Premature NCD Deaths'},
    {col:'sdg_3_8_progress',id:'SDG 3.8',name:'Universal Health Coverage'},
    {col:'sdg_3b_progress', id:'SDG 3.b',name:'Essential Medicines Access'},
  ];
  const c=document.getElementById('sdgGrid');
  defs.forEach(def=>{
    const vals=DATA.sdg_indicators.map(r=>({region:r.region,val:r[def.col]}));
    const ga=avg(vals.map(v=>v.val));
    c.innerHTML+=`<div class="sdg-item"><div class="sdg-header"><span class="sdg-badge">${def.id}</span><span class="sdg-name">${def.name}</span><span class="sdg-pct" style="color:${ga>=75?'#2ecc71':'#ff6b6b'}">${ga.toFixed(0)}%</span></div>${vals.sort((a,b)=>b.val-a.val).map(v=>`<div style="margin-bottom:5px"><div style="display:flex;justify-content:space-between;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--muted);margin-bottom:3px"><span>${v.region}</span><span>${v.val.toFixed(0)}%</span></div><div class="progress-bar"><div class="progress-fill ${v.val>=75?'on-track':'at-risk'}" style="width:${v.val}%"></div></div></div>`).join('')}</div>`;
  });
}

/* Table */
let cSort='uhc_index',sDesc=true;
function buildTable(metric='uhc_index'){
  const latest=DATA.timeseries.filter(r=>r.year===2024);
  const sorted=[...latest].sort((a,b)=>sDesc?b[metric]-a[metric]:a[metric]-b[metric]).slice(0,15);
  let html=`<thead><tr><th>Rank</th><th>Country</th><th>Region</th><th>Life Exp</th><th>UHC</th><th>Vacc %</th><th>U5 MR</th><th>Hosp Beds</th></tr></thead><tbody>`;
  sorted.forEach((r,i)=>{
    const sparkVals=DATA.timeseries.filter(d=>d.country===r.country).sort((a,b)=>a.year-b.year).map(d=>d[metric]);
    const smax=Math.max(...sparkVals),smin=Math.min(...sparkVals);
    const spark=sparkVals.map(v=>`<span style="height:${Math.max(3,Math.round((v-smin)/(smax-smin+.01)*18))}px"></span>`).join('');
    html+=`<tr><td><span class="rank-badge ${i<3?'top':''}">${i+1}</span></td><td style="font-weight:600">${r.country}</td><td><span class="dot" style="background:${RC[r.region]}"></span>${r.region}</td><td>${r.life_expectancy.toFixed(1)}</td><td>${r.uhc_index.toFixed(1)}<span class="sparkbar">${spark}</span></td><td>${r.vaccination_coverage.toFixed(1)}</td><td>${r.u5_mortality_rate.toFixed(1)}</td><td>${r.hospital_beds_per_1k.toFixed(2)}</td></tr>`;
  });
  document.getElementById('rankTable').innerHTML=html+'</tbody>';
}
function sortTable(m,btn){
  if(cSort===m)sDesc=!sDesc;else{cSort=m;sDesc=true;}
  document.querySelectorAll('.controls .btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');buildTable(m);
}

/* Findings */
function buildFindings(){
  const items=[
    {t:"<strong>Life expectancy rose 2.1 years</strong> from 2015→2024. COVID-19 caused a sharp −1.2yr dip in 2020, fully recovered by 2023."},
    {t:"<strong>21-year equity gap</strong> persists between North America (81.3 yrs) and Sub-Saharan Africa (60.2 yrs) — the largest regional disparity."},
    {t:"<strong>Vaccination coverage fell 9.6%</strong> during COVID-19. South Asia and Sub-Saharan Africa show the slowest recovery trajectories."},
    {t:"<strong>Cardiovascular disease dominates</strong> high-income regions; Malaria and HIV/AIDS remain the leading burden in Sub-Saharan Africa."},
    {t:"<strong>UHC Index is the strongest predictor</strong> of life expectancy (r = +0.97), making universal coverage the highest-leverage policy intervention."},
    {t:"<strong>Only 3 of 7 regions</strong> are on track for SDG 3.8 by 2030. Middle East, Latin America, and South Asia face critical gaps."},
  ];
  const c=document.getElementById('findingsGrid');
  items.forEach((f,i)=>c.innerHTML+=`<div class="finding-card"><div class="finding-num">0${i+1}</div><div class="finding-text">${f.t}</div></div>`);
}

/* Region select */
function buildSelect(){
  const s=document.getElementById('regionSelect');
  REGIONS.forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;s.appendChild(o);});
}

/* Init */
window.addEventListener('DOMContentLoaded',()=>{
  buildKPIs();buildLine();buildCovid();
  buildSelect();buildDisease();buildFinancing();
  buildScatter();buildRadar();buildSDG();buildTable();buildFindings();
  setTimeout(()=>{
    document.querySelectorAll('.progress-fill').forEach(el=>{
      const w=el.style.width;el.style.width='0';
      requestAnimationFrame(()=>{el.style.width=w;});
    });
  },300);
});
</script>
</body>
</html>"""

# Inject data
HTML = HTML.replace("__DATA_PLACEHOLDER__", DATA_JS)

with open("public/dashboard.html", "w") as f:
    f.write(HTML)

print(f"Dashboard built: {len(HTML):,} chars")
print("Saved to public/dashboard.html")
