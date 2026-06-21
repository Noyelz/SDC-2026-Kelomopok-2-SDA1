
// ══════════════════════════════════════════════════════
//  DATA — loaded from Python API
// ══════════════════════════════════════════════════════
let currentRole = '{{ session.role }}';
let currentEmpId = '{{ session.pegawai_id }}';
let SEMUA_PEGAWAI = [];

const PERIODE_LABELS_ALL  = ['Q1 2024','Q2 2024','Q3 2024','Q4 2024','Q1 2025','Q2 2025'];
const PERIODE_LABELS_2024 = ['Q1 2024','Q2 2024','Q3 2024'];
const PERIODE_LABELS_2025 = ['Q4 2024','Q1 2025','Q2 2025'];
const TRAINING_IDX = 2;

const NAVY  = '#132B50';
const GOLD  = '#A49063';
const NAVY_L = '#2a5298';
const NAVY_PALE = '#9ab4d4';
const empColors = [NAVY,GOLD,NAVY_L,'#4a7c59','#8b6914','#5b7fa6','#a05c5c','#6b5ba6','#5ba69b','#a0845c',
                   '#7a5a3a','#3a7a6a','#7a3a5a','#3a5a7a','#6a7a3a','#7a6a3a','#3a7a3a','#7a3a3a','#5a3a7a','#3a5a3a'];

Chart.defaults.font.family = "'DM Sans', Arial, sans-serif";
Chart.defaults.color = '#6b7a8d';

// ══════════════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════════════
let filteredPegawai = [];
let activePeriodeLabels = PERIODE_LABELS_ALL;
let activePeriodeIndices = [0,1,2,3,4,5];

function avg(arr){ return arr.reduce((a,b)=>a+b,0)/arr.length; }

// ══════════════════════════════════════════════════════
//  API HELPERS
// ══════════════════════════════════════════════════════
async function fetchJSON(url){
  const res = await fetch(url);
  return res.json();
}

async function loadAllPegawai(divisi='all'){
  const url = divisi && divisi !== 'all' ? `/api/pegawai?divisi=${encodeURIComponent(divisi)}` : '/api/pegawai';
  SEMUA_PEGAWAI = await fetchJSON(url);
  filteredPegawai = [...SEMUA_PEGAWAI];
  return SEMUA_PEGAWAI;
}

// ══════════════════════════════════════════════════════
//  FILTER
// ══════════════════════════════════════════════════════
async function applyFilter(){
  const div   = document.getElementById('filterDivisi').value;
  const tahun = document.getElementById('filterTahun').value;

  await loadAllPegawai(div);

  if(tahun === '2024'){
    activePeriodeLabels  = PERIODE_LABELS_2024;
    activePeriodeIndices = [0,1,2];
  } else if(tahun === '2025'){
    activePeriodeLabels  = PERIODE_LABELS_2025;
    activePeriodeIndices = [3,4,5];
  } else {
    activePeriodeLabels  = PERIODE_LABELS_ALL;
    activePeriodeIndices = [0,1,2,3,4,5];
  }

  renderMgrAll();
}

// ══════════════════════════════════════════════════════
//  RENDER ALL (manager)
// ══════════════════════════════════════════════════════
function renderAll(){ 
  renderMgrAll(); 
  if(currentRole === 'supadmin') {
    loadUsers();
    loadAdminPegawai();
    loadAdminCourses();
  }
}
function renderMgrAll(){
  updateKPI();
  renderTabelPegawai();
  renderRankTables();
  renderTabelKinerja();
  renderTabelInterpretasi();
  destroyAndRebuildCharts();
}

// ══════════════════════════════════════════════════════
//  KPI
// ══════════════════════════════════════════════════════
function updateKPI(){
  const fp = filteredPegawai;
  const total   = fp.length;
  const aktif   = fp.filter(p=>p.status==='Aktif').length;
  const pct     = total ? Math.round(aktif/total*100) : 0;
  const rataKenaikan= total ? Math.round(fp.reduce((a,p)=>a+(p.postScore-p.preScore),0)/total) : 0;
  const remedial= fp.filter(p=>(p.postScore-p.preScore)<15).length;
  const stagnan = fp.filter(p=>{
    const ki=p.kinerja; const pre=avg(ki.slice(0,3)); const post=avg(ki.slice(3));
    return Math.abs(post-pre)<0.2;
  }).length;
  el('kpi-total').textContent    = total;
  el('kpi-pct').textContent      = pct;
  el('kpi-pct-n').textContent    = aktif;
  el('kpi-pct-total').textContent= total;
  el('kpi-delta').textContent    = rataKenaikan;
  el('kpi-flagged').textContent  = remedial+stagnan;
  el('kpi-flag-detail').textContent = remedial+' remedial, '+stagnan+' stagnan';
}

// ══════════════════════════════════════════════════════
//  RANK TABLES (Top 5 / Bot 5)
// ══════════════════════════════════════════════════════
let activeRankTab = 'top';

function switchRankTab(tab){
  activeRankTab = tab;
  document.querySelectorAll('.rank-tab').forEach((t,i)=>{
    t.classList.toggle('active', (i===0&&tab==='top')||(i===1&&tab==='bot'));
  });
  document.querySelectorAll('.rank-panel').forEach((p,i)=>{
    p.classList.toggle('active', (i===0&&tab==='top')||(i===1&&tab==='bot'));
  });
}

function renderRankTables(){
  const fp = [...filteredPegawai];
  const withAvg = fp.map(p=>({ ...p, avgKin: avg(p.kinerja.slice(3)) }));
  withAvg.sort((a,b)=>b.avgKin-a.avgKin);

  const top5 = withAvg.slice(0,5);
  const bot5 = [...withAvg].reverse().slice(0,5);

  el('tbody-top').innerHTML = top5.map((p,i)=>rankRow(p,i+1,'top')).join('');
  el('tbody-bot').innerHTML = bot5.map((p,i)=>rankRow(p,i+1,'bot')).join('');
  el('meta-top').textContent = 'Berdasarkan rata-rata skor kinerja Q4 2024 – Q2 2025';
  el('meta-bot').textContent = 'Berdasarkan rata-rata skor kinerja Q4 2024 – Q2 2025';
}

function rankRow(p, rank, type){
  const kenaikan = p.postScore - p.preScore;
  const dcls  = kenaikan>=20?'delta-up':kenaikan>=10?'delta-low':'delta-neg';
  const stBadge = p.status==='Aktif'?'badge-aktif':p.status==='Belum'?'badge-belum':'badge-expired';
  const badgeCls = type==='top'?'rank-top':'rank-bot';
  return `<tr>
    <td data-label="No." style="text-align:center"><span class="rank-badge ${badgeCls}">${rank}</span></td>
    <td data-label="Nama"><strong>${p.nama}</strong></td>
    <td data-label="Jabatan" style="font-size:11.5px">${p.jabatan}</td>
    <td data-label="Divisi">${p.divisi}</td>
    <td data-label="Status"><span class="badge ${stBadge}">${p.status}</span></td>
    <td data-label="Nilai Awal" class="mono" style="text-align:center">${p.preScore}</td>
    <td data-label="Nilai Akhir" class="mono" style="text-align:center">${p.postScore}</td>
    <td data-label="Kenaikan" class="mono ${dcls}" style="text-align:center">${kenaikan>0?'+':''}${kenaikan}</td>
    <td data-label="Rata-rata Kinerja" class="mono" style="text-align:center;font-weight:600;color:var(--navy)">${p.avgKin.toFixed(2)}</td>
  </tr>`;
}

