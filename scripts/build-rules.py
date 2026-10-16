"""Generate auditable RTDB rules: private accounts, atomic spending and proven rewards."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'firebase.rules.json').read_text())['rules']
owner="auth != null && root.child('members').child(auth.uid).child('player').val() === $player && root.child('playerOwners').child($player).val() === auth.uid"
g="root.child('gameState').child($player)";w=g+".child('wallet')";e='newData'
def ch(s,*keys):
 for key in keys:s+=".child("+(key[1:] if key.startswith('@') else "'"+key+"'")+")"
 return s
def val(s):return s+'.val()'
def v(s,*keys):return val(ch(s,*keys))
def and_(*a):return '('+' && '.join(a)+')'
def or_(*a):return '('+' || '.join(a)+')'
def proof(i):return ch(e,'proofs',str(i))
def passed(pf,start,end,player='$player'):
 ident=v(pf,'id');key=v(pf,'key');record=ch('root','pasados','@'+key);hist=ch('root','historial',"@"+ident+" + '_' + "+player)
 return and_(ch(pf,'id')+'.isString()',ch(pf,'key')+'.isString()',v(record,'id')+' === '+ident,v(record,'@'+player)+' === true',v(hist,'demonKey')+' === '+ident,v(hist,'player')+' === '+player,ch(hist,'timestamp')+'.isNumber()',v(hist,'timestamp')+' >= '+start,v(hist,'timestamp')+' < '+end)
def eligible(q,start,end,depth=0):
 kind=v(q,'kind');target=v(q,'target');start='('+start+' > '+v(q,'createdAt')+' ? '+start+' : '+v(q,'createdAt')+')';p0=proof(0);opts=ch(q,'options');lid=v(q,'level','id')
 level=and_(v(p0,'id')+' === '+lid,passed(p0,start,end))
 choice=and_(or_(*(v(p0,'id')+' === '+v(opts,str(i),'id') for i in range(3))),passed(p0,start,end))
 easychecks=[target+' >= 1',target+' <= 5'];creatorchecks=[target+' >= 1',target+' <= 3']
 for i in range(5):
  valid=and_(passed(proof(i),start,end),v(ch('root','levelCatalog','@'+v(proof(i),'id')),'difficulty')+" === 'Easy'")
  easychecks.append(or_(target+' <= '+str(i),valid))
  if i<3:creatorchecks.append(or_(target+' <= '+str(i),valid))
  for j in range(i):
   easychecks.append(or_(target+' <= '+str(i),v(proof(i),'id')+' !== '+v(proof(j),'id')))
   if i<3:creatorchecks.append(or_(target+' <= '+str(i),v(ch('root','levelCatalog','@'+v(proof(i),'id')),'creator')+' !== '+v(ch('root','levelCatalog','@'+v(proof(j),'id')),'creator')))
 easy=and_(*easychecks);creators=and_(*creatorchecks)
 runs=ch('root','runs','@$player','@'+lid);goal=ch('root','objetivos','@$player');profile=ch('root','verifiedProfiles','@$player')
 percent=or_(level,and_(v(runs,'best')+' >= '+target,v(runs,'updatedAt')+' >= '+start,v(runs,'updatedAt')+' < '+end),and_(v(goal,'id')+' === '+lid,v(goal,'best')+' >= '+target,v(goal,'updatedAt')+' >= '+start,v(goal,'updatedAt')+' < '+end))
 stat=and_(ch(q,'baseline')+'.isNumber()',v(q,'waitingBaseline')+' !== true',v(profile,'at')+' >= '+v(q,'baselineAt'),v(profile,'at')+' < '+end,v(profile,'stats','@'+v(q,'stat'))+' >= '+v(q,'baseline')+' + '+target)
 two=and_(target+' === 2',passed(proof(0),start,end),passed(proof(1),start,end),v(proof(0),'id')+' !== '+v(proof(1),'id'),or_(and_(v(proof(0),'id')+' === '+v(opts,'0','id'),v(proof(1),'id')+' === '+v(opts,'1','id')),and_(v(proof(1),'id')+' === '+v(opts,'0','id'),v(proof(0),'id')+' === '+v(opts,'1','id'))))
 awards=[target+' >= 1',target+' <= 10']
 for i in range(10):
  award=v(proof(i),'award');entry=ch(w,'ledger','@'+award)
  category=or_(*(and_(v(q,'awardType')+" === '"+k+"'",ch(proof(i),'award')+".val().matches(/^"+k+"_/)" ) for k in ['mission','daily','weekly','team']),and_(v(q,'awardType')+" === 'statmission'",ch(proof(i),'award')+".val().matches(/^mission_/)",v(entry,'statMission')+' === true'))
  valid=and_(ch(proof(i),'award')+'.isString()',entry+'.exists()',v(entry,'at')+' >= '+start,v(entry,'at')+' < '+end,category)
  awards.append(or_(target+' <= '+str(i),valid))
  for j in range(i):awards.append(or_(target+' <= '+str(i),v(proof(i),'award')+' !== '+v(proof(j),'award')))
 if depth>0:return or_(and_(kind+" === 'level'",level),and_(kind+" === 'stat'",stat),and_(kind+" === 'percent'",percent))
 cases=[and_(kind+" === 'level'",level),and_(kind+" === 'choice'",choice),and_(kind+" === 'levels_count'",or_(and_(target+' === 1',choice),two)),and_(kind+" === 'easy_count'",easy),and_(kind+" === 'creator_count'",creators),and_(kind+" === 'percent'",percent),and_(kind+" === 'stat'",stat)]
 if depth==0:cases.append(and_(kind+" === 'combo'",eligible(ch(q,'parts','0'),start,end,1),eligible(ch(q,'parts','1'),start,end,1)))
 # Award counters occur in bingo only; skip exponential expansion in combo children.
 if depth==0:cases.append(and_(kind+" === 'awards'",and_(*awards)))
 return or_(v(q,'completed')+' === true',and_(v(q,'unavailable')+' !== true',or_(*cases)))
# Receipt eligibility is evaluated once, at creation. Other leaves point at it.
kind=v(e,'kind');period=v(e,'period');slot=v(e,'slot');item=v(e,'item');level=v(e,'levelId')
product=ch('root','shopCatalog','@'+item);daily=ch(g,'daily');bingo=ch(g,'bingo');q=ch(daily,'quests','@'+slot);cell=ch(bingo,'cells','@'+slot)
cases=[]
def case(k,idexpr,amount,xp,checks):
 cases.append(and_(kind+" === '"+k+"'",'$receipt === '+idexpr,v(e,'amount')+' === '+amount,v(e,'xp')+' === '+xp,*checks))
case('purchase',"'buy_' + "+item,'0 - '+v(product,'price'),'0',[product+'.exists()',v(product,'price')+' >= 0',v(w,'owned','@'+item)+' !== true',v('newData.parent().parent()','owned','@'+item)+' === true',v(w,'balance')+' >= '+v(product,'price'),v(e,'statMission')+' === false',v(e,'reason')+" === 'Compra: ' + "+v(product,'name')])
tier=v(ch('root','levelCatalog','@'+level),'tier');amount='20 + ('+tier+' * 2) - (('+tier+' * 2) % 1)'
case('level',"'level_' + "+level,amount,'10',[ch('root','levelCatalog','@'+level)+'.exists()',v(w,'paidLevels','@'+level)+' !== true',v('newData.parent().parent()','paidLevels','@'+level)+' === true',v(proof(0),'id')+' === '+level,passed(proof(0),v(g,'activatedAt'),'now + 1'),v(e,'statMission')+' === false'])
case('mission',"'mission_' + "+v(q,'id'),v(q,'reward'),v(q,'xp'),[period+' === '+v(daily,'day'),ch(e,'slot')+'.isString()',v(e,'statMission')+' === ('+v(q,'kind')+" === 'stat' || "+v(q,'kind')+" === 'combo')",eligible(q,v(daily,'startsAt'),v(daily,'endsAt'))])
for k,reward,xp in [('daily',50,35),('weekly',100,75),('coop',60,40),('team',90,60)]:
 c=ch(g,'assignments',{'coop':'cooperative','team':'cooperative'}.get(k,k));checks=[c+'.exists()',period+' === '+v(c,'period'),v(e,'statMission')+' === false']
 if k=='team':
  for i,p in enumerate(['thiaguinhio','michaeelp','nzrv']):checks.extend([v(proof(i),'id')+' === '+v(c,'id'),passed(proof(i),v(c,'startsAt'),v(c,'endsAt'),"'"+p+"'")])
 else:checks.extend([v(proof(0),'id')+' === '+v(c,'id'),passed(proof(0),v(c,'startsAt'),v(c,'endsAt'))])
 case(k,"'"+k+"_' + "+period,str(reward),str(xp),checks)
case('all',"'all_' + "+period,'75','60',[period+' === '+v(daily,'day'),v(e,'statMission')+' === false',*(ch(w,'ledger',"@'mission_' + "+v(daily,'quests',str(i),'id'))+'.exists()' for i in range(4))])
case('bingo',"'bingo_' + "+period+" + '_cell_' + "+slot,v(cell,'reward'),'30',[period+' === '+v(bingo,'month'),v(e,'statMission')+' === false',eligible(cell,v(bingo,'activatedAt'),v(bingo,'endsAt'))])
lines=[[i*4+j for j in range(4)] for i in range(4)]+[[i+j*4 for j in range(4)] for i in range(4)]+[[0,5,10,15],[3,6,9,12]]
linechecks=[]
for i,line in enumerate(lines):linechecks.append(and_(slot+" === '"+str(i)+"'",*(ch(w,'ledger',"@'bingo_' + "+period+" + '_cell_"+str(j)+"'")+'.exists()' for j in line)))
case('line',"'bingo_' + "+period+" + '_line_' + "+slot,'100','50',[period+' === '+v(bingo,'month'),v(e,'statMission')+' === false',or_(*linechecks)])
case('full',"'bingo_' + "+period+" + '_full'",'400','200',[period+' === '+v(bingo,'month'),v(e,'statMission')+' === false',*(ch(w,'ledger',"@'bingo_' + "+period+" + '_cell_"+str(i)+"'")+'.exists()' for i in range(16))])
newwallet='newData.parent().parent()';oldwallet='data.parent().parent()'
receipt_validation=and_("newData.hasChildren(['kind','amount','xp','reason','at','statMission'])","newData.child('at').val() === now","newData.child('amount').isNumber()","newData.child('xp').isNumber()","newData.child('reason').isString()","newData.child('reason').val().length <= 300",v(newwallet,'lastOp')+' === $receipt',v(newwallet,'balance')+' === '+v(oldwallet,'balance')+' + '+v(e,'amount'),v(newwallet,'xp')+' === '+v(oldwallet,'xp')+' + '+v(e,'xp'),v(newwallet,'earned')+' === '+v(oldwallet,'earned')+' + ('+v(e,'amount')+' > 0 ? '+v(e,'amount')+' : 0)',or_(*cases))
wallet={}
for field in ['balance','xp','earned']:
 nw='newData.parent()';ow='data.parent()';receipt=ch(nw,'ledger','@'+v(nw,'lastOp'));delta=v(receipt,'amount') if field=='balance' else v(receipt,'xp') if field=='xp' else '('+v(receipt,'amount')+' > 0 ? '+v(receipt,'amount')+' : 0)'
 wallet[field]={'.write':and_(owner,'newData.isNumber()',ch(nw,'lastOp')+'.isString()',ch(ow,'ledger','@'+v(nw,'lastOp'))+'.exists() === false',receipt+'.exists()'),'.validate':and_('newData.val() >= 0','newData.val() === data.val() + '+delta)}
nw='newData.parent()';ow='data.parent()'
wallet['lastOp']={'.write':and_(owner,'newData.isString()',"newData.val().length <= 200",ch(ow,'ledger','@newData.val()')+'.exists() === false',ch(nw,'ledger','@newData.val()')+'.exists()')}
wallet['ledger']={'$receipt':{'.write':and_(owner,'!data.exists()','newData.exists()'),'.validate':receipt_validation}}
nw='newData.parent().parent()';receipt=ch(nw,'ledger','@'+v(nw,'lastOp'))
wallet['owned']={'$item':{'.write':and_(owner,'!data.exists()','newData.val() === true',v(receipt,'kind')+" === 'purchase'",v(receipt,'item')+' === $item',ch('data.parent().parent()','ledger','@'+v(nw,'lastOp'))+'.exists() === false')}}
wallet['paidLevels']={'$level':{'.write':and_(owner,'!data.exists()','newData.val() === true',v(receipt,'kind')+" === 'level'",v(receipt,'levelId')+' === $level',ch('data.parent().parent()','ledger','@'+v(nw,'lastOp'))+'.exists() === false')}}
r['gameState']={'.read':False,'.write':False,'$player':{'.read':owner,'wallet':wallet}}
for name in ['runs','preferences','requests']:
 r[name]['.read']=False
 node=r[name]['$player'];node['.read']=owner
 if name=='preferences':node['.write']=owner
 elif name=='requests':node['$request']['.write']=owner+' && !data.exists() && newData.exists()'
 else:node['$id']['.write']=owner
for name in ['desafios','cooperativas','challengeArchive']:r[name]={'.read':False,'.write':False}
r['shopCatalog']={'.read':True,'.write':False}
r['publicProfiles']={'.read':True,'$player':{}}
public=r['publicProfiles']['$player']
for kind in ['title','color','badge','theme','font']:
 public[kind]={'.write':owner,'.validate':"newData.isString() && root.child('shopCatalog').child(newData.val()).child('kind').val() === '"+kind+"' && (root.child('shopCatalog').child(newData.val()).child('price').val() === 0 || "+v(w,'owned','@newData.val()')+' === true)'}
for name,limit in [('bio',160),('nickname',30)]:public[name]={'.write':owner,'.validate':f'newData.isString() && newData.val().length <= {limit}'}
public['showActivity']={'.write':owner,'.validate':'newData.isBoolean()'}
public['$other']={'.validate':False}
# Expanded private preferences, with only known fields accepted.
prefs=r['preferences']['$player']
for k in ['sound','reducedMotion','compact','autoRewards','confirmPurchase','hideCompleted','highContrast']:prefs[k]={'.validate':'newData.isBoolean()'}
prefs['home']={'.validate':"newData.val() === 'home' || newData.val() === 'quests' || newData.val() === 'challenges' || newData.val() === 'bingo' || newData.val() === 'wallet'"}
prefs['shopView']={'.validate':"newData.val() === 'all' || newData.val() === 'owned' || newData.val() === 'unowned'"}
prefs['releaseSeen']={'.validate':'newData.isString() && newData.val().length <= 20'}
(ROOT/'firebase.rules.json').write_text(json.dumps({'rules':r},ensure_ascii=False,indent=2)+'\n')
print('Rules:',(ROOT/'firebase.rules.json').stat().st_size,'bytes; receipt validator:',len(receipt_validation))
