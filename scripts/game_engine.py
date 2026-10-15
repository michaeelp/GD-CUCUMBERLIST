"""Pure mission/economy engine. Only the trusted worker writes its results."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import hashlib,math,random
PLAYERS=('thiaguinhio','michaeelp','nzrv')
DAY=86400000
SHOP=[{'id':'title_explorador','name':'Explorador','kind':'title','value':'Explorador','price':150},{'id':'title_cazador','name':'Cazador de demons','kind':'title','value':'Cazador de demons','price':500},{'id':'title_veterano','name':'Veterano','kind':'title','value':'Veterano','price':1500},{'id':'color_cyan','name':'Cian','kind':'color','value':'#62e8ff','price':250},{'id':'color_gold','name':'Dorado','kind':'color','value':'#ffe274','price':350},{'id':'color_pink','name':'Rosa','kind':'color','value':'#ff83ca','price':250},{'id':'badge_star','name':'Estrella','kind':'badge','value':'★','price':300},{'id':'badge_diamond','name':'Diamante','kind':'badge','value':'◆','price':600}]
STATS={'stars':'estrellas','moons':'lunas','diamonds':'diamantes','userCoins':'user coins','demons':'demons'}
def period(now):
 d=datetime.fromtimestamp(now/1000,ZoneInfo('America/Montevideo'));start=d.replace(hour=0,minute=0,second=0,microsecond=0);week=start-timedelta(days=start.weekday());month=start.replace(day=1);end=(month.replace(day=28)+timedelta(days=4)).replace(day=1)
 return {'day':start.date().isoformat(),'start':int(start.timestamp()*1000),'end':int((start+timedelta(days=1)).timestamp()*1000),'week':week.date().isoformat(),'weekStart':int(week.timestamp()*1000),'weekEnd':int((week+timedelta(days=7)).timestamp()*1000),'month':month.strftime('%Y-%m'),'monthEnd':int(end.timestamp()*1000),'daysLeft':(end.date()-start.date()).days}
def rng(seed):return random.Random(int(hashlib.sha256(seed.encode()).hexdigest(),16))
def clean(d):return {k:d.get(k,'' if k!='tier' else 0) for k in ('id','name','creator','difficulty','tier')}
def merged(records,catalog):
 out={str(d['id']):{**clean(d),'id':str(d['id'])} for d in catalog}
 names={}
 for d in catalog:names.setdefault((d['name'].lower(),d.get('creator','').lower()),[]).append(str(d['id']))
 for key,d in records.items():
  if not isinstance(d,dict) or not d.get('name'):continue
  ident=str(d.get('id',key))
  if not ident.isdigit():
   found=names.get((d['name'].lower(),d.get('creator','').lower()),[])
   if len(found)==1:ident=found[0]
  old=out.get(ident,{});item={**old,**clean(d),'id':ident,'tier':float(d.get('tier',old.get('tier',0)))}
  for p in PLAYERS:item[p]=bool(old.get(p) or d.get(p))
  item['_keys']=[*old.get('_keys',[]),key];out[ident]=item
 return list(out.values())
def choose(pool,seed,target=None,blocked=()):
 pool=[d for d in pool if str(d.get('id','')).isdigit() and d.get('name')]
 available=[d for d in pool if d['id'] not in blocked];pool=available or pool
 if not pool:return None
 pool=sorted(pool,key=lambda d:(abs(d['tier']-target) if target is not None else 0,d['id']))
 if target is not None:pool=pool[:32]
 return clean(rng(seed).choice(pool))
def hardest(levels,p):return max([d['tier'] for d in levels if d.get(p)]+[0])
def rounded(n):return math.floor(n*10+.5)/10
def snapshot(d,kind,p,key,start,end,ref,now):return {**d,'kind':kind,'player':p,'period':key,'startsAt':start,'endsAt':end,'referenceTier':rounded(ref),'targetTier':rounded(ref*(.5 if kind=='daily' else .6)),'createdAt':now,'version':2}
def assignments(root,levels,now):
 t=period(now);out={};ds=root.get('desafios',{});daily=ds.get('diarios',{}).get(t['day'],{});weekly=ds.get('semanales',{}).get(t['week'])
 if not weekly or weekly.get('version',1)<2:
  refs=[hardest(levels,p) for p in PLAYERS];ref=sum(refs)/3;target=ref*.6
  pool=[d for d in levels if not any(d.get(p) for p in PLAYERS) and d['tier']<=target*1.15]
  blocked=[d['id'] for k,d in sorted(ds.get('semanales',{}).items())[-4:]]
  d=choose(pool,'weekly-v2:'+t['week'],target,blocked)
  if d and min(refs)>0:weekly=snapshot(d,'weekly','all',t['week'],t['weekStart'],t['weekEnd'],ref,now);out['desafios/semanales/'+t['week']]=weekly
 for p in PLAYERS:
  if p in daily and daily[p].get('version',1)>=2:continue
  ref=hardest(levels,p) or 1.5;target=ref*.5
  pool=[d for d in levels if not d.get(p) and d['tier']<=min(ref,target*1.2)]
  recent=[v[p]['id'] for k,v in sorted(ds.get('diarios',{}).items())[-7:] if p in v]
  if weekly:recent.append(weekly['id'])
  d=choose(pool,'daily-v2:'+t['day']+p,target,recent)
  if d:out[f'desafios/diarios/{t["day"]}/{p}']=snapshot(d,'daily',p,t['day'],t['start'],t['end'],ref,now)
 coop=root.get('cooperativas',{}).get(t['day'])
 if not coop:
  prior=[v['id'] for k,v in sorted(root.get('cooperativas',{}).items())[-14:]]
  pool=[d for d in levels if d.get('difficulty')=='Easy' and not any(d.get(p) for p in PLAYERS)]
  ref=min(hardest(levels,p) or 1.5 for p in PLAYERS)*.5
  d=choose(pool,'coop:'+t['day'],min(3,ref),prior)
  if d:out['cooperativas/'+t['day']]={**d,'startsAt':now,'endsAt':t['end'],'period':t['day'],'reward':60,'bonus':90}
 return out

def events(root,levels,p,start,end):
 active={d['id'] for d in levels if d.get(p)};aliases={k:d['id'] for d in levels for k in d.get('_keys',[])};seen={}
 for h in root.get('historial',{}).values():
  if not isinstance(h,dict) or h.get('player')!=p or not isinstance(h.get('timestamp'),(int,float)) or not start<=h['timestamp']<end:continue
  ident=aliases.get(str(h.get('demonKey')),str(h.get('demonKey')))
  if ident in active:seen[ident]=h
 return seen

def credit(g,key,amount,reason,now,xp=0):
 w=g['wallet'];ledger=w.setdefault('ledger',{})
 if key in ledger:return False
 ledger[key]={'amount':int(amount),'reason':reason,'at':now,'xp':xp};w['balance']=w.get('balance',0)+int(amount);w['earned']=w.get('earned',0)+max(0,int(amount));w['xp']=w.get('xp',0)+xp;return True

def manual_best(root,p,ident):
 return max(root.get('runs',{}).get(p,{}).get(ident,{}).get('best',0),root.get('objetivos',{}).get(p,{}).get('best',0) if root.get('objetivos',{}).get(p,{}).get('id')==ident else 0)

def make_quest(root,levels,p,seed,index,now,variant=0):
 r=rng(f'{seed}:{p}:{index}:{variant}');pending=[d for d in levels if not d.get(p) and d['id'].isdigit()];easy=[d for d in pending if d.get('difficulty')=='Easy'];h=hardest(levels,p);profile=root.get('verifiedProfiles',{}).get(p,{});fresh=now-25*60000<=profile.get('at',0)<=now and profile.get('at',0)>=period(now)['start']
 recent=[q.get('level',{}).get('id') for _,day in sorted(root.get('gameState',{}).get(p,{}).get('archive',{}).items())[-7:] for q in day.get('quests',[])]
 q={'id':f'{seed}_{index}_{variant}','kind':'count','target':1,'reward':40,'xp':25,'createdAt':now,'progress':0,'completed':False}
 if index==0:
  mode=r.randrange(12);pool=easy
  if mode==1:pool=[d for d in easy if any(d.get(other) for other in PLAYERS if other!=p)] or easy
  if mode==2:pool=[d for d in easy if all(d.get(other) for other in PLAYERS if other!=p)] or easy
  if mode==3:pool=[d for d in easy if not any(d.get(other) for other in PLAYERS)] or easy
  if mode==10:
   creators={d.get('creator') for d in levels if d.get(p)};pool=[d for d in easy if d.get('creator') not in creators] or easy
  if mode==11:pool=[d for d in pending if d.get('difficulty')=='Medium' and d['tier']<=h*.65] or easy
  if mode==8:
   options=r.sample(sorted(easy,key=lambda d:d['id']),min(2,len(easy))) if easy else [];q.update(kind='levels_count',title='Completar los dos Easy Demons asignados',options=[clean(d) for d in options],target=len(options),reward=65)
  elif mode==9:
   author=r.choice(easy).get('creator') if easy else '';options=[d for d in easy if d.get('creator')==author];options=r.sample(options,min(3,len(options)));q.update(kind='choice',title='Completar un Easy de '+author,options=[clean(d) for d in options])
  elif mode==4:q.update(kind='easy_count',title='Completar dos Easy Demons',target=min(2,len(easy)),reward=65)
  elif mode==5:q.update(kind='creator_count',title='Completar Easy Demons de dos creadores',target=min(2,len({d.get('creator') for d in easy})),reward=65)
  elif mode==6:
   options=r.sample(sorted(easy,key=lambda d:d['id']),min(3,len(easy))) if easy else [];q.update(kind='choice',title='Completar uno de estos Easy Demons',options=[clean(d) for d in options])
  elif mode==7:q.update(kind='easy_count',title='Completar un Easy Demon',target=1)
  else:
   d=choose(pool,seed+p+str(index)+str(variant),min(3,h*.5 or 1),recent)
   if d:q.update(kind='level',title='Completar '+d['name'],level=d)
 elif index==1:
  goal=root.get('objetivos',{}).get(p);pool=[d for d in pending if d.get('difficulty')=='Medium' and d['tier']<=max(4,h*.8)] or easy
  d=choose(pool,seed+p+'progress'+str(variant),min(5,max(2,h*.4)),recent)
  if goal and r.randrange(3)==0 and manual_best(root,p,goal['id'])<95:d=next((x for x in levels if x['id']==goal['id'] and not x.get(p)),d)
  if d:
   base=manual_best(root,p,d['id']);target=min(100,base+r.choice([5,10])) if base else r.choice([20,35,50]);q.update(kind='percent',level=clean(d),baseline=base,target=target,title=f'{d["name"]}: alcanzar {target} %',reward=35)
 elif index in [2,3]:
  stat=r.choice(['stars','moons']) if index==2 else r.choice(['diamonds','userCoins','demons']);target=r.choice({'stars':[10,20,30,50],'moons':[5,10,15],'diamonds':[20,40,60],'userCoins':[1,2],'demons':[1]}[stat]);q.update(kind='stat',stat=stat,target=target,title=f'Ganar {target} {STATS[stat]}',reward=25 if target<30 else 40)
  if fresh and isinstance(profile.get('stats',{}).get(stat),(int,float)):q.update(baseline=profile['stats'][stat],baselineAt=profile['at'])
  else:q['waitingBaseline']=True
 if q['kind']=='count':
  d=choose(easy,seed+p+str(variant));q.update(kind='level',level=d,title='Completar '+d['name']) if d else q.update(kind='easy_count',title='Completar un Easy Demon',target=1)
 if index==1 and easy and r.randrange(7)==0:
  d=choose(easy,seed+p+'combo'+str(variant));stat=r.choice(['diamonds','moons']);amount=20 if stat=='diamonds' else 5
  a={'id':q['id']+'_a','kind':'level','level':d,'title':'Completar '+d['name'],'target':1,'reward':0,'createdAt':now,'progress':0,'completed':False}
  b={'id':q['id']+'_b','kind':'stat','stat':stat,'title':f'Ganar {amount} {STATS[stat]}','target':amount,'reward':0,'createdAt':now,'progress':0,'completed':False}
  if fresh and isinstance(profile.get('stats',{}).get(stat),(int,float)):b.update(baseline=profile['stats'][stat],baselineAt=profile['at'])
  else:b['waitingBaseline']=True
  q.update(kind='combo',title='Nivel y estadísticas',target=2,parts=[a,b],reward=60);q.pop('level',None)
 if not q.get('target'):q.update(target=1,unavailable=True)
 return q

def rerolled(root,levels,p,seed,index,now,previous,variant):
 def signature(q):return (q.get('kind'),q.get('title'),q.get('target'),q.get('level',{}).get('id'),q.get('stat'))
 candidate=previous
 for offset in range(12):
  candidate=make_quest(root,levels,p,seed,index,now,variant+offset)
  if signature(candidate)!=signature(previous):break
 return candidate

def progress_quest(q,root,levels,p,start,end,now):
 out=deepcopy(q)
 if out.get('completed'):return out
 ev=events(root,levels,p,max(start,q.get('createdAt',start)),end);lookup={d['id']:d for d in levels};kind=q['kind'];value=0
 if kind=='combo':
  out['parts']=[progress_quest(part,root,levels,p,start,end,now) for part in q.get('parts',[])];value=sum(part['completed'] for part in out['parts'])
 elif kind=='level':value=int(q.get('level',{}).get('id') in ev)
 elif kind=='choice':value=int(any(d['id'] in ev for d in q.get('options',[])))
 elif kind=='levels_count':value=sum(d['id'] in ev for d in q.get('options',[]))
 elif kind=='easy_count':value=sum(lookup.get(i,{}).get('difficulty')=='Easy' for i in ev)
 elif kind=='creator_count':value=len({lookup[i].get('creator') for i in ev if i in lookup and lookup[i].get('difficulty')=='Easy'})
 elif kind=='percent':
  ident=q.get('level',{}).get('id');run=root.get('runs',{}).get(p,{}).get(ident,{})
  if ident in ev:value=100
  elif max(start,q.get('createdAt',start))<=run.get('updatedAt',0)<end:value=run.get('best',0)
  goal=root.get('objetivos',{}).get(p,{})
  if goal.get('id')==ident and max(start,q.get('createdAt',start))<=goal.get('updatedAt',0)<end:value=max(value,goal.get('best',0))
 elif kind=='stat':
  profile=root.get('verifiedProfiles',{}).get(p,{});at=profile.get('at',0);stat=q['stat'];n=profile.get('stats',{}).get(stat)
  if out.get('waitingBaseline') and max(start,q.get('createdAt',start))<=at<end and isinstance(n,(int,float)):
   out.update(baseline=n,baselineAt=at,waitingBaseline=False)
  if isinstance(n,(int,float)) and isinstance(out.get('baseline'),(int,float)) and out.get('baselineAt',end)<=at<end:value=max(0,n-out['baseline'])
  else:value=q.get('progress',0)
 out['progress']=min(q['target'],max(q.get('progress',0),value));out['completed']=out['progress']>=q['target'] and not out.get('unavailable');out['expired']=now>=end and not out['completed']
 if out['completed']:out['completedAt']=now
 return out

def make_bingo(root,levels,p,now):
 t=period(now);days=t['daysLeft'];scale=min(1,days/24);cells=[]
 def add(kind,title,target=1,**extra):cells.append({'id':str(len(cells)),'kind':kind,'title':title,'target':target,'progress':0,'completed':False,'reward':50,'xp':30,'createdAt':now,**extra})
 easy=[d for d in levels if d.get('difficulty')=='Easy' and not d.get(p)];pick=choose(easy,t['month']+p)
 add('easy_count','Completar Easy Demons',max(1,min(len(easy),math.ceil(5*scale))))
 add('creator_count','Easy Demons de distintos creadores',max(1,min(len({d.get('creator') for d in easy}),math.ceil(3*scale))))
 if pick:add('level','Completar '+pick['name'],level=pick)
 else:add('easy_count','Completar un Easy Demon')
 for stat,target in [('stars',150),('moons',40),('diamonds',250),('userCoins',5)]:
  q={'kind':'stat','stat':stat,'title':f'Ganar {STATS[stat]}','target':max(1,math.ceil(target*scale))};profile=root.get('verifiedProfiles',{}).get(p,{})
  if now-25*60000<=profile.get('at',0)<=now and profile.get('at',0)>=t['start'] and isinstance(profile.get('stats',{}).get(stat),(int,float)):q.update(baseline=profile['stats'][stat],baselineAt=profile['at'])
  else:q['waitingBaseline']=True
  add(**q)
 for key,title,target in [('mission','Completar misiones diarias',max(1,math.ceil(10*scale))),('daily','Completar demons diarios',max(1,min(days,math.ceil(5*scale)))),('team','Completar cooperativas',max(1,min(days,math.ceil(3*scale)))),('weekly','Completar un demon semanal',1)]:
  weekly=root.get('desafios',{}).get('semanales',{}).get(t['week'])
  if key=='weekly' and (not weekly or weekly['tier']>hardest(levels,p)*.85):key,title='mission','Completar una misión diaria'
  add('awards',title,target,awardType=key)
 for i in range(3):
  q=make_quest(root,levels,p,t['month']+'bingo'+str(i),1,now);q.update(id=str(len(cells)),reward=50);cells.append(q)
 add('easy_count','Completar un Easy Demon',1)
 add('awards','Completar una misión de estadísticas',1,awardType='statmission')
 return {'month':t['month'],'activatedAt':now,'endsAt':t['monthEnd'],'cells':cells[:16],'replacementsUsed':0}

def update_player(old,root,levels,p,manifest,now):
 g=deepcopy(old or {});t=period(now);w=g.setdefault('wallet',{'balance':0,'earned':0,'xp':0,'ledger':{},'paidLevels':{},'owned':{},'equipped':{}})
 initial=manifest['players'][p]
 if 'retro_v1' not in w.setdefault('ledger',{}):
  credit(g,'retro_v1',initial['coins'],'Saldo inicial: puntos y demons registrados',now)
  w.setdefault('paidLevels',{}).update({str(i):True for i in initial['levelIds']});g['activatedAt']=now
 catalog={str(d['id']):d for d in root.get('_catalog',[])}
 for ident,hist in events(root,levels,p,manifest['cutoff'],now+1).items():
  if ident in w['paidLevels'] or ident not in catalog:continue
  d=catalog[ident];amount=20+math.floor(float(d['tier'])*2);credit(g,'level_'+ident,amount,'Completación: '+d['name'],now,10);w['paidLevels'][ident]=True
 daily=g.get('daily')
 def finish_day(d):
  d=deepcopy(d);d['quests']=[progress_quest(q,root,levels,p,d['startsAt'],d['endsAt'],now) for q in d['quests']]
  for q in d['quests']:
   if q['completed']:credit(g,'mission_'+q['id'],q['reward'],q['title'],now,q.get('xp',25))
  if all(q['completed'] for q in d['quests']):credit(g,'all_'+d['day'],75,'Cuatro misiones del día',now,60)
  return d
 if daily and daily['day']!=t['day']:
  g.setdefault('archive',{})[daily['day']]=finish_day(daily);daily=None
  g['archive']=dict(sorted(g['archive'].items())[-90:])
 if not daily:daily={'day':t['day'],'startsAt':now,'endsAt':t['end'],'rerollsUsed':0,'quests':[make_quest(root,levels,p,t['day'],i,now) for i in range(4)]}
 daily=finish_day(daily);g['daily']=daily
 # Requests are immutable, owned by the player; the worker validates each command.
 for ident,cmd in sorted(root.get('requests',{}).get(p,{}).items(),key=lambda kv:kv[1].get('at',0)):
  if ident in g.setdefault('processed',{}):continue
  ok=True;message='Aplicado';kind=cmd.get('kind');item=cmd.get('item','');i=cmd.get('index',-1)
  if kind=='purchase':
   product=next((x for x in SHOP if x['id']==item),None)
   if not product:ok=False;message='Artículo inexistente'
   elif item in w.setdefault('owned',{}):message='Ya comprado'
   elif w['balance']<product['price']:ok=False;message='Monedas insuficientes'
   else:credit(g,'buy_'+item,-product['price'],'Compra: '+product['name'],now);w['owned'][item]=True
  elif kind=='equip':
   product=next((x for x in SHOP if x['id']==item),None)
   if not product or not w.setdefault('owned',{}).get(item):ok=False;message='Primero comprá el artículo'
   else:w.setdefault('equipped',{})[product['kind']]=item
  elif kind=='rerollQuest':
   if cmd.get('period')!=t['day'] or daily['rerollsUsed']>=1 or not isinstance(i,int) or i not in range(4) or daily['quests'][i].get('completed'):ok=False;message='Cambio diario no disponible'
   else:daily['quests'][i]=rerolled(root,levels,p,t['day'],i,now,daily['quests'][i],1);daily['rerollsUsed']+=1
  elif kind=='rerollBingo':
   b=g.get('bingo')
   if not b or b['month']!=t['month'] or cmd.get('period')!=t['month'] or b.get('replacementsUsed',0)>=2 or not isinstance(i,int) or i not in range(16) or b['cells'][i].get('completed'):ok=False;message='Cambio de casilla no disponible'
   else:
    q=rerolled(root,levels,p,t['month']+'replace'+str(i),i%4,now,b['cells'][i],b['replacementsUsed']+1);q.update(id=str(i),reward=50);b['cells'][i]=q;b['replacementsUsed']=b.get('replacementsUsed',0)+1
  elif kind=='verify':message='Perfil comprobado en esta ejecución'
  else:ok=False;message='Solicitud desconocida'
  g['processed'][ident]={'ok':ok,'message':message,'at':now}
 g['daily']=finish_day(daily)
 # Personal and shared challenges have unique reward identifiers per period.
 for key,d in root.get('desafios',{}).get('diarios',{}).items():
  c=d.get(p)
  if c and c['id'] in events(root,levels,p,c['startsAt'],c['endsAt']):credit(g,'daily_'+key,50,'Demon diario: '+c['name'],now,35)
 for key,c in root.get('desafios',{}).get('semanales',{}).items():
  if c['id'] in events(root,levels,p,c['startsAt'],c['endsAt']):credit(g,'weekly_'+key,100,'Demon semanal: '+c['name'],now,75)
 for key,c in root.get('cooperativas',{}).items():
  done=[other for other in PLAYERS if c['id'] in events(root,levels,other,c['startsAt'],c['endsAt'])]
  if p in done:credit(g,'coop_'+key,c['reward'],'Cooperativa: '+c['name'],now,40)
  if len(done)==3:credit(g,'team_'+key,c['bonus'],'Bonus de equipo',now,60)
 b=g.get('bingo')
 def finish_bingo(b):
  b=deepcopy(b)
  for i,q in enumerate(b['cells']):
   if q['kind']=='awards':
    label=q['awardType'];count=sum((key.startswith(label+'_') if label!='statmission' else key.startswith('mission_') and any(term in entry['reason'] for term in STATS.values())) and b['activatedAt']<=entry['at']<b['endsAt'] for key,entry in w['ledger'].items());q={**q,'progress':min(q['target'],count),'completed':count>=q['target']}
   else:q=progress_quest(q,root,levels,p,b['activatedAt'],b['endsAt'],now)
   b['cells'][i]=q
   if q['completed']:credit(g,f'bingo_{b["month"]}_cell_{i}',q['reward'],f'Bingo: {q["title"]}',now,30)
  lines=[[i*4+j for j in range(4)] for i in range(4)]+[[i+j*4 for j in range(4)] for i in range(4)]+[[0,5,10,15],[3,6,9,12]]
  b['lines']=[i for i,line in enumerate(lines) if all(b['cells'][j].get('completed') for j in line)]
  for i in b['lines']:credit(g,f'bingo_{b["month"]}_line_{i}',100,'Línea de bingo',now,50)
  b['completed']=all(q['completed'] for q in b['cells'])
  if b['completed']:credit(g,'bingo_'+b['month']+'_full',400,'Bingo completo',now,200)
  return b
 if b and b['month']!=t['month']:g.setdefault('bingoArchive',{})[b['month']]=finish_bingo(b);b=None
 if not b:b=make_bingo(root,levels,p,now)
 g['bingo']=finish_bingo(b);g['updatedAt']=now;return g
