import {resolve} from 'node:path';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {PLAYERS} from '../lib/config';
import {buildLevels,type Level,type Histories} from '../lib/domain';
import {challengePeriods,chooseDaily,chooseWeekly,challengeCompleted,challengeProgress,nextGoal,shiftDay,type Challenge,type DailyMap} from '../lib/competition';
const folder=resolve('../data');
const records=JSON.parse(readFileSync(folder+'/pasados.json','utf8')).data;
const catalog=JSON.parse(readFileSync(folder+'/catalog.json','utf8')).data;
const real=buildLevels(records,catalog);
const now=Date.parse('2026-10-15T18:00:00Z');const periods=challengePeriods(now);
const level=(id:string,tier:number,extra:Partial<Level>={}):Level=>({id,name:`Nivel ${id}`,creator:'Creador',difficulty:'Hard',tier,...extra});
const base=[level('1',20,{thiaguinhio:true}),level('2',10,{michaeelp:true}),level('3',15,{nzrv:true})];
const pool=[...base,...Array.from({length:120},(_,i)=>level(String(1000+i),i<60?10:9))];
test('el día cambia exactamente a medianoche de Uruguay, no a medianoche UTC',()=>{
 const before=challengePeriods(Date.parse('2026-10-16T02:59:59.999Z'));const after=challengePeriods(Date.parse('2026-10-16T03:00:00Z'));
 assert.equal(before.daily.key,'2026-10-15');assert.equal(after.daily.key,'2026-10-16');assert.equal(before.daily.endsAt,after.daily.startsAt);
});
test('la semana cambia el lunes de Uruguay y cruza el año correctamente',()=>{
 const sunday=challengePeriods(Date.parse('2026-10-19T02:59:59.999Z'));const monday=challengePeriods(Date.parse('2026-10-19T03:00:00Z'));
 assert.equal(sunday.weekly.key,'2026-10-12');assert.equal(monday.weekly.key,'2026-10-19');assert.equal(sunday.weekly.endsAt,monday.weekly.startsAt);
 assert.equal(challengePeriods(Date.parse('2027-01-01T12:00:00Z')).weekly.key,'2026-12-28');assert.equal(shiftDay('2026-12-31',1),'2027-01-01');
});
test('los diarios reales usan su hardest y una meta cercana al 50 %, sin superarlo',()=>{
 const expected={thiaguinhio:[24.9,12.5],michaeelp:[6.6,3.3],nzrv:[20.2,10.1]};
 for(const p of PLAYERS){const d=chooseDaily(real,p,periods.daily,{},null,now)!;assert.ok(d);assert.deepEqual([d.referenceTier,d.targetTier],expected[p]);assert.equal(d.player,p);assert.ok(d.tier<d.referenceTier);assert.equal(!!real.find(l=>l.id===d.id)?.[p],false);assert.equal(d.period,periods.daily.key);}
});
test('el semanal real usa la media de los tres hardests y está pendiente para todos',()=>{
 const d=chooseWeekly(real,periods.weekly,{},now)!;assert.ok(d);assert.equal(d.referenceTier,17.2);assert.equal(d.targetTier,10.3);assert.equal(d.player,'all');assert.ok(d.tier>=17.2333333333*.6*.85&&d.tier<=17.2333333334*.6*1.15);assert.ok(PLAYERS.every(p=>!real.find(l=>l.id===d.id)?.[p]));
});
test('la selección es reproducible aunque cambie el orden del catálogo',()=>{
 const reversed=[...real].reverse();for(const p of PLAYERS)assert.deepEqual(chooseDaily(real,p,periods.daily,{},null,now),chooseDaily(reversed,p,periods.daily,{},null,now));assert.deepEqual(chooseWeekly(real,periods.weekly,{},now),chooseWeekly(reversed,periods.weekly,{},now));
});
test('evita repetir los últimos siete diarios y el semanal cuando hay alternativas',()=>{
 const first=chooseDaily(pool,'thiaguinhio',periods.daily,{},null,now)!;const recent:DailyMap={[shiftDay(periods.daily.key,-1)]:{thiaguinhio:first}};
 const second=chooseDaily(pool,'thiaguinhio',periods.daily,recent,null,now)!;assert.notEqual(second.id,first.id);
 const third=chooseDaily(pool,'thiaguinhio',periods.daily,recent,second,now)!;assert.notEqual(third.id,second.id);assert.notEqual(third.id,first.id);
});
test('los diarios nunca eligen completados ni suben del hardest cuando faltan candidatos',()=>{
 const d=chooseDaily([...base,level('4',2),level('5',25)],'thiaguinhio',periods.daily,{},null,now)!;assert.ok(!base.find(l=>l.id===d.id)?.thiaguinhio);assert.ok(d.tier<=20);
 assert.equal(chooseDaily([base[0],level('5',25)],'thiaguinhio',periods.daily,{},null,now),null);
});
test('el semanal espera tres hardests y excluye cualquier nivel ya completado por alguien',()=>{
 assert.equal(chooseWeekly([base[0],base[1],level('7',15)],periods.weekly,{},now),null);
 assert.equal(chooseWeekly(base,periods.weekly,{},now),null);
});
test('solo una completación fechada dentro del período supera un desafío',()=>{
 const c=chooseDaily(pool,'thiaguinhio',periods.daily,{},null,now)!;const completed=[level(c.id,c.tier,{thiaguinhio:true})];
 const history=(timestamp?:number):Histories=>({h:{player:'thiaguinhio',demonKey:c.id,demon:c.name,tier:c.tier,...(timestamp===undefined?{}:{timestamp})}});
 assert.equal(challengeCompleted(c,'thiaguinhio',history(c.startsAt),completed),true);
 assert.equal(challengeCompleted(c,'thiaguinhio',history(c.endsAt-1),completed),true);
 assert.equal(challengeCompleted(c,'thiaguinhio',history(c.startsAt-1),completed),false);
 assert.equal(challengeCompleted(c,'thiaguinhio',history(c.endsAt),completed),false);
 assert.equal(challengeCompleted(c,'thiaguinhio',history(),completed),false);
 assert.equal(challengeCompleted(c,'thiaguinhio',history(now),[level(c.id,c.tier)]),false);
 assert.equal(challengeCompleted(c,'nzrv',history(now),completed),false);
});
test('el progreso solo usa el objetivo del mismo nivel y no inventa 100 % sin un registro',()=>{
 const c=chooseDaily(pool,'thiaguinhio',periods.daily,{},null,now)!;const goal=nextGoal(null,c,83,now);
 assert.equal(challengeProgress(c,'thiaguinhio',{thiaguinhio:goal},{},pool),83);
 assert.equal(challengeProgress(c,'thiaguinhio',{thiaguinhio:{...goal,id:'99999'}},{},pool),0);
 assert.equal(challengeProgress(c,'thiaguinhio',{thiaguinhio:{...goal,best:100}},{},pool),0);
});
test('mantiene el mejor porcentaje del mismo nivel y permite reiniciar al cambiarlo',()=>{
 const first=nextGoal(null,level('4',20),67,now);const lower=nextGoal(first,level('4',20),42,now+5);
 assert.equal(lower.best,67);assert.equal(lower.createdAt,now);assert.equal(lower.updatedAt,now+5);
 const higher=nextGoal(lower,level('4',20),93,now+10);assert.equal(higher.best,93);
 const another=nextGoal(higher,level('5',22),3,now+20);assert.equal(another.best,3);assert.equal(another.createdAt,now+20);
});
test('rechaza porcentajes inválidos e IDs no verificados',()=>{
 for(const best of [-1,101,3.5,NaN])assert.throws(()=>nextGoal(null,level('4',20),best,now));
 assert.throws(()=>nextGoal(null,level('legacy',20),50,now));
});
test('las propuestas no mutan la lista, los registros ni el historial de desafíos',()=>{
 const original=JSON.stringify(real);const d=chooseDaily(real,'nzrv',periods.daily,{},null,now)!;const before=JSON.stringify(d);const saved={...d} as Challenge;
 chooseDaily([...real,level('987654321',50,{nzrv:true})],'nzrv',periods.daily,{},null,now+1);
 assert.equal(JSON.stringify(real),original);assert.equal(JSON.stringify(saved),before);assert.ok(!('_keys' in d));assert.ok(!('nzrv' in d));
});
