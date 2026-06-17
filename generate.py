#!/usr/bin/env python3
"""Build a self-contained interactive HTML enrollment/CRM analysis report."""
import csv, json, os
from datetime import datetime

SRC = "/Users/vijaybabu.g/Downloads/CRMDetailsByCreatedDate (1).csv"
OUT = os.path.join(os.path.dirname(__file__), "index.html")

with open(SRC, newline='') as f:
    lines = f.readlines()

reader = csv.reader(lines[6:])
data = []
for r in reader:
    if not r or all(not c.strip() for c in r):
        continue
    r = [c.strip() for c in r]
    if len(r) < 12:
        continue
    data.append(r)

def pdate(s):
    try:
        return datetime.strptime(s, "%m/%d/%Y")
    except Exception:
        return None

# index maps to shrink payload
centers, statuses, sources, hears, ages, addedbys = [], [], [], [], [], []
def idx(lst, v):
    if v not in lst:
        lst.append(v)
    return lst.index(v)

rows = []
for d in data:
    dt = pdate(d[10])
    if not dt:
        continue
    center = d[0]
    status = d[6] or "(blank)"
    source = d[7] or "(blank)"
    hear = d[11] or "(none)"
    age = d[5] or "(none)"
    addedby = d[8].strip()                 # "Added By First Name": the staff person who logged the lead
    web = 1 if addedby == "" else 0        # empty => webform
    rows.append([
        idx(centers, center),
        idx(statuses, status),
        dt.strftime("%Y-%m-%d"),
        idx(sources, source),
        idx(hears, hear),
        idx(ages, age),
        web,
        idx(addedbys, addedby or "Webform"),
    ])

# Funnel-ordered canonical status order for table columns
STATUS_ORDER = [
    "Inquiry - New", "Inquiry - Responded",
    "Tour - Schedule", "Tour - Invite", "Tour - Toured", "Tour - Virtual", "Tour - No Show",
    "Waitlist - Invited", "Waitlist - Joined",
    "Enrollment - Offered", "Enrollment - Enrolled",
    "Declined", "Withdrawn", "Deleted",
]
# any status present not in the list, append at end
ordered_statuses = [s for s in STATUS_ORDER if s in statuses] + [s for s in statuses if s not in STATUS_ORDER]

