import {FORMS} from './config';
export function parsePairs(text:string){
  const arr=text.split(':');const out:Record<string,string>={};
  for(let i=0;i<arr.length-1;i+=2)out[arr[i]]=arr[i+1];
  return out;
}
export function parseProfile(raw:Record<string,string>){
  const n=(key:string)=>raw[key]===undefined?null:Number(raw[key]);
  const icons:Record<string,number|null>={};
  ['21','22','23','24','25','26','43','53','54'].forEach((key,i)=>icons[FORMS[i]]=n(key));
  return {username:raw['1'],accountId:raw['16'],userId:raw['2'],stars:n('3'),moons:n('52'),diamonds:n('46'),secretCoins:n('13'),userCoins:n('17'),demons:n('4'),creatorPoints:n('8'),rank:n('30'),color1:n('10'),color2:n('11'),color3:n('51'),glow:raw['28']==='1',icons};
}
export type GDProfile=ReturnType<typeof parseProfile>;
const origin='https://www.boomlings.com/database/';
export async function gdPost(endpoint:'getGJUserInfo20.php'|'getGJUsers20.php'|'getGJLevels21.php',params:Record<string,string>){
  const res=await fetch(origin+endpoint,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','User-Agent':''},body:new URLSearchParams({...params,secret:'Wmfd2893gb7',gameVersion:'22',binaryVersion:'45'}),signal:AbortSignal.timeout(14000)});
  if(!res.ok)throw Error('El servidor de GD no está disponible.');
  const text=await res.text();if(!text||text.trim()==='-1'||text.startsWith('<'))throw Error('GD no devolvió un resultado público.');
  return text;
}
export async function fetchGDProfile(accountId:string){
  const text=await gdPost('getGJUserInfo20.php',{targetAccountID:accountId});const raw=parsePairs(text);
  if(!raw['1']||raw['16']!==accountId)throw Error('No se pudo verificar la cuenta.');
  return {profile:parseProfile(raw),raw,fetchedAt:new Date().toISOString()};
}
export async function resolveGDUser(username:string){
  const text=await gdPost('getGJUsers20.php',{str:username,type:'0',page:'0'});
  const matches=text.split('#')[0].split('|').map(parsePairs).filter(p=>p['1']?.toLowerCase()===username.toLowerCase()&&Number(p['16'])>0);
  if(matches.length!==1)throw Error('No se encontró una cuenta con ese nombre exacto.');
  return fetchGDProfile(matches[0]['16']);
}
export async function fetchGDLevel(id:string){
  if(['1','2','3'].includes(id))return {official:true,id,message:'Nivel oficial: el ID de la hoja es interno, no un ID online.'};
  const text=await gdPost('getGJLevels21.php',{str:id,type:'0',page:'0'});
  const sections=text.split('#');const raw=sections[0].split('|').map(parsePairs).find(d=>d['1']===id);
  if(!raw)throw Error('No hay información pública para este ID.');
  const creator=(sections[1]||'').split('|').map(t=>t.split(':')).find(t=>t[0]===raw['6'])?.[1]||null;
  const n=(key:string)=>raw[key]===undefined?null:Number(raw[key]);
  const songId=n('35');let song=raw['12']===undefined?null:`Canción oficial #${Number(raw['12'])+1}`;
  if(songId){const entry=(sections[2]||'').split('~:~').find(t=>t.includes(`1~|~${songId}~|~`));if(entry){const a=entry.split('~|~');const obj=Object.fromEntries(Array.from({length:Math.floor(a.length/2)},(_,i)=>[a[i*2],a[i*2+1]]));song=obj['2']||`Canción #${songId}`;}else song=`Canción #${songId}`;}
  return {id,name:raw['2'],creator,stars:n('18'),downloads:n('10'),likes:n('14'),length:['Tiny','Short','Medium','Long','XL','Platformer'][Number(raw['15'])]||null,song,songId,fetchedAt:new Date().toISOString()};
}