// ══════════════════════════════════════════════════════
//  TABEL FULL PEGAWAI
// ══════════════════════════════════════════════════════
function renderTabelPegawai(){
  const fp = filteredPegawai;
  el('tabel-meta').textContent = 'Menampilkan '+fp.length+' pegawai';
  el('tabel-pegawai-body').innerHTML = fp.map(p=>{
    const kenaikan = p.postScore - p.preScore;
    const dcls  = kenaikan>=20?'delta-up':kenaikan>=10?'delta-low':'delta-neg';
    const stBadge = p.status==='Aktif'?'badge-aktif':p.status==='Belum'?'badge-belum':'badge-expired';
    const avgKin  = avg(p.kinerja).toFixed(2);
    return `<tr>
      <td data-label="ID" class="mono" style="color:var(--text-muted);font-size:11px">${p.id}</td>
      <td data-label="Nama"><strong>${p.nama}</strong></td>
      <td data-label="Jabatan" style="font-size:11.5px">${p.jabatan}</td>
      <td data-label="Divisi">${p.divisi}</td>
      <td data-label="Sertifikat" style="font-size:11px">${p.sertifikat}</td>
      <td data-label="Status"><span class="badge ${stBadge}">${p.status}</span></td>
      <td data-label="Nilai Awal" class="mono" style="text-align:center">${p.preScore}</td>
      <td data-label="Nilai Akhir" class="mono" style="text-align:center">${p.postScore}</td>
      <td data-label="Kenaikan" class="mono ${dcls}" style="text-align:center">${kenaikan>0?'+':''}${kenaikan}</td>
      <td data-label="Rata-rata Kinerja" class="mono" style="text-align:center">${avgKin}</td>
    </tr>`;
  }).join('');
}

// ══════════════════════════════════════════════════════
//  TABEL KINERJA
// ══════════════════════════════════════════════════════
function renderTabelKinerja(){
  const fp = filteredPegawai;
  const idx = activePeriodeIndices;
  el('tabel-kinerja-body').innerHTML = fp.map(p=>{
    const k = p.kinerja;
    const preAvg  = avg(k.slice(0,3));
    const postAvg = avg(k.slice(3));
    const naik    = postAvg - preAvg;
    const dcls    = naik>=0.4?'delta-up':naik>=0.1?'delta-low':'delta-neg';
    const tren    = naik>=0.4?'↑ Membaik':naik>=0.1?'↗ Sedikit naik':naik<0?'↓ Menurun':'→ Tidak berubah';
    const cells   = idx.map((qi,ci)=>`<td class="mono" style="text-align:center;${qi===2?'background:rgba(164,144,99,.07);font-weight:600':''}">${k[qi].toFixed(1)}</td>`).join('');
    return `<tr>
      <td><strong>${p.nama}</strong><br><span style="font-size:10.5px;color:var(--text-muted)">${p.jabatan}</span></td>
      ${cells}
      <td class="mono ${dcls}" style="text-align:center">${naik>0?'+':''}${naik.toFixed(2)}</td>
      <td style="font-size:11.5px;color:var(--text-muted)">${tren}</td>
    </tr>`;
  }).join('');
}

// ══════════════════════════════════════════════════════
//  FLAGGING
// ══════════════════════════════════════════════════════
function getFlag(p){
  const kenaikan = p.postScore - p.preScore;
  const kinNaik = avg(p.kinerja.slice(3)) - avg(p.kinerja.slice(0,3));
  if(kenaikan>=20 && kinNaik>=0.4 && p.status==='Aktif') return 'siap';
  if(kenaikan<15 || kinNaik<0) return 'remedial';
  if(Math.abs(kinNaik)<0.2) return 'stagnan';
  return 'monitor';
}
function getRekomen(p){
  const f = getFlag(p);
  if(f==='siap')     return 'Daftarkan ke LSP Pariwisata; kandidat sertifikasi lanjutan';
  if(f==='remedial') return 'Ikutkan pelatihan ulang; jadwalkan bimbingan intensif';
  if(f==='stagnan')  return 'Evaluasi faktor eksternal; konsultasi dengan supervisor';
  return 'Pantau 1 kuartal ke depan; pertimbangkan coaching';
}

function renderTabelInterpretasi(){
  const fp = filteredPegawai;
  const counts = {siap:0,remedial:0,stagnan:0,monitor:0};
  fp.forEach(p=>counts[getFlag(p)]++);

  el('interp-tiles').innerHTML = [
    {k:'siap',    label:'Siap Sertifikasi',  desc:'Nilai naik signifikan & kinerja membaik'},
    {k:'remedial',label:'Perlu Remedial',    desc:'Skor rendah atau kinerja menurun'},
    {k:'stagnan', label:'Kinerja Stagnan',   desc:'Tidak ada perubahan signifikan'},
    {k:'monitor', label:'Perlu Monitoring',  desc:'Progres ada, perlu dipantau'}
  ].map(t=>`<div class="interp-tile ${t.k}">
    <div class="interp-count">${counts[t.k]}</div>
    <div class="interp-label">${t.label}</div>
    <div class="interp-desc">${t.desc}</div>
  </div>`).join('');

  const flagBadge = {siap:'badge-siap',remedial:'badge-remedial',stagnan:'badge-stagnan',monitor:'badge-monitor'};
  const flagLabel = {siap:'Siap Sertifikasi',remedial:'Perlu Remedial',stagnan:'Stagnan',monitor:'Pantau'};
  el('tabel-interpretasi-body').innerHTML = fp.map(p=>{
    const kenaikan = p.postScore - p.preScore;
    const kinNaik = avg(p.kinerja.slice(3)) - avg(p.kinerja.slice(0,3));
    const tren = kinNaik>=0.4?'↑ Membaik':kinNaik<0?'↓ Menurun':'→ Tidak banyak berubah';
    const flag = getFlag(p);
    const dcls = kenaikan>=20?'delta-up':kenaikan>=10?'delta-low':'delta-neg';
    return `<tr>
      <td><strong>${p.nama}</strong><br><span style="font-size:10.5px;color:var(--text-muted)">${p.jabatan} — ${p.divisi}</span></td>
      <td class="mono ${dcls}" style="text-align:center">${kenaikan>0?'+':''}${kenaikan} poin</td>
      <td style="font-size:12px">${tren}</td>
      <td><span class="badge badge-monitor">${p.label_tindakan_nama}</span></td>
      <td style="font-size:11.5px;line-height:1.5">${p.label_rekomendasi_nama}</td>
    </tr>`;
  }).join('');
}

