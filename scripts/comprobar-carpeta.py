from pathlib import Path
from urllib.parse import urljoin,urlsplit
import json,re,zipfile,sys
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
references=re.findall(r'(?:src|href)=[\"\']([^\"\']+)',html)
assert references and all(not r.startswith('/') for r in references)
for ref in references:assert (root/ref.split('?')[0]).is_file(),ref
for css in (root/'assets').glob('*.css'):
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
print('OK: recursos HTML/CSS, rutas raíz y subcarpetas, tres perfiles verificados, 27 formas equipadas, 259 completaciones y flujo de Pages.')
