/* ========== 生成データの読み込み（Sonnet 量産分） ========== */
/*GEN_START*/const GEN={decisions:[],events:[],tracks:[]};/*GEN_END*/
const TRACKS=Object.fromEntries((GEN.tracks||[]).map(t=>[t.id,t]));
const fill=t=>typeof t==="string"?t.replace(/\{pref\}/g,s.pref).replace(/\{job\}/g,s.job?s.job.name:"仕事"):t;

function req(r){
  if(!r)return true;
  if(r.status&&!r.status.includes(s.status))return false;
  if(r.married!==undefined&&!!s.married!==r.married)return false;
  if(r.kids_min!==undefined&&s.kids<r.kids_min)return false;
  if(r.money_min!==undefined&&s.money<r.money_min)return false;
  if(r.money_max!==undefined&&s.money>r.money_max)return false;
  for(const k in r.stat_min||{})if(s[k]<r.stat_min[k])return false;
  for(const k in r.stat_max||{})if(s[k]>r.stat_max[k])return false;
  for(const k in r.cond_min||{})if(s.cd[k]<r.cond_min[k])return false;
  for(const k in r.cond_max||{})if(s.cd[k]>r.cond_max[k])return false;
  if(r.parents_alive!==undefined&&s.parentsAlive!==r.parents_alive)return false;
  if(r.goal&&!r.goal.includes(s.goal))return false;
  if(r.track&&s.track!==r.track)return false;
  if(r.flags_any&&!r.flags_any.some(f=>s.flags[f]))return false;
  if(r.flags_none&&r.flags_none.some(f=>s.flags[f]))return false;
  return true;
}
const genFx=fx=>{const o={};for(const k in fx||{})o[k==="income_mul"?"incMul":k]=fx[k];return o};
function applySet(st){
  if(!st)return;
  if(st.job)setJob(s,st.job.name,st.job.income,st.job.grow,st.job.kind);
  if(st.status){s.status=st.status;if(st.status!=="work")s.job=null;if(st.status==="hikikomori")s.hikiSince=s.hikiSince||s.age}
  if(st.married!==undefined)s.married=st.married;
  if(st.kids_delta)s.kids=Math.max(0,s.kids+st.kids_delta);
  for(const f of st.flags||[])s.flags[f]=1;
  for(const k in st.cond||{})s.cd[k]=Math.max(0,Math.min(3,s.cd[k]+st.cond[k]));
  for(const k in st.press||{})s.press[k]+=st.press[k];
  if(st.track){s.track=st.track;s.trackSince=s.age}
  if(st.bankrupt){s.money=0;s.flags.bankrupt=1;s.bankruptAge=s.age;s.cd.poor=0}
}
const prioOf=x=>{const r=x.requires||{};return !!(r.cond_min||r.money_max!==undefined&&r.money_max<0||(r.status||[]).some(v=>v==="hikikomori"||v==="jobless"||v==="futoko"))};
function genDecision(x){
  return{id:x.id,title:x.title,text:fill(x.text),gen:1,choices:x.choices.map(c=>{const r=c.roll,av=()=>avgOf(s,r.stats);
    const mk=(k,w)=>{const z=r[k];return o(z.label,w,genFx(z.fx),fill(z.text),z.set?()=>applySet(z.set):undefined)};
    return{l:c.label,cost:-(c.cost&&c.cost.money||0),fx:genFx(c.fx),roll:{q:r.name,why:r.stats,o:[
      mk("good",()=>Math.max(1,av()-r.difficulty)),mk("mid",45),mk("bad",()=>Math.max(1,(100-av())*.45))]}}})};
}
function genEligible(x){
  const a=x.age||[0,120];
  if(s.age<a[0]||s.age>a[1])return false;
  if(!req(x.requires))return false;
  if(x.spend){const m=-(x.fx&&x.fx.money||0);if(s.money<m*3||s.cd.poor>0)return false}
  return true;
}

/* 虹：能力条件（gate）を満たしたときだけ、虹のルーレットに巡り合う */
function gateOk(t){const g=t.gate||{};if(s.track||s.trackTried[t.id]>=2)return false;
  if(g.age&&(s.age<g.age[0]||s.age>g.age[1]))return false;
  for(const k in g.stat_min||{})if(s[k]<g.stat_min[k])return false;
  if(g.goal&&!g.goal.includes(s.goal))return false;
  return true}
function rainbowDecision(t){
  const c=t.chance,av=()=>avgOf(s,c.stats);
  s.trackTried[t.id]=(s.trackTried[t.id]||0)+1;
  return{rainbow:1,title:"★ 虹の兆し",text:`${t.name}への道が、一瞬だけ開いている。`,choices:[
    {l:"運命に身を任せる",fx:{},roll:{q:c.name,why:c.stats,o:[
      o("道が開く",()=>Math.max(1,av()-c.difficulty),genFx(c.hit.fx),c.hit.text,()=>{if(c.hit.job)setJob(s,c.hit.job.name,c.hit.job.income,c.hit.job.grow,c.hit.job.kind);s.track=t.id;s.trackSince=s.age;s.rainbow++}),
      o("すれ違う",()=>45+(100-av())*.45,genFx(c.miss.fx),c.miss.text)]}}]};
}
function trackEnd(){
  const t=TRACKS[s.track];if(!t||!t.end||s.trackEnded)return;
  const a=t.end.age;if(s.age<a[0])return;
  if(s.age>=a[1]||Math.random()<.3){s.trackEnded=1;addRow("life","区切り",t.end.text);if(t.end.job)setJob(s,t.end.job.name,t.end.job.income,t.end.job.grow,t.end.job.kind)}
}