// ══════════════════════════════════════════════════════
//  CHARTS
// ══════════════════════════════════════════════════════
const charts = {};
function destroyChart(id){ if(charts[id]){charts[id].destroy();delete charts[id];} }
function el(id){ return document.getElementById(id); }

function chartResponsiveDefaults(){
  const w = window.innerWidth;
  const isMobile = w<=768, isTablet = w<=1024;
  return {
    fontSize      : isMobile ? 9  : isTablet ? 10 : 11,
    legendFontSize: isMobile ? 10 : isTablet ? 11 : 12,
    titleFontSize : isMobile ? 10 : isTablet ? 11 : 11,
    pointRadius   : isMobile ? 2  : isTablet ? 3  : 4,
    pointHover    : isMobile ? 4  : isTablet ? 5  : 6,
    borderWidth   : isMobile ? 1.5: isTablet ? 2  : 2.5,
    showAxisTitle : !isMobile,
    legendPos     : isMobile ? 'bottom' : 'top',
  };
}
function applyChartDefaults(){
  const d = chartResponsiveDefaults();
  Chart.defaults.font.size = d.fontSize;
  Chart.defaults.plugins.legend.labels.font = {size:d.legendFontSize};
  Chart.defaults.elements.point.radius      = d.pointRadius;
  Chart.defaults.elements.point.hoverRadius = d.pointHover;
  Chart.defaults.elements.line.borderWidth  = d.borderWidth;
}
applyChartDefaults();
let _resizeTimer;
window.addEventListener('resize',()=>{
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(()=>{
    applyChartDefaults();
    const anyMgrVisible = ['dashboard','prepost','tren','interpretasi','pegawai']
      .some(v=>document.getElementById('view-'+v)?.classList.contains('active'));
    if(anyMgrVisible) destroyAndRebuildMgrCharts();
  },250);
});

function destroyAndRebuildCharts(){ destroyAndRebuildMgrCharts(); }
function destroyAndRebuildMgrCharts(){
  Object.keys(charts).forEach(id=>{charts[id].destroy();delete charts[id];});
  buildChartPrePost();
  buildChartDonut();
  buildChartTrenDash();
  buildChartPrePostFull();
  buildChartDivisi();
  buildChartScatter();
  buildChartTren();
  populateEmpSelect();
}

// ─── 1. Dash Bar Pre/Post ─────────────────────────────
function buildChartPrePost(){
  const fp = filteredPegawai.slice(0,10);
  const ctx = el('chartPrePost').getContext('2d');
  const rd = chartResponsiveDefaults();
  charts['prepost'] = new Chart(ctx,{
    type:'bar',
    data:{labels:fp.map(p=>p.nama.split(' ')[0]),datasets:[
      {label:'Nilai Awal',  data:fp.map(p=>p.preScore),  backgroundColor:NAVY,borderWidth:0},
      {label:'Nilai Akhir', data:fp.map(p=>p.postScore), backgroundColor:GOLD,borderWidth:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{title:items=>fp[items[0].dataIndex].nama}}},
      scales:{
        x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},
        y:{min:0,max:100,grid:{color:'#eee'},ticks:{stepSize:20,font:{size:rd.fontSize}}}
      }}
  });
}

// ─── 2. Donut ─────────────────────────────────────────
function buildChartDonut(){
  const fp = filteredPegawai;
  const ctx = el('chartDonut').getContext('2d');
  const rd = chartResponsiveDefaults();
  charts['donut'] = new Chart(ctx,{
    type:'doughnut',
    data:{labels:['Aktif','Belum Sertifikasi','Kadaluarsa'],datasets:[{
      data:[fp.filter(p=>p.status==='Aktif').length,fp.filter(p=>p.status==='Belum').length,fp.filter(p=>p.status==='Kadaluarsa').length],
      backgroundColor:[NAVY,GOLD,'#d9cdb8'],borderColor:'#fff',borderWidth:3,hoverOffset:6
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'65%',
      plugins:{legend:{position:'bottom',labels:{padding:12,font:{size:rd.legendFontSize},usePointStyle:true,pointStyleWidth:10}}}
    }
  });
}

// ─── 3. Tren Dash ─────────────────────────────────────
function buildChartTrenDash(){
  const divisiList = ['Akomodasi','F&B','Tur & Perjalanan'];
  const rd = chartResponsiveDefaults();
  const datasets = [];
  divisiList.forEach((d,di)=>{
    const emps = filteredPegawai.filter(p=>p.divisi===d);
    if(!emps.length) return;
    const c = [NAVY,GOLD,NAVY_L][di];
    datasets.push({
      label:d,
      data:activePeriodeIndices.map(qi=>parseFloat(avg(emps.map(p=>p.kinerja[qi])).toFixed(2))),
      borderColor:c,backgroundColor:'transparent',borderWidth:rd.borderWidth,
      pointBackgroundColor:c,pointRadius:rd.pointRadius,pointHoverRadius:rd.pointHover,tension:0.35
    });
  });
  el('tren-legend-dash').innerHTML = datasets.map(ds=>
    `<span><span class="legend-dot" style="background:${ds.borderColor}"></span>${ds.label}</span>`
  ).join('');
  const trainIdx = activePeriodeIndices.indexOf(TRAINING_IDX);
  const ctx = el('chartTrenDash').getContext('2d');
  charts['trenDash'] = new Chart(ctx,{
    type:'line',data:{labels:activePeriodeLabels,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},
      scales:{
        x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},
        y:{min:2.5,max:5,ticks:{stepSize:0.5,font:{size:rd.fontSize}},grid:{color:'#eee'}}
      }},
    plugins:[makeVerticalLinePlugin(trainIdx)]
  });
}

// ─── 4. Bar Pre/Post Full ─────────────────────────────
function buildChartPrePostFull(){
  const fp = filteredPegawai;
  const ctx = el('chartPrePostFull').getContext('2d');
  const rd = chartResponsiveDefaults();
  charts['prepostFull'] = new Chart(ctx,{
    type:'bar',
    data:{labels:fp.map(p=>p.nama.split(' ')[0]),datasets:[
      {label:'Nilai Awal',  data:fp.map(p=>p.preScore),  backgroundColor:NAVY,borderWidth:0,barPercentage:0.7},
      {label:'Nilai Akhir', data:fp.map(p=>p.postScore), backgroundColor:GOLD,borderWidth:0,barPercentage:0.7}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:rd.legendPos,labels:{padding:12,usePointStyle:true,pointStyleWidth:10,font:{size:rd.legendFontSize}}},
        tooltip:{callbacks:{afterBody:items=>'Kenaikan: +'+(fp[items[0].dataIndex].postScore-fp[items[0].dataIndex].preScore)+' poin'}}
      },
      scales:{
        x:{grid:{display:false},ticks:{maxRotation:35,font:{size:rd.fontSize}}},
        y:{min:0,max:100,grid:{color:'#eee'},ticks:{stepSize:10,font:{size:rd.fontSize}}}
      }}
  });
}

