import {PLAYERS,type Player} from './config';
export type Level = {id:string;name:string;creator:string;difficulty:string;tier:number;history?:Partial<Record<Player,string>>;thiaguinhio?:boolean;michaeelp?:boolean;nzrv?:boolean;_keys?:string[];_rank?:number};
export type History = {player:string;demonKey:string;demon:string;tier:number;difficulty?:string;creator?:string;timestamp?:number;_key?:string};
export type Records = Record<string,Level>;
export type Histories = Record<string,History>;
export type Change = {id:string;name:string;changes:{field:string;from:unknown;to:unknown}[]};
export const points = (tier:number) => Math.round(Number(tier)*10*1e8)/1e8;
export const normalize = (v:unknown) => String(v??'').trim().toLowerCase();
export const completed = (d:Level) => PLAYERS.some(p=>!!d[p]);
export function parseSheet(text:string):Level[]{
  const m=text.match(/google\.visualization\.Query\.setResponse\(([\s\S]*)\);?\s*$/);
  if(!m) throw Error('La hoja no devolvió un documento válido.');
  const json=JSON.parse(m[1]);
  if(json.status==='error'||!Array.isArray(json.table?.rows)) throw Error('No se pudo leer la hoja pública.');
  const seen=new Set<string>();
  return json.table.rows.flatMap((r:{c:({v:unknown}|null)[]})=>{
    const c=r.c;
    const id=String(c[0]?.v??''); const name=String(c[1]?.v??'').trim();
    const raw=c[5]?.v; const tier=Math.floor(Number(raw)*10)/10;
    if(!/^\d+$/.test(id)||!name||raw===null||raw===undefined||raw===''||!Number.isFinite(tier)||tier<0||seen.has(id))return [];
    seen.add(id);
    return [{id,name,creator:String(c[2]?.v??''),difficulty:String(c[4]?.v??''),tier}];
  }).sort((a:Level,b:Level)=>b.tier-a.tier||a.name.localeCompare(b.name));
}
export function resolveSheetLevel(item:Partial<Level>,key:string,catalog:Level[]):Level|undefined{
  const id=String(item.id??key);
  const direct=catalog.find(d=>d.id===id);
  if(direct)return direct;
  if(item.id||/^\d+$/.test(key))return undefined;
  const matches=catalog.filter(d=>normalize(d.name)===normalize(item.name)&&(!item.creator||normalize(d.creator)===normalize(item.creator)));
  return matches.length===1?matches[0]:undefined;
}
export function buildLevels(records:Records,catalog:Level[]):Level[]{
  const map=new Map<string,Level>(catalog.map(d=>[d.id,{...d,_keys:[] as string[]}]));
  for(const [key,item] of Object.entries(records)){
    if(!item||typeof item!=='object'||!item.name||!Number.isFinite(Number(item.tier)))continue;
    const matched=resolveSheetLevel(item,key,catalog);
    const id=String(item.id??matched?.id??key);
    const prior=map.get(id);
    const active=prior?._keys?.length;
    const d:Level=active?{...prior}:{...prior,...item,id,tier:Number(item.tier),_keys:[]};
    d._keys=[...(prior?._keys||[]),key];
    for(const p of PLAYERS)d[p]=!!prior?.[p]||!!item[p];
    d.history={...(prior?.history||{}),...(item.history||{})};
    map.set(id,d);
  }
  return Array.from(map.values()).sort((a,b)=>b.tier-a.tier||a.name.localeCompare(b.name)).map((d,i)=>({...d,_rank:i+1}));
}
export function rankings(levels:Level[]){
  return PLAYERS.map(player=>{
    const list=levels.filter(d=>d[player]).sort((a,b)=>b.tier-a.tier);
    const score=points(list.reduce((sum,d)=>sum+d.tier,0));
    return {player,list,score,count:list.length,hardest:list[0],average:list.length?list.reduce((s,d)=>s+d.tier,0)/list.length:0};
  }).sort((a,b)=>b.score-a.score||PLAYERS.indexOf(a.player)-PLAYERS.indexOf(b.player));
}
export function historyMatches(h:History,d:Level){
  if(String(h.demonKey)===d.id||d._keys?.includes(String(h.demonKey)))return true;
  if(/^\d+$/.test(String(h.demonKey)))return false;
  return normalize(h.demon)===normalize(d.name)&&(!h.creator||normalize(h.creator)===normalize(d.creator));
}
export function addPatch(d:Level,player:Player,records:Records,timestamp:unknown){
  if(!PLAYERS.includes(player))throw Error('Jugador no válido.');
  if(!/^\d+$/.test(d.id))throw Error('Este registro necesita vincularse a un ID verificado antes de añadir completaciones.');
  if(d[player])throw Error('Este jugador ya completó el nivel.');
  const key=d._keys?.[0]||d.id;
  const historyKey=`${d.id}_${player}`;
  const base=`pasados/${key}`;
  const patch:Record<string,unknown>={};
  if(!records[key])for(const f of ['id','name','creator','difficulty','tier'] as const)patch[`${base}/${f}`]=d[f]??'';
  else if(!records[key].id)patch[`${base}/id`]=d.id;
  patch[`${base}/${player}`]=true;
  patch[`${base}/history/${player}`]=historyKey;
  patch[`historial/${historyKey}`]={player,demonKey:d.id,demon:d.name,creator:d.creator||'',difficulty:d.difficulty||'',tier:d.tier,timestamp};
  return patch;
}
export function removePatch(d:Level,player:Player,records:Records,history:Histories){
  if(!PLAYERS.includes(player))throw Error('Jugador no válido.');
  const patch:Record<string,unknown>={};
  for(const key of d._keys||[d.id]){
    if(!records[key]?.[player])continue;
    patch[`pasados/${key}/${player}`]=false;
    patch[`pasados/${key}/history/${player}`]=null;
    const old=records[key]?.history?.[player];
    // A damaged old pointer may belong to another player: never delete it.
    if(old&&history[old]?.player===player&&historyMatches(history[old],d))patch[`historial/${old}`]=null;
  }
  for(const [key,h] of Object.entries(history))if(h.player===player&&historyMatches(h,d))patch[`historial/${key}`]=null;
  return patch;
}
export function diffLevel(old:Partial<Level>,d:Level):Change['changes']{
  return (['tier','difficulty','name','creator'] as const).flatMap(field=>{
    const from=field==='tier'?Number(old[field]):String(old[field]??'');
    const to=d[field];
    return from===to?[]:[{field,from,to}];
  });
}
export function syncPatch(records:Records,history:Histories,catalog:Level[]){
  const patch:Record<string,unknown>={};const changes:Change[]=[];
  for(const [key,item] of Object.entries(records)){
    const d=resolveSheetLevel(item,key,catalog);if(!d)continue;
    const diff=diffLevel(item,d);
    if(diff.length)changes.push({id:d.id,name:d.name,changes:diff});
    for(const c of diff)patch[`pasados/${key}/${c.field}`]=c.to;
    if(!item.id)patch[`pasados/${key}/id`]=d.id;
  }
  for(const [key,h] of Object.entries(history)){
    const item=records[h.demonKey];
    const match=catalog.find(d=>d.id===String(h.demonKey))|| (item?resolveSheetLevel(item,h.demonKey,catalog):undefined);
    const byName=match||(()=>{const a=catalog.filter(d=>normalize(d.name)===normalize(h.demon)&&(!h.creator||normalize(d.creator)===normalize(h.creator)));return a.length===1?a[0]:undefined;})();
    if(!byName)continue;
    for(const c of diffLevel({name:h.demon,creator:h.creator,difficulty:h.difficulty,tier:h.tier},byName))patch[`historial/${key}/${c.field==='name'?'demon':c.field}`]=c.to;
  }
  return {patch,changes};
}
export function applyMultiPath<T>(initial:T,patch:Record<string,unknown>):T{
  const next=JSON.parse(JSON.stringify(initial));
  for(const [path,value] of Object.entries(patch)){
    const keys=path.split('/').filter(Boolean);let node=next;
    for(const k of keys.slice(0,-1))node=node[k]??=( {} );
    const last=keys[keys.length-1];if(value===null)delete node[last];else node[last]=value;
  }
  return next;
}
