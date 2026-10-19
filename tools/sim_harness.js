/* tools/sim.py が template.html のエンジンの後ろに連結して実行するハーネス。
   UI 関数を差し替え、N 回の人生を回して集計を JSON で出す。
   SIM_POLICY=random … 払える選択肢からランダム
   SIM_POLICY=smart  … 資金不足・傾きが深いときは損失の期待値が最小の選択肢、余裕があれば期待値が最大の選択肢 */
function render(){}
function addRow(k,l,t){LOG.push(k+":"+t)}
function setAuto(v){auto=v}
function doRoll(r){const ws=r.o.map(x=>Math.max(.5,typeof x.w==="function"?x.w(s):x.w));
  if(ws.some(w=>!isFinite(w)))throw new Error("bad w "+r.q);
  const x=r.o[pickW(ws,v=>v)];applyFx(x.fx);if(x.set)x.set(s);tx(x.t,s);return x}

const POLICY=process.env.SIM_POLICY||"random";
/* 会社員前提の汎用分岐（workDecision / genericLife）を、最初の選択肢のラベルで見分ける */
const GENERIC_FIRST=new Set(["上を目指してがむしゃらに働く","正社員を目指して就職活動","学び直す"]);
/* 状態の価値：能力値の合計 + お金/20 + 年収/5 + 家族 − 傾き。outcome の set は関数なので、状態を複製して実際に当てて測る */
const worth=t=>t.health+t.happy+t.know+t.bond+t.luck+t.money/20+(t.status==="work"&&t.job?t.job.inc/5:0)
  +(t.married?8:0)+t.kids*8-(t.flags.bankrupt?10:0)
  +Object.values(t.cd).reduce((a,v)=>a-v*4,0)+Object.values(t.press).reduce((a,v)=>a-v*2,0);
function tryOut(c,x){
  const keep=s,logLen=LOG.length,keepUsed=new Set(used);
  const{hist,forks,...rest}=keep;s=structuredClone(rest);s.hist=[];s.forks=[];
  try{if(c.cost)s.money-=c.cost;applyFx(c.fx||{});if(c.set)c.set(s);applyFx(x.fx);if(x.set)x.set(s);return worth(s)-worth(keep)}
  finally{s=keep;LOG.length=logLen;used.clear();keepUsed.forEach(v=>used.add(v))}
}
function evalChoice(c){
  const os=c.roll.o,ws=os.map(x=>Math.max(.5,typeof x.w==="function"?x.w(s):x.w)),t=ws.reduce((a,b)=>a+b,0);
  const ov=os.map(x=>tryOut(c,x));
  return{ev:ov.reduce((a,v,i)=>a+v*ws[i]/t,0),risk:ov.reduce((a,v,i)=>a+Math.max(0,-v)*ws[i]/t,0)}
}
const distressed=()=>(s.age>=22&&s.money<240)||Math.max(...Object.values(s.cd))>=2;
function choose(d,ok){
  if(POLICY!=="smart")return ok[R(0,ok.length-1)];
  const e=ok.map(c=>({c,...evalChoice(c)}));
  if(distressed())e.sort((a,b)=>a.risk-b.risk||b.ev-a.ev);else e.sort((a,b)=>b.ev-a.ev);
  return e[0].c}

function showDecision(d){
  if(!d.choices||!d.choices.length)throw new Error("no choices "+s.age);
  tx(d.text,s);
  if(d.choices[0]&&GENERIC_FIRST.has(d.choices[0].l)){
    if(s.track&&s.trackEndKind!=="fail")GENERIC.track++;
    else if(s.job&&["pro","art","founder"].includes(s.job.kind))GENERIC.special++;}
  const need=c=>(c.cost||0)+Math.max(0,-((c.fx||{}).money||0));
  let ok=d.choices.filter(c=>!(need(c)>0&&s.money<need(c)));if(!ok.length)ok=d.choices;
  const c=choose(d,ok);
  if(!c.roll)throw new Error("no roll "+d.title+" "+c.l);
  if(c.cost)s.money-=c.cost;applyFx(c.fx||{});if(c.set)c.set(s);doRoll(c.roll);if(c.then)doRoll(c.then(s));
  if(!d.birth&&!d.rainbow){s.forks.push(1);if(d.gen){GENUSE++;if(d.id)USED[d.id]=(USED[d.id]||0)+1}}snap();pending=false;
  if(typeof afterDecision==="function")afterDecision();
}
function die(){s.alive=false}

let LOG=[],GENUSE=0;const USED={},GENERIC={track:0,special:0};
const N=+(process.env.SIM_N||2000);
const L=[];
for(let n=0;n<N;n++){LOG=[];newLife();let g=0,em=false,mk=0,first=null,sk40=null,sk60=null,max=0,at45=null,tv5=null;
  while(s.alive&&g++<200){step();if(s.married)em=true;mk=Math.max(mk,s.kids);if(s.track&&s.tv!==undefined&&s.age===s.trackSince+5&&!s.trackEnded)tv5=s.tv;
    if(s.job&&!s.job.legacy){if(first===null)first=s.skill;max=Math.max(max,s.skill);
      if(s.age===40)sk40=s.skill;if(s.age===60)sk60=s.skill;if(s.age===45)at45={skill:s.skill,inc:s.job.inc,type:s.job.type,form:s.job.form}}}
  if(isNaN(s.money))throw new Error("NaN");
  L.push({age:s.age,money:typeof netWorth==="function"?netWorth():s.money,minMoney:s.minMoney,forks:s.forks.length,rainbow:s.rainbow>0,track:s.track||null,
    bankrupt:!!s.bankruptAge,hiki:s.hikiYears>=10,hikiAny:s.hikiYears>0,
    futoko:LOG.some(l=>l.includes("不登校")||l.includes("足が動かなく")),
    married:!!s.married,everMarried:em,divorced:!!s.divorces,bkCount:s.bankruptCount||0,cause:s.deathCause||null,illAge:s.illSince||null,assets:(s.assets||[]).map(x=>[x.k,Math.round(x.v-(x.loan||0))]),kidsOut:(s.kidList||[]).map(k=>({grow:Math.round(k.grow),edu:k.edu,path:k.path,married:k.married})),grand:s.grandkids||0,kids:mk,jobs:s.jobs.length,cd:{...s.cd},job:{first,sk40,sk60,max,at45},
    tr:s.track?{id:s.track,since:s.trackSince,end:s.trackEndKind||null,endAge:s.trackEndAge||null,peakAge:s.tvPeakAge||null,tv5}:null});
}
const decIds=(GEN.decisions||[]).map(x=>x.id);
console.log(JSON.stringify({N,policy:POLICY,genUse:GENUSE,used:USED,decIds,generic:GENERIC,lives:L}));
