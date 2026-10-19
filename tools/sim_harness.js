/* tools/sim.py が template.html のエンジンの後ろに連結して実行するハーネス。
   UI 関数を差し替え、選択はランダム（払える選択肢から）で N 回の人生を回し、集計を JSON で出す。 */
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
  if(!d.birth&&!d.rainbow){s.forks.push(1);if(d.gen){GENUSE++;if(d.id)USED[d.id]=(USED[d.id]||0)+1}}snap();pending=false;
}
function die(){s.alive=false}

let LOG=[],GENUSE=0;const USED={};
const N=+(process.env.SIM_N||2000);
const L=[];
for(let n=0;n<N;n++){LOG=[];newLife();let g=0;
  while(s.alive&&g++<200){step();}
  if(isNaN(s.money))throw new Error("NaN");
  L.push({age:s.age,money:s.money,minMoney:s.minMoney,forks:s.forks.length,rainbow:s.rainbow>0,track:s.track||null,
    bankrupt:!!s.bankruptAge,hiki:s.hikiYears>=10,hikiAny:s.hikiYears>0,
    futoko:LOG.some(l=>l.includes("不登校")||l.includes("足が動かなく")),
    married:!!s.married,kids:s.kids,jobs:s.jobs.length,cd:{...s.cd}});
}
const decIds=(GEN.decisions||[]).map(x=>x.id);
console.log(JSON.stringify({N,genUse:GENUSE,used:USED,decIds,lives:L}));