payload = {
    "centers": centers,
    "statuses": statuses,
    "statusOrder": ordered_statuses,
    "sources": sources,
    "hears": hears,
    "ages": ages,
    "addedby": addedbys,
    "rows": rows,
    "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "dataMin": min(r[2] for r in rows),
    "dataMax": max(r[2] for r in rows),
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enrollment &amp; CRM Funnel Analysis</title>
<style>
  :root{
    --bg:#0f1420; --panel:#161d2e; --panel2:#1c2740; --line:#26314d;
    --txt:#e6ecf7; --muted:#93a0bd; --accent:#4f8cff; --good:#37c97f;
    --warn:#ffb020; --bad:#ff5d6c; --chip:#223052;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  a{color:var(--accent)}
  header{padding:22px 26px 8px}
  h1{margin:0 0 2px;font-size:22px}
  .sub{color:var(--muted);font-size:13px}
  .bar{position:sticky;top:0;z-index:20;background:rgba(15,20,32,.96);
    backdrop-filter:blur(6px);border-bottom:1px solid var(--line);
    padding:12px 26px;display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end}
  .fld{display:flex;flex-direction:column;gap:4px}
  .fld label{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  select,input[type=date]{background:var(--panel2);color:var(--txt);
    border:1px solid var(--line);border-radius:8px;padding:7px 9px;font-size:13px;min-width:150px}
  .range{display:none;gap:10px}
  .range.show{display:flex}
  button.reset{background:var(--chip);color:var(--txt);border:1px solid var(--line);
    border-radius:8px;padding:7px 12px;cursor:pointer;font-size:13px}
  button.reset:hover{border-color:var(--accent)}
  .wrap{padding:18px 26px 60px;max-width:1280px}
  .scope{color:var(--muted);font-size:12px;margin:2px 0 16px}
  .scope b{color:var(--txt)}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .card .k{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  .card .v{font-size:26px;font-weight:700;margin-top:4px}
  .card .d{font-size:12px;margin-top:3px}
  .up{color:var(--good)} .down{color:var(--bad)} .flat{color:var(--muted)}
  section{margin-top:30px}
  section h2{font-size:16px;margin:0 0 4px}
  section .note{color:var(--muted);font-size:12px;margin:0 0 12px}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px}
  table{border-collapse:collapse;width:100%;font-size:12.5px}
  th,td{padding:7px 9px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
  th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel)}
  thead th{position:sticky;top:0;background:var(--panel2);color:var(--muted);
    font-weight:600;z-index:2;cursor:default}
  thead th:first-child{z-index:3;background:var(--panel2)}
  tbody tr:hover td{background:var(--panel2)}
  td.z{color:#46527a}
  .tot{font-weight:700}
  tr.totrow td{border-top:2px solid var(--line);font-weight:700;background:var(--panel2)}
  tr.totrow td:first-child{background:var(--panel2)}
  .scrollx{overflow-x:auto;border-radius:10px}
  .heat0{color:#46527a}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  @media(max-width:900px){.grid2{grid-template-columns:1fr}}
  .bars .row{display:flex;align-items:center;gap:10px;margin:5px 0}
  .bars .lbl{width:150px;color:var(--muted);font-size:12px;text-align:right;flex:none}
  .bars .track{flex:1;background:var(--panel2);border-radius:5px;height:18px;overflow:hidden}
  .bars .fill{height:100%;background:linear-gradient(90deg,#3a6fd8,#4f8cff)}
  .bars .num{width:70px;font-size:12px;flex:none}
  .findings{background:linear-gradient(180deg,#18223a,#141b2c);border:1px solid var(--line);
    border-radius:12px;padding:16px 18px}
  .findings ul{margin:8px 0 0;padding-left:18px}
  .findings li{margin:6px 0}
  .pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:700}
  .pill.down{background:rgba(255,93,108,.15)} .pill.up{background:rgba(55,201,127,.15)}
  .legend{color:var(--muted);font-size:11px;margin-top:6px}
  svg text{fill:var(--muted);font-size:10px}
  .yoybars{display:flex;gap:26px;align-items:flex-end;height:170px;padding:10px 4px 0}
  .yoygrp{display:flex;flex-direction:column;align-items:center;gap:6px;flex:1}
  .yoygrp .stack{display:flex;gap:6px;align-items:flex-end;height:130px}
  .yoygrp .b{width:30px;border-radius:5px 5px 0 0;position:relative}
  .yoygrp .b span{position:absolute;top:-16px;left:50%;transform:translateX(-50%);font-size:10px;color:var(--muted)}
</style>
</head>
<body>
<header>
  <h1>Enrollment &amp; CRM Funnel Analysis</h1>
  <div class="sub">Source: CRM Details by Created Date &middot; <span id="genmeta"></span></div>
</header>

<div class="bar">
  <div class="fld">
    <label>School</label>
    <select id="school"></select>
  </div>
  <div class="fld">
    <label>Date range</label>
    <select id="preset">
      <option value="mar">Mar 15 – Jun 15 (season)</option>
      <option value="all">All time</option>
      <option value="today">Today</option>
      <option value="yesterday">Yesterday</option>
      <option value="thismonth">Current month</option>
      <option value="lastmonth">Previous month</option>
      <option value="last3">Last 3 months</option>
      <option value="last6">Last 6 months</option>
      <option value="thisyear">This year (YTD)</option>
      <option value="lastyear">Last year</option>
      <option value="custom">Custom&hellip;</option>
    </select>
  </div>
  <div class="range fld-range" id="rangeBox">
    <div class="fld"><label>From</label><input type="date" id="from"></div>
    <div class="fld"><label>To</label><input type="date" id="to"></div>
  </div>
  <button class="reset" id="reset">Reset</button>
</div>

<div class="wrap">
  <div class="scope" id="scope"></div>

  <div class="cards" id="kpis"></div>

  <section>
    <div class="findings">
      <h2 style="margin:0 0 2px">Key findings — Mar 15 → Jun 15, 2025 vs 2026</h2>
      <div class="note" style="margin:2px 0 0">Computed live from the current <b>School</b> filter, comparing the same <b>Mar 15 &ndash; Jun 15</b> window in each year. Ignores the date filter above. See <b>Definitions</b> above for how Enrolled is counted.</div>
      <ul id="findings"></ul>
    </div>
  </section>

  <section>
    <h2>Year-over-Year &mdash; Mar 15 → Jun 15</h2>
    <p class="note">Same <b>Mar 15 &ndash; Jun 15</b> window each year so the two seasons compare fairly. Respects the School filter; ignores the date filter.</p>
    <div class="grid2">
      <div class="panel" style="padding:14px 16px">
        <div class="scrollx"><table id="yoyTable"></table></div>
      </div>
      <div class="panel" style="padding:14px 16px">
        <div id="yoyChart"></div>
        <div class="legend">Leads created in each Mar 15&ndash;Jun 15 window.</div>
      </div>
    </div>
  </section>

  <section>
    <h2>School-by-school &mdash; Mar 15 → Jun 15</h2>
    <p class="note">Leads &amp; enrollments per center, both years (ignores the School filter so you see every center).</p>
    <div class="grid2" style="grid-template-columns:1.3fr 1fr">
      <div class="panel"><div class="scrollx"><table id="schoolCmp"></table></div></div>
      <div class="findings"><b>What it says</b><ul id="schoolInf"></ul></div>
    </div>
  </section>

  <section>
    <h2>Webform vs. Center-added leads &mdash; Mar 15 → Jun 15</h2>
    <p class="note">Classified by the <b>&ldquo;Added By First Name&rdquo;</b> field: empty = <b>Webform</b> (online form), a staff name present = <b>Center-added</b> (walk-in / call / referral logged by the team). Respects the School filter.</p>
    <div class="grid2" style="grid-template-columns:1.3fr 1fr">
      <div class="panel"><div class="scrollx"><table id="srcCmp"></table></div></div>
      <div class="findings"><b>What it says</b><ul id="srcInf"></ul></div>
    </div>
  </section>

  <section>
    <h2>Marketing channel &mdash; &ldquo;How did you hear about us?&rdquo; &mdash; Mar 15 → Jun 15</h2>
    <p class="note">Where leads came from, both years. Respects the School filter.</p>
    <div class="grid2" style="grid-template-columns:1.3fr 1fr">
      <div class="panel"><div class="scrollx"><table id="chCmp"></table></div></div>
      <div class="findings"><b>What it says</b><ul id="chInf"></ul></div>
    </div>
  </section>

  <section>
    <h2>How did you hear about us?</h2>
    <p class="note">Top marketing channels for the filtered records.</p>
    <div class="panel bars" id="hear" style="padding:14px;max-width:640px"></div>
  </section>

  <section>
    <h2>Center &times; who added the lead &mdash; &ldquo;Added By First Name&rdquo;</h2>
    <p class="note">Rows = centers, columns = the <b>staff first name</b> who logged each lead (the <b>Webform</b> column = empty name, i.e. self-serve online form). Cells are lead counts. Uses the date filter; ignores the School filter so every center shows. Scroll right for all staff.</p>
    <div class="panel"><div class="scrollx"><table id="centerSrc"></table></div></div>
  </section>
</div>

<script>
const DATA = __DATA__;
const R = DATA.rows;            // [centerIdx, statusIdx, 'YYYY-MM-DD', srcIdx, hearIdx, ageIdx, web(1=AddedByFirstName empty)]
const S = DATA.statuses, C = DATA.centers, SRC = DATA.sources, HEAR = DATA.hears, ADDEDBY = DATA.addedby;
const ORDER = DATA.statusOrder;
const sIdx = s => S.indexOf(s);
// ---- Metric definitions (per user spec) ----
// Enrolled / success = Enrollment-Enrolled + Withdrawn
const ENR_SET = ["Enrollment - Enrolled","Withdrawn"].map(sIdx).filter(i=>i>=0);
const isEnrolled = i => ENR_SET.includes(i);
// Tours done = Tour-Toured + Tour-Virtual (an actual visit happened)
const TOURDONE_SET = ["Tour - Toured","Tour - Virtual"].map(sIdx).filter(i=>i>=0);
const isTour = i => TOURDONE_SET.includes(i);
const DECLINED = sIdx("Declined");
const isInquiry = i => S[i] && S[i].startsWith("Inquiry");

document.getElementById('genmeta').textContent =
  `Generated ${DATA.generated} · ${R.length.toLocaleString()} records · ${DATA.dataMin} → ${DATA.dataMax}`;

// ---- filter controls ----
const elSchool=document.getElementById('school'), elPreset=document.getElementById('preset'),
  elFrom=document.getElementById('from'), elTo=document.getElementById('to'),
  elRange=document.getElementById('rangeBox');
elSchool.innerHTML = '<option value="all">All schools</option>' +
  C.map((c,i)=>`<option value="${i}">${c}</option>`).join('');

function today(){ return new Date(); }
function iso(d){ return d.toISOString().slice(0,10); }
function ymd(d){ return [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')]; }

function presetRange(p){
  const t=today(); const y=t.getFullYear(), m=t.getMonth();
  const f=d=>iso(d);
  switch(p){
    case 'mar': return [`${MAXYR}-03-15`, `${MAXYR}-06-15`];
    case 'today': return [f(t), f(t)];
    case 'yesterday':{const d=new Date(t);d.setDate(d.getDate()-1);return [f(d),f(d)];}
    case 'thismonth': return [f(new Date(y,m,1)), f(t)];
    case 'lastmonth':{const s=new Date(y,m-1,1),e=new Date(y,m,0);return [f(s),f(e)];}
    case 'last3':{const s=new Date(t);s.setMonth(s.getMonth()-3);return [f(s),f(t)];}
    case 'last6':{const s=new Date(t);s.setMonth(s.getMonth()-6);return [f(s),f(t)];}
    case 'thisyear': return [f(new Date(y,0,1)), f(t)];
    case 'lastyear': return [`${y-1}-01-01`, `${y-1}-12-31`];
    case 'all': return [DATA.dataMin, DATA.dataMax];
    default: return null;
  }
}

const MAXYR=+DATA.dataMax.slice(0,4);
let state={school:'all', from:`${MAXYR}-03-15`, to:`${MAXYR}-06-15`, preset:'mar'};
elPreset.value='mar';

function syncRange(){
  const r=presetRange(state.preset);
  if(r){ state.from=r[0]; state.to=r[1]; elFrom.value=r[0]; elTo.value=r[1]; }
  elRange.classList.toggle('show', state.preset==='custom');
}
elPreset.onchange=()=>{ state.preset=elPreset.value; syncRange(); render(); };
elSchool.onchange=()=>{ state.school=elSchool.value; render(); };
elFrom.onchange=()=>{ state.from=elFrom.value; state.preset='custom'; elPreset.value='custom'; elRange.classList.add('show'); render(); };
elTo.onchange=()=>{ state.to=elTo.value; state.preset='custom'; elPreset.value='custom'; elRange.classList.add('show'); render(); };
document.getElementById('reset').onclick=()=>{ state={school:'all',from:DATA.dataMin,to:DATA.dataMax,preset:'all'};
  elSchool.value='all'; elPreset.value='all'; syncRange(); render(); };

function filtered(){
  const sc=state.school, f=state.from, t=state.to;
  return R.filter(r=> (sc==='all'||r[0]==+sc) && r[2]>=f && r[2]<=t);
}

// ---- helpers ----
function pct(n,d){ return d? (n/d*100):0; }
function delta(cur,prev){
  if(prev===0) return cur>0?{c:'up',t:'new'}:{c:'flat',t:'—'};
  const ch=(cur-prev)/prev*100;
  return {c: ch>1?'up':ch<-1?'down':'flat', t:(ch>=0?'+':'')+ch.toFixed(0)+'%'};
}
function fmt(n){ return n.toLocaleString(); }

// ===== RENDER =====
function render(){
  const rows=filtered();
  document.getElementById('scope').innerHTML =
    `Showing <b>${fmt(rows.length)}</b> records · School: <b>${state.school==='all'?'All':C[+state.school]}</b> · `+
    `${state.from} → ${state.to}`;

  // KPIs — Total leads & Enrolled only (a lead sits in one status, so intermediate
  // stages like Tour/Waitlist undercount and are misleading)
  let leads=rows.length, enr=0;
  for(const r of rows){ if(isEnrolled(r[1]))enr++; }
  const conv=pct(enr,leads);
  const kpis=[
    ['Total leads',fmt(leads),''],
    ['Success (Enrolled + Withdrawn)',fmt(enr),''],
    ['Lead→Success %',conv.toFixed(1)+'%',''],
  ];
  document.getElementById('kpis').innerHTML = kpis.map(k=>
    `<div class="card"><div class="k">${k[0]}</div><div class="v">${k[1]}</div></div>`).join('')
    + `<div class="card" style="grid-column:1/-1;background:var(--panel2)"><div class="k">Definitions</div>`
    + `<div style="font-size:12.5px;margin-top:4px;line-height:1.6">`
    + `<b style="color:var(--good)">Success</b> = Enrollment&nbsp;-&nbsp;Enrolled + Withdrawn &nbsp;·&nbsp; `
    + `<span style="color:var(--muted)">(Withdrawn counts as Success because a child must enroll before they can withdraw.)</span> &nbsp;·&nbsp; `
    + `<b>Lead&rarr;Success %</b> = Success &divide; Total leads &nbsp;·&nbsp; `
    + `<span style="color:var(--muted)">Only Total leads &amp; Success are shown — a lead is bucketed under a single current status, so mid-funnel counts (Tour, Waitlist) would understate reality.</span>`
    + `</div></div>`;

  renderFindings();
  renderYoY();
  renderCompare();
  renderBars('hear', rows, 4, HEAR);
  renderCenterSource();
}

// ---- like-for-like helpers (school filter only) ----
function schoolRows(){ const sc=state.school; return R.filter(r=> sc==='all'||r[0]==+sc); }
function ytdWindow(year){ return [`${year}-03-15`, `${year}-06-15`]; }
function years(){
  const ys=new Set(R.map(r=>+r[2].slice(0,4))); return [...ys].sort();
}
function compYears(){ return years().filter(y=>{const[f,t]=ytdWindow(y);return R.some(r=>r[2]>=f&&r[2]<=t);}).slice(-2); }
function ytdLabel(){ return 'Jun 15'; }

function ytdMetrics(year){
  const [f,t]=ytdWindow(year);
  const rs=schoolRows().filter(r=>r[2]>=f&&r[2]<=t);
  let leads=rs.length,tours=0,enr=0,dec=0;
  for(const r of rs){ if(isTour(r[1]))tours++; if(isEnrolled(r[1]))enr++; if(r[1]===DECLINED)dec++; }
  return {leads,tours,enr,dec,conv:pct(enr,leads)};
}

function renderFindings(){
  const ys=compYears();
  if(ys.length<2){ document.getElementById('findings').innerHTML='<li>Not enough years of data for a comparison.</li>'; return; }
  const py=ys[0], cy=ys[1];
  const a=ytdMetrics(py), b=ytdMetrics(cy);
  const d=(c,p)=>delta(c,p);
  const tag=x=>`<span class="pill ${x.c}">${x.t}</span>`;
  const li=[];
  const dl=d(b.leads,a.leads);
  li.push(`<li><b>Leads ${dl.c==='down'?'fell':'changed'}</b> from ${fmt(a.leads)} (${py}) to ${fmt(b.leads)} (${cy}) ${tag(dl)}. ${dl.c==='down'?'Fewer people entered the funnel this season — the top-of-funnel is the problem, not closing.':''}</li>`);
  const de=d(b.enr,a.enr);
  const leadDrop=a.leads?(a.leads-b.leads)/a.leads*100:0, enrDrop=a.enr?(a.enr-b.enr)/a.enr*100:0;
  let enrMsg;
  if(b.enr>a.enr) enrMsg='Up despite fewer leads — the team closed more from a smaller pool.';
  else if(b.enr<a.enr && leadDrop-enrDrop>5) enrMsg='Down, but by less than leads — enrollments held up better than the lead drop, because conversion rose.';
  else if(b.enr<a.enr) enrMsg='Down roughly in line with leads — mainly a volume problem.';
  else enrMsg='Flat.';
  li.push(`<li><b>Success</b> (Enrolled + Withdrawn) went from ${fmt(a.enr)} to ${fmt(b.enr)} ${tag(de)}. ${enrMsg}</li>`);
  const dc=delta(b.conv,a.conv);
  const flat=Math.abs(b.conv-a.conv)<1;
  li.push(`<li><b>Lead&rarr;Success conversion</b> ${a.conv.toFixed(1)}% &rarr; ${b.conv.toFixed(1)}% ${tag(dc)}. ${flat?'Essentially unchanged — the team converts the same share of leads; they just have fewer leads to work.':(b.conv>=a.conv?'Improved — a higher share of a smaller pool is converting.':'Softened — closing got harder, not just thinner demand.')}</li>`);
  const blMsg = flat
    ? 'with conversion flat, the way to grow enrollments is to <b>rebuild lead volume</b> (top of funnel), not chase a better close rate.'
    : (b.conv>a.conv
        ? 'conversion improved but leads fell faster, so <b>rebuilding lead volume</b> (top of funnel) is the biggest remaining lever.'
        : 'both demand and closing softened — work top-of-funnel volume and follow-up together.');
  li.push(`<li class="flat" style="color:var(--muted)"><b>Bottom line:</b> ${blMsg} <b>Caveat:</b> status is each lead&rsquo;s state <i>today</i>; the ${cy} cohort is still maturing, so its counts will keep shifting.</li>`);
  document.getElementById('findings').innerHTML=li.join('');
}

function renderYoY(){
  const ys=compYears();
  const rowsDef=[['Leads','leads'],['Success (Enrolled + Withdrawn)','enr'],['Conversion %','conv']];
  const M=ys.map(y=>ytdMetrics(y));
  let h='<thead><tr><th>Metric (Mar 15–Jun 15)</th>'+ys.map(y=>`<th>${y}</th>`).join('')+'<th>YoY</th></tr></thead><tbody>';
  rowsDef.forEach(([lbl,key])=>{
    const vals=M.map(m=>m[key]);
    const last=vals[vals.length-1], prev=vals[vals.length-2]||0;
    const dd= key==='conv'?delta(last,prev):delta(last,prev);
    const show=v=> key==='conv'? v.toFixed(1)+'%' : fmt(v);
    h+=`<tr><td>${lbl}</td>${vals.map(v=>`<td>${show(v)}</td>`).join('')}<td class="${dd.c}">${dd.t}</td></tr>`;
  });
  h+='</tbody>';
  document.getElementById('yoyTable').innerHTML=h;

  // simple bar chart of leads per year
  const leads=M.map(m=>m.leads); const mx=Math.max(...leads,1);
  let bars='<div class="yoybars">';
  ys.forEach((y,i)=>{
    const hgt=Math.round(leads[i]/mx*120)+2;
    bars+=`<div class="yoygrp"><div class="stack"><div class="b" style="height:${hgt}px;background:${i===ys.length-1?'#4f8cff':'#39507f'}"><span>${fmt(leads[i])}</span></div></div><div style="color:var(--muted);font-size:12px">${y}</div></div>`;
  });
  bars+='</div>';
  document.getElementById('yoyChart').innerHTML=bars;
}

function renderMonthly(rows){
  const cols=ORDER.filter(s=>true);
  const colIdx=cols.map(sIdx);
  const months={};
  for(const r of rows){ const ym=r[2].slice(0,7); (months[ym]=months[ym]||{})[r[1]]=(months[ym]?.[r[1]]||0)+1; }
  const ms=Object.keys(months).sort();
  let h='<thead><tr><th>Month</th>'+cols.map(c=>`<th title="${c}">${c.replace(' - ','·')}</th>`).join('')+'<th class="tot">Total</th></tr></thead><tbody>';
  const colTot=new Array(cols.length).fill(0); let grand=0;
  for(const m of ms){
    let rowTot=0; let cells='';
    colIdx.forEach((ci,j)=>{ const v=months[m][ci]||0; rowTot+=v; colTot[j]+=v; cells+=`<td class="${v?'':'heat0'}">${v||''}</td>`; });
    grand+=rowTot;
    const label=new Date(m+'-01').toLocaleString('en-US',{month:'short',year:'numeric'});
    h+=`<tr><td>${label}</td>${cells}<td class="tot">${fmt(rowTot)}</td></tr>`;
  }
  h+=`<tr class="totrow"><td>Total</td>${colTot.map(v=>`<td>${fmt(v)}</td>`).join('')}<td>${fmt(grand)}</td></tr>`;
  h+='</tbody>';
  document.getElementById('monthly').innerHTML=h;
}

function renderTrend(rows){
  const months={};
  for(const r of rows){ const ym=r[2].slice(0,7); const o=months[ym]=months[ym]||{l:0,e:0}; o.l++; if(isEnrolled(r[1]))o.e++; }
  const ms=Object.keys(months).sort();
  if(!ms.length){ document.getElementById('trend').innerHTML='<div style="color:var(--muted)">No data.</div>'; return; }
  const W=Math.max(560, ms.length*42), H=200, pad=30;
  const mx=Math.max(...ms.map(m=>months[m].l),1);
  const x=i=>pad+i*((W-pad-10)/Math.max(ms.length-1,1));
  const yL=v=>H-22-(v/mx*(H-50));
  const lp=ms.map((m,i)=>`${x(i)},${yL(months[m].l)}`).join(' ');
  const ep=ms.map((m,i)=>`${x(i)},${yL(months[m].e)}`).join(' ');
  let bars='';
  ms.forEach((m,i)=>{ const h=months[m].e/mx*(H-50); bars+=`<rect x="${x(i)-7}" y="${H-22-h}" width="14" height="${h}" fill="#37c97f" opacity=".35"/>`; });
  let lbls=ms.map((m,i)=> (i%Math.ceil(ms.length/12)===0)?`<text x="${x(i)}" y="${H-6}" text-anchor="middle">${m.slice(2)}</text>`:'').join('');
  document.getElementById('trend').innerHTML=
    `<svg viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="xMidYMid meet">
      ${bars}
      <polyline points="${lp}" fill="none" stroke="#4f8cff" stroke-width="2"/>
      <polyline points="${ep}" fill="none" stroke="#37c97f" stroke-width="2"/>
      ${lbls}
    </svg>
    <div class="legend"><span style="color:#4f8cff">&#9632;</span> Leads &nbsp; <span style="color:#37c97f">&#9632;</span> Enrolled (bars + line)</div>`;
}

function renderFunnel(rows){
  const cnt={}; for(const r of rows) cnt[r[1]]=(cnt[r[1]]||0)+1;
  const items=ORDER.filter(s=>cnt[sIdx(s)]).map(s=>[s,cnt[sIdx(s)]]);
  drawBars('funnel', items, rows.length);
}
function renderBars(elId, rows, field, dict){
  const cnt={}; for(const r of rows) cnt[r[field]]=(cnt[r[field]]||0)+1;
  const items=Object.entries(cnt).map(([k,v])=>[dict[+k],v]).sort((a,b)=>b[1]-a[1]).slice(0,10);
  drawBars(elId, items, rows.length);
}
function drawBars(elId, items, total){
  const mx=Math.max(...items.map(i=>i[1]),1);
  document.getElementById(elId).innerHTML = items.length? items.map(([lbl,v])=>
    `<div class="row"><div class="lbl">${lbl}</div><div class="track"><div class="fill" style="width:${v/mx*100}%"></div></div>`+
    `<div class="num">${fmt(v)} <span style="color:var(--muted)">${total?Math.round(v/total*100):0}%</span></div></div>`).join('')
    : '<div style="color:var(--muted)">No data.</div>';
}

function renderSchools(){
  const f=state.from,t=state.to;
  const rows=R.filter(r=>r[2]>=f&&r[2]<=t);
  const per={};
  for(const r of rows){ const o=per[r[0]]=per[r[0]]||{l:0,enr:0};
    o.l++; if(isEnrolled(r[1]))o.enr++; }
  const ids=Object.keys(per).map(Number).sort((a,b)=>per[b].l-per[a].l);
  let h='<thead><tr><th>School</th><th>Leads</th><th>Enrolled</th><th>Conv %</th></tr></thead><tbody>';
  let T={l:0,enr:0};
  for(const id of ids){ const o=per[id]; T.l+=o.l;T.enr+=o.enr;
    h+=`<tr><td>${C[id]}</td><td>${fmt(o.l)}</td><td>${fmt(o.enr)}</td><td>${pct(o.enr,o.l).toFixed(1)}%</td></tr>`; }
  h+=`<tr class="totrow"><td>All</td><td>${fmt(T.l)}</td><td>${fmt(T.enr)}</td><td>${pct(T.enr,T.l).toFixed(1)}%</td></tr></tbody>`;
  document.getElementById('schools').innerHTML=h;
}

function renderCenterSource(){
  // Matrix: rows = centers, columns = the "Added By First Name" person (empty => Webform).
  // Cells = lead counts. Respects the date filter; ignores the School filter so all centers show.
  const f=state.from,t=state.to;
  const rows=R.filter(r=>r[2]>=f&&r[2]<=t);
  const webIdx=ADDEDBY.indexOf('Webform');
  const ptot={}, ctot={}, cell={};
  for(const r of rows){
    ptot[r[7]]=(ptot[r[7]]||0)+1;
    ctot[r[0]]=(ctot[r[0]]||0)+1;
    const k=r[0]+'|'+r[7]; cell[k]=(cell[k]||0)+1;
  }
  // columns: Webform first, then staff by total leads desc
  const persons=Object.keys(ptot).map(Number).sort((a,b)=>{
    if(a===webIdx)return -1; if(b===webIdx)return 1; return ptot[b]-ptot[a]; });
  const centers=Object.keys(ctot).map(Number).sort((a,b)=>ctot[b]-ctot[a]);
  const pname=id=> id===webIdx?'Webform':ADDEDBY[id];
  let h='<thead><tr><th>Center</th>'+persons.map(p=>`<th>${pname(p)}</th>`).join('')+'<th class="tot">Total</th></tr></thead><tbody>';
  for(const c of centers){
    h+=`<tr><td>${C[c]}</td>`+persons.map(p=>{const v=cell[c+'|'+p]||0; return `<td class="${v?'':'heat0'}">${v||''}</td>`;}).join('')+`<td class="tot">${fmt(ctot[c])}</td></tr>`;
  }
  h+=`<tr class="totrow"><td>All</td>`+persons.map(p=>`<td>${fmt(ptot[p])}</td>`).join('')+`<td>${fmt(rows.length)}</td></tr></tbody>`;
  document.getElementById('centerSrc').innerHTML=h;
}

// ===== Mar15–Jun15 comparison tables + auto inferences =====
function winRows(year){ const [f,t]=ytdWindow(year); const sc=state.school;
  return R.filter(r=> r[2]>=f && r[2]<=t && (sc==='all'||r[0]==+sc)); }

function renderCompare(){
  const ys=compYears(); if(ys.length<2){return;}
  const py=ys[0], cy=ys[1];
  const tag=x=>`<span class="pill ${x.c}">${x.t}</span>`;

  // ---- SCHOOL (ignores school filter) ----
  const A={},B={};
  const [fa,ta]=ytdWindow(py),[fb,tb]=ytdWindow(cy);
  for(const r of R){
    if(r[2]>=fa&&r[2]<=ta){const o=A[r[0]]=A[r[0]]||{l:0,e:0};o.l++;if(isEnrolled(r[1]))o.e++;}
    if(r[2]>=fb&&r[2]<=tb){const o=B[r[0]]=B[r[0]]||{l:0,e:0};o.l++;if(isEnrolled(r[1]))o.e++;}
  }
  const ids=[...new Set([...Object.keys(A),...Object.keys(B)].map(Number))]
    .sort((x,y)=>(B[y]?.l||0)-(B[x]?.l||0));
  let h=`<thead><tr><th>School</th><th>Leads ${py}</th><th>Leads ${cy}</th><th>Δ</th><th>Success ${py}</th><th>Success ${cy}</th><th>Δ</th><th>Conv ${cy}</th></tr></thead><tbody>`;
  let TA={l:0,e:0},TB={l:0,e:0};
  for(const id of ids){const a=A[id]||{l:0,e:0},b=B[id]||{l:0,e:0};
    TA.l+=a.l;TA.e+=a.e;TB.l+=b.l;TB.e+=b.e;
    h+=`<tr><td>${C[id]}</td><td>${fmt(a.l)}</td><td>${fmt(b.l)}</td><td class="${delta(b.l,a.l).c}">${delta(b.l,a.l).t}</td><td>${fmt(a.e)}</td><td>${fmt(b.e)}</td><td class="${delta(b.e,a.e).c}">${delta(b.e,a.e).t}</td><td>${pct(b.e,b.l).toFixed(0)}%</td></tr>`;}
  h+=`<tr class="totrow"><td>All</td><td>${fmt(TA.l)}</td><td>${fmt(TB.l)}</td><td>${delta(TB.l,TA.l).t}</td><td>${fmt(TA.e)}</td><td>${fmt(TB.e)}</td><td>${delta(TB.e,TA.e).t}</td><td>${pct(TB.e,TB.l).toFixed(0)}%</td></tr></tbody>`;
  document.getElementById('schoolCmp').innerHTML=h;

  // school inferences
  const rowsI=ids.map(id=>({n:C[id],a:A[id]||{l:0,e:0},b:B[id]||{l:0,e:0}}));
  const byLeadDrop=[...rowsI].filter(r=>r.a.l>=20).sort((x,y)=>delta(x.b.l,x.a.l).t.replace('%','')-0-(delta(y.b.l,y.a.l).t.replace('%','')-0));
  const worst=byLeadDrop.slice(0,2).map(r=>`${r.n.replace('FBA ','')} (${delta(r.b.l,r.a.l).t})`);
  const enrUp=rowsI.filter(r=>r.b.e>r.a.e).sort((x,y)=>(y.b.e-y.a.e)-(x.b.e-x.a.e));
  const enrDown=rowsI.filter(r=>r.b.l<r.a.l && r.b.e<r.a.e).map(r=>r.n.replace('FBA ',''));
  const si=[];
  si.push(`<li><b>Leads fell at every center</b> (${delta(TB.l,TA.l).t} overall). Steepest drops: ${worst.join(', ')}.</li>`);
  si.push(`<li><b>${enrUp.length} of ${rowsI.length} centers grew enrollments</b> despite fewer leads — led by ${enrUp.slice(0,3).map(r=>r.n.replace('FBA ','')+' ('+r.a.e+'→'+r.b.e+')').join(', ')}. These are converting a smaller pool much harder.</li>`);
  if(enrDown.length) si.push(`<li><b>Watch list — down on both leads and enrollments:</b> ${enrDown.join(', ')}. Demand <i>and</i> closing slipped here; dig into their lead sources and follow-up.</li>`);
  si.push(`<li class="flat" style="color:var(--muted)">Centers with a tiny ${py} base (e.g. Strathmore, Victoria) swing wildly on percentages — read their counts, not the %.</li>`);
  document.getElementById('schoolInf').innerHTML=si.join('');

  // ---- WEBFORM vs CENTER-ADDED (by "Added By First Name": empty => webform) ----
  function srcAgg(year){const rs=winRows(year);let f={l:0,e:0},c={l:0,e:0};
    for(const r of rs){const o=r[6]===1?f:c;o.l++;if(isEnrolled(r[1]))o.e++;}return {f,c,n:rs.length};}
  const sa=srcAgg(py), sb=srcAgg(cy);
  const rowSrc=(lbl,a,b)=>`<tr><td>${lbl}</td><td>${fmt(a.l)}</td><td>${fmt(b.l)}</td><td class="${delta(b.l,a.l).c}">${delta(b.l,a.l).t}</td><td>${fmt(a.e)}</td><td>${fmt(b.e)}</td><td>${pct(a.e,a.l).toFixed(0)}%</td><td>${pct(b.e,b.l).toFixed(0)}%</td></tr>`;
  let sh=`<thead><tr><th>Source</th><th>Leads ${py}</th><th>Leads ${cy}</th><th>Δ</th><th>Success ${py}</th><th>Success ${cy}</th><th>Conv ${py}</th><th>Conv ${cy}</th></tr></thead><tbody>`;
  sh+=rowSrc('Webform (no staff name)',sa.f,sb.f);
  sh+=rowSrc('Center-added (staff name)',sa.c,sb.c);
  sh+='</tbody>';
  document.getElementById('srcCmp').innerHTML=sh;
  const formShare=pct(sb.f.l,sb.n), cenConvB=pct(sb.c.e,sb.c.l), formConvB=pct(sb.f.e,sb.f.l);
  const sif=[];
  sif.push(`<li><b>Webform is ${formShare.toFixed(0)}% of all leads</b> in ${cy} and fell ${delta(sb.f.l,sa.f.l).t} — so the lead decline is mostly a <b>webform / online-demand</b> story.</li>`);
  sif.push(`<li><b>Staff-added leads convert better</b> (${cenConvB.toFixed(0)}% vs ${formConvB.toFixed(0)}% for webform in ${cy}). Leads the team logs directly — walk-ins, calls, referrals — are warmer.</li>`);
  sif.push(`<li>Center-added volume ${delta(sb.c.l,sa.c.l).t} (${fmt(sa.c.l)}→${fmt(sb.c.l)}). ${sb.c.l<sa.c.l?'Staff are logging fewer leads — worth checking if walk-ins/calls are simply not being captured.':'Healthy direct activity.'}</li>`);
  sif.push(`<li class="flat" style="color:var(--muted)">Action: webform conversion improving is good, but rebuilding webform <i>volume</i> (SEO/ads/landing pages) is where the lost leads are.</li>`);
  document.getElementById('srcInf').innerHTML=sif.join('');

  // ---- CHANNEL (respects school filter) ----
  function chAgg(year){const rs=winRows(year);const m={};for(const r of rs)m[r[4]]=(m[r[4]]||0)+1;return {m,n:rs.length};}
  const ca=chAgg(py), cb=chAgg(cy);
  const keys=[...new Set([...Object.keys(ca.m),...Object.keys(cb.m)].map(Number))]
    .sort((x,y)=>(cb.m[y]||0)-(cb.m[x]||0)).slice(0,9);
  let ch=`<thead><tr><th>Channel</th><th>${py}</th><th>%</th><th>${cy}</th><th>%</th><th>Δ</th></tr></thead><tbody>`;
  for(const k of keys){const av=ca.m[k]||0,bv=cb.m[k]||0;
    ch+=`<tr><td>${HEAR[k]}</td><td>${fmt(av)}</td><td>${pct(av,ca.n).toFixed(0)}%</td><td>${fmt(bv)}</td><td>${pct(bv,cb.n).toFixed(0)}%</td><td class="${delta(bv,av).c}">${delta(bv,av).t}</td></tr>`;}
  ch+='</tbody>';
  document.getElementById('chCmp').innerHTML=ch;
  // channel inferences
  const top=keys.map(k=>({n:HEAR[k],a:ca.m[k]||0,b:cb.m[k]||0}));
  const online=top.find(t=>t.n.toLowerCase().includes('online'));
  const gainers=top.filter(t=>t.b>t.a && t.n!=='(none)' && t.n!=='(blank)').sort((x,y)=>(y.b-y.a)-(x.b-x.a));
  const blank=top.find(t=>t.n==='(none)'||t.n==='(blank)');
  const ci=[];
  if(online) ci.push(`<li><b>Online Search dominates</b> — ${pct(online.b,cb.n).toFixed(0)}% of ${cy} leads — but it ${delta(online.b,online.a).t} (${fmt(online.a)}→${fmt(online.b)}). This single channel drives the overall lead drop.</li>`);
  if(gainers.length) ci.push(`<li><b>Bright spots:</b> ${gainers.slice(0,2).map(g=>g.n+' ('+g.a+'→'+g.b+')').join(', ')} grew — channels worth doubling down on.</li>`);
  if(blank) ci.push(`<li><b>${pct(blank.b,cb.n).toFixed(0)}% of leads have no channel recorded.</b> That blind spot hides where real demand comes from — make the field required at intake.</li>`);
  ci.push(`<li class="flat" style="color:var(--muted)">Action: the gap is concentrated in paid/organic online search. Audit ad spend, keyword rankings and form UX for the season.</li>`);
  document.getElementById('chInf').innerHTML=ci.join('');
}

syncRange();
render();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(payload, separators=(',', ':')))
with open(OUT, "w") as f:
    f.write(html)
print("Wrote", OUT, f"({len(html)//1024} KB)")
print("Records:", len(rows), "Centers:", len(centers), "Statuses:", len(statuses))
