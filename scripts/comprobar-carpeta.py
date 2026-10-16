from pathlib import Path
from urllib.parse import urljoin,urlsplit
import json,re,zipfile,sys
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
references=re.findall(r'(?:src|href)=[\"\']([^\"\']+)',html)
assert references and all(not r.startswith('/') for r in references)
for ref in references:assert (root/ref.split('?')[0]).is_file(),ref
for css in (root/'assets').rglob('*.css'):
 for ref in re.findall(r'url\([\"\']?([^\)\"\']+)',css.read_text()):
  if ref.startswith(('data:','http:','https:')):continue
  assert not ref.startswith('/'),ref
  assert (css.parent/ref.split('?')[0]).resolve().is_file(),ref
for base in ['https://usuario.github.io/','https://usuario.github.io/cucumberlist/','https://example.com/carpeta/index.html']:
 for ref in references:
  resolved=urljoin(base,ref)
  assert resolved.startswith(urljoin(base,'.')),(base,ref,resolved)
profiles=json.loads((root/'data/profiles.json').read_text())
assert profiles['nzrv']['raw']['16']=='13334739'
assert profiles['nzrv']['raw']['1'].lower()=='nzrvv'
for player in ['thiaguinhio','michaeelp','nzrv']:
 assert (root/'assets/avatars'/f'{player}.png').is_file()
 raw=profiles[player]['raw']
 for key,form in {'21':'player','22':'ship','23':'player_ball','24':'bird','25':'dart','26':'robot','43':'spider','53':'swing','54':'jetpack'}.items():
  base=f'{form}_{int(raw[key]):02d}'
  assert (root/'assets/icons'/(base+'-hd.plist')).is_file(),base
  assert (root/'assets/icons'/(base+'-hd.png')).is_file(),base
records=json.loads((root/'data/pasados.json').read_text())['data']
assert sum(sum(bool(d.get(p)) for p in ['thiaguinhio','michaeelp','nzrv']) for d in records.values())==259
levels=json.loads((root/'data/level-details.json').read_text())['data']
assert len(levels)>=60
workflow=(root/'.github/workflows/pages.yml').read_text()
for item in ['actions/checkout@v6','actions/configure-pages@v5','actions/upload-pages-artifact@v4','actions/deploy-pages@v4','actualizar-datos.py']:assert item in workflow
assert not (root/'runtime-config.js').exists()
shop=json.loads((root/'data/shop.json').read_text())
assert len(shop)==len({d['id'] for d in shop})==102
assert {kind:sum(d['kind']==kind for d in shop) for kind in ['title','color','badge','theme','font']}=={'title':30,'color':24,'badge':24,'theme':12,'font':12}
assert all(re.fullmatch('[A-Za-z0-9_]+',d['id']) and isinstance(d['price'],int) and d['price']>=0 for d in shop)
for ttf in (root/'assets/fonts/profiles').glob('*.ttf'):assert ttf.with_name(ttf.stem+'-OFL.txt').is_file(),ttf
assert len(list((root/'assets/fonts/profiles').glob('*.ttf')))==10
assert json.loads((root/'data/game-preview.json').read_text())=={'removed':True,'version':4}
assert (root/'firebase.rules.json').stat().st_size<262144
releases=json.loads((root/'data/releases.json').read_text());assert releases[0]['version']=='4.0.0'
print('OK: recursos HTML/CSS, rutas relativas, perfiles, 259 completaciones, 102 cosméticos, 10 fuentes con licencia, versiones y reglas.')
