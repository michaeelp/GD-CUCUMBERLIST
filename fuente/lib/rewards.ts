import {PLAYERS,type Player} from './config';
import {historyMatches,type Level,type Records,type Histories} from './domain';
import type {Quest,GameState} from '../app/useGame';
export type Receipt={key:string;kind:string;amount:number;xp:number;reason:string;statMission:boolean;item?:string;levelId?:string;period?:string;slot?:string;proofs?:{id?:string;key?:string;award?:string}[]};
export type RewardContext={player:Player;levels:Level[];records:Records;history:Histories;runs:Record<string,any>;goal:any;profile:any;now:number};
const lines=[[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15],[0,4,8,12],[1,5,9,13],[2,6,10,14],[3,7,11,15],[0,5,10,15],[3,6,9,12]];
function proof(c:RewardContext,id:string,p:Player=c.player){const level=c.levels.find(d=>d.id===id);const key=Object.keys(c.records).find(key=>c.records[key]?.[p]&&(String(c.records[key].id||key)===id||level?._keys?.includes(key)));return key?{id,key}:null;}
function events(c:RewardContext,start:number,end:number,p:Player=c.player){return c.levels.flatMap(d=>{if(!d[p])return [];const h=Object.values(c.history).find(h=>h.player===p&&historyMatches(h,d)&&typeof h.timestamp==='number'&&h.timestamp>=start&&h.timestamp<end);const f=h&&proof(c,d.id,p);return f?[{...f,level:d,at:h!.timestamp!}]:[];});}
function evaluate(q:Quest,c:RewardContext,start:number,end:number,w:GameState['wallet']):{q:Quest;proofs:Receipt['proofs']}{
 start=Math.max(start,q.createdAt||start);const ev=events(c,start,end);let value=0;let proofs:Receipt['proofs']=[];let parts=q.parts;
 if(q.kind==='combo'){const a=(q.parts||[]).map(part=>evaluate(part,c,start,end,w));parts=a.map(x=>x.q);value=parts.filter(q=>q.completed).length;proofs=a.flatMap(x=>x.proofs||[]);}
 else if(['level','choice','levels_count','easy_count','creator_count'].includes(q.kind)){
  let found=ev.filter(e=>q.kind==='level'?e.id===q.level?.id:q.options?q.options.some(d=>d.id===e.id):e.level.difficulty==='Easy');
  if(q.kind==='creator_count'){const names=new Set<string>();found=found.filter(e=>{if(names.has(e.level.creator))return false;names.add(e.level.creator);return true;});}
  value=q.kind==='choice'?Number(found.length>0):found.length;proofs=found.slice(0,q.target).map(({id,key})=>({id,key}));
 }else if(q.kind==='percent'&&q.level){
  const run=c.runs[q.level.id];if(run?.updatedAt>=start&&run.updatedAt<end)value=run.best;
  if(c.goal?.id===q.level.id&&c.goal.updatedAt>=start&&c.goal.updatedAt<end)value=Math.max(value,c.goal.best);
  const win=ev.find(e=>e.id===q.level!.id);if(win){value=100;proofs=[{id:win.id,key:win.key}];}
 }else if(q.kind==='stat'){
  const at=c.profile?.at||0,n=c.profile?.stats?.[q.stat!];if(!q.waitingBaseline&&typeof q.baseline==='number'&&typeof n==='number'&&at>=(q.baselineAt||start)&&at<end)value=Math.max(0,n-q.baseline);
 }else if(q.kind==='awards'){
  const found=Object.entries(w.ledger||{}).filter(([key,e])=>e.at>=start&&e.at<end&&(q.awardType==='statmission'?key.startsWith('mission_')&&e.statMission:key.startsWith(q.awardType+'_')));value=found.length;proofs=found.slice(0,q.target).map(([award])=>({award}));
 }
 const progress=Math.min(q.target,Math.max(q.progress||0,value));return {q:{...q,parts,progress,completed:q.completed||progress>=q.target,expired:c.now>=end&&!q.completed&&progress<q.target},proofs};
}
export function liveRewards(raw:GameState,c:RewardContext){
 const state:GameState={...raw,daily:{...raw.daily},bingo:{...raw.bingo}};const w=raw.wallet;const receipts:Receipt[]=[];const add=(r:Receipt)=>{if(!w.ledger?.[r.key])receipts.push(r);};
 for(const e of events(c,raw.activatedAt||0,c.now+1))if(!w.paidLevels?.[e.id])add({key:'level_'+e.id,kind:'level',levelId:e.id,amount:20+Math.floor(e.level.tier*2),xp:10,reason:'Completación: '+e.level.name,statMission:false,proofs:[{id:e.id,key:e.key}]});
 state.daily.quests=raw.daily.quests.map((q,i)=>{const result=evaluate(q,c,raw.daily.startsAt,raw.daily.endsAt,w);if(result.q.completed)add({key:'mission_'+q.id,kind:'mission',period:raw.daily.day,slot:String(i),amount:q.reward,xp:q.xp||25,reason:q.title,statMission:q.kind==='stat'||q.kind==='combo',proofs:result.proofs});return result.q;});
 if(state.daily.quests.every(q=>w.ledger?.['mission_'+q.id]))add({key:'all_'+raw.daily.day,kind:'all',period:raw.daily.day,amount:75,xp:60,reason:'Cuatro misiones del día',statMission:false});
 const assignments=raw.assignments||{};
 for(const [kind,amount,xp] of [['daily',50,35],['weekly',100,75],['coop',60,40],['team',90,60]] as const){
  const challenge=assignments[kind==='team'||kind==='coop'?'cooperative':kind];if(!challenge)continue;
  const players=kind==='team'?PLAYERS:[c.player];const proofs=players.map(p=>events(c,challenge.startsAt,challenge.endsAt,p).find(e=>e.id===challenge.id));
  if(proofs.every(Boolean))add({key:kind+'_'+challenge.period,kind,period:challenge.period,amount,xp,reason:kind==='team'?'Bonus de equipo':`${kind==='daily'?'Demon diario':kind==='weekly'?'Demon semanal':'Cooperativa'}: ${challenge.name}`,statMission:false,proofs:proofs.map(e=>({id:e!.id,key:e!.key}))});
 }
 state.bingo.cells=raw.bingo.cells.map((q,i)=>{const result=evaluate(q,c,raw.bingo.activatedAt,raw.bingo.endsAt,w);if(result.q.completed)add({key:`bingo_${raw.bingo.month}_cell_${i}`,kind:'bingo',period:raw.bingo.month,slot:String(i),amount:q.reward,xp:30,reason:'Bingo: '+q.title,statMission:false,proofs:result.proofs});return result.q;});
 state.bingo.lines=lines.flatMap((line,i)=>line.every(j=>state.bingo.cells[j]?.completed)?[i]:[]);
 for(let i=0;i<lines.length;i++)if(lines[i].every(j=>w.ledger?.[`bingo_${raw.bingo.month}_cell_${j}`]))add({key:`bingo_${raw.bingo.month}_line_${i}`,kind:'line',period:raw.bingo.month,slot:String(i),amount:100,xp:50,reason:'Línea de bingo',statMission:false});
 if(state.bingo.cells.every((_,i)=>w.ledger?.[`bingo_${raw.bingo.month}_cell_${i}`]))add({key:`bingo_${raw.bingo.month}_full`,kind:'full',period:raw.bingo.month,amount:400,xp:200,reason:'Bingo completo',statMission:false});
 state.bingo.completed=state.bingo.cells.every(q=>q.completed);return {state,receipts};
}
