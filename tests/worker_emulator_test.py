"""Actual verifier against isolated RTDB emulator, never production."""
import subprocess,urllib.request,urllib.error,json,time,sys,importlib.util,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('worker',ROOT/'scripts/verificar-juego.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
jar=sys.argv[1];process=subprocess.Popen(['java','-jar',jar,'--host','127.0.0.1','--port','9013'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));original_urlopen=urllib.request.urlopen;urllib.request.urlopen=opener.open
worker.DATABASE='http://127.0.0.1:9013';ns='demo-cucumber-worker'
# The emulator namespace goes in the query, preserving Database's real ETag behavior.
base_request=worker.Database.request
def namespaced(self,path,method='GET',value=None,etag=None):
 headers={'Content-Type':'application/json','Authorization':'Bearer owner'}
 if method=='GET':headers['X-Firebase-ETag']='true'
 if etag is not None:headers['if-match']=etag
 req=urllib.request.Request(worker.DATABASE+'/'+path.strip('/')+'.json?ns='+ns,data=json.dumps(value).encode() if value is not None else None,headers=headers,method=method)
 try:
  with opener.open(req,timeout=25) as r:return json.loads(r.read() or 'null'),r.headers.get('ETag')
 except urllib.error.HTTPError as e:
  if e.code==412:return None,'conflict'
  raise
worker.Database.request=namespaced;db=worker.Database('owner');catalog=json.loads((ROOT/'data/catalog.json').read_text())['data']
worker.load_catalog=lambda db:catalog
profiles=json.loads((ROOT/'data/profiles.json').read_text())
def fake_profile(p,account):
 raw=profiles[p]['raw'];return p,{'accountId':account,'raw':raw,'at':int(time.time()*1000),'fetchedAt':profiles[p]['fetchedAt'],'stats':{k:int(raw[n]) for k,n in {'stars':'3','moons':'52','diamonds':'46','userCoins':'17','demons':'4'}.items()}}
worker.fetch_profile=fake_profile
try:
 for _ in range(80):
  try:db.get('');break
  except urllib.error.URLError:time.sleep(.1)
 root={k:json.loads((ROOT/'data'/f'{k}.json').read_text())['data'] for k in ['pasados','historial']};root['legacyKeep']={'preserved':True};db.request('','PUT',root)
 worker.run(db,admin_uid='adminUID')
 first=db.get('gameState');assert {p:first[p]['wallet']['balance'] for p in worker.PLAYERS}=={'thiaguinhio':5916,'michaeelp':529,'nzrv':1637}
 assert db.get('legacyKeep')=={'preserved':True}
 assert sum(sum(bool(d.get(p)) for p in worker.PLAYERS) for d in db.get('pasados').values())==259
 worker.run(db,bind_uid='uidNzrv',bind_player='nzrv')
 assert db.get('playerOwners/nzrv')=='uidNzrv'
 assert db.get('members/uidNzrv')['accountId']=='13334739'
 second=db.get('gameState');assert all(second[p]['wallet']['balance']==first[p]['wallet']['balance'] for p in worker.PLAYERS)
 db.patch('requests/nzrv',{'r1':{'kind':'purchase','item':'color_gold','at':int(time.time()*1000)},'r2':{'kind':'purchase','item':'color_gold','at':int(time.time()*1000)}})
 worker.run(db);assert db.get('gameState/nzrv/wallet/balance')==1637-350
 # Two actual CAS transactions do not lose either credit.
 def add_one(key):
  def apply(old):
   state=old or {'balance':0,'seen':{}}
   if key not in state['seen']:state['seen'][key]=True;state['balance']+=1
   return state
  return db.transaction('cas-test',apply)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(add_one,['a','b']))
 assert db.get('cas-test')['balance']==2
 print('PASS: worker real, saldo retroactivo único, asociaciones, conservación de 259 registros, compras duplicadas y concurrencia ETag.')
finally:
 process.terminate()
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:process.kill()
 urllib.request.urlopen=original_urlopen