// ─── 5. Bar per Divisi ────────────────────────────────
function buildChartDivisi(){
  const divisiList = ['Akomodasi','F&B','Tur & Perjalanan'];
  const preA  = divisiList.map(d=>{const e=filteredPegawai.filter(p=>p.divisi===d);return e.length?Math.round(avg(e.map(p=>p.preScore))):0;});
  const postA = divisiList.map(d=>{const e=filteredPegawai.filter(p=>p.divisi===d);return e.length?Math.round(avg(e.map(p=>p.postScore))):0;});
  const ctx = el('chartDivisi').getContext('2d');
  const rd = chartResponsiveDefaults();
  charts['divisi'] = new Chart(ctx,{
    type:'bar',data:{labels:divisiList,datasets:[
      {label:'Nilai Awal', data:preA,  backgroundColor:NAVY,borderWidth:0},
      {label:'Nilai Akhir',data:postA, backgroundColor:GOLD,borderWidth:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:rd.legendPos,labels:{usePointStyle:true,pointStyleWidth:10,padding:12,font:{size:rd.legendFontSize}}}},
      scales:{
        x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},
        y:{min:0,max:100,grid:{color:'#eee'},ticks:{stepSize:20,font:{size:rd.fontSize}}}
      }}
  });
}

// ─── 6. Scatter ───────────────────────────────────────
function buildChartScatter(){
  const fp = filteredPegawai;
  const ctx = el('chartScatter').getContext('2d');
  const rd = chartResponsiveDefaults();
  const colMap = {'Akomodasi':NAVY,'F&B':GOLD,'Tur & Perjalanan':NAVY_L};
  charts['scatter'] = new Chart(ctx,{
    type:'scatter',
    data:{datasets:[{
      label:'Pegawai',
      data:fp.map(p=>({x:p.preScore,y:p.postScore,nama:p.nama})),
      backgroundColor:fp.map(p=>colMap[p.divisi]||NAVY),
      pointRadius:rd.pointRadius+3,pointHoverRadius:rd.pointHover+3
    }]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const d=c.raw;return `${d.nama}: Awal=${d.x}, Akhir=${d.y} (naik ${d.y-d.x} poin)`;}} }},
      scales:{
        x:{min:35,max:80,title:{display:rd.showAxisTitle,text:'Nilai Sebelum Pelatihan',font:{size:rd.titleFontSize}},grid:{color:'#eee'},ticks:{font:{size:rd.fontSize}}},
        y:{min:50,max:100,title:{display:rd.showAxisTitle,text:'Nilai Sesudah Pelatihan',font:{size:rd.titleFontSize}},grid:{color:'#eee'},ticks:{font:{size:rd.fontSize}}}
      }}
  });
}

// ─── 7. Line Tren ─────────────────────────────────────
function buildChartTren(){
  const fp = filteredPegawai;
  const trainIdx = activePeriodeIndices.indexOf(TRAINING_IDX);
  const ctx = el('chartTren').getContext('2d');
  const rd = chartResponsiveDefaults();
  const avgData = activePeriodeIndices.map(qi=>parseFloat(avg(fp.map(p=>p.kinerja[qi])).toFixed(2)));
  const datasets = [{
    label:'Rata-rata Semua',data:avgData,
    borderColor:GOLD,backgroundColor:'rgba(164,144,99,.08)',
    borderWidth:rd.borderWidth+0.5,pointRadius:rd.pointRadius+1,tension:0.35,fill:true,hidden:false
  }];
  fp.forEach((p,i)=>{
    datasets.push({
      label:p.nama,data:activePeriodeIndices.map(qi=>p.kinerja[qi]),
      borderColor:empColors[i%empColors.length],backgroundColor:'transparent',
      borderWidth:rd.borderWidth,pointRadius:rd.pointRadius,tension:0.35,hidden:true
    });
  });
  charts['tren'] = new Chart(ctx,{
    type:'line',data:{labels:activePeriodeLabels,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},
      scales:{
        x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},
        y:{min:2.0,max:5,ticks:{stepSize:0.5,font:{size:rd.fontSize}},grid:{color:'#eee'}}
      }},
    plugins:[makeVerticalLinePlugin(trainIdx)]
  });
}

// ─── Vertical Line Plugin ─────────────────────────────
function makeVerticalLinePlugin(trainIdx){
  return {
    id:'verticalLine',
    afterDraw(chart){
      if(trainIdx<0) return;
      const ctx = chart.ctx;
      const xScale = chart.scales.x;
      const yScale = chart.scales.y;
      if(!xScale||!yScale) return;
      const x = xScale.getPixelForValue(trainIdx);
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x,yScale.top);
      ctx.lineTo(x,yScale.bottom);
      ctx.strokeStyle=GOLD;ctx.lineWidth=1.5;ctx.setLineDash([6,4]);ctx.stroke();
      ctx.restore();
    }
  };
}

// ── Employee Select Populate ──────────────────────────
function populateEmpSelect(){
  const sel = el('selectEmp');
  sel.innerHTML = '<option value="all">Semua (Rata-rata)</option>';
  filteredPegawai.forEach(p=>{
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.nama+' — '+p.jabatan;
    sel.appendChild(opt);
  });
}

function updateTrenChart(){
  const val   = el('selectEmp').value;
  const chart = charts['tren'];
  if(!chart) return;
  chart.data.datasets.forEach((ds,i)=>{
    ds.hidden = val==='all' ? i!==0 : (i===0 ? true : filteredPegawai[i-1]?.id !== val);
  });
  chart.update();
}

// ══════════════════════════════════════════════════════
//  NAVIGATION (extended for manager + pegawai roles)
// ══════════════════════════════════════════════════════

const MGR_VIEW_TITLES = {
  dashboard:'Dashboard Utama', pegawai:'Tabel Pegawai',
  prepost:'Perbandingan Nilai', tren:'Tren Kinerja', interpretasi:'Interpretasi & Flagging'
};
const MGR_VIEW_ORDER = ['dashboard','pegawai','prepost','tren','interpretasi'];
const EMP_VIEW_TITLES = {
  'emp-progress':'Progress Saya','emp-sertifikat':'Sertifikat Saya',
  'emp-penilaian':'Hasil Penilaian','emp-tren':'Tren Kinerja','emp-rekomendasi':'Rekomendasi Course'
};
const EMP_VIEW_ORDER = ['emp-progress','emp-sertifikat','emp-penilaian','emp-tren','emp-rekomendasi'];
const ADM_VIEW_TITLES = {
  'admin-users': 'Manajemen Akun User', 'admin-pegawai': 'Database Pegawai', 'admin-courses': 'Database Courses'
};
const ADM_VIEW_ORDER = ['admin-users', 'admin-pegawai', 'admin-courses'];

