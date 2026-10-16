"""Exercise real-time private wallets against the real, isolated RTDB emulator."""
import base64,concurrent.futures,json,subprocess,sys,time,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ns='demo-cucumber-v4';base='http://127.0.0.1:9014';opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def req(path,method='GET',data=None,auth=None):
 headers={'Content-Type':'application/json'};url=base+'/'+path.strip('/')+'.json?ns='+ns
 if auth=='owner':headers['Authorization']='Bearer owner'
 elif auth:url+='&auth='+auth
 try:
  with opener.open(urllib.request.Request(url,method=method,headers=headers,data=json.dumps(data).encode() if data is not None else None),timeout=25) as r:return r.status,json.loads(r.read() or 'null')
 except urllib.error.HTTPError as e:
  body=e.read().decode()
  try:body=json.loads(body)
  except ValueError:pass
  return e.code,body

def token(uid):
 enc=lambda a:base64.urlsafe_b64encode(json.dumps(a).encode()).decode().rstrip('=')
 return enc({'alg':'none','typ':'JWT'})+'.'+enc({'iss':'https://securetoken.google.com/'+ns,'aud':ns,'sub':uid,'user_id':uid,'iat':int(time.time()),'exp':int(time.time())+3600,'firebase':{'sign_in_provider':'password'}})+'.'
def expect(label,status,result):
 assert result[0]==status,(label,result);print('PASS',label,status,flush=True)
