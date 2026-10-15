import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildLevels,rankings,points,addPatch,removePatch,syncPatch,applyMultiPath,parseSheet,historyMatches,resolveSheetLevel,type Level,type Records} from '../lib/domain';
import {parseProfile,parsePairs,fetchGDLevel} from '../lib/gd';
import snapshot from '../lib/bootstrap.json';
const catalog=JSON.parse(readFileSync('../data/catalog.json','utf8')).data;
const source={pasados:snapshot.records,historial:snapshot.history};
const d:Level={id:'42',name:'Prueba',creator:'Creator',difficulty:'Hard',tier:12.3};

test('los puntajes y las 259 completaciones reales se conservan',()=>{
 const ranks=rankings(buildLevels(snapshot.records as any,catalog));
 assert.deepEqual(ranks.map(r=>[r.player,r.count,r.score]),[['thiaguinhio',179,11680],['nzrv',58,2387],['michaeelp',22,447]]);
 assert.equal(ranks.reduce((s,p)=>s+p.count,0),259);
 assert.equal(points(12.3),123);
});
test('dos jugadores registran el mismo demon sin sobrescribir sus datos o historial',()=>{
 const a=addPatch(d,'thiaguinhio',{},1000);const b=addPatch(d,'michaeelp',{},2000);
 const first=applyMultiPath(applyMultiPath({pasados:{},historial:{}},a),b) as any;
 const second=applyMultiPath(applyMultiPath({pasados:{},historial:{}},b),a) as any;
 for(const result of [first,second]){assert.equal(result.pasados['42'].thiaguinhio,true);assert.equal(result.pasados['42'].michaeelp,true);assert.equal(Object.keys(result.historial).length,2);assert.equal(result.historial['42_thiaguinhio'].timestamp,1000);}
});
test('un registro existente conserva metadatos y el resto de los jugadores',()=>{
 const records:Records={'42':{...d,creator:'Actualizado en Sheets',thiaguinhio:true,history:{thiaguinhio:'old'}}};
 const a=addPatch({...d,_keys:['42']},'michaeelp',records,1000);
 assert.equal(a['pasados/42/creator'],undefined);assert.equal(a['pasados/42/thiaguinhio'],undefined);
 const result=applyMultiPath({pasados:records,historial:{old:{player:'thiaguinhio'}}},a) as any;
 assert.equal(result.pasados['42'].history.thiaguinhio,'old');assert.equal(result.pasados['42'].creator,'Actualizado en Sheets');
});
test('el mismo jugador no recibe un historial duplicado',()=>{
 const a=addPatch(d,'nzrv',{},1000),b=addPatch(d,'nzrv',{},2000);
 assert.deepEqual(Object.keys(a),Object.keys(b));
 const result=applyMultiPath(applyMultiPath({pasados:{},historial:{}},a),b) as any;
 assert.equal(Object.keys(result.historial).length,1);
 assert.throws(()=>addPatch({...d,nzrv:true},'nzrv',{},1000),/ya completó/);
});
test('retirar nunca elimina el historial de otro jugador aunque un puntero antiguo esté dañado',()=>{
 const records:Records={'42':{...d,thiaguinhio:true,michaeelp:true,history:{michaeelp:'someone-else',thiaguinhio:'someone-else'}}};
 const h:any={'someone-else':{player:'thiaguinhio',demonKey:'42',demon:'Prueba',tier:12.3,timestamp:1},correct:{player:'michaeelp',demonKey:'42',demon:'Prueba',tier:12.3,timestamp:2}};
 const delta=removePatch({...d,...records['42'],_keys:['42']},'michaeelp',records,h);
 assert.equal(delta['historial/someone-else'],undefined);assert.equal(delta['historial/correct'],null);
 const result=applyMultiPath({pasados:records,historial:h},delta) as any;
 assert.equal(result.pasados['42'].thiaguinhio,true);assert.equal(result.historial['someone-else'].player,'thiaguinhio');assert.equal(result.pasados['42'].history.thiaguinhio,'someone-else');
});
test('retirar y agregar otro jugador son conmutativos',()=>{
 const records:Records={'42':{...d,thiaguinhio:true}};const rm=removePatch({...records['42'],_keys:['42']},'thiaguinhio',records,{});const add=addPatch({...d,_keys:['42']},'nzrv',records,100);
 const a=applyMultiPath(applyMultiPath({pasados:records,historial:{}},rm),add);const b=applyMultiPath(applyMultiPath({pasados:records,historial:{}},add),rm);
 assert.deepEqual(a,b);assert.equal((a as any).pasados['42'].nzrv,true);assert.ok((a as any).pasados['42']);
});
test('sincronizar modifica solo metadatos sin fechas o completaciones',()=>{
 const records:Records={'42':{...d,thiaguinhio:true,history:{thiaguinhio:'a'}}};const history:any={a:{player:'thiaguinhio',demonKey:'42',demon:'Prueba',tier:12.3,timestamp:17}};
 const {patch,changes}=syncPatch(records,history,[{...d,tier:15.2,name:'Renombrado',creator:'Nuevo'}]);
 assert.ok(changes.length);assert.equal(patch['pasados/42/tier'],15.2);assert.equal(patch['historial/a/demon'],'Renombrado');
 assert.equal(patch['historial/a/timestamp'],undefined);assert.equal(patch['pasados/42/thiaguinhio'],undefined);assert.equal(patch['pasados/42/history'],undefined);
 const repeat=syncPatch((applyMultiPath({pasados:records,historial:history},patch) as any).pasados,(applyMultiPath({pasados:records,historial:history},patch) as any).historial,[{...d,tier:15.2,name:'Renombrado',creator:'Nuevo'}]);
 assert.equal(Object.keys(repeat.patch).length,0);
});
test('los registros con el mismo ID se deduplican en memoria, sin borrar filas antiguas',()=>{
 const raw:Records={old:{...d,thiaguinhio:true},'42':{...d,michaeelp:true}};
 const out=buildLevels(raw,[d]);assert.equal(out.length,1);assert.equal(out[0].thiaguinhio,true);assert.equal(out[0].michaeelp,true);assert.equal(Object.keys(raw).length,2);
});
test('IDs distintos con el mismo nombre no comparten historial',()=>{
 assert.equal(historyMatches({player:'nzrv',demon:'Prueba',demonKey:'99',creator:'Creator',tier:1},d),false);
 assert.equal(resolveSheetLevel({name:'Prueba',creator:'Creator'},'old',[d,{...d,id:'43'}]),undefined);
});
test('la hoja rechaza IDs vacíos y tiers nulos o inválidos',()=>{
 const rows=[{c:[{v:1},{v:'Valid'},{v:'Creator'},null,{v:'Easy'},{v:1.234}]},{c:[null,{v:'Bad'},null,null,null,{v:1}]},{c:[{v:2},{v:'Bad'},null,null,null,null]},{c:[{v:3},{v:'Bad'},null,null,null,{v:'x'}]}];
 const out=parseSheet(`google.visualization.Query.setResponse(${JSON.stringify({table:{rows}})});`);
 assert.equal(out.length,1);assert.equal(out[0].tier,1.2);assert.equal(out[0].id,'1');
});
test('los niveles oficiales usan sus IDs internos sin consultar un nivel online equivocado',async()=>{
 const info=await fetchGDLevel('1');assert.equal(info.official,true);
});
test('se parsean las estadísticas e iconos reales de GD sin fabricar datos ausentes',()=>{
 const raw=snapshot.profiles.michaeelp.raw;const p=parseProfile(raw);
 assert.equal(p.accountId,'24854395');assert.equal(p.stars,1016);assert.equal(p.icons.cube,3);assert.equal(p.icons.ship,163);assert.equal(p.glow,false);assert.equal(parseProfile({'1':'test','16':'1'}).stars,null);
 assert.deepEqual(parsePairs('1:abc:2:123'),{'1':'abc','2':'123'});
});
test('operaciones de escritura nunca eliminan una colección completa',()=>{
 const lev=buildLevels(snapshot.records as any,catalog).find(d=>d.michaeelp)!;
 const patch=removePatch(lev,'michaeelp',snapshot.records as any,snapshot.history as any);
 for(const key of Object.keys(patch)){assert.ok(key.startsWith('pasados/')||key.startsWith('historial/'));assert.ok(key.split('/').length>=2);assert.notEqual(key,'pasados');assert.notEqual(key,'historial');}
 assert.equal((source.pasados as any)[lev.id].michaeelp,true);
});
test('las reglas cierran la escritura pública y preservan lecturas de la lista',()=>{
 const rules=JSON.parse(readFileSync('../firebase.rules.json','utf8')).rules;assert.equal(rules['.write'],false);assert.equal(rules.pasados['.read'],true);assert.equal(rules.historial['.read'],true);assert.equal(rules.editors.$uid['.write'],false);assert.equal(rules.changelogSeen['.write'],false);
});