function showView(id){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  el('view-'+id).classList.add('active');
  
  if(MGR_VIEW_ORDER.includes(id)){
    document.querySelectorAll('#nav-manager a').forEach(a=>a.classList.remove('active'));
    document.querySelectorAll('#nav-admin a').forEach(a=>a.classList.remove('active'));
    const idx = MGR_VIEW_ORDER.indexOf(id);
    if(idx>=0) document.querySelectorAll('#nav-manager a')[idx].classList.add('active');
    el('topbar-title').textContent = MGR_VIEW_TITLES[id]||id;
    el('topbar-sub').textContent   = 'Evaluasi Pelatihan & Sertifikasi 2024–2025';
  } else if (ADM_VIEW_ORDER.includes(id)) {
    document.querySelectorAll('#nav-manager a').forEach(a=>a.classList.remove('active'));
    document.querySelectorAll('#nav-admin a').forEach(a=>a.classList.remove('active'));
    const idx = ADM_VIEW_ORDER.indexOf(id);
    if(idx>=0) document.querySelectorAll('#nav-admin a')[idx].classList.add('active');
    el('topbar-title').textContent = ADM_VIEW_TITLES[id]||id;
    el('topbar-sub').textContent   = 'Manajemen Database SDC';
  } else {
    document.querySelectorAll('#nav-pegawai a').forEach(a=>a.classList.remove('active'));
    const idx = EMP_VIEW_ORDER.indexOf(id);
    if(idx>=0) document.querySelectorAll('#nav-pegawai a')[idx].classList.add('active');
    el('topbar-title').textContent = EMP_VIEW_TITLES[id]||id;
    const p = SEMUA_PEGAWAI.find(x=>x.id===currentEmpId);
    el('topbar-sub').textContent   = p ? p.nama+' · '+p.divisi : 'Tampilan Pegawai';
  }
}

// ── Sidebar toggle (mobile) ───────────────────────
function toggleSidebar(){
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebar-overlay').classList.toggle('open');
}
function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-overlay').classList.remove('open');
}
document.querySelectorAll('nav a').forEach(a=>{
  a.addEventListener('click',()=>{ if(window.innerWidth<=768) closeSidebar(); });
});
document.querySelectorAll('#nav-manager a, #nav-pegawai a, #nav-admin a').forEach(a=>{
  a.addEventListener('click',()=>window.innerWidth<=768&&el('sidebar').classList.remove('open'));
});
el('sidebar-overlay').addEventListener('click',()=>el('sidebar').classList.remove('open'));

// ══════════════════════════════════════════════════════
//  INIT — Load data from API then render
// ══════════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', async ()=>{
  await loadAllPegawai();
  initRoleDisplay();
  if(currentRole==='manager' || currentRole==='supadmin') {
    renderAll();
  }
});

// ════════════════════════════════════════════════════
//  ROLE SWITCH
// ════════════════════════════════════════════════════
function initRoleDisplay(){
  el('nav-manager').style.display = (currentRole==='manager' || currentRole==='supadmin')?'block':'none';
  el('nav-pegawai').style.display = currentRole==='pegawai'?'block':'none';
  el('nav-admin').style.display = currentRole==='supadmin'?'block':'none';
  el('emp-profile-block').style.display = 'none'; // Only show for manager looking at emp, or we just rely on topbar sub
  el('mgr-filters').style.display = (currentRole==='manager' || currentRole==='supadmin')?'flex':'none';
  el('sidebar-kq-block').style.display = (currentRole==='manager' || currentRole==='supadmin')?'block':'none';
  el('topbar-role-badge').textContent = currentRole==='pegawai'?'Pegawai':(currentRole==='supadmin'?'Admin':'Manajer');
  el('topbar-role-badge').className = 'role-badge-topbar role-badge-manager';
  
  if(currentRole==='manager' || currentRole==='supadmin'){ showView('dashboard'); }
  else { showView('emp-progress'); renderEmpViews(); }
}

function populateEmpProfileSelect(){
  const sel = el('selectEmpProfile');
  sel.innerHTML = SEMUA_PEGAWAI.map(p=>
    `<option value="${p.id}"${p.id===currentEmpId?' selected':''}>${p.nama} — ${p.jabatan}</option>`
  ).join('');
  updateSidebarEmpProfile();
}
function changeEmpProfile(){
  currentEmpId = el('selectEmpProfile').value;
  updateSidebarEmpProfile();
  renderEmpViews();
  const p = SEMUA_PEGAWAI.find(x=>x.id===currentEmpId);
  if(p) el('topbar-sub').textContent = p.nama+' · '+p.divisi;
}
function updateSidebarEmpProfile(){
  const p = SEMUA_PEGAWAI.find(x=>x.id===currentEmpId);
  if(!p) return;
  el('sidebar-emp-name').textContent = p.nama;
  el('sidebar-emp-role').textContent = p.jabatan+' · '+p.divisi;
}

// ════════════════════════════════════════════════════
//  EMPLOYEE VIEW RENDERERS
// ════════════════════════════════════════════════════
function renderEmpViews(){
  const p = SEMUA_PEGAWAI.find(x=>x.id===currentEmpId);
  if(!p) return;
  renderEmpProgress(p);
  renderEmpSertifikat(p);
  renderEmpPenilaian(p);
  renderEmpTren(p);
  renderEmpRekomendasi(p);
}

