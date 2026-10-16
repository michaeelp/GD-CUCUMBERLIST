"""Trusted scheduled verifier. Service account stays in a GitHub Actions secret."""
import argparse,json,os,sys,time,urllib.request,urllib.error
from copy import deepcopy
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from game_engine import PLAYERS,merged,assignments,update_player,SHOP
ROOT=Path(__file__).resolve().parents[1]
DATABASE='https://gd-cucumberlist-default-rtdb.firebaseio.com'
class Database:
 def __init__(self,token):self.token=token
 def request(self,path,method='GET',value=None,etag=None):
  headers={'Content-Type':'application/json','Authorization':'Bearer '+self.token}
  if method=='GET':headers['X-Firebase-ETag']='true'
  if etag is not None:headers['if-match']=etag
  req=urllib.request.Request(DATABASE+'/'+path.strip('/')+'.json',data=json.dumps(value,separators=(',',':')).encode() if value is not None else None,headers=headers,method=method)
  try:
   with urllib.request.urlopen(req,timeout=25) as response:return json.loads(response.read() or 'null'),response.headers.get('ETag')
  except urllib.error.HTTPError as e:
   if e.code==412:return None,'conflict'
   raise RuntimeError('Firebase rechazó la operación ('+str(e.code)+').') from None
 def get(self,path):return self.request(path)[0]
 def patch(self,path,value):return self.request(path,'PATCH',value)[0]
 def transaction(self,path,calculate):
  for _ in range(6):
   old,etag=self.request(path)
   if not etag:raise RuntimeError('Firebase no devolvió un ETag.')
   new=calculate(deepcopy(old))
   if new==old:return old
   result,status=self.request(path,'PUT',new,etag)
   if status!='conflict':return result
  raise RuntimeError('Reintentá: hay otra actualización en curso.')
