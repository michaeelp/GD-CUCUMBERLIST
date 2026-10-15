'use client';
import {useEffect,useState} from 'react';
import {PLAYER_META,type Player} from '@/lib/config';
import type {GDProfile} from '@/lib/gd';
import {assetUrl} from '@/lib/catalog-client';
const pending=new Map<string,Promise<string>>();
let rendererPromise:Promise<{renderer:any;apps:any[];colorHex:(n:number)=>string|null}>|null=null;
let queue:Promise<unknown>=Promise.resolve();
function engine(){
  if(!rendererPromise)rendererPromise=Promise.all([import('pixi.js'),import('gavatar/renderer'),import('gavatar/utils')]).then(([PIXI,lib,utils])=>{
    const apps:any[]=[];
    class CapturedApplication extends PIXI.Application{constructor(options:any){super({...options,preserveDrawingBuffer:true});apps.push(this);}}
    const pixi={...PIXI,Application:CapturedApplication};
    return {renderer:new lib.IconRenderer(pixi as any,{assetsPath:assetUrl('assets'),defaultSize:400}),apps,colorHex:utils.colorIndexToHex};
  });
  return rendererPromise!;
}
function iconData(profile:GDProfile,form:string){
  const id=profile.icons[form];
  if(id===null||id===undefined) return Promise.reject(Error('Forma no informada por GD.'));
  const key=JSON.stringify([form,id,profile.color1,profile.color2,profile.color3,profile.glow]);
  if(pending.has(key))return pending.get(key)!;
  try{const cached=sessionStorage.getItem(`gd-icon:${key}`);if(cached)return Promise.resolve(cached);}catch{}
  const task=queue.catch(()=>{}).then(async()=>{
    const {renderer,apps,colorHex}=await engine();
    if(id>renderer.getMaxIconID(form))throw Error('El renderizador todavía no conoce este ID.');
    try{
      const canvas:HTMLCanvasElement=await Promise.race([renderer.render({form,iconID:id,col1:profile.color1??0,col2:profile.color2??0,glow:profile.glow,glowColor:profile.color3===null?undefined:colorHex(profile.color3)??undefined,size:400}),new Promise<never>((_,reject)=>setTimeout(()=>reject(Error('Tiempo de renderizado agotado.')),15000))]);
      const copy=window.document.createElement('canvas');copy.width=canvas.width;copy.height=canvas.height;const ctx=copy.getContext('2d')!;ctx.drawImage(canvas,0,0);const pixels=ctx.getImageData(0,0,copy.width,copy.height).data;let x0=copy.width,y0=copy.height,x1=0,y1=0;for(let y=0;y<copy.height;y++)for(let x=0;x<copy.width;x++){if(pixels[(y*copy.width+x)*4+3]>8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}}if(x1<x0||y1<y0)throw Error('El icono no tiene capas disponibles.');const out=window.document.createElement('canvas');out.width=180;out.height=180;const target=out.getContext('2d')!;const width=x1-x0+1,height=y1-y0+1,scale=154/Math.max(width,height);target.drawImage(copy,x0,y0,width,height,(180-width*scale)/2,(180-height*scale)/2,width*scale,height*scale);const data=out.toDataURL('image/png');try{sessionStorage.setItem(`gd-icon:${key}`,data);}catch{}return data;
    }finally{for(const app of apps.splice(0))try{app.destroy(true,{children:true,texture:false,baseTexture:false});}catch{}}
  });
  queue=task;pending.set(key,task);task.catch(()=>pending.delete(key));return task;
}
export function Avatar({player,profile,size=60}:{player:Player;profile?:GDProfile;size?:number}){
  const [src,setSrc]=useState<string|undefined>(profile?.accountId===PLAYER_META[player].accountId?assetUrl(`assets/avatars/${player}.png`):undefined);
  useEffect(()=>{let active=true;setSrc(profile?.accountId===PLAYER_META[player].accountId?assetUrl(`assets/avatars/${player}.png`):undefined);if(profile)iconData(profile,'cube').then(s=>{if(active)setSrc(s);}).catch(()=>{});return()=>{active=false;};},[profile]);
  return <span className={`gd-avatar ${!profile?'unverified-avatar':''}`} style={{width:size,height:size,'--avatar-color':PLAYER_META[player].color} as React.CSSProperties}>{src?<img src={src} alt={`Icono cube de ${profile?.username||player}`} width={size} height={size} draggable={false} onError={()=>setSrc(undefined)}/>:<span className="unknown-avatar" title="Cuenta GD sin vincular">?</span>}</span>;
}
export function FormIcon({profile,form}:{profile:GDProfile;form:string}){
  const [src,setSrc]=useState<string>();const [failed,setFailed]=useState(false);
  useEffect(()=>{let active=true;setSrc(undefined);setFailed(false);iconData(profile,form).then(data=>{if(active)setSrc(data);}).catch(()=>{if(active)setFailed(true);});return()=>{active=false;};},[profile,form]);
  return <span className="form-icon">{src?<img src={src} alt={`${form} #${profile.icons[form]} de ${profile.username}`} width={68} height={68}/>:<span title={failed?'No se pudo renderizar esta forma':'Cargando forma'}>{failed?'—':'· · ·'}</span>}</span>;
}