TS={'.sv':'timestamp'};user=token('uid_nzrv');other=token('uid_michaeelp');now=int(time.time()*1000)
process=subprocess.Popen(['java','-jar',sys.argv[1],'--host','127.0.0.1','--port','9014'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
try:
 for _ in range(80):
  try:req('',auth='owner');break
  except urllib.error.URLError:time.sleep(.1)
 rules=json.loads((ROOT/'firebase.rules.json').read_text());expect('reglas válidas',200,req('.settings/rules','PUT',rules,'owner'))
 catalog=json.loads((ROOT/'data/shop.json').read_text());shop={d['id']:d for d in catalog}
 wallet={'balance':1000,'earned':1000,'xp':0,'ledger':{'retro_v1':{'amount':1000,'at':now}},'paidLevels':{'42':True}}
 seed={'members':{'uid_nzrv':{'player':'nzrv','accountId':'13334739'},'uid_michaeelp':{'player':'michaeelp','accountId':'24854395'}},'playerOwners':{'nzrv':'uid_nzrv','michaeelp':'uid_michaeelp'},'admins':{'admin':True},'shopCatalog':shop,'gameState':{'nzrv':{'wallet':wallet,'activatedAt':now-10000},'michaeelp':{'wallet':wallet}},'levelCatalog':{'500':{'id':'500','name':'Test','tier':2.1,'creator':'X','difficulty':'Easy'}},'pasados':{'500':{'id':'500','name':'Test','tier':2.1,'nzrv':True}},'historial':{'500_nzrv':{'player':'nzrv','demonKey':'500','timestamp':now}}}
 expect('semilla aislada',200,req('','PUT',seed,'owner'))
 expect('raíz privada de cuentas',401,req('gameState',auth=user));expect('cuenta propia',200,req('gameState/nzrv',auth=user));expect('cuenta ajena',401,req('gameState/michaeelp',auth=user));expect('sin sesión',401,req('gameState/nzrv'));expect('administrador no vinculado sin acceso privado',401,req('gameState/nzrv',auth=token('admin')))
 def purchase(item,balance):
  price=shop[item]['price'];id='buy_'+item
  return {'gameState/nzrv/wallet/lastOp':id,'gameState/nzrv/wallet/ledger/'+id:{'kind':'purchase','item':item,'amount':-price,'xp':0,'at':TS,'reason':'Compra: '+shop[item]['name'],'statMission':False},'gameState/nzrv/wallet/balance':balance-price,'gameState/nzrv/wallet/owned/'+item:True}
 expect('compra instantánea atómica',200,req('','PATCH',purchase('color_gold',1000),user));assert req('gameState/nzrv/wallet',auth=user)[1]['balance']==650
 expect('no se duplica compra',401,req('','PATCH',purchase('color_gold',650),user))
 bad=purchase('color_pink',650);bad['gameState/nzrv/wallet/balance']=649;expect('precio manipulado',401,req('','PATCH',bad,user))
 expect('no se escribe saldo solo',401,req('gameState/nzrv/wallet/balance','PUT',999999,user));expect('no se regala inventario',401,req('gameState/nzrv/wallet/owned/font_orbitron','PUT',True,user));expect('no se borra recibo',401,req('gameState/nzrv/wallet/ledger/buy_color_gold','DELETE',auth=user));expect('no se borra saldo',401,req('gameState/nzrv/wallet/balance','DELETE',auth=user))
 expect('equipar comprado al instante',200,req('publicProfiles/nzrv/color','PUT','color_gold',user));expect('equipar no comprado',401,req('publicProfiles/nzrv/theme','PUT','theme_void',user));expect('fuente gratis',200,req('publicProfiles/nzrv/font','PUT','font_pusab',user));expect('perfil público',200,req('publicProfiles/nzrv'));expect('personalizar ajeno',401,req('publicProfiles/nzrv/bio','PUT','hola',other));expect('biografía válida',200,req('publicProfiles/nzrv/bio','PUT','Mi perfil',user));expect('biografía demasiado larga',401,req('publicProfiles/nzrv/bio','PUT','x'*161,user))
 receipt={'kind':'level','levelId':'500','amount':24,'xp':10,'reason':'Completación: Test','at':TS,'statMission':False,'proofs':[{'id':'500','key':'500'}]}
 patch={'gameState/nzrv/wallet/lastOp':'level_500','gameState/nzrv/wallet/ledger/level_500':receipt,'gameState/nzrv/wallet/balance':674,'gameState/nzrv/wallet/earned':1024,'gameState/nzrv/wallet/xp':10,'gameState/nzrv/wallet/paidLevels/500':True}
 expect('recompensa por nivel validada e instantánea',200,req('','PATCH',patch,user));expect('recompensa duplicada',401,req('','PATCH',patch,user))
 # A stale simultaneous purchase fails, then can retry against the current balance.
 patches=[purchase('color_pink',674),purchase('color_cyan',674)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda p:req('','PATCH',p,user),patches))
 assert sorted(r[0] for r in results)==[200,401],results
 loser=0 if results[0][0]==401 else 1;item=['color_pink','color_cyan'][loser];current=req('gameState/nzrv/wallet',auth=user)[1]['balance'];expect('reintento concurrente conserva ambos descuentos',200,req('','PATCH',purchase(item,current),user));assert req('gameState/nzrv/wallet',auth=user)[1]['balance']==174
 # Every reward uses the same atomic receipt contract as the browser.
 start=now-10000;end=now+86400000;day='test-day';month='test-month'
 def quest(kind,id,target=1,**extra):return {'kind':kind,'id':id,'title':id,'target':target,'reward':50,'xp':25,'createdAt':start,'completed':False,**extra}
 level=lambda id:{'id':id,'name':'Test '+id}
 quests=[quest('level','q0',level=level('500')),quest('percent','q1',35,level=level('501')),quest('stat','q2',20,stat='stars',baseline=1000,baselineAt=start),quest('easy_count','q3',2)]
 setup={'gameState/nzrv/daily':{'day':day,'startsAt':start,'endsAt':end,'quests':quests},'levelCatalog/501':{'id':'501','name':'Second','tier':2,'creator':'Y','difficulty':'Easy'},'pasados/501':{'id':'501','nzrv':True},'historial/501_nzrv':{'player':'nzrv','demonKey':'501','timestamp':now},'runs/nzrv/501':{'best':34,'updatedAt':now},'preferences/nzrv/sound':True,'verifiedProfiles/nzrv':{'at':now,'stats':{'stars':1019}}}
 expect('asignaciones de prueba',200,req('','PATCH',setup,'owner'))
 for path in ['runs','preferences','requests']:
  expect(path+' ajeno privado',401,req(path+'/nzrv',auth=other));expect(path+' invitado privado',401,req(path+'/nzrv'))
 expect('preferencias propias en vivo',200,req('preferences/nzrv/confirmPurchase','PUT',False,user));expect('ajuste desconocido rechazado',401,req('preferences/nzrv/unknown','PUT',True,user))
 def payout(key,kind,amount,xp,expected=200,stat=False,**extra):
  w=req('gameState/nzrv/wallet',auth=user)[1];body={'kind':kind,'amount':amount,'xp':xp,'reason':'Premio de prueba','at':TS,'statMission':stat,**extra};prefix='gameState/nzrv/wallet/'
  patch={prefix+'lastOp':key,prefix+'ledger/'+key:body,prefix+'balance':w['balance']+amount,prefix+'earned':w['earned']+max(0,amount),prefix+'xp':w['xp']+xp}
  expect(key+(' rechazado' if expected!=200 else ''),expected,req('','PATCH',patch,user))
 proofs=[{'id':'500','key':'500'},{'id':'501','key':'501'}]
 payout('all_'+day,'all',75,60,401,period=day)
 payout('mission_q0','mission',50,25,period=day,slot='0',proofs=proofs[:1])
 payout('mission_q1','mission',50,25,401,period=day,slot='1');expect('nuevo porcentaje propio',200,req('runs/nzrv/501','PUT',{'best':35,'updatedAt':TS},user));payout('mission_q1','mission',50,25,period=day,slot='1')
 payout('mission_q2','mission',50,25,401,stat=True,period=day,slot='2');req('verifiedProfiles/nzrv/stats/stars','PUT',1020,'owner');payout('mission_q2','mission',50,25,stat=True,period=day,slot='2')
 payout('mission_q3','mission',50,25,401,period=day,slot='3',proofs=proofs[:1]*2);payout('mission_q3','mission',50,25,period=day,slot='3',proofs=proofs)
 payout('all_'+day,'all',75,60,period=day);payout('all_'+day,'all',75,60,401,period=day)
 challenge={'id':'500','period':day,'startsAt':start,'endsAt':end}
 req('gameState/nzrv/assignments','PUT',{'daily':challenge,'weekly':{**challenge,'period':'test-week'},'cooperative':challenge},'owner')
 for kind,amount,xp,period in [('daily',50,35,day),('weekly',100,75,'test-week'),('coop',60,40,day)]:payout(kind+'_'+period,kind,amount,xp,period=period,proofs=proofs[:1])
 payout('team_'+day,'team',90,60,401,period=day,proofs=proofs[:1]*3)
 req('','PATCH',{'pasados/500/thiaguinhio':True,'pasados/500/michaeelp':True,**{'historial/500_'+p:{'demonKey':'500','player':p,'timestamp':now} for p in ['thiaguinhio','michaeelp']}},'owner')
 payout('team_'+day,'team',90,60,period=day,proofs=proofs[:1]*3)
 cells=[quest('choice','b0',options=[level('500'),level('501')]),quest('levels_count','b1',2,options=[level('500'),level('501')]),quest('creator_count','b2',2),quest('combo','b3',2,parts=[quest('level','part0',level=level('500')),quest('stat','part1',20,stat='stars',baseline=1000,baselineAt=start)]),quest('awards','b4',2,awardType='mission'),quest('awards','b5',1,awardType='statmission'),quest('percent','b6',50,level=level('501')),quest('easy_count','b7',2),*[quest('level','b'+str(i),level=level('500')) for i in range(8,16)]]
 req('gameState/nzrv/bingo','PUT',{'month':month,'activatedAt':start,'endsAt':end,'cells':cells},'owner')
 payout('bingo_'+month+'_line_0','line',100,50,401,period=month,slot='0');payout('bingo_'+month+'_full','full',400,200,401,period=month)
 def cell(i,proofs=None,expected=200):payout('bingo_'+month+'_cell_'+str(i),'bingo',50,30,expected,period=month,slot=str(i),**({'proofs':proofs} if proofs is not None else {}))
 cell(0,[{'id':'999','key':'999'}],401);cell(0,proofs[:1]);cell(1,proofs[:1]*2,401);cell(1,proofs);cell(2,proofs[:1]*2,401);cell(2,proofs);cell(3,proofs[:1])
 payout('bingo_'+month+'_line_0','line',100,50,period=month,slot='0')
 cell(4,[{'award':'retro_v1'},{'award':'mission_q0'}],401);cell(4,[{'award':'mission_q0'}]*2,401);cell(4,[{'award':'mission_q0'},{'award':'mission_q1'}]);cell(5,[{'award':'mission_q0'}],401);cell(5,[{'award':'mission_q2'}]);cell(6,None,401)
 req('runs/nzrv/501','PUT',{'best':55,'updatedAt':TS},user);cell(6);cell(7,proofs)
 for i in range(8,16):cell(i,proofs[:1])
 for i in range(1,10):payout('bingo_'+month+'_line_'+str(i),'line',100,50,period=month,slot=str(i))
 payout('bingo_'+month+'_full','full',400,200,period=month)
 expect('no se falsifica catálogo',401,req('shopCatalog/color_gold/price','PUT',0,user));expect('no se borra cuenta privada',401,req('gameState/nzrv','DELETE',auth=user))
 req('','PATCH',{'members/uid_nzrv':None,'members/replacement':{'player':'nzrv','accountId':'13334739'},'playerOwners/nzrv':'replacement'},'owner')
 expect('UID anterior pierde lectura privada',401,req('gameState/nzrv',auth=user));expect('UID reemplazante conserva la cuenta y sus compras',200,req('gameState/nzrv/wallet/owned/color_gold',auth=token('replacement')))
 print('ALL REALTIME WALLET CHECKS PASSED',flush=True)
finally:
 process.terminate()
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:process.kill()