// ── Progress ──────────────────────────────────────
function renderEmpProgress(p){
  el('emp-hero-name').textContent = p.nama;
  el('emp-hero-role').textContent = p.jabatan;
  el('emp-hero-divisi').textContent = p.divisi;
  el('emp-stat-pre').textContent  = p.preScore;
  el('emp-stat-post').textContent = p.postScore;
  const delta = p.postScore - p.preScore;
  const dEl = el('emp-stat-delta');
  dEl.textContent = (delta>0?'+':'')+delta;
  dEl.style.color = delta>=20?'var(--green)':delta>=10?'var(--amber)':'var(--red)';
  el('emp-stat-kin').textContent = avg(p.kinerja).toFixed(2);

  const stBadge = p.status==='Aktif'?'badge-aktif':p.status==='Belum'?'badge-belum':'badge-expired';
  const stDesc  = p.status==='Aktif'?'Sertifikat valid dan aktif':p.status==='Belum'?'Belum mengikuti sertifikasi':'Sertifikat telah kadaluarsa';
  el('emp-cert-summary-content').innerHTML = `
    <div style="margin-bottom:14px">
      <div style="font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted)">Sertifikat Utama</div>
      <div style="font-family:var(--font-display);font-size:17px;font-weight:600;color:var(--navy);margin-top:5px;line-height:1.3">${p.sertifikat}</div>
      <div style="margin-top:8px"><span class="badge ${stBadge}">${p.status}</span></div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:6px">${stDesc}</div>
    </div>
    <div style="padding:10px 12px;background:var(--row-alt);border:1px solid var(--border)">
      <div style="font-size:9.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted)">Berlaku Sampai</div>
      <div style="font-family:var(--font-mono);font-size:13px;font-weight:600;color:var(--navy);margin-top:3px">${p.tanggal||'Belum Tersedia'}</div>
    </div>`;

  const divEmps = SEMUA_PEGAWAI.filter(x=>x.divisi===p.divisi);
  const avgPre  = Math.round(avg(divEmps.map(x=>x.preScore)));
  const avgPost = Math.round(avg(divEmps.map(x=>x.postScore)));

  destroyChart('empPrePost');
  const rd = chartResponsiveDefaults();
  charts['empPrePost'] = new Chart(el('chartEmpPrePost').getContext('2d'),{
    type:'bar',
    data:{labels:['Nilai Awal','Nilai Akhir'],datasets:[
      {label:p.nama, data:[p.preScore,p.postScore], backgroundColor:[NAVY,GOLD], borderWidth:0, barPercentage:0.5},
      {label:'Rata-rata '+p.divisi, data:[avgPre,avgPost], backgroundColor:['rgba(19,43,80,.25)','rgba(164,144,99,.35)'], borderWidth:0, barPercentage:0.5}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:rd.legendPos,labels:{usePointStyle:true,pointStyleWidth:10,padding:12,font:{size:rd.legendFontSize}}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},y:{min:0,max:100,ticks:{stepSize:20,font:{size:rd.fontSize}},grid:{color:'#eee'}}}}
  });

  destroyChart('empTrenSummary');
  const divAvgData = [0,1,2,3,4,5].map(qi=>parseFloat(avg(divEmps.map(x=>x.kinerja[qi])).toFixed(2)));
  charts['empTrenSummary'] = new Chart(el('chartEmpTrenSummary').getContext('2d'),{
    type:'line',
    data:{labels:PERIODE_LABELS_ALL,datasets:[
      {label:p.nama, data:p.kinerja, borderColor:NAVY, backgroundColor:'rgba(19,43,80,.08)', fill:true, borderWidth:rd.borderWidth, pointRadius:rd.pointRadius+1, tension:0.35},
      {label:'Rata-rata '+p.divisi, data:divAvgData, borderColor:GOLD, backgroundColor:'transparent', borderDash:[4,4], borderWidth:rd.borderWidth-0.5, pointRadius:rd.pointRadius, tension:0.35}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},
      scales:{x:{grid:{display:false},ticks:{font:{size:rd.fontSize}}},y:{min:2,max:5.5,ticks:{stepSize:0.5,font:{size:rd.fontSize}},grid:{color:'#eee'}}}},
    plugins:[makeVerticalLinePlugin(TRAINING_IDX)]
  });
}

// ── Sertifikat ────────────────────────────────────
function renderEmpSertifikat(p){
  const stBadge = p.status==='Aktif'?'badge-aktif':p.status==='Belum'?'badge-belum':'badge-expired';
  const stColor = p.status==='Aktif'?'var(--green)':p.status==='Belum'?'var(--amber)':'var(--red)';
  el('emp-cert-cards-container').innerHTML = `
    <div class="cert-card" style="border-top:3px solid ${stColor}">
      <div class="cert-card-header">
        <div>
          <div class="cert-name">${p.sertifikat}</div>
          <div class="cert-meta">${p.jabatan} &middot; ${p.divisi}</div>
        </div>
        <span class="badge ${stBadge}">${p.status}</span>
      </div>
      <div class="cert-detail-grid">
        <div class="cert-detail-item"><div class="cert-detail-label">Lembaga Sertifikasi</div><div class="cert-detail-value">LSP Pariwisata Nasional / BNSP</div></div>
        <div class="cert-detail-item"><div class="cert-detail-label">Tanggal Sertifikasi</div><div class="cert-detail-value">${p.tanggal||'—'}</div></div>
        <div class="cert-detail-item"><div class="cert-detail-label">Masa Berlaku</div><div class="cert-detail-value">${p.status==='Aktif'?'3 tahun sejak terbit':p.status==='Belum'?'Belum ada':'Sudah habis'}</div></div>
      </div>
      <div style="margin-top:16px">
        <div style="font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:10px">Skor Ujian Sertifikasi</div>
        <div class="cert-score-row">
          <div class="cert-score-label">Pre-Test</div>
          <div class="cert-score-bar-wrap"><div class="cert-score-bar bar-navy" style="width:${p.preScore}%"></div></div>
          <div class="cert-score-val">${p.preScore}</div>
        </div>
        <div class="cert-score-row" style="margin-top:8px">
          <div class="cert-score-label">Post-Test</div>
          <div class="cert-score-bar-wrap"><div class="cert-score-bar bar-gold" style="width:${p.postScore}%"></div></div>
          <div class="cert-score-val">${p.postScore}</div>
        </div>
      </div>
      ${p.status==='Kadaluarsa'?`<div style="margin-top:14px;padding:10px 14px;background:#fde8e8;border-left:3px solid var(--red);font-size:11.5px;color:#8b1a1a"><strong>Perhatian:</strong> Sertifikat Anda sudah kadaluarsa sejak ${p.tanggal}. Segera hubungi supervisor untuk menjadwalkan resertifikasi.</div>`:''}
      ${p.status==='Belum'?`<div style="margin-top:14px;padding:10px 14px;background:#fff3cd;border-left:3px solid var(--amber);font-size:11.5px;color:#7a4e0d"><strong>Catatan:</strong> Anda belum mengikuti ujian sertifikasi. Konsultasikan dengan supervisor untuk pendaftaran ke LSP Pariwisata.</div>`:''}
    </div>`;
  el('emp-test-history-body').innerHTML = `
    <tr>
      <td>${p.sertifikat}</td>
      <td class="mono" style="text-align:center">${p.preScore}</td>
      <td class="mono" style="text-align:center">${p.postScore}</td>
      <td class="mono delta-up" style="text-align:center">+${p.postScore-p.preScore}</td>
      <td style="font-size:11.5px">${p.tanggal||'Belum ada'}</td>
      <td><span class="badge ${p.postScore>=70?'badge-siap':'badge-remedial'}">${p.postScore>=70?'Lulus':'Perlu Remedial'}</span></td>
    </tr>
    <tr>
      <td>Pelatihan Layanan Pelanggan</td>
      <td class="mono" style="text-align:center">${Math.max(p.preScore-8,30)}</td>
      <td class="mono" style="text-align:center">${Math.min(p.postScore+3,100)}</td>
      <td class="mono delta-up" style="text-align:center">+11</td>
      <td style="font-size:11.5px">2024-06-10</td>
      <td><span class="badge badge-siap">Lulus</span></td>
    </tr>`;
}

