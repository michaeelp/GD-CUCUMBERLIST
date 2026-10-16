'use client';
import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {type Player} from '@/lib/config';
import {assetUrl} from '@/lib/catalog-client';
import {addPatch,buildLevels,type Level,type Records,type Histories} from '@/lib/domain';
import {liveRewards,type Receipt} from '@/lib/rewards';
export type Quest={id:string;kind:string;title:string;target:number;progress:number;reward:number;xp?:number;completed:boolean;expired?:boolean;level?:Level;options?:Level[];stat?:string;baseline?:number;baselineAt?:number;createdAt?:number;waitingBaseline?:boolean;awardType?:string;parts?:Quest[]};
export type GameState={wallet:{balance:number;earned:number;xp:number;ledger:Record<string,{amount:number;reason:string;at:number;statMission?:boolean;kind?:string}>;paidLevels?:Record<string,boolean>;owned:Record<string,boolean>;equipped?:Record<string,string>};daily:{day:string;startsAt:number;endsAt:number;rerollsUsed:number;quests:Quest[]};bingo:{month:string;activatedAt:number;endsAt:number;replacementsUsed:number;cells:Quest[];lines?:number[];completed?:boolean};archive?:Record<string,GameState['daily']>;bingoArchive?:Record<string,GameState['bingo']>;processed?:Record<string,{ok:boolean;message:string;at:number}>;assignments?:Record<string,any>;initialCredit?:any;activatedAt?:number;version?:number;updatedAt:number};
export type Product={id:string;name:string;kind:string;value:string;price:number;palette?:{background:string;panel:string;accent:string;text:string;muted:string}};
export type PublicProfile={title?:string;color?:string;badge?:string;theme?:string;font?:string;nickname?:string;bio?:string;showActivity?:boolean};
export function useGame({firebase,player,admin,catalog,levels,records,history,notify}:{firebase:any;player:Player|null;admin:boolean;catalog:Level[];levels:Level[];records:Records;history:Histories;notify:(s:string)=>void}){
 const [storedRaw,setRaw]=useState<GameState|null>(null),[publicProfiles,setPublicProfiles]=useState<Record<string,PublicProfile>>({}),[storedPrefs,setPrefs]=useState<Record<string,any>>({}),[storedRuns,setOwnRuns]=useState<Record<string,any>>({}),[storedGoal,setGoal]=useState<any>(null),[storedProfile,setProfile]=useState<any>(null),[meta,setMeta]=useState<any>({}),[shop,setShop]=useState<Product[]>([]),[loaded,setLoaded]=useState(false),[rulesError,setRulesError]=useState(false),[connected,setConnected]=useState(false),[now,setNow]=useState(Date.now()),[revision,setRevision]=useState(0),[bankBusy,setBankBusy]=useState(false);
 const privateOwner=useRef<Player|null>(null),sameAccount=privateOwner.current===player;
 const raw=sameAccount?storedRaw:null,prefs=sameAccount?storedPrefs:{},ownRuns=sameAccount?storedRuns:{},goal=sameAccount?storedGoal:null,profile=sameAccount?storedProfile:null;
 const offset=useRef(0),pending=useRef(new Set<string>()),settling=useRef(false),currentPlayer=useRef(player);currentPlayer.current=player;
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()+offset.current),30000);return()=>clearInterval(timer);},[]);
 useEffect(()=>{let active=true;fetch(assetUrl('data/shop.json')).then(r=>r.json()).then((d:any)=>{if(active)setShop(Array.isArray(d)?d:Object.values(d));}).catch(()=>{});return()=>{active=false;};},[]);
 useEffect(()=>{privateOwner.current=player;setRaw(null);setOwnRuns({});setPrefs({});setGoal(null);setProfile(null);setLoaded(false);setRulesError(false);pending.current.clear();if(!firebase)return;const db=firebase.database(),cleanups:(()=>void)[]=[];let active=true;
 const listen=(path:string,cb:(v:any)=>void,privateData=false)=>{const ref=db.ref(path),on=(s:any)=>{if(active)cb(s.val());},fail=()=>{if(active&&privateData){setRulesError(true);setLoaded(true);}};ref.on('value',on,fail);cleanups.push(()=>ref.off('value',on));};
 listen('publicProfiles',v=>setPublicProfiles(v||{}));listen('gameMeta',v=>{setMeta(v||{});if(v?.shop)setShop(Array.isArray(v.shop)?v.shop:Object.values(v.shop));});listen('.info/connected',v=>setConnected(v===true));listen('.info/serverTimeOffset',v=>{offset.current=Number(v)||0;setNow(Date.now()+offset.current);});
 if(player){listen('gameState/'+player,v=>{setRaw(v||null);setLoaded(true);setRulesError(false);},true);listen('runs/'+player,v=>setOwnRuns(v||{}),true);listen('preferences/'+player,v=>setPrefs(v||{}),true);listen('objetivos/'+player,v=>setGoal(v));listen('verifiedProfiles/'+player,v=>setProfile(v));}else setLoaded(true);
 return()=>{active=false;cleanups.forEach(fn=>fn());};},[firebase,player]);
 const canEdit=useCallback((p:Player)=>!!firebase?.auth().currentUser&&p===player,[firebase,player]);
 const guard=(p:Player)=>{if(!canEdit(p)||currentPlayer.current!==p)throw Error('Esta sección pertenece a la cuenta que inició sesión.');if(!connected)throw Error('Sin conexión a Firebase.');};
 const live=useMemo(()=>raw&&player?liveRewards(raw,{player,levels,records,history,runs:ownRuns,goal,profile,now}):null,[raw,player,levels,records,history,ownRuns,goal,profile,now,revision]);
 const states=useMemo(()=>player&&live?{[player]:live.state}:{} as Partial<Record<Player,GameState>>,[player,live]);
 const commit=async(p:Player,receipt:Receipt)=>{guard(p);const uid=firebase.auth().currentUser.uid;const db=firebase.database(),base='gameState/'+p+'/wallet';
 for(let attempt=0;attempt<4;attempt++){
  if(currentPlayer.current!==p||firebase.auth().currentUser?.uid!==uid)throw Error('La sesión cambió.');
  const wallet=(await db.ref(base).get()).val();if(!wallet)throw Error('Falta activar la cuenta con el verificador.');if(wallet.ledger?.[receipt.key])return false;
  const {key,...body}=receipt;let amount=body.amount;
  if(body.kind==='purchase'){const item=(await db.ref('shopCatalog/'+body.item).get()).val();if(!item)throw Error('Actualizá el catálogo con el verificador.');if(wallet.owned?.[body.item!])return false;amount=-item.price;if(wallet.balance+amount<0)throw Error('Monedas insuficientes.');body.reason='Compra: '+item.name;}
  if(body.kind==='level'){const item=(await db.ref('levelCatalog/'+body.levelId).get()).val();if(!item)throw Error('Nivel pendiente de verificar en el catálogo.');amount=20+Math.floor(item.tier*2);}
  if(currentPlayer.current!==p||firebase.auth().currentUser?.uid!==uid)throw Error('La sesión cambió.');
  const patch:Record<string,unknown>={[base+'/lastOp']:key,[base+'/ledger/'+key]:{...body,amount,at:firebase.database.ServerValue.TIMESTAMP},[base+'/balance']:wallet.balance+amount,[base+'/xp']:(wallet.xp||0)+body.xp,[base+'/earned']:(wallet.earned||0)+Math.max(0,amount)};
  if(body.kind==='purchase')patch[base+'/owned/'+body.item]=true;if(body.kind==='level')patch[base+'/paidLevels/'+body.levelId]=true;
  try{await db.ref().update(patch);return true;}catch(e:any){if(attempt===3)throw e;}
 }return false;};
 useEffect(()=>{if(!player||!raw||!live||!connected||raw.version!==4||prefs.autoRewards===false||settling.current||!live.receipts.length)return;settling.current=true;void(async()=>{let changed=false;try{for(const receipt of live.receipts){if(currentPlayer.current!==player)break;try{changed=await commit(player,receipt)||changed;}catch{break;}}}finally{settling.current=false;if(changed&&currentPlayer.current===player)setRevision(n=>n+1);}})();},[player,raw,live,connected,prefs.autoRewards,revision]);
 const collect=async()=>{if(!player||!live)return;setBankBusy(true);try{for(const receipt of live.receipts)await commit(player,receipt);notify('Recompensas confirmadas.');setRevision(n=>n+1);}catch{notify('No se pudo confirmar una recompensa. Revisá conexión y reglas.');}finally{setBankBusy(false);}};
 const customize=async(field:keyof PublicProfile,value:string|boolean|null)=>{if(!player)return;guard(player);await firebase.database().ref(`publicProfiles/${player}/${field}`).set(value);};
 const request=async(p:Player,kind:string,extra:Record<string,unknown>={})=>{try{guard(p);
  if(kind==='purchase'){const item=shop.find(x=>x.id===extra.item);if(!item)throw Error('Artículo no disponible.');setBankBusy(true);const applied=await commit(p,{key:'buy_'+item.id,kind:'purchase',item:item.id,amount:-item.price,xp:0,reason:'Compra: '+item.name,statMission:false});notify(applied?'Compra confirmada.':'Ya tenés este artículo.');return;}
  if(kind==='equip'){const item=shop.find(x=>x.id===extra.item);if(!item)throw Error('Artículo no disponible.');await customize(item.kind as keyof PublicProfile,item.id);notify('Perfil actualizado.');return;}
  if(!raw)throw Error('Activá el verificador para recibir misiones.');const ref=firebase.database().ref('requests/'+p).push();await ref.set({kind,...extra,at:firebase.database.ServerValue.TIMESTAMP});pending.current.add(ref.key);notify('Solicitud guardada para la próxima verificación.');
 }catch(e:any){notify(e?.code==='PERMISSION_DENIED'?'Firebase rechazó la operación. Publicá las reglas de esta versión y comprobá tu cuenta.':e.message||'No se pudo guardar.');}finally{setBankBusy(false);}};
 useEffect(()=>{const processed=raw?.processed||{};for(const id of [...pending.current])if(processed[id]){notify(processed[id].message);pending.current.delete(id);}},[raw,notify]);
 const progress=async(p:Player,d:Level,best:number)=>{guard(p);if(!Number.isInteger(best)||best<0||best>100)throw Error('Usá un porcentaje entero de 0 a 100.');const db=firebase.database(),timestamp=firebase.database.ServerValue.TIMESTAMP;
 if(best===100){const data:Records=(await db.ref('pasados').get()).val()||{},current=buildLevels(data,catalog).find(l=>l.id===d.id)||d;const patch:Record<string,unknown>=current[p]?{}:addPatch(current,p,data,timestamp);patch[`runs/${p}/${d.id}`]={best:100,updatedAt:timestamp};await db.ref().update(patch);}else await db.ref(`runs/${p}/${d.id}`).transaction((old:any)=>({best:Math.max(old?.best||0,best),updatedAt:timestamp}),undefined,false);notify(best===100?'Completación registrada.':'Porcentaje guardado.');};
 const preference=async(path:string,value:unknown)=>{if(!player)return;try{guard(player);await firebase.database().ref(`preferences/${player}/${path}`).set(value);}catch{notify('No se pudo guardar el ajuste.');}};
 const coop:Record<string,any>=player&&raw?.assignments?.cooperative?{[String(raw.assignments.cooperative.period)]:raw.assignments.cooperative}:{};
 const initial=player&&raw?.initialCredit?{players:{[player]:raw.initialCredit}}:null;
 return {states,raw,coop,prefs,runs:player?{[player]:ownRuns}:{},meta,shop,preview:!raw,loaded,rulesError,connected,initial,player,admin,canEdit,request,progress,preference,now,publicProfiles,customize,bankBusy,collect,pendingRewards:live?.receipts.length||0};
}
export type Game=ReturnType<typeof useGame>;
