import {SHEET_URL} from './config';
import {parseSheet} from './domain';
import {parseProfile} from './gd';
export function assetUrl(path:string){return `./${path.replace(/^\/+/, '')}`;}
let profileTask:Promise<any>|null=null;
let profileAt=0;
async function publishedProfiles(){
 if(!profileTask||Date.now()-profileAt>120000){profileAt=Date.now();profileTask=fetch(assetUrl(`data/profiles.json?v=${Math.floor(Date.now()/120000)}`)).then(async r=>{if(!r.ok)throw Error('No se pudieron cargar los perfiles publicados.');return r.json();}).catch(e=>{profileTask=null;throw e;});}
 return profileTask;
}
export async function gdRequest(query:string):Promise<Response>{
 const params=new URLSearchParams(query);const level=params.get('level');
 if(level){
  if(['1','2','3'].includes(level))return Response.json({official:true,id:level,message:'Nivel oficial: el ID de la hoja es interno.'});
  const r=await fetch(assetUrl('data/level-details.json'));if(!r.ok)return Response.json({error:'Sin datos de GD publicados para este nivel.'},{status:404});
  const json:any=await r.json();const d=json.data?.[level];return d?Response.json(d):Response.json({error:'Sin datos de GD publicados para este nivel.'},{status:404});
 }
 const profiles=await publishedProfiles();
 const account=params.get('account'),user=params.get('user')?.toLowerCase();
 const data=Object.values(profiles).find((d:any)=>d?.raw&&(account?d.raw['16']===account:d.raw['1']?.toLowerCase()===user)) as any;
 if(!data)return Response.json({error:'Esta cuenta no está en los datos publicados. Agregala en cuentas.json y ejecutá GitHub Actions.'},{status:404});
 return Response.json({profile:parseProfile(data.raw),fetchedAt:data.fetchedAt});
}
export function sheetJSONP(){
 return new Promise<{data:ReturnType<typeof parseSheet>;fetchedAt:string}>((resolve,reject)=>{
  const name=`cucumberSheet${Date.now()}${Math.floor(Math.random()*100000)}`;
  const script=window.document.createElement('script');
  const cleanup=()=>{clearTimeout(timer);script.remove();delete (window as any)[name];};
  const timer=setTimeout(()=>{cleanup();reject(Error('Google Sheets no respondió.'));},20000);
  (window as any)[name]=(json:unknown)=>{try{const data=parseSheet(`google.visualization.Query.setResponse(${JSON.stringify(json)});`);cleanup();resolve({data,fetchedAt:new Date().toISOString()});}catch(e){cleanup();reject(e);}};
  const url=new URL(SHEET_URL);url.searchParams.set('tqx',`out:json;responseHandler:${name}`);script.src=url.toString();script.onerror=()=>{cleanup();reject(Error('No se pudo cargar Google Sheets.'));};window.document.head.appendChild(script);
 });
}