// ── Penilaian ─────────────────────────────────────
const ASPEK_KINERJA = ['Kualitas Layanan','Kepatuhan SOP','Inisiatif','Kerja Tim'];
function getAspekScores(p){
  const base = avg(p.kinerja.slice(3));
  return [Math.min(5,parseFloat((base+0.15).toFixed(1))),Math.min(5,parseFloat((base-0.05).toFixed(1))),Math.min(5,parseFloat((base-0.2).toFixed(1))),Math.min(5,parseFloat((base+0.1).toFixed(1)))];
}
function getAspekScoresPre(p){
  const base = avg(p.kinerja.slice(0,3));
  return [Math.min(5,parseFloat((base+0.1).toFixed(1))),Math.min(5,parseFloat((base-0.1).toFixed(1))),Math.min(5,parseFloat((base-0.15).toFixed(1))),Math.min(5,parseFloat((base+0.05).toFixed(1)))];
}
function renderEmpPenilaian(p){
  const aspekPost = getAspekScores(p);
  const aspekPre  = getAspekScoresPre(p);
  const standar   = [3.5,3.5,3.0,3.5];
  el('emp-penilaian-breakdown').innerHTML = ASPEK_KINERJA.map((label,i)=>{
    const naik = aspekPost[i]-aspekPre[i];
    const nc = naik>=0.3?'delta-up':naik>=0?'delta-low':'delta-neg';
    return `<div class="penilaian-aspect">
      <div class="penilaian-aspect-label">${label}</div>
      <div class="penilaian-aspect-score">${aspekPost[i].toFixed(1)}<span class="unit">/5</span></div>
      <div class="penilaian-bar"><div class="penilaian-bar-fill" style="width:${(aspekPost[i]/5*100).toFixed(0)}%"></div></div>
      <div class="${nc}" style="font-family:var(--font-mono);font-size:11px;margin-top:5px">${naik>=0?'↑ ':''}${naik>=0?'+':''}${naik.toFixed(1)} vs lalu</div>
    </div>`;
  }).join('');

  destroyChart('empAspek');
  const rdP = chartResponsiveDefaults();
  charts['empAspek'] = new Chart(el('chartEmpAspek').getContext('2d'),{
    type:'bar',
    data:{labels:ASPEK_KINERJA,datasets:[
      {label:'Skor Anda', data:aspekPost, backgroundColor:GOLD, borderWidth:0, barPercentage:0.6},
      {label:'Standar Minimum', data:standar, backgroundColor:'rgba(19,43,80,.2)', borderWidth:0, barPercentage:0.6}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:rdP.legendPos,labels:{usePointStyle:true,pointStyleWidth:10,font:{size:rdP.legendFontSize}}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:rdP.fontSize}}},y:{min:0,max:5,ticks:{stepSize:1,font:{size:rdP.fontSize}},grid:{color:'#eee'}}}}
  });

  const divEmps = SEMUA_PEGAWAI.filter(x=>x.divisi===p.divisi);
  divEmps.sort((a,b)=>avg(b.kinerja.slice(3))-avg(a.kinerja.slice(3)));
  destroyChart('empRank');
  charts['empRank'] = new Chart(el('chartEmpRank').getContext('2d'),{
    type:'bar',
    data:{labels:divEmps.map(x=>x.nama.split(' ')[0]),datasets:[{
      label:'Rata-rata Kinerja', data:divEmps.map(x=>avg(x.kinerja.slice(3))),
      backgroundColor:divEmps.map(x=>x.id===p.id?NAVY:'rgba(164,144,99,.3)'), borderWidth:0, barPercentage:0.7
    }]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'Kinerja: '+c.raw.toFixed(2)}}},
      scales:{x:{min:2,max:5.5,grid:{color:'#eee'},ticks:{font:{size:rdP.fontSize}}},y:{grid:{display:false},ticks:{font:{size:rdP.fontSize}}}}}
  });

  el('emp-penilaian-history').innerHTML = PERIODE_LABELS_ALL.map((periode,qi)=>{
    const base = p.kinerja[qi];
    const scores = [Math.min(5,(base+0.1).toFixed(1)),Math.min(5,(base-0.1).toFixed(1)),Math.min(5,(base-0.2).toFixed(1)),Math.min(5,(base+0.1).toFixed(1))];
    const rataScore = avg(scores.map(Number));
    return `<tr>
      <td style="font-family:var(--font-mono);font-size:11.5px">${periode}${qi===2?' ✦':''}</td>
      ${scores.map(s=>`<td class="mono" style="text-align:center">${s}</td>`).join('')}
      <td class="mono" style="text-align:center;font-weight:600;color:var(--navy)">${rataScore.toFixed(2)}</td>
      <td><span class="badge ${qi>=3?'badge-aktif':'badge-belum'}">${qi>=3?'Post-Training':'Pre-Training'}</span></td>
    </tr>`;
  }).join('');
}

// ── Tren (emp) ────────────────────────────────────
function renderEmpTren(p){
  const preAvg  = avg(p.kinerja.slice(0,3));
  const postAvg = avg(p.kinerja.slice(3));
  const perubahan = postAvg - preAvg;
  const pCls = perubahan>=0.4?'kpi-green':'kpi-warn';
  const pColor = perubahan>=0.4?'var(--green)':perubahan>=0.1?'var(--amber)':'var(--red)';
  el('emp-tren-kpi').innerHTML = `
    <div class="kpi-card kpi-accent">
      <div class="kpi-label">Rata-rata Pre-Training</div>
      <div class="kpi-value">${preAvg.toFixed(2)}</div>
      <div class="kpi-note">Q1–Q3 2024</div>
    </div>
    <div class="kpi-card kpi-green">
      <div class="kpi-label">Rata-rata Post-Training</div>
      <div class="kpi-value">${postAvg.toFixed(2)}</div>
      <div class="kpi-note">Q4 2024–Q2 2025</div>
    </div>
    <div class="kpi-card ${pCls}">
      <div class="kpi-label">Perubahan Kinerja</div>
      <div class="kpi-value" style="color:${pColor}">${perubahan>=0?'+':''}${perubahan.toFixed(2)}</div>
      <div class="kpi-note">${perubahan>=0.4?'↑ Signifikan membaik':perubahan>=0.1?'↗ Sedikit meningkat':'→ Tidak banyak berubah'}</div>
    </div>`;

  const divEmps = SEMUA_PEGAWAI.filter(x=>x.divisi===p.divisi);
  const allAvg  = [0,1,2,3,4,5].map(qi=>parseFloat(avg(SEMUA_PEGAWAI.map(x=>x.kinerja[qi])).toFixed(2)));
  const divAvg  = [0,1,2,3,4,5].map(qi=>parseFloat(avg(divEmps.map(x=>x.kinerja[qi])).toFixed(2)));

  destroyChart('empTrenFull');
  const rdT = chartResponsiveDefaults();
  charts['empTrenFull'] = new Chart(el('chartEmpTrenFull').getContext('2d'),{
    type:'line',
    data:{labels:PERIODE_LABELS_ALL,datasets:[
      {label:p.nama, data:p.kinerja, borderColor:NAVY, backgroundColor:'rgba(19,43,80,.07)', fill:true, borderWidth:rdT.borderWidth, pointRadius:rdT.pointRadius+1, tension:0.35},
      {label:'Rata-rata '+p.divisi, data:divAvg, borderColor:GOLD, borderDash:[5,4], backgroundColor:'transparent', borderWidth:rdT.borderWidth-0.5, pointRadius:rdT.pointRadius, tension:0.35},
      {label:'Rata-rata Program', data:allAvg, borderColor:NAVY_PALE, borderDash:[2,3], backgroundColor:'transparent', borderWidth:rdT.borderWidth-1, pointRadius:Math.max(1,rdT.pointRadius-1), tension:0.35}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},
      scales:{x:{grid:{display:false},ticks:{font:{size:rdT.fontSize}}},y:{min:2,max:5.5,ticks:{stepSize:0.5,font:{size:rdT.fontSize}},grid:{color:'#eee'}}}},
    plugins:[makeVerticalLinePlugin(TRAINING_IDX)]
  });

  destroyChart('empBeforeAfter');
  charts['empBeforeAfter'] = new Chart(el('chartEmpBeforeAfter').getContext('2d'),{
    type:'bar',
    data:{labels:[p.nama.split(' ')[0]+' (Sbl)',p.nama.split(' ')[0]+' (Ssd)',p.divisi+' (Sbl)',p.divisi+' (Ssd)'],
      datasets:[{data:[preAvg, postAvg, avg(divEmps.map(x=>avg(x.kinerja.slice(0,3)))), avg(divEmps.map(x=>avg(x.kinerja.slice(3))))],
        backgroundColor:[NAVY,GOLD,'rgba(19,43,80,.3)','rgba(164,144,99,.4)'], borderWidth:0, barPercentage:0.5}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{grid:{display:false},ticks:{font:{size:rdT.fontSize}}},y:{min:2,max:5.5,ticks:{stepSize:0.5,font:{size:rdT.fontSize}},grid:{color:'#eee'}}}}
  });
}

