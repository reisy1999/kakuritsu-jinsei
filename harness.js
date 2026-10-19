function render(){}
function addRow(k,l,t){LOG.push(k+":"+t)}
function setAuto(v){auto=v}
function doRoll(r){const ws=r.o.map(x=>Math.max(.5,typeof x.w==="function"?x.w(s):x.w));
  if(ws.some(w=>!isFinite(w)))throw new Error("bad w "+r.q);
  const x=r.o[pickW(ws,v=>v)];applyFx(x.fx);if(x.set)x.set(s);tx(x.t,s);return x}
function showDecision(d){
  if(!d.choices||!d.choices.length)throw new Error("no choices "+s.age);
  tx(d.text,s);
  const need=c=>(c.cost||0)+Math.max(0,-((c.fx||{}).money||0));
  let ok=d.choices.filter(c=>!(need(c)>0&&s.money<need(c)));if(!ok.length)ok=d.choices;
  const c=ok[R(0,ok.length-1)];
  if(!c.roll)throw new Error("no roll "+d.title+" "+c.l);
  if(c.cost)s.money-=c.cost;applyFx(c.fx||{});if(c.set)c.set(s);doRoll(c.roll);if(c.then)doRoll(c.then(s));
  if(!d.birth&&!d.rainbow){s.forks.push(1);TITLES[d.title]=(TITLES[d.title]||0)+1;if(d.gen)GENUSE++}snap();pending=false;
}
function die(){s.alive=false}
let LOG=[],TITLES={},GENUSE=0;const N=+(process.argv[2]||2000),st={age:[],money:[],hiki:0,futoko:0,forks:[],married:0,track:{},bankrupt:0,parentDeath:[],spendDebt:0,gray:0};
for(let n=0;n<N;n++){LOG=[];newLife();let g=0;
  while(s.alive&&g++<200){step();}
  if(isNaN(s.money))throw new Error("NaN");
  st.age.push(s.age);st.money.push(s.money);st.forks.push(s.forks.length);
  if(s.hikiYears>=10)st.hiki++;if(LOG.some(l=>l.includes("不登校")||l.includes("足が動かなく")))st.futoko++;if(s.married)st.married++;
  if(s.track)st.track[s.track]=(st.track[s.track]||0)+1;if(s.bankruptAge)st.bankrupt++;
  LOG.filter(l=>l.includes("両親とも亡くなった")).forEach(l=>st.parentDeath.push(1));
}
const avg=a=>a.reduce((x,y)=>x+y,0)/a.length,so=a=>[...a].sort((x,y)=>x-y);
console.log("age avg",avg(st.age).toFixed(1),"| money med",Math.round(so(st.money)[N/2]),"p10",Math.round(so(st.money)[N*.1|0]),"p90",Math.round(so(st.money)[N*.9|0]));
console.log("forks avg",avg(st.forks).toFixed(1),"gen-decisions/life",(GENUSE/N).toFixed(1),"futoko%",(st.futoko/N*100).toFixed(1),"hiki10y%",(st.hiki/N*100).toFixed(1),"married%",(st.married/N*100).toFixed(1),"bankrupt%",(st.bankrupt/N*100).toFixed(1));
console.log("tracks %",Object.entries(st.track).map(([k,v])=>k+":"+(v/N*100).toFixed(1)).join(" "));