def fetch_profile(p,account):
 body=urlencode({'targetAccountID':account,'secret':'Wmfd2893gb7','gameVersion':'22','binaryVersion':'45'}).encode();req=urllib.request.Request('https://www.boomlings.com/database/getGJUserInfo20.php',data=body,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':''})
 try:
  with urllib.request.urlopen(req,timeout=16) as r:parts=r.read().decode().split(':')
  raw=dict(zip(parts[::2],parts[1::2]))
  if raw.get('16')!=str(account) or not raw.get('1'):return p,None
  stats={name:int(raw[key]) if raw.get(key,'').isdigit() else None for name,key in {'stars':'3','moons':'52','diamonds':'46','userCoins':'17','demons':'4'}.items()}
  return p,{'accountId':str(account),'raw':raw,'stats':stats,'at':int(time.time()*1000),'fetchedAt':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
 except Exception:return p,None

def load_catalog(db):
 import re,math
 try:
  url='https://docs.google.com/spreadsheets/d/1qKlWKpDkOpU1ZF6V6xGfutDY2NvcA8MNPnsv6GBkKPQ/gviz/tq?tqx=out:json&gid=0'
  with urllib.request.urlopen(url,timeout=20) as response:text=response.read().decode()
  match=re.search(r'google\.visualization\.Query\.setResponse\(([\s\S]*)\);?\s*$',text)
  rows=json.loads(match.group(1))['table']['rows'];out={}
  for row in rows:
   c=row['c'];get=lambda i:None if not c[i] else c[i].get('v');value=get(0);ident=str(int(value)) if isinstance(value,(int,float)) and float(value).is_integer() else str(value);raw=get(5)
   if not ident.isdigit() or not get(1) or raw is None or raw=='':continue
   tier=math.floor(float(raw)*10)/10
   if not math.isfinite(tier) or tier<0:continue
   out.setdefault(ident,{'id':ident,'name':str(get(1)).strip(),'creator':str(get(2) or ''),'difficulty':str(get(4) or ''),'tier':tier})
  if len(out)<100:raise ValueError('Catálogo incompleto')
  return list(out.values())
 except Exception:
  previous=db.get('levelCatalog') or {}
  return list(previous.values()) if previous else json.loads((ROOT/'data/catalog.json').read_text())['data']

def run(db,bind_uid='',bind_player='',admin_uid=''):
 now=int(time.time()*1000);catalog=load_catalog(db);manifest=json.loads((ROOT/'data/economy-bootstrap.json').read_text());accounts=json.loads((ROOT/'cuentas.json').read_text())
 if admin_uid and not db.get('admins'):db.patch('admins',{admin_uid:True})
 if bind_uid and bind_player in PLAYERS:
  import re
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',bind_uid):raise RuntimeError('UID inválido.')
  owners=db.get('playerOwners') or {};members=db.get('members') or {}
  if owners.get(bind_player) not in [None,bind_uid]:raise RuntimeError('Ese jugador ya tiene un UID. Usá el panel de administración para reemplazarlo.')
  if bind_uid in members and members[bind_uid].get('player')!=bind_player:raise RuntimeError('Ese UID ya está asociado con otro jugador.')
  db.patch('',{f'members/{bind_uid}':{'player':bind_player,'accountId':str(accounts[bind_player]['accountId'])},f'playerOwners/{bind_player}':bind_uid})
 paths=['pasados','historial','runs','objetivos','requests','gameState','desafios','cooperativas','verifiedProfiles','gameMeta']
 with ThreadPoolExecutor(max_workers=5) as pool:root=dict(zip(paths,pool.map(lambda p:db.get(p) or {},paths)))
 root['_catalog']=catalog;levels=merged(root['pasados'],catalog);lookup={str(d['id']):d for d in catalog};metadata={};aliases={}
 for d in levels:
  trusted=lookup.get(d['id'])
  if not trusted:continue
  for key in d.get('_keys',[]):
   aliases[key]=d['id']
   for field in ['id','name','creator','difficulty','tier']:
    if root['pasados'][key].get(field)!=trusted.get(field):metadata[f'pasados/{key}/{field}']=trusted.get(field,'');root['pasados'][key][field]=trusted.get(field,'')
 for key,h in root['historial'].items():
  trusted=lookup.get(aliases.get(str(h.get('demonKey')),str(h.get('demonKey'))))
  if trusted:
   for field in ['name','creator','difficulty','tier']:
    dest='demon' if field=='name' else field
    if h.get(dest)!=trusted.get(field):metadata[f'historial/{key}/{dest}']=trusted.get(field,'');h[dest]=trusted.get(field,'')
 if metadata:db.patch('',metadata)
 levels=merged(root['pasados'],catalog)
 with ThreadPoolExecutor(max_workers=3) as pool:profiles=list(pool.map(lambda p:fetch_profile(p,str(accounts[p]['accountId'])),PLAYERS))
 for p,profile in profiles:
  if profile:db.patch('verifiedProfiles',{p:profile});root['verifiedProfiles'][p]=profile
  else:print('Perfil sin consulta nueva:',p)
 now=int(time.time()*1000)
 signature=__import__('hashlib').sha256(json.dumps(catalog,sort_keys=True).encode()).hexdigest()
 if root['gameMeta'].get('catalogHash')!=signature:
  db.request('levelCatalog','PUT',{str(d['id']):{k:d.get(k,'') for k in ['id','name','creator','difficulty','tier']} for d in catalog})
  db.patch('gameMeta',{'catalogHash':signature})
 # Assignments are create-once, even when two trusted runs overlap.
 for path,value in assignments(root,levels,now).items():
  previous=db.get(path)
  if previous and path.startswith('desafios/') and previous.get('version',1)<2:
   db.transaction('challengeArchive/'+path.replace('/','_'),lambda old:old or previous)
  actual=db.transaction(path,lambda old:old if old and (not path.startswith('desafios/') or old.get('version',1)>=2) else value);node=root
  keys=path.split('/')
  for key in keys[:-1]:node=node.setdefault(key,{})
  node[keys[-1]]=actual
 # Fill legacy IDs without changing flags, dates, or deleting rows.
 patch={}
 for d in levels:
  if not d['id'].isdigit():continue
  for key in d.get('_keys',[]):
   if not root['pasados'][key].get('id'):patch['pasados/'+key+'/id']=d['id']
 if patch:db.patch('',patch)
 db.request('shopCatalog','PUT',{item['id']:item for item in SHOP})
 for p in PLAYERS:
  previous=db.get('gameState/'+p) or {}
  if previous.get('version',0)<4:
   legacy=previous.get('wallet',{}).get('equipped',{})
   db.transaction('publicProfiles/'+p,lambda current:{**legacy,**(current or {})} or {'showActivity':True})
  state=db.transaction('gameState/'+p,lambda old:update_player(old,root,levels,p,manifest,now));print(p,'saldo',state['wallet']['balance'],'misiones',sum(q['completed'] for q in state['daily']['quests']))
 db.patch('gameMeta',{'lastRun':now,'version':4,'shop':SHOP,'initialFormula':manifest['formula']})
 print('Verificación finalizada. No se modificaron usuarios ni reglas.')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
 if args.dry_run:
  catalog=json.loads((ROOT/'data/catalog.json').read_text())['data'];root={name:json.loads((ROOT/'data'/f'{name}.json').read_text())['data'] for name in ['pasados','historial']};root['_catalog']=catalog;levels=merged(root['pasados'],catalog);manifest=json.loads((ROOT/'data/economy-bootstrap.json').read_text());now=int(time.time()*1000)
  for path,value in assignments(root,levels,now).items():
   node=root;keys=path.split('/')
   for key in keys[:-1]:node=node.setdefault(key,{})
   node[keys[-1]]=value
  preview={p:update_player({},root,levels,p,manifest,now) for p in PLAYERS};(ROOT/'tests/game-preview.local.json').write_text(json.dumps({'preview':True,'gameState':preview,'cooperativas':root.get('cooperativas',{}),'desafios':root.get('desafios',{}),'shop':SHOP},ensure_ascii=False,separators=(',',':')))
  print('Vista previa generada; no se escribió en Firebase.');return
 secret=os.environ.get('FIREBASE_SERVICE_ACCOUNT','')
 if not secret:raise RuntimeError('Falta el secret FIREBASE_SERVICE_ACCOUNT. Consultá ACTIVAR_SISTEMA.md.')
 from google.oauth2 import service_account
 from google.auth.transport.requests import Request
 info=json.loads(secret)
 if info.get('project_id')!='gd-cucumberlist':raise RuntimeError('La cuenta de servicio pertenece a otro proyecto.')
 credentials=service_account.Credentials.from_service_account_info(info,scopes=['https://www.googleapis.com/auth/firebase.database','https://www.googleapis.com/auth/userinfo.email']);credentials.refresh(Request())
 run(Database(credentials.token),os.environ.get('LINK_UID','').strip(),os.environ.get('LINK_PLAYER','').strip(),os.environ.get('INITIAL_ADMIN_UID','').strip())
if __name__=='__main__':
 try:main()
 except Exception as e:print('Error:',str(e),file=sys.stderr);sys.exit(1)
