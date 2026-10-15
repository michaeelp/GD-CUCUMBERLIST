"""Actualiza datos públicos de GD para GitHub Pages. Nunca escribe en Firebase."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import io,json,math,plistlib,re,time,sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
ICONS=ROOT/'assets/icons'
SPRITES=json.loads((ROOT/'scripts/gd-sprites.json').read_text())
COLORS=json.loads((ROOT/'scripts/gd-colors.json').read_text())
FORMS={'21':'player','22':'ship','23':'player_ball','24':'bird','25':'dart','26':'robot','43':'spider','53':'swing','54':'jetpack'}
DATABASE='https://gd-cucumberlist-default-rtdb.firebaseio.com'
SHEET='https://docs.google.com/spreadsheets/d/1qKlWKpDkOpU1ZF6V6xGfutDY2NvcA8MNPnsv6GBkKPQ/gviz/tq?tqx=out:json&gid=0'
GD='https://www.boomlings.com/database/'
SPRITE_BASE='https://raw.githubusercontent.com/Supernova3339/gavatar/master/assets/icons/'
NOW=lambda:datetime.now(timezone.utc).isoformat()
def read(path,fallback=None):
 try:return json.loads(path.read_text())
 except (OSError,ValueError):return fallback

def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(path.suffix+'.tmp')
 temp.write_text(json.dumps(value,separators=(',',':'),ensure_ascii=False))
 temp.replace(path)

def get(url,data=None):
 headers={'User-Agent':'' if url.startswith(GD) else 'GD-Cucumberlist-Pages/2.1'}
 if data is not None:headers['Content-Type']='application/x-www-form-urlencoded'
 with urlopen(Request(url,data=urlencode(data).encode() if data is not None else None,headers=headers),timeout=18) as r:return r.read()

def post(endpoint,data):
 text=get(GD+endpoint,{**data,'secret':'Wmfd2893gb7','gameVersion':'22','binaryVersion':'45'}).decode()
 if not text or text.strip()=='-1' or text.startswith('<'):raise ValueError('GD no devolvió datos públicos')
 return text

def pairs(text):
 fields=text.split(':');return dict(zip(fields[::2],fields[1::2]))

def sprite(name):
 if not re.fullmatch(r'(?:player_ball|player|ship|bird|dart|robot|spider|swing|jetpack)_\d{2,3}(?:_[a-zA-Z0-9]+|-[a-z]+)*\.(?:png|plist)',name):return False
 path=ICONS/name
 if path.is_file():return True
 try:
  body=get(SPRITE_BASE+name)
  if name.endswith('.png') and not body.startswith(b'\x89PNG'):return False
  if name.endswith('.plist'):plistlib.loads(body)
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body);return True
 except Exception:return False

def texture(base,name):
 path=ICONS/name
 if path.is_file() and name in SPRITES:
  return Image.open(path).convert('RGBA'),SPRITES[name]['spriteOffset']
 plist=ICONS/(base+'-hd.plist');sheet=ICONS/(base+'-hd.png')
 data=plistlib.loads(plist.read_bytes());frame=data['frames'].get(name)
 if not frame:raise ValueError('Capa no disponible: '+name)
 nums=list(map(int,re.findall(r'-?\d+',frame['textureRect'])))
 x,y,w,h=nums
 if frame.get('textureRotated'):w,h=h,w
 image=Image.open(sheet).convert('RGBA').crop((x,y,x+w,y+h))
 if frame.get('textureRotated'):image=image.transpose(Image.Transpose.ROTATE_90)
 offset=list(map(int,re.findall(r'-?\d+',frame.get('spriteOffset','{0,0}'))))
 return image,offset

def portrait(player,raw):
 base=f"player_{int(raw['21']):02d}"
 canvas=Image.new('RGBA',(512,512))
 layers=[]
 if raw.get('28')=='1' or raw.get('10')=='15':layers.append((base+'_glow_001.png',raw.get('51',raw.get('11','12'))))
 layers.extend([(base+'_2_001.png',raw['11']),(base+'_001.png',raw['10'])])
 extra=base+'_extra_001.png'
 frame_data=plistlib.loads((ICONS/(base+'-hd.plist')).read_bytes())['frames'] if (ICONS/(base+'-hd.plist')).exists() else {}
 if extra in SPRITES or extra in frame_data:layers.append((extra,'12'))
 for name,color in layers:
  image,(ox,oy)=texture(base,name)
  c=COLORS.get(str(color))
  if not c:raise ValueError('Color no disponible')
  tint=ImageChops.multiply(image.convert('RGB'),Image.new('RGB',image.size,(c['r'],c['g'],c['b']))).convert('RGBA')
  tint.putalpha(image.getchannel('A'))
  canvas.alpha_composite(tint,(round(256-image.width/2+ox),round(256-image.height/2-oy)))
 bounds=canvas.getbbox()
 if not bounds:raise ValueError('Icono vacío')
 cropped=canvas.crop(bounds);scale=154/max(cropped.size);cropped=cropped.resize((max(1,round(cropped.width*scale)),max(1,round(cropped.height*scale))),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(180,180));out.alpha_composite(cropped,((180-cropped.width)//2,(180-cropped.height)//2))
 target=ROOT/'assets/avatars'/f'{player}.png';target.parent.mkdir(exist_ok=True,parents=True);out.save(target,optimize=True)

def update_profiles(offline=False):
 config=read(ROOT/'cuentas.json',{})
 previous=read(DATA/'profiles.json',{})
 for player,account in config.items():
  try:
   if offline:raw=previous[player]['raw'];when=previous[player]['fetchedAt']
   else:
    id=str(account.get('accountId',''))
    if not re.fullmatch(r'\d{1,12}',id):
     username=account['username'];users=post('getGJUsers20.php',{'str':username,'type':'0','page':'0'})
     matches=[pairs(t) for t in users.split('#')[0].split('|') if pairs(t).get('1','').lower()==username.lower()]
     if len(matches)!=1:raise ValueError('Nombre exacto no único')
     id=matches[0]['16']
    raw=pairs(post('getGJUserInfo20.php',{'targetAccountID':id}))
    if raw.get('16')!=id or not raw.get('1'):raise ValueError('Cuenta no verificada')
    when=NOW()
   names=set()
   for key,form in FORMS.items():
    if key not in raw:continue
    base=f'{form}_{int(raw[key]):02d}'
    names.update(name for name in SPRITES if name.startswith(base+'_'))
    names.update([base+'-hd.png',base+'-hd.plist'])
   with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(sprite,sorted(names)))
   portrait(player,raw)
   previous[player]={'raw':raw,'fetchedAt':when}
   print(f"Perfil actualizado: {player} → {raw['1']} ({raw['16']}), {sum(results)}/{len(results)} recursos")
  except Exception as e:print(f'Conservando perfil guardado de {player}: {type(e).__name__}: {e}')
 write(DATA/'profiles.json',previous)

def update_firebase_copies():
 for route in ['pasados','historial']:
  try:
   data=json.loads(get(f'{DATABASE}/{route}.json'))
   if data is not None and not isinstance(data,dict):raise ValueError('Formato no válido')
   write(DATA/(route+'.json'),{'data':data or {},'fetchedAt':NOW()})
  except Exception as e:print('Conservando copia de',route,type(e).__name__)

def update_catalog():
 try:
  text=get(SHEET).decode();match=re.search(r'setResponse\(([\s\S]*)\);?\s*$',text)
  parsed=json.loads(match[1]);out=[];seen=set()
  for row in parsed['table']['rows']:
   c=row['c']
   try:
    id=str(int(c[0]['v']));name=str(c[1]['v']).strip();raw=c[5]['v']
    if raw is None or raw=='' or not name or id in seen:continue
    tier=math.floor(float(raw)*10)/10
    if not math.isfinite(tier) or tier<0:continue
    out.append({'id':id,'name':name,'creator':str(c[2]['v']) if c[2] else '', 'difficulty':str(c[4]['v']) if c[4] else '', 'tier':tier});seen.add(id)
   except (ValueError,KeyError,TypeError,IndexError):continue
  if not out:raise ValueError('Catálogo vacío')
  write(DATA/'catalog.json',{'data':out,'fetchedAt':NOW()});print('Catálogo:',len(out),'niveles')
 except Exception as e:print('Conservando catálogo guardado:',type(e).__name__)

def update_levels():
 records=read(DATA/'pasados.json',{}).get('data',{})
 current=read(DATA/'level-details.json',{'data':{}}).get('data',{})
 ids=[str(d.get('id',key)) for key,d in records.items() if isinstance(d,dict) and any(d.get(p) for p in ['thiaguinhio','michaeelp','nzrv'])]
 ids=[id for id in ids if re.fullmatch(r'\d+',id) and id not in ['1','2','3']]
 ids=sorted(set(ids),key=lambda id:current.get(id,{}).get('fetchedAt',''))[:60]
 for start in range(0,len(ids),20):
  requested=ids[start:start+20]
  try:
   sections=post('getGJLevels21.php',{'str':','.join(requested),'type':'10','page':'0'}).split('#')
   users={u.split(':')[0]:u.split(':')[1] for u in sections[1].split('|') if ':' in u} if len(sections)>1 else {}
   for text in sections[0].split('|'):
    r=pairs(text);id=r.get('1')
    if id not in requested:continue
    number=lambda key:int(r[key]) if key in r and re.fullmatch(r'-?\d+',r[key]) else None
    song_id=number('35')
    current[id]={'id':id,'name':r.get('2'),'creator':users.get(r.get('6')),'stars':number('18'),'downloads':number('10'),'likes':number('14'),'length':{0:'Tiny',1:'Short',2:'Medium',3:'Long',4:'XL',5:'Platformer'}.get(number('15')),'song':f'Canción #{song_id}' if song_id else f"Canción oficial #{int(r['12'])+1}" if '12' in r else None,'songId':song_id,'fetchedAt':NOW()}
  except Exception as e:print('Detalles de niveles no actualizados:',type(e).__name__)
 write(DATA/'level-details.json',{'data':current,'fetchedAt':NOW()});print('Detalles públicos guardados:',len(current))

def main():
 offline='--offline' in sys.argv
 DATA.mkdir(exist_ok=True,parents=True);ICONS.mkdir(exist_ok=True,parents=True)
 update_profiles(offline)
 if not offline:update_firebase_copies();update_catalog();update_levels()
 print('Actualización terminada. Firebase no recibió ninguna escritura.')
if __name__=='__main__':main()
