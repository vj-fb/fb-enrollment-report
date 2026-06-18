#!/usr/bin/env python3
"""Build a self-contained DAILY lead-trend tracker (daily.html)."""
import csv, json, os, glob
from datetime import datetime

SRC_DIR = "/Users/vijaybabu.g/Desktop/FuelingBrains/FBClaude/crm_source"
OUT = os.path.join(os.path.dirname(__file__), "daily.html")
FLOOR = datetime(2024, 6, 1)   # keep ~2 years; guards against an accidental all-history export

# Merge every CSV in the source folder (one file per CRM account / login).
data = []
seen = set()
for fp in sorted(glob.glob(os.path.join(SRC_DIR, "*.csv"))):
    with open(fp, newline='', encoding='utf-8-sig') as f:
        body = f.readlines()[6:]
    for r in csv.reader(body):
        if not r or all(not c.strip() for c in r):
            continue
        r = [c.strip() for c in r]
        if len(r) < 12:
            continue
        key = tuple(r[:12])
        if key in seen:
            continue
        seen.add(key)
        data.append(r)

def pdate(s):
    try: return datetime.strptime(s, "%m/%d/%Y")
    except Exception: return None

centers, statuses, hears = [], [], []
def idx(lst, v):
    if v not in lst: lst.append(v)
    return lst.index(v)

rows = []
for d in data:
    dt = pdate(d[10])
    if not dt or dt < FLOOR: continue
    web = 1 if d[8].strip() == "" else 0
    rows.append([
        idx(centers, d[0]),
        idx(statuses, d[6] or "(blank)"),
        dt.strftime("%Y-%m-%d"),
        idx(hears, d[11] or "(none)"),
        web,
    ])

