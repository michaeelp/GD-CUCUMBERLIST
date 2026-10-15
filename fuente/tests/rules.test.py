"""Run against an isolated RTDB emulator; never uses production Firebase."""
import base64, concurrent.futures, json, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path
jar = sys.argv[1] if len(sys.argv)>1 else ''
if not jar or not Path(jar).is_file():
    raise SystemExit('Usage: python3 tests/rules.test.py /path/firebase-database-emulator.jar')
process = subprocess.Popen(['java','-jar',jar,'--host','127.0.0.1','--port','9012'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
base='http://127.0.0.1:9012'
ns='demo-cucumber-isolated'
def request(path, method='GET', data=None, auth=None):
    url=base+path+('&' if '?' in path else '?')+'ns='+ns
    headers={'Content-Type':'application/json'}
    if auth=='owner':headers['Authorization']='Bearer owner'
    elif auth:url+='&auth='+auth
    req=urllib.request.Request(url,method=method,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    try:
        with opener.open(req,timeout=10) as r:return r.status,json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        content=e.read().decode()
        try:content=json.loads(content)
        except ValueError:pass
        return e.code,content

def token(uid):
    def enc(x):return base64.urlsafe_b64encode(json.dumps(x,separators=(',',':')).encode()).decode().rstrip('=')
    return enc({'alg':'none','typ':'JWT'})+'.'+enc({'iss':'https://securetoken.google.com/'+ns,'aud':ns,'iat':int(time.time()),'exp':int(time.time())+3600,'sub':uid,'user_id':uid,'firebase':{'sign_in_provider':'password'}})+'.'

def add(player):
    return {f'pasados/42/{player}':True,f'pasados/42/history/{player}':f'42_{player}',f'historial/42_{player}':{'player':player,'demonKey':'42','demon':'Test','creator':'Creator','difficulty':'Hard','tier':12.3,'timestamp':{'.sv':'timestamp'}}}

def expect(name,status,actual):
    assert actual[0]==status,(name,actual)
    print('PASS',name,actual[0],flush=True)
try:
    for _ in range(60):
        try:
            request('/.json',auth='owner');break
        except urllib.error.URLError:time.sleep(.1)
    rules=json.loads(Path('../firebase.rules.json').read_text())
    expect('reglas válidas',200,request('/.settings/rules.json','PUT',rules,'owner'))
    expect('datos solo del emulador',200,request('/.json','PUT',{'editors':{'editor':True},'admins':{'editor':True},'pasados':{'42':{'id':'42','name':'Test','creator':'Creator','difficulty':'Hard','tier':12.3}},'historial':{},'changelogSeen':{'legacy':'keep'}},'owner'))
    editor=token('editor');outsider=token('visitor')
    expect('lectura pública de lista',200,request('/pasados.json'))
    expect('lectura pública de historial',200,request('/historial.json'))
    expect('raíz privada',401,request('/.json'))
    expect('IP antiguas privadas',401,request('/changelogSeen.json'))
    expect('alta anónima denegada',401,request('/.json','PATCH',add('michaeelp')))
    expect('cuenta no autorizada denegada',401,request('/.json','PATCH',add('michaeelp'),outsider))
    expect('editor consulta su autorización',200,request('/editors/editor.json',auth=editor))
    expect('no se permite elevar otro UID',401,request('/editors/visitor.json','PUT',True,editor))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda player:request('/.json','PATCH',add(player),editor),['michaeelp','thiaguinhio']))
    for i,result in enumerate(results):expect('altas concurrentes de jugadores distintos '+str(i),200,result)
    data=request('/pasados/42.json')[1]
    assert data['michaeelp'] is True and data['thiaguinhio'] is True
    assert len(data['history'])==2
    print('PASS ambos jugadores y sus punteros conservados',flush=True)
    expect('evento duplicado rechazado de forma atómica',401,request('/.json','PATCH',add('michaeelp'),editor))
    expect('fecha no reescribible',401,request('/historial/42_michaeelp/timestamp.json','PUT',42,editor))
    expect('sincronización de atributos permitida',200,request('/.json','PATCH',{'pasados/42/tier':15.2,'historial/42_michaeelp/tier':15.2},editor))
    expect('retiro limitado a un jugador',200,request('/.json','PATCH',{'pasados/42/michaeelp':False,'pasados/42/history/michaeelp':None,'historial/42_michaeelp':None},editor))
    assert request('/pasados/42/thiaguinhio.json')[1] is True
    assert request('/historial/42_thiaguinhio.json')[0]==200
    expect('prohibido borrar colección pasados',401,request('/pasados.json','DELETE',auth=editor))
    expect('prohibido borrar fila completa',401,request('/pasados/42.json','DELETE',auth=editor))
    expect('catálogo nuevo por multipath permitido',200,request('/.json','PATCH',{'pasados/99/id':'99','pasados/99/name':'Nuevo','pasados/99/creator':'Creator','pasados/99/difficulty':'Easy','pasados/99/tier':2.1,'pasados/99/nzrv':True,'pasados/99/history/nzrv':'99_nzrv','historial/99_nzrv':{'player':'nzrv','demonKey':'99','demon':'Nuevo','tier':2.1,'timestamp':{'.sv':'timestamp'}}},editor))
    expect('sembrar historial antiguo sin fecha',200,request('/historial/legacy.json','PUT',{'player':'nzrv','demonKey':'42','demon':'Test','tier':12.3},'owner'))
    expect('sincronizar historial antiguo sin inventar fecha',200,request('/historial/legacy/tier.json','PUT',15.2,editor))
    assert 'timestamp' not in request('/historial/legacy.json')[1]
    expect('asociación de GD permitida',200,request('/playerAccounts/nzrv.json','PUT',{'accountId':'123','username':'Candidate'},editor))
    expect('asociación pública denegada',401,request('/playerAccounts/nzrv.json','PUT',{'accountId':'123','username':'Other'}))
    expect('cambios de la hoja permitidos',200,request('/cucumberChangelog/event.json','PUT',{'changes':{'0':{'id':'42','name':'Test','changes':{'0':{'field':'tier','from':12.3,'to':15.2}}}},'timestamp':{'.sv':'timestamp'},'signature':'test'},editor))
    expect('exclusión temporal del editor permitida',200,request('/syncState/lease.json','PUT',{'uid':'editor','until':int(time.time()*1000)+900000},editor))
    # The new paths use the same editor identity and public read access.
    ts={'.sv':'timestamp'}
    goal={'id':'200','name':'Objetivo','creator':'Creator','difficulty':'Insane','tier':18.2,'best':63,'createdAt':ts,'updatedAt':ts}
    expect('objetivos de lectura pública',200,request('/objetivos.json'))
    expect('progreso anónimo denegado',401,request('/objetivos/nzrv.json','PUT',goal))
    expect('progreso sin autorización denegado',401,request('/objetivos/nzrv.json','PUT',goal,outsider))
    expect('guardar objetivo por editor',200,request('/objetivos/nzrv.json','PUT',goal,editor))
    original_goal=request('/objetivos/nzrv.json')[1]
    update={**original_goal,'best':81,'updatedAt':ts}
    expect('mejorar porcentaje',200,request('/objetivos/nzrv.json','PUT',update,editor))
    expect('no retroceder el mejor porcentaje',401,request('/objetivos/nzrv.json','PUT',{**update,'best':20},editor))
    expect('porcentaje mayor que 100 rechazado',401,request('/objetivos/nzrv.json','PUT',{**update,'best':101},editor))
    expect('porcentaje fraccionario rechazado',401,request('/objetivos/nzrv.json','PUT',{**update,'best':81.5},editor))
    expect('ID no numérico rechazado',401,request('/objetivos/nzrv.json','PUT',{**goal,'id':'otro'},editor))
    expect('jugador desconocido rechazado',401,request('/objetivos/otro.json','PUT',goal,editor))
    expect('reiniciar porcentaje al cambiar nivel',200,request('/objetivos/nzrv.json','PUT',{**goal,'id':'201','best':4},editor))
    expect('retiro de objetivo permitido',200,request('/objetivos/nzrv.json','DELETE',auth=editor))
    assert request('/pasados/99/nzrv.json')[1] is True
    # Goal and completion are one atomic multipath write, including a server date.
    fullgoal={**goal,'id':'202','best':100}
    completion={'player':'nzrv','demonKey':'202','demon':'Objetivo','creator':'Creator','difficulty':'Insane','tier':18.2,'timestamp':ts}
    patch={'objetivos/nzrv':fullgoal,'pasados/202/id':'202','pasados/202/name':'Objetivo','pasados/202/creator':'Creator','pasados/202/difficulty':'Insane','pasados/202/tier':18.2,'pasados/202/nzrv':True,'pasados/202/history/nzrv':'202_nzrv','historial/202_nzrv':completion}
    expect('objetivo y completación al 100 atómicos',200,request('/.json','PATCH',patch,editor))
    assert request('/objetivos/nzrv/best.json')[1]==100 and request('/pasados/202/nzrv.json')[1] is True
    bad={**patch,'objetivos/nzrv':{**fullgoal,'best':101},'pasados/202/thiaguinhio':True}
    expect('porcentaje inválido revierte toda la escritura',401,request('/.json','PATCH',bad,editor))
    assert request('/pasados/202/thiaguinhio.json')[1] is None
    expect('conservar progreso de otro jugador',200,request('/objetivos/michaeelp.json','PUT',goal,editor))
    expect('no borrar colección de objetivos',401,request('/objetivos.json','DELETE',auth=editor))
    expect('el cliente no puede escribir saldos',401,request('/gameState/nzrv/wallet/balance.json','PUT',999999,editor))
    expect('el cliente no puede fijar desafíos',401,request('/desafios/diarios/2026-01-01/nzrv.json','PUT',{},editor))
    expect('el cliente no puede inventar perfiles verificados',401,request('/verifiedProfiles/nzrv.json','PUT',{'stats':{'stars':99999}},editor))
    expect('el cliente no puede modificar catálogo confiable',401,request('/levelCatalog/42/tier.json','PUT',99,editor))
    expect('el cliente no puede crear administradores',401,request('/admins/visitor.json','PUT',True,editor))
    # Bind one account per player and test every personal write boundary.
    member=token('uid_nzrv');other=token('uid_michaeelp')
    expect('vinculación administrativa atómica',200,request('/.json','PATCH',{'members/uid_nzrv':{'player':'nzrv','accountId':'13334739'},'playerOwners/nzrv':'uid_nzrv','members/uid_michaeelp':{'player':'michaeelp','accountId':'24854395'},'playerOwners/michaeelp':'uid_michaeelp'},editor))
    expect('miembro consulta su asociación',200,request('/members/uid_nzrv.json',auth=member))
    expect('miembro no lee asociaciones ajenas',401,request('/members/uid_michaeelp.json',auth=member))
    expect('miembro no se apropia de otro jugador',401,request('/members/uid_nzrv/player.json','PUT','thiaguinhio',member))
    expect('editor antiguo sin rol nuevo no tiene permisos',401,request('/pasados/42/nzrv.json','PUT',True,token('old_editor')))
    expect('jugador registra su propia bandera',200,request('/pasados/42/nzrv.json','PUT',True,member))
    expect('jugador no modifica otra bandera',401,request('/pasados/42/michaeelp.json','PUT',True,member))
    expect('jugador no borra historial de otro',401,request('/historial/42_thiaguinhio.json','DELETE',auth=member))
    expect('jugador no falsifica tiers',401,request('/pasados/42/tier.json','PUT',999,member))
    expect('catálogo semilla confiable',200,request('/levelCatalog/500.json','PUT',{'id':'500','name':'Catalogado','creator':'Creador','difficulty':'Easy','tier':2.1},'owner'))
    metadata={f'pasados/500/{key}':value for key,value in {'id':'500','name':'Catalogado','creator':'Creador','difficulty':'Easy','tier':2.1,'nzrv':True}.items()}
    expect('miembro crea nivel con metadatos del catálogo',200,request('/.json','PATCH',metadata,member))
    expect('objetivo propio permitido',200,request('/objetivos/nzrv.json','PUT',{**goal,'id':'500'},member))
    expect('objetivo de otro denegado',401,request('/objetivos/michaeelp.json','PUT',goal,member))
    expect('porcentaje propio permitido',200,request('/runs/nzrv/500.json','PUT',{'best':35,'updatedAt':ts},member))
    expect('porcentaje de otro denegado',401,request('/runs/michaeelp/500.json','PUT',{'best':35,'updatedAt':ts},member))
    expect('solicitud propia de compra permitida',200,request('/requests/nzrv/r1.json','PUT',{'kind':'purchase','item':'color_gold','at':ts},member))
    expect('solicitud ajena denegada',401,request('/requests/michaeelp/r1.json','PUT',{'kind':'purchase','item':'color_gold','at':ts},member))
    expect('solicitud no reescribible',401,request('/requests/nzrv/r1.json','PUT',{'kind':'purchase','item':'color_cyan','at':ts},member))
    expect('saldo dentro de solicitud denegado',401,request('/requests/nzrv/r2.json','PUT',{'kind':'purchase','item':'color_cyan','at':ts,'balance':9999},member))
    expect('preferencia propia permitida',200,request('/preferences/nzrv/wishlist/500.json','PUT',True,member))
    expect('preferencia ajena denegada',401,request('/preferences/michaeelp/wishlist/500.json','PUT',True,member))
    own_completion={'pasados/500/nzrv':True,'pasados/500/history/nzrv':'500_nzrv','historial/500_nzrv':{'player':'nzrv','demonKey':'500','demon':'Catalogado','tier':2.1,'timestamp':ts},'runs/nzrv/500':{'best':100,'updatedAt':ts}}
    expect('100 por miembro con historial atómico',200,request('/.json','PATCH',own_completion,member))
    expect('miembro no crea historial en nombre de otro',401,request('/historial/500_thiaguinhio.json','PUT',{'player':'thiaguinhio','demonKey':'500','demon':'Catalogado','tier':2.1,'timestamp':ts},member))
    expect('reemplazo administrativo conserva datos',200,request('/.json','PATCH',{'members/uid_nzrv':None,'members/new_nzrv':{'player':'nzrv','accountId':'13334739'},'playerOwners/nzrv':'new_nzrv'},editor))
    expect('UID anterior pierde acceso de edición',401,request('/pasados/500/nzrv.json','PUT',False,member))
    expect('UID nuevo obtiene solo su jugador',200,request('/pasados/500/nzrv.json','PUT',True,token('new_nzrv')))
    print('ALL FIREBASE EMULATOR CHECKS PASSED',flush=True)
finally:
    process.terminate()
    try:process.wait(timeout=6)
    except subprocess.TimeoutExpired:process.kill()
