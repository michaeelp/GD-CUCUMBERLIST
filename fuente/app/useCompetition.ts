'use client';
import {useEffect,useMemo,useRef,useState,useCallback} from 'react';
import {PLAYERS,type Player} from '@/lib/config';
import {addPatch,buildLevels,type Level,type Records} from '@/lib/domain';
import {challengePeriods,chooseDaily,chooseWeekly,nextGoal,shiftDay,type Goals,type Goal,type Challenge,type DailyMap,type WeeklyMap} from '@/lib/competition';
export function useCompetition({firebase,editor,levels,catalog,notify,canEdit}:{firebase:any;editor:boolean;levels:Level[];catalog:Level[];notify:(text:string)=>void;canEdit?:(p:Player)=>boolean}){
 const [goals,setGoals]=useState<Goals>({});const [dailies,setDailies]=useState<DailyMap>({});const [weeklies,setWeeklies]=useState<WeeklyMap>({});
 const [now,setNow]=useState(()=>Date.now());const [loaded,setLoaded]=useState(false);const [connected,setConnected]=useState(false);const [rulesError,setRulesError]=useState(false);const [busy,setBusy]=useState(false);
 const serverOffset=useRef(0);const ensuring=useRef(false);const attempted=useRef('');
 const periods=useMemo(()=>challengePeriods(now),[now]);
 useEffect(()=>{const tick=()=>setNow(Date.now()+serverOffset.current);const timer=setInterval(tick,30000);document.addEventListener('visibilitychange',tick);return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',tick);};},[]);
 useEffect(()=>{
  if(!firebase)return;const db=firebase.database();setRulesError(false);setLoaded(false);let remaining=3;
  const cleanups:(()=>void)[]=[];const first=new Set<string>();
  const done=(key:string)=>{if(!first.has(key)){first.add(key);remaining--;if(!remaining)setLoaded(true);}};
  const listen=(query:any,key:string,apply:(value:any)=>void)=>{const on=(snap:any)=>{apply(snap.val()||{});done(key);};const fail=()=>{setRulesError(true);done(key);};query.on('value',on,fail);cleanups.push(()=>query.off('value',on));};
  listen(db.ref('objetivos'),'goals',setGoals);
  listen(db.ref('desafios/diarios').orderByKey().startAt(shiftDay(periods.daily.key,-14)),'daily',setDailies);
  listen(db.ref('desafios/semanales').orderByKey().limitToLast(8),'weekly',setWeeklies);
  const offset=db.ref('.info/serverTimeOffset');const onOffset=(s:any)=>{serverOffset.current=s.val()||0;setNow(Date.now()+serverOffset.current);};offset.on('value',onOffset);cleanups.push(()=>offset.off('value',onOffset));
  const connection=db.ref('.info/connected');const onConnection=(s:any)=>setConnected(s.val()===true);connection.on('value',onConnection);cleanups.push(()=>connection.off('value',onConnection));
  return()=>cleanups.forEach(f=>f());
 },[firebase,periods.daily.key]);
 const weeklyPreview=useMemo(()=>chooseWeekly(levels,periods.weekly,weeklies,now),[levels,periods.weekly.key,weeklies]);
 const weekly=weeklies[periods.weekly.key]||weeklyPreview;
 const daily=useMemo(()=>Object.fromEntries(PLAYERS.map(p=>[p,dailies[periods.daily.key]?.[p]||chooseDaily(levels,p,periods.daily,dailies,weekly,now)])) as Record<Player,Challenge|null>,[levels,periods.daily.key,dailies,weekly]);
 const ensure=useCallback(async()=>{notify('Los desafíos se asignan en la verificación programada.');},[notify]);
 const saveGoal=useCallback(async(p:Player,d:Level,best:number)=>{
  if(!firebase?.auth().currentUser||!editor||!connected||(canEdit&&!canEdit(p)))throw Error('Iniciá sesión con tu cuenta y comprobá la conexión para guardar.');
  setBusy(true);const db=firebase.database();
  try{
   const timestamp=firebase.database.ServerValue.TIMESTAMP;
   if(best===100){
    const [a,b]=await Promise.all([db.ref('pasados').get(),db.ref(`objetivos/${p}`).get()]);
    const raw:Records=a.val()||{};const live=buildLevels(raw,catalog).find(l=>l.id===d.id)||d;
    const goal=nextGoal(b.val(),live,100,Date.now()+serverOffset.current);
    const patch:Record<string,unknown>=live[p]?{}:addPatch(live,p,raw,timestamp);
    patch[`objetivos/${p}`]={...goal,createdAt:b.val()?.id===d.id?b.val().createdAt:timestamp,updatedAt:timestamp};
    await db.ref().update(patch);notify(`${p}: ¡${d.name} al 100 %! La completación quedó registrada.`);
   }else{
    await db.ref(`objetivos/${p}`).transaction((old:Goal|null)=>{const next=nextGoal(old,d,best,Date.now()+serverOffset.current);return {...next,createdAt:old?.id===d.id?old.createdAt:timestamp,updatedAt:timestamp};},undefined,false);
    notify(`Progreso de ${p} guardado.`);
   }
   setRulesError(false);
  }catch(e:any){if(e?.code==='PERMISSION_DENIED'||e?.code==='permission_denied'){setRulesError(true);throw Error('Publicá firebase.rules.json de esta versión para guardar objetivos.');}throw e;}
  finally{setBusy(false);}
 },[firebase,editor,connected,catalog,notify,canEdit]);
 const clearGoal=useCallback(async(p:Player)=>{
  if(!firebase?.auth().currentUser||!editor||!connected||(canEdit&&!canEdit(p)))throw Error('Necesitás la cuenta de este jugador y una conexión activa.');
  setBusy(true);try{await firebase.database().ref(`objetivos/${p}`).remove();notify(`Objetivo de ${p} retirado. Sus completaciones se conservan.`);}finally{setBusy(false);}
 },[firebase,editor,connected,notify,canEdit]);
 return {goals,daily,weekly,dailies,weeklies,periods,now,loaded,connected,rulesError,busy,ensure,saveGoal,clearGoal,isDailySaved:(p:Player)=>!!dailies[periods.daily.key]?.[p],isWeeklySaved:!!weeklies[periods.weekly.key]};
}
export type Competition=ReturnType<typeof useCompetition>;