payload = {
    "centers": centers, "statuses": statuses, "hears": hears, "rows": rows,
    "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "dataMax": max(r[2] for r in rows), "dataMin": min(r[2] for r in rows),
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Lead Tracker</title>
<style>
  :root{--bg:#0f1420;--panel:#161d2e;--panel2:#1c2740;--line:#26314d;--txt:#e6ecf7;
    --muted:#93a0bd;--accent:#4f8cff;--good:#37c97f;--warn:#ffb020;--bad:#ff5d6c;--chip:#223052;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  a{color:var(--accent)}
  header{padding:22px 26px 8px}
  h1{margin:0 0 2px;font-size:22px}
  .sub{color:var(--muted);font-size:13px}
  .bar{position:sticky;top:0;z-index:20;background:rgba(15,20,32,.96);backdrop-filter:blur(6px);
    border-bottom:1px solid var(--line);padding:12px 26px;display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end}
  .fld{display:flex;flex-direction:column;gap:4px}
  .fld label{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  select{background:var(--panel2);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:7px 9px;font-size:13px;min-width:150px}
  .wrap{padding:18px 26px 60px;max-width:1180px}
  .scope{color:var(--muted);font-size:12px;margin:2px 0 16px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .card .k{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  .card .v{font-size:26px;font-weight:700;margin-top:4px}
  .card .d{font-size:12px;margin-top:3px}
  .up{color:var(--good)} .down{color:var(--bad)} .flat{color:var(--muted)}
  section{margin-top:30px}
  section h2{font-size:16px;margin:0 0 4px}
  section .note{color:var(--muted);font-size:12px;margin:0 0 12px}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
  table{border-collapse:collapse;width:100%;font-size:12.5px}
  th,td{padding:7px 9px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
  th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel)}
  thead th{position:sticky;top:0;background:var(--panel2);color:var(--muted);font-weight:600;z-index:2}
  thead th:first-child{z-index:3;background:var(--panel2)}
  tbody tr:hover td{background:var(--panel2)}
  tr.totrow td{border-top:2px solid var(--line);font-weight:700;background:var(--panel2)}
  .scrollx{overflow-x:auto;border-radius:10px}
  .heat0{color:#46527a}
  .legend{color:var(--muted);font-size:11px;margin-top:8px}
  svg text{fill:var(--muted);font-size:10px}
  .today{color:var(--warn)}
</style>
</head>
<body>
<header>
  <h1>Daily Lead Tracker <span style="font-size:13px;color:var(--muted)">&middot; <a href="index.html">full analysis &rarr;</a></span></h1>
  <div class="sub">New leads per day (by Created Date) &middot; <span id="genmeta"></span></div>
</header>

<div class="bar">
  <div class="fld"><label>School</label><select id="school"></select></div>
  <div class="fld"><label>Window</label>
    <select id="days">
      <option value="10">Last 10 days</option>
      <option value="14">Last 14 days</option>
      <option value="30">Last 30 days</option>
      <option value="60">Last 60 days</option>
      <option value="90">Last 90 days</option>
    </select>
  </div>
</div>

<div class="wrap">
  <div class="scope" id="scope"></div>
  <div class="cards" id="kpis"></div>

  <section>
    <h2>Daily new leads &mdash; trend</h2>
    <p class="note">Bars = new leads per day. <span style="color:var(--accent)">Line</span> = 7-day moving average.</p>
    <div class="panel"><div id="chart"></div>
      <div class="legend"><span style="color:#4f8cff">&#9632;</span> New leads &nbsp; <span style="color:#9db4e6">&#9472;</span> 7-day avg</div>
    </div>
  </section>

  <section>
    <h2>Daily summary</h2>
    <p class="note">Per day: total new leads, how they came in (Webform = no staff name vs Added at center), and the three outcome statuses shown separately &mdash; <b>Offered</b> (Enrollment&nbsp;-&nbsp;Offered), <b>Enrolled</b> (Enrollment&nbsp;-&nbsp;Enrolled), <b>Withdrawn</b>.</p>
    <div class="panel"><div class="scrollx"><table id="summary"></table></div></div>
  </section>

  <section>
    <h2>By center &mdash; day &times; center</h2>
    <p class="note">New leads per day by center. Ignores the School filter so all centers show.</p>
    <div class="panel"><div class="scrollx"><table id="byCenter"></table></div></div>
  </section>

  <section>
    <h2>By marketing channel &mdash; &ldquo;How did you hear about us?&rdquo;</h2>
    <p class="note">New leads per day by channel (top channels in the window). Respects the School filter.</p>
    <div class="panel"><div class="scrollx"><table id="byChannel"></table></div></div>
  </section>
</div>

<script>
const DATA = __DATA__;
const R = DATA.rows;          // [centerIdx, statusIdx, 'YYYY-MM-DD', hearIdx, web]
const C = DATA.centers, S = DATA.statuses, HEAR = DATA.hears;
const sIdx = s => S.indexOf(s);
// three outcome statuses kept SEPARATE (not combined)
const I_OFF = sIdx('Enrollment - Offered'), I_ENR = sIdx('Enrollment - Enrolled'), I_WD = sIdx('Withdrawn');
const MAXD = DATA.dataMax;
function fmt(n){ return n.toLocaleString(); }
function pct(n,d){ return d? n/d*100:0; }

document.getElementById('genmeta').textContent =
  `Generated ${DATA.generated} · latest data ${MAXD} · ${R.length.toLocaleString()} total records`;

const elSchool=document.getElementById('school'), elDays=document.getElementById('days');
elSchool.innerHTML='<option value="all">All schools</option>'+C.map((c,i)=>`<option value="${i}">${c}</option>`).join('');
let state={school:'all', days:10};
elSchool.onchange=()=>{state.school=elSchool.value;render();};
elDays.onchange=()=>{state.days=+elDays.value;render();};

// date helpers (string YYYY-MM-DD math via Date in UTC to avoid TZ drift)
function addDays(iso, n){ const d=new Date(iso+'T00:00:00Z'); d.setUTCDate(d.getUTCDate()+n); return d.toISOString().slice(0,10); }
function dayLabel(iso){ const d=new Date(iso+'T00:00:00Z');
  return d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',timeZone:'UTC'}); }

function schoolRows(){ const sc=state.school; return R.filter(r=> sc==='all'||r[0]==+sc); }

// daily aggregates over ALL days (for moving average history)
function dailyMap(rows){
  const m={};
  for(const r of rows){ const o=m[r[2]]=m[r[2]]||{total:0,web:0,staff:0,off:0,enr:0,wd:0};
    o.total++; if(r[4]===1)o.web++; else o.staff++;
    if(r[1]===I_OFF)o.off++; if(r[1]===I_ENR)o.enr++; if(r[1]===I_WD)o.wd++; }
  return m;
}
function windowDays(n){ const out=[]; for(let i=n-1;i>=0;i--) out.push(addDays(MAXD,-i)); return out; }

function render(){
  const rows=schoolRows();
  const m=dailyMap(rows);
  const N=state.days;
  const days=windowDays(N);
  const get=d=>m[d]||{total:0,web:0,staff:0,off:0,enr:0,wd:0};

  // KPIs
  const sum=arr=>arr.reduce((a,d)=>a+get(d).total,0);
  const total=sum(days);
  const prev=windowDays(N).map(d=>addDays(d,-N));
  const prevTotal=prev.reduce((a,d)=>a+get(d).total,0);
  const offTotal=days.reduce((a,d)=>a+get(d).off,0);
  const enrTotal=days.reduce((a,d)=>a+get(d).enr,0);
  const wdTotal=days.reduce((a,d)=>a+get(d).wd,0);
  const todayN=get(MAXD).total;
  const avg=total/N;
  const ch=prevTotal?((total-prevTotal)/prevTotal*100):0;
  const chCls=ch>1?'up':ch<-1?'down':'flat';
  document.getElementById('scope').innerHTML=
    `School: <b style="color:var(--txt)">${state.school==='all'?'All':C[+state.school]}</b> · `+
    `window: <b style="color:var(--txt)">${days[0]} → ${MAXD}</b> (${N} days)`;
  const kpis=[
    [`Leads on ${dayLabel(MAXD)}`, fmt(todayN), '<span class="today">latest day — may be partial</span>'],
    [`Last ${N} days`, fmt(total), ''],
    ['Daily average', avg.toFixed(1), ''],
    [`vs previous ${N} days`, (ch>=0?'+':'')+ch.toFixed(0)+'%', `<span class="${chCls}">${fmt(prevTotal)} → ${fmt(total)}</span>`],
    [`Offered (${N}d)`, fmt(offTotal), 'Enrollment - Offered'],
    [`Enrolled (${N}d)`, fmt(enrTotal), 'Enrollment - Enrolled'],
    [`Withdrawn (${N}d)`, fmt(wdTotal), 'Withdrawn'],
  ];
  document.getElementById('kpis').innerHTML=kpis.map(k=>
    `<div class="card"><div class="k">${k[0]}</div><div class="v">${k[1]}</div>${k[2]?`<div class="d">${k[2]}</div>`:''}</div>`).join('');

  renderChart(days,get,m);
  renderSummary(days,get);
  renderByCenter(days);
  renderByChannel(days,rows);
}

function ma7(d,m){ let s=0,c=0; for(let i=0;i<7;i++){const k=addDays(d,-i); if(m[k]){s+=m[k].total;} c++;} return s/7; }

function renderChart(days,get,m){
  const W=Math.max(620, days.length*44), H=240, padL=28, padB=34, padT=18;
  const maxV=Math.max(...days.map(d=>get(d).total),1);
  const x=i=>padL+i*((W-padL-12)/Math.max(days.length-1,1));
  const y=v=>H-padB-(v/maxV*(H-padB-padT));
  const bw=Math.max(8, Math.min(26,(W-padL-12)/days.length*0.6));
  let bars='';
  days.forEach((d,i)=>{const o=get(d);
    const h=o.total/maxV*(H-padB-padT); bars+=`<rect x="${x(i)-bw/2}" y="${y(o.total)}" width="${bw}" height="${h}" rx="2" fill="#4f8cff"/>`;
    bars+=`<text x="${x(i)}" y="${y(o.total)-4}" text-anchor="middle" fill="#cdd7ee">${o.total||''}</text>`;
  });
  const mp=days.map((d,i)=>`${x(i)},${y(ma7(d,m))}`).join(' ');
  const lbls=days.map((d,i)=>{const step=Math.ceil(days.length/12);return i%step===0?`<text x="${x(i)}" y="${H-padB+16}" text-anchor="middle">${d.slice(5)}</text>`:'';}).join('');
  document.getElementById('chart').innerHTML=
    `<svg viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="xMidYMid meet">
      ${bars}
      <polyline points="${mp}" fill="none" stroke="#9db4e6" stroke-width="2" stroke-dasharray="4 3"/>
      ${lbls}
    </svg>`;
}

function renderSummary(days,get){
  let h='<thead><tr><th>Day</th><th>New leads</th><th>Webform</th><th>At center</th><th>Offered</th><th>Enrolled</th><th>Withdrawn</th></tr></thead><tbody>';
  let T={t:0,w:0,s:0,off:0,enr:0,wd:0};
  [...days].reverse().forEach(d=>{const o=get(d);T.t+=o.total;T.w+=o.web;T.s+=o.staff;T.off+=o.off;T.enr+=o.enr;T.wd+=o.wd;
    const isToday=d===MAXD;
    h+=`<tr><td>${dayLabel(d)}${isToday?' <span class="today">•</span>':''}</td><td>${fmt(o.total)}</td><td>${fmt(o.web)}</td><td>${fmt(o.staff)}</td><td>${o.off||''}</td><td>${o.enr||''}</td><td>${o.wd||''}</td></tr>`;});
  h+=`<tr class="totrow"><td>Total</td><td>${fmt(T.t)}</td><td>${fmt(T.w)}</td><td>${fmt(T.s)}</td><td>${fmt(T.off)}</td><td>${fmt(T.enr)}</td><td>${fmt(T.wd)}</td></tr></tbody>`;
  document.getElementById('summary').innerHTML=h;
}

function renderByCenter(days){
  // ignores school filter; rows=days, cols=centers
  const cell={},ctot={};
  for(const r of R){ if(r[2]<days[0]||r[2]>MAXD) continue;
    cell[r[2]+'|'+r[0]]=(cell[r[2]+'|'+r[0]]||0)+1; ctot[r[0]]=(ctot[r[0]]||0)+1; }
  const cols=C.map((_,i)=>i).filter(i=>ctot[i]).sort((a,b)=>ctot[b]-ctot[a]);
  let h='<thead><tr><th>Day</th>'+cols.map(c=>`<th>${C[c].replace('FBA ','')}</th>`).join('')+'<th>Total</th></tr></thead><tbody>';
  [...days].reverse().forEach(d=>{let rt=0;let cells=cols.map(c=>{const v=cell[d+'|'+c]||0;rt+=v;return `<td class="${v?'':'heat0'}">${v||''}</td>`;}).join('');
    h+=`<tr><td>${dayLabel(d)}${d===MAXD?' <span class="today">•</span>':''}</td>${cells}<td>${fmt(rt)}</td></tr>`;});
  h+=`<tr class="totrow"><td>Total</td>${cols.map(c=>`<td>${fmt(ctot[c])}</td>`).join('')}<td>${fmt(cols.reduce((a,c)=>a+ctot[c],0))}</td></tr></tbody>`;
  document.getElementById('byCenter').innerHTML=h;
}

function renderByChannel(days,rows){
  const cell={},htot={};
  for(const r of rows){ if(r[2]<days[0]||r[2]>MAXD) continue;
    cell[r[2]+'|'+r[3]]=(cell[r[2]+'|'+r[3]]||0)+1; htot[r[3]]=(htot[r[3]]||0)+1; }
  const cols=Object.keys(htot).map(Number).sort((a,b)=>htot[b]-htot[a]).slice(0,7);
  let h='<thead><tr><th>Day</th>'+cols.map(c=>`<th>${HEAR[c]}</th>`).join('')+'</tr></thead><tbody>';
  [...days].reverse().forEach(d=>{let cells=cols.map(c=>{const v=cell[d+'|'+c]||0;return `<td class="${v?'':'heat0'}">${v||''}</td>`;}).join('');
    h+=`<tr><td>${dayLabel(d)}${d===MAXD?' <span class="today">•</span>':''}</td>${cells}</tr>`;});
  h+=`<tr class="totrow"><td>Total</td>${cols.map(c=>`<td>${fmt(htot[c])}</td>`).join('')}</tbody>`;
  document.getElementById('byChannel').innerHTML=h;
}

render();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(payload, separators=(',', ':')))
with open(OUT, "w") as f:
    f.write(html)
print("Wrote", OUT, f"({len(html)//1024} KB)")
print("Records:", len(rows), "dataMax:", payload["dataMax"])
