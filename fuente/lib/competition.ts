import {PLAYERS,type Player} from './config';
import {historyMatches,type Level,type Histories} from './domain';
export type Period={key:string;startsAt:number;endsAt:number};
export type Goal={id:string;name:string;creator:string;difficulty:string;tier:number;best:number;createdAt:number;updatedAt:number};
export type Goals=Partial<Record<Player,Goal>>;
export type Challenge={id:string;name:string;creator:string;difficulty:string;tier:number;kind:'daily'|'weekly';period:string;player:Player|'all';referenceTier:number;targetTier:number;startsAt:number;endsAt:number;createdAt:number;version:number};
export type DailyMap=Record<string,Partial<Record<Player,Challenge>>>;
export type WeeklyMap=Record<string,Challenge>;
const DAY=86400000;
export function shiftDay(key:string,days:number){return new Date(Date.parse(key+'T12:00:00Z')+days*DAY).toISOString().slice(0,10);}
export function challengePeriods(now=Date.now()){
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Montevideo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const get=(name:string)=>parts.find(p=>p.type===name)!.value;
 const day=`${get('year')}-${get('month')}-${get('day')}`;
 const startsAt=Date.parse(day+'T00:00:00-03:00');
 const weekday=new Date(day+'T12:00:00Z').getUTCDay();
 const monday=shiftDay(day,-((weekday+6)%7));const weekStart=Date.parse(monday+'T00:00:00-03:00');
 return {daily:{key:day,startsAt,endsAt:startsAt+DAY},weekly:{key:monday,startsAt:weekStart,endsAt:weekStart+7*DAY}};
}
export function seededIndex(seed:string,length:number){let h=2166136261;for(const c of seed){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return (h>>>0)%length;}
export const hardestTier=(levels:Level[],p:Player)=>Math.max(0,...levels.filter(d=>d[p]).map(d=>d.tier));
const round=(n:number)=>Math.round(n*10)/10;
function select(pool:Level[],seed:string,target:number,min:number,max:number,blocked:Set<string>){
 const unique=Array.from(new Map(pool.filter(d=>/^\d+$/.test(d.id)&&d.name&&Number.isFinite(d.tier)&&d.tier>=0).map(d=>[d.id,d])).values());
 let bounded=unique.filter(d=>d.tier>=min&&d.tier<=max);
 if(!bounded.length)bounded=unique.filter(d=>d.tier<=max);
 if(!bounded.length)return null;
 const fresh=bounded.filter(d=>!blocked.has(d.id));if(fresh.length)bounded=fresh;
 const nearest=bounded.sort((a,b)=>Math.abs(a.tier-target)-Math.abs(b.tier-target)||(a.id<b.id?-1:a.id>b.id?1:0)).slice(0,32);
 return nearest[seededIndex(seed,nearest.length)];
}
function snapshot(d:Level,kind:Challenge['kind'],player:Challenge['player'],period:Period,reference:number,target:number,now:number):Challenge{
 return {id:d.id,name:d.name,creator:d.creator||'',difficulty:d.difficulty||'',tier:d.tier,kind,player,period:period.key,startsAt:period.startsAt,endsAt:period.endsAt,referenceTier:round(reference),targetTier:round(target),createdAt:now,version:1};
}
export function chooseDaily(levels:Level[],p:Player,period:Period,recent:DailyMap={},weekly?:Challenge|null,now=Date.now()){
 const hardest=hardestTier(levels,p);const reference=hardest||1.5;const target=round(reference*.5);
 const blocked=new Set<string>();
 for(const [day,players] of Object.entries(recent))if(day<period.key&&day>=shiftDay(period.key,-7)&&players[p]?.id)blocked.add(players[p]!.id);
 if(weekly)blocked.add(weekly.id);
 const d=select(levels.filter(d=>!d[p]),`daily-v1:${period.key}:${p}`,target,reference*.40,hardest?reference*.60:reference,blocked);
 return d?snapshot(d,'daily',p,period,reference,target,now):null;
}
export function chooseWeekly(levels:Level[],period:Period,previous:WeeklyMap={},now=Date.now()){
 const hardests=PLAYERS.map(p=>hardestTier(levels,p));if(hardests.some(t=>t<=0))return null;
 const mean=hardests.reduce((a,b)=>a+b,0)/3;
 const blocked=new Set(Object.entries(previous).filter(([key])=>key<period.key).sort(([a],[b])=>a.localeCompare(b)).slice(-4).map(([,d])=>d.id));
 const pendingForAll=levels.filter(d=>PLAYERS.every(p=>!d[p]));
 const d=select(pendingForAll,`weekly-v2:${period.key}`,mean*.6,mean*.6*.85,mean*.6*1.15,blocked);
 return d?snapshot(d,'weekly','all',period,mean,mean*.6,now):null;
}
export function challengeCompleted(c:Challenge|null|undefined,p:Player,history:Histories,levels:Level[]){
 if(!c)return false;
 const level=levels.find(d=>d.id===c.id);if(!level?.[p])return false;
 return Object.values(history).some(h=>h.player===p&&historyMatches(h,level)&&typeof h.timestamp==='number'&&h.timestamp>=c.startsAt&&h.timestamp<c.endsAt);
}
export function challengeProgress(c:Challenge|null|undefined,p:Player,goals:Goals,history:Histories,levels:Level[]){
 if(challengeCompleted(c,p,history,levels))return 100;
 return c&&goals[p]?.id===c.id&&goals[p]!.best<100?goals[p]!.best:0;
}
export function nextGoal(old:Goal|null,d:Level,best:number,timestamp:number):Goal{
 if(!/^\d+$/.test(d.id)||!d.name||!Number.isFinite(d.tier))throw Error('Seleccioná un nivel con ID verificado.');
 if(!Number.isInteger(best)||best<0||best>100)throw Error('El porcentaje debe ser un entero entre 0 y 100.');
 return {id:d.id,name:d.name,creator:d.creator||'',difficulty:d.difficulty||'',tier:d.tier,best:old?.id===d.id?Math.max(old.best,best):best,createdAt:old?.id===d.id?old.createdAt:timestamp,updatedAt:timestamp};
}