// ── Rekomendasi (loads from API) ──────────────────
async function renderEmpRekomendasi(p){
  // ML Inference Request
  el('emp-rekomen-banner').innerHTML = `<div style="padding:16px 20px;">Memuat analisis ML...</div>`;
  
  try {
    const mlData = await fetchJSON(`/api/ml/recommend/${encodeURIComponent(p.id)}`);
    
    const bannerColor = 'var(--navy)';
    const bannerText  = `Model Rekomendasi merekomendasikan kategori: <strong>${mlData.label_name}</strong> dengan confidence ${mlData.confidence}%.`;
    el('emp-rekomen-banner').innerHTML = `
      <div style="padding:16px 20px;background:var(--surface);border:1px solid var(--border);border-left:4px solid ${bannerColor}">
        <div style="font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:5px">Analisis Machine Learning untuk ${p.nama} &middot; ${p.jabatan}</div>
        <div style="font-size:13px;color:var(--text-main);line-height:1.6">${bannerText}</div>
      </div>`;

    const courses = mlData.courses;
    el('emp-course-grid').innerHTML = courses.map(c=>`
      <div class="course-card course-recommended">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
          <span class="badge badge-recommended">Rekomendasi ML</span>
          <span style="font-size:10px;color:var(--text-muted)">${c.mode}</span>
        </div>
        <div class="course-title">${c.nama_course}</div>
        <div class="course-provider">${c.provider} &middot; ${c.level}</div>
        <div class="course-tags"><span class="course-tag">${c.skill_target_utama}</span></div>
        <div class="course-reason">${c.deskripsi}</div>
        <div class="course-meta" style="margin-top:10px;font-size:11px;color:var(--text-muted)">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" style="vertical-align:middle;margin-right:4px"><circle cx="6" cy="6" r="5"/><path d="M6 3v3l2 1.5"/></svg>
          ${c.durasi}
        </div>
      </div>`).join('');

    el('emp-career-path-body').innerHTML = courses.map((c, i) => `
      <tr>
        <td>Tahap ${i+1}</td>
        <td>${c.skill_target_utama}</td>
        <td>${c.nama_course}<br><small style="color:var(--text-muted)">${c.provider}</small></td>
        <td>${c.durasi}</td>
        <td>${i === 0 ? '<span class="badge badge-aktif" style="background:#5ba69b;color:white;border:none">Tinggi</span>' : '<span class="badge badge-belum" style="background:#ddd;color:#555;border:none">Menengah</span>'}</td>
      </tr>
    `).join('');
  } catch(e) {
    el('emp-rekomen-banner').innerHTML = `<div style="color:var(--red);">Gagal memuat rekomendasi ML. Error: ${e}</div>`;
  }
}
// ════════════════════════════════════════════════════
//  ADMIN PANEL FUNCTIONS
// ════════════════════════════════════════════════════
async function loadUsers() {
  try {
    const res = await fetch('/api/admin/users');
    const data = await res.json();
    const tbody = document.querySelector('#table-users tbody');
    tbody.innerHTML = data.map(u => `
      <tr>
        <td>${u.id}</td>
        <td>${u.email}</td>
        <td>${u.nama}</td>
        <td>
          <select onchange="changeRole(${u.id}, this.value)" class="form-control" style="width: auto; display: inline-block;">
            <option value="pegawai" ${u.role === 'pegawai' ? 'selected' : ''}>Pegawai</option>
            <option value="manager" ${u.role === 'manager' ? 'selected' : ''}>Manager</option>
            <option value="supadmin" ${u.role === 'supadmin' ? 'selected' : ''}>SupAdmin</option>
          </select>
        </td>
        <td>${u.pegawai_id || '-'}</td>
        <td>
          <button class="btn btn-danger" style="padding:4px 8px;font-size:12px" onclick="deleteUser(${u.id})">Hapus</button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Error loading users:', e);
  }
}

async function changeRole(userId, newRole) {
  if(!confirm('Anda yakin ingin mengubah role user ini?')) return loadUsers();
  try {
    const res = await fetch('/api/admin/users/'+userId+'/role', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({role: newRole})
    });
    if(res.ok) {
      alert('Role berhasil diubah!');
      loadUsers();
    } else {
      alert('Gagal mengubah role');
      loadUsers();
    }
  } catch (e) {
    console.error(e);
    alert('Terjadi kesalahan');
    loadUsers();
  }
}

async function deleteUser(userId) {
  if(!confirm('Hapus user ini?')) return;
  alert('Fitur hapus user belum diimplementasikan di backend, namun UI sudah siap.');
}

async function loadAdminPegawai() {
  const tbody = document.querySelector('#table-pegawai-admin tbody');
  tbody.innerHTML = SEMUA_PEGAWAI.map(p => `
    <tr>
      <td>${p.id}</td>
      <td>${p.nama}</td>
      <td>${p.jabatan}</td>
      <td>${p.divisi}</td>
      <td><span class="badge ${p.status==='Aktif'?'badge-aktif':p.status==='Belum'?'badge-belum':'badge-expired'}">${p.status}</span></td>
      <td>${p.preScore} / ${p.postScore}</td>
      <td>${p.label_rekomendasi || '-'}</td>
      <td>${p.label_tindakan || '-'}</td>
    </tr>
  `).join('');
}

async function loadAdminCourses() {
  try {
    const res = await fetch('/api/courses');
    const data = await res.json();
    const tbody = document.querySelector('#table-courses-admin tbody');
    tbody.innerHTML = data.map(c => `
      <tr>
        <td>${c.id}</td>
        <td>${c.nama_course}</td>
        <td>${c.provider}</td>
        <td>${c.level}</td>
        <td>${c.durasi}</td>
        <td><span class="course-tag">${c.skill_target_utama}</span></td>
      </tr>
    `).join('');
  } catch(e) {
    console.error(e);
  }
}
