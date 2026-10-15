import {resolve} from 'node:path';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {assetUrl,gdRequest} from '../lib/catalog-client';
const folder=resolve('..');
const requests:string[]=[];
globalThis.fetch=async(input:any)=>{const path=String(input);requests.push(path);assert.ok(path.startsWith('./data/'),path);return new Response(readFileSync(folder+'/'+path.split('?')[0]),{headers:{'Content-Type':'application/json'}});};
test('rutas válidas en raíz y bajo cualquier repositorio',()=>{
 for(const base of ['https://usuario.github.io/','https://usuario.github.io/mi-repo/','https://ejemplo.com/carpeta/index.html']){
  for(const path of ['assets/avatars/nzrv.png','assets/vendor/firebase-app-compat.js','data/profiles.json']){
   const url=new URL(assetUrl(path),base);const expected=new URL('.',base);assert.ok(url.href.startsWith(expected.href));
  }
 }
 assert.equal(assetUrl('/assets/x.png'),'./assets/x.png');
});
test('Nzrvv se carga del JSON publicado sin un backend',async()=>{
 const r=await gdRequest('account=13334739');const d:any=await r.json();assert.equal(r.status,200);assert.equal(d.profile.username.toLowerCase(),'nzrvv');assert.equal(d.profile.accountId,'13334739');assert.equal(d.profile.demons,68);
});
test('búsqueda de cuenta publicada sin diferencia de mayúsculas',async()=>{
 const r=await gdRequest('user=Nzrvv');const d:any=await r.json();assert.equal(r.status,200);assert.equal(d.profile.accountId,'13334739');
});
test('cuenta desconocida se muestra como no disponible',async()=>{const r=await gdRequest('user=NombreNoPublicado');assert.equal(r.status,404);});
test('detalles usan un nivel verificado de la copia publicada',async()=>{
 const levels=JSON.parse(readFileSync(folder+'/data/level-details.json','utf8')).data;const id=Object.keys(levels)[0];assert.ok(id);const r=await gdRequest('level='+id);const d:any=await r.json();assert.equal(r.status,200);assert.equal(d.id,id);assert.equal(d.name,levels[id].name);
});
test('ninguna petición intenta acceder a /api en GitHub Pages',()=>{assert.ok(requests.length>0);assert.ok(requests.every(path=>!path.includes('/api/')));});
