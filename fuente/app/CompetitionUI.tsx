'use client';
import {useEffect,useMemo,useRef,useState,type CSSProperties} from 'react';
import {ArrowRight,CalendarDays,Check,CheckCheck,Clock,Flame,LoaderCircle,Pencil,Plus,Search,Target,Trash2,Trophy,X} from 'lucide-react';
import {PLAYERS,PLAYER_META,type Player} from '@/lib/config';
import {assetUrl} from '@/lib/catalog-client';
import {challengeCompleted,challengeProgress,hardestTier,type Challenge} from '@/lib/competition';
import {type Level,type Histories} from '@/lib/domain';
import {type Competition} from './useCompetition';

type Shared={competition:Competition;levels:Level[];history:Histories;editor:boolean;canEdit?:(p:Player)=>boolean;onAccess:()=>void;onLevel:(d:Level)=>void};
type Edit={player:Player;level?:Level;complete?:boolean};
const tier=(n:number)=>n.toFixed(1).replace('.',',');
const style=(p:Player)=>({'--player-color':PLAYER_META[p].color} as CSSProperties);
const date=(n:number)=>new Date(n).toLocaleString('es-UY',{timeZone:'America/Montevideo',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
function remaining(end:number,now:number){const minutes=Math.max(0,Math.ceil((end-now)/60000));if(minutes>=1440)return `${Math.floor(minutes/1440)} d ${Math.floor(minutes%1440/60)} h`;if(minutes>=60)return `${Math.floor(minutes/60)} h ${minutes%60} min`;return `${minutes} min`;}
function Face({value}:{value:string}){const key=value==='Official'?'hard':value.toLowerCase();return <img className="challenge-face" src={assetUrl(`assets/difficulties/demon-${key}.png`)} alt={value==='Official'?'Nivel oficial':`${value} Demon`} width="62" height="62"/>;}
function Progress({value,label}:{value:number;label:string}){return <div className="challenge-progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}><span style={{width:`${value}%`}}/></div>;}
function LevelTitle({d,onLevel}:{d:Level;onLevel:(d:Level)=>void}){return <div className="challenge-level"><Face value={d.difficulty}/><div><button className="challenge-level-name" onClick={()=>onLevel(d)}>{d.name}</button><span>{d.creator||'Creador sin datos'} · ID {d.id}</span><b>Tier {tier(d.tier)}</b></div></div>;}
function ChallengeCard({c,player,saved,shared,onEdit}:{c:Challenge|null;player:Player;saved:boolean;shared:Shared;onEdit:(edit:Edit)=>void}){
 const {competition:s,history,levels}=shared;
 const progress=challengeProgress(c,player,s.goals,history,levels);
 const done=challengeCompleted(c,player,history,levels);
 return <article className={`challenge-card ${done?'is-complete':''}`} style={style(player)}>
  <div className="challenge-player"><img src={assetUrl(`assets/avatars/${player}.png`)} alt="" width="39" height="39"/><strong>{player}</strong><span className={`challenge-chip ${done?'success':''}`}>{done?<><CheckCheck size={13}/>Superado</>:saved?'DIARIO':'Por fijar'}</span></div>
  {c?<><LevelTitle d={c} onLevel={shared.onLevel}/><p className="challenge-reference">Hardest base: <b>{tier(c.referenceTier)}</b> · meta: <b>{tier(c.targetTier)}</b></p><div className="challenge-progress-label"><span>{done?'':progress?'Mejor porcentaje':'Todavía sin progreso'}</span><strong>{progress} %</strong></div><Progress value={progress} label={`Desafío diario de ${player}`}/><div className="challenge-card-actions">{done?<span className="challenge-win"><Trophy size={16}/></span>:<><button className="game-button green small" onClick={()=>onEdit({player,level:c})}><Target size={16}/>{s.goals[player]?.id===c.id?'Actualizar %':'Jugar'}</button><button className="text-link" onClick={()=>onEdit({player,level:c,complete:true})}><Check size={16}/>100 %</button></>}</div></>:<p className="challenge-muted">No hay niveles pendientes dentro del rango. Se necesita el catálogo para elegir el desafío.</p>}
 </article>;
}
function WeeklyCard({shared,onEdit}:{shared:Shared;onEdit:(edit:Edit)=>void}){
 const s=shared.competition,c=s.weekly,p=s.player;if(!p)return null;
 const done=challengeCompleted(c,p,shared.history,shared.levels),progress=challengeProgress(c,p,s.goals,shared.history,shared.levels);
 return <section className="weekly-challenge game-panel"><div className="weekly-heading"><div><h2><CalendarDays size={25}/>Mi desafío semanal</h2></div><div className="weekly-clock"><span><Clock size={14}/>{remaining(s.periods.weekly.endsAt,s.now)}</span></div></div>{c?<><div className="weekly-level-row"><LevelTitle d={c} onLevel={shared.onLevel}/><div className="weekly-target"><small>60 % DE LA MEDIA</small><strong>{tier(c.targetTier)}</strong><span>tier de referencia</span></div></div><div style={style(p)}><div className="challenge-progress-label"><span>{done?'Superado':'Mi progreso'}</span><strong>{progress} %</strong></div><Progress value={progress} label="Mi desafío semanal"/></div>{!done&&<button className="game-button green small weekly-personal-action" onClick={()=>onEdit({player:p,level:c})}>Actualizar progreso</button>}</>:<p className="challenge-empty">Pendiente de asignación.</p>}</section>;
}
function GoalCard({player,shared,onEdit}:{player:Player;shared:Shared;onEdit:(edit:Edit)=>void}){
 const goal=shared.competition.goals[player];const level:Level|undefined=goal&&(shared.levels.find(d=>d.id===goal.id)||goal);
 const done=!!level?.[player];const best=done?100:goal?.best||0;
 const hardest=hardestTier(shared.levels,player);
 return <article className={`goal-card ${done?'is-complete':''}`} style={style(player)}><div className="challenge-player"><img src={assetUrl(`assets/avatars/${player}.png`)} alt="" width="39" height="39"/><strong>{player}</strong><Target size={19}/></div>
  {goal&&level?<><div className="goal-badge">{done?'¡OBJETIVO COMPLETADO!':level.tier>hardest?'PRÓXIMO HARDEST':'EN JUEGO'}</div><LevelTitle d={level} onLevel={shared.onLevel}/><div className="goal-best"><span>Mejor porcentaje</span><strong>{best}<small> %</small></strong></div><Progress value={best} label={`Mejor porcentaje de ${player} en ${goal.name}`}/><p className="challenge-muted">{done?'Ya figura entre sus completaciones. Elegí el próximo objetivo.':level.tier>hardest?`Salto de +${tier(level.tier-hardest)} tiers sobre su hardest actual.`:`Hardest actual: tier ${tier(hardest)}. Este nivel está en progreso.`}</p><button className="game-button blue small goal-edit" onClick={()=>onEdit({player})}><Pencil size={15}/>{done?'Elegir próximo objetivo':'Actualizar objetivo'}</button></>:<div className="goal-empty"><div><Target size={32}/></div><h3></h3><p>Elegí el nivel que está jugando y guardá su mejor porcentaje.</p><button className="game-button green small" onClick={()=>onEdit({player})}><Plus size={16}/>Elegir nivel</button></div>}
 </article>;
}
function GoalEditor({edit,shared,onClose}:{edit:Edit;shared:Shared;onClose:()=>void}){
 const saved=shared.competition.goals[edit.player];const initial=edit.level||(saved&&(shared.levels.find(d=>d.id===saved.id)||saved));
 const [selected,setSelected]=useState<Level|null>(initial||null);const [query,setQuery]=useState('');const [best,setBest]=useState(edit.complete?'100':String(initial?.id===saved?.id?saved?.best||0:0));
 const [error,setError]=useState('');const [remove,setRemove]=useState(false);const [pending,setPending]=useState(false);
 const dialog=useRef<HTMLDialogElement>(null);const onCloseRef=useRef(onClose);onCloseRef.current=onClose;const pendingRef=useRef(false);pendingRef.current=pending||shared.competition.busy;
 const busy=pending||shared.competition.busy;
 useEffect(()=>{const element=dialog.current;const before=document.activeElement as HTMLElement;element?.showModal();const cancel=(e:Event)=>{e.preventDefault();if(!pendingRef.current)onCloseRef.current();};element?.addEventListener('cancel',cancel);return()=>{element?.removeEventListener('cancel',cancel);element?.close();before?.focus();};},[]);
 const results=useMemo(()=>{const q=query.trim().toLowerCase();if(!q)return [];return shared.levels.filter(d=>/^\d+$/.test(d.id)&&!d[edit.player]&&`${d.name} ${d.id} ${d.creator}`.toLowerCase().includes(q)).sort((a,b)=>Number(b.id===q)-Number(a.id===q)||Number(b.name.toLowerCase()===q)-Number(a.name.toLowerCase()===q)).slice(0,25);},[query,shared.levels,edit.player]);
 const pick=(d:Level)=>{setSelected(d);setBest(String(d.id===saved?.id?saved.best:0));setQuery('');setError('');};
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setError('');if(!selected){setError('Elegí un nivel del catálogo.');return;}if(!/^\d{1,3}$/.test(best)||Number(best)>100){setError('Ingresá un porcentaje entero entre 0 y 100.');return;}setPending(true);try{await shared.competition.saveGoal(edit.player,selected,Number(best));onClose();}catch(e:any){setError(e?.message||'No se pudo guardar. Reintentá.');}finally{setPending(false);}};
 const clear=async()=>{setPending(true);setError('');try{await shared.competition.clearGoal(edit.player);onClose();}catch(e:any){setError(e?.message||'No se pudo retirar el objetivo.');}finally{setPending(false);}};
 return <dialog ref={dialog} className="game-modal goal-modal" aria-label={`Objetivo de ${edit.player}`}><div className="modal-title"><h2><Target size={22}/>Objetivo de {edit.player}</h2><button className="circle-button red" aria-label="Cerrar objetivo" disabled={busy} onClick={onClose}><X/></button></div><div className="modal-body"><form onSubmit={submit}>
  <p className="goal-form-intro"></p>
  <label className="goal-field"><span><Search size={15}/>Buscar nivel o ID</span><input autoFocus value={query} onChange={e=>{setQuery(e.target.value);setRemove(false);}} placeholder="Nombre, creador o ID del catálogo" disabled={busy}/></label>
  {!!query.trim()&&<div className="goal-results" aria-label="Resultados del catálogo">{results.length?results.map(d=><button key={d.id} type="button" onClick={()=>pick(d)}><Face value={d.difficulty}/><span><b>{d.name}</b><small>{d.creator} · ID {d.id}</small></span><strong>{tier(d.tier)}</strong></button>):<p>No hay niveles pendientes que coincidan. Probá con su ID.</p>}</div>}
  {selected&&<div className="goal-selected"><Face value={selected.difficulty}/><span><b>{selected.name}</b><small>{selected.creator} · ID {selected.id}</small></span><strong>Tier {tier(selected.tier)}</strong></div>}
  <label className="goal-field"><span>Mejor porcentaje (%)</span><input type="number" inputMode="numeric" min="0" max="100" step="1" value={best} onChange={e=>{setBest(e.target.value);setRemove(false);}} required disabled={busy}/></label>
  <p className="caption">{Number(best)===100?'Al guardar el 100 %, también se registra la completación y sus puntos en una misma operación.':'Se conserva el mejor porcentaje del mismo nivel. Al elegir otro nivel, el progreso empieza de nuevo.'}</p>
  {error&&<p className="form-error" role="alert">{error}</p>}
  <div className="modal-actions"><button type="button" className="text-link" disabled={busy} onClick={onClose}>Cancelar</button><button type="submit" className="game-button green" disabled={busy||!selected}>{busy?<LoaderCircle className="spin" size={17}/>:Number(best)===100?<CheckCheck size={18}/>:<Check size={18}/>} {Number(best)===100?'Registrar 100 %':'Guardar progreso'}</button></div>
  {saved&&<div className="goal-remove">{remove?<><p>¿Retirar el objetivo de {edit.player}? Sus completaciones se conservan.</p><button type="button" className="game-button red small" disabled={busy} onClick={()=>void clear()}>Retirar objetivo</button><button type="button" className="text-link" disabled={busy} onClick={()=>setRemove(false)}>Conservar</button></>:<button type="button" className="text-link" disabled={busy} onClick={()=>setRemove(true)}><Trash2 size={14}/>Retirar objetivo actual</button>}</div>}
 </form></div></dialog>;
}
function Area({shared,player}:{shared:Shared;player?:Player}){
 const [edit,setEdit]=useState<Edit|null>(null);const s=shared.competition;
 const onEdit=(value:Edit)=>{if(!shared.editor||(shared.canEdit&&!shared.canEdit(value.player))){shared.onAccess();return;}setEdit(value);};
 return <>
  {player?<section className="game-panel player-goal-panel"><div className="panel-heading"><h2><Target size={21}/>Su próximo objetivo</h2></div><GoalCard player={player} shared={shared} onEdit={onEdit}/></section>:<>
   <div className="page-title competition-title"><div><span className="eyebrow"></span><h1>Desafíos</h1><p></p></div><div className="competition-clock"><Clock size={18}/><span>El diario renueva en <b>{remaining(s.periods.daily.endsAt,s.now)}</b><small>00:00 de Uruguay · semanal: lunes</small></span></div></div>
   {s.rulesError?<div className="competition-notice" role="status"><InfoText/><span>Para activar los desafíos y objetivos, publicá <b>firebase.rules.json</b> de esta versión en Realtime Database → Rules.</span></div>:!s.connected&&s.loaded?<div className="competition-notice" role="status"><Clock size={20}/><span>Sin conexión a Firebase. Los cambios necesitan una conexión activa.</span></div>:null}
   <div className="competition-section-title"><div><h2><Target size={23}/>Desafíos diarios</h2><p>Referencia: 50 % del tier de tu hardest.</p></div><span className="challenge-chip">{date(s.periods.daily.startsAt).split(',')[0]}</span></div>
   <div className="challenge-grid personal-challenge-grid">{(s.player?[s.player]:[]).map(p=><ChallengeCard key={p} c={s.daily[p]} player={p} saved={s.isDailySaved(p)} shared={shared} onEdit={onEdit}/>)}</div>
   {(!!s.player&&(!s.isDailySaved(s.player)||!s.isWeeklySaved))&&<div className="challenge-preview-note"><span>Las propuestas se fijan durante la próxima verificación programada.</span>{shared.editor&&<button className="text-link" disabled={!s.loaded||!s.connected} onClick={()=>void s.ensure()}>Verificar asignación<ArrowRight size={15}/></button>}</div>}
   <WeeklyCard shared={shared} onEdit={onEdit}/>
   <div className="competition-section-title"><div><h2><Flame size={23}/>En juego · próximo hardest</h2><p></p></div></div>
   <div className="challenge-grid goal-grid personal-challenge-grid">{(s.player?[s.player]:[]).map(p=><GoalCard key={p} player={p} shared={shared} onEdit={onEdit}/>)}</div>
   <p className="competition-footnote">Para superar un desafío, la completación debe quedar registrada dentro de su día o semana. El progreso no suma puntos hasta completar el nivel. </p>
  </>}
  {edit&&<GoalEditor key={`${edit.player}:${edit.level?.id||'current'}:${!!edit.complete}`} edit={edit} shared={shared} onClose={()=>setEdit(null)}/>}
 </>;
}
function InfoText(){return <Target size={22}/>;}
export function CompetitionPage(props:Shared){return <Area shared={props}/>;}
export function PlayerGoalPanel(props:Shared&{player:Player}){return <Area shared={props} player={props.player}/>;}
export function CompetitionHome({competition:s,onOpen}:{competition:Competition;onOpen:()=>void}){const p=s.player;if(!p)return null;const c=s.daily[p];return <section className="game-panel home-challenges personal-home-challenges"><div className="panel-heading"><h2><Target size={22}/>Mis desafíos</h2><button className="panel-link" onClick={onOpen}>Abrir<ArrowRight size={15}/></button></div><div className="home-challenge-list"><button onClick={onOpen} style={style(p)}><img src={assetUrl(`assets/avatars/${p}.png`)} alt="" width="42" height="42"/><span><small>MI DEMON DIARIO</small><b>{c?.name||'Pendiente de asignación'}</b><em>{c?`Tier ${tier(c.tier)}`:''}</em></span><ArrowRight size={16}/></button><button className="home-weekly" onClick={onOpen}><CalendarDays size={32}/><span><small>MI SEMANAL</small><b>{s.weekly?.name||'Pendiente de asignación'}</b><em>{s.weekly?`Tier ${tier(s.weekly.tier)}`:''}</em></span><ArrowRight size={16}/></button></div></section>;}
