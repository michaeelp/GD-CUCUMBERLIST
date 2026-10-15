import sys,json,unittest,copy
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from game_engine import *
NOW=int(datetime.fromisoformat('2026-10-15T18:00:00+00:00').timestamp()*1000)
CAT=json.loads((ROOT/'data/catalog.json').read_text())['data'];BASE={name:json.loads((ROOT/'data'/f'{name}.json').read_text())['data'] for name in ['pasados','historial']};MAN=json.loads((ROOT/'data/economy-bootstrap.json').read_text());MAN['cutoff']=NOW

def setup():
 root=deepcopy(BASE);root['_catalog']=CAT;levels=merged(root['pasados'],CAT)
 for path,d in assignments(root,levels,NOW).items():
  node=root;keys=path.split('/')
  for key in keys[:-1]:node=node.setdefault(key,{})
  node[keys[-1]]=d
 for p in PLAYERS:root.setdefault('verifiedProfiles',{})[p]={'at':NOW,'stats':{'stars':1000,'moons':50,'diamonds':500,'userCoins':100,'demons':20}}
 return root,levels

def complete(root,p,d,at=NOW+1000):
 root['pasados'].setdefault(d['id'],clean(d))[p]=True
 root['historial'][d['id']+'_'+p]={'player':p,'demonKey':d['id'],'demon':d['name'],'tier':d['tier'],'timestamp':at}

class Engine(unittest.TestCase):
 def test_retroactive_once_for_every_player(self):
  root,levels=setup()
  for p,amount in [('thiaguinhio',5916),('michaeelp',529),('nzrv',1637)]:
   g=update_player({},root,levels,p,MAN,NOW);self.assertEqual(g['wallet']['balance'],amount);self.assertEqual(g['wallet']['ledger']['retro_v1']['amount'],amount)
   again=update_player(g,root,levels,p,MAN,NOW+100);self.assertEqual(again['wallet']['balance'],amount);self.assertEqual(len(again['wallet']['paidLevels']),MAN['players'][p]['count'])
 def test_withdraw_and_add_old_level_cannot_farm(self):
  root,levels=setup();p='nzrv';g=update_player({},root,levels,p,MAN,NOW);ident=MAN['players'][p]['levelIds'][0];d=next(d for d in levels if d['id']==ident)
  for key in d.get('_keys',[]):root['pasados'][key][p]=False
  g=update_player(g,root,merged(root['pasados'],CAT),p,MAN,NOW+100)
  complete(root,p,d);again=update_player(g,root,merged(root['pasados'],CAT),p,MAN,NOW+2000)
  self.assertNotIn('level_'+ident,again['wallet']['ledger'])
 def test_new_level_awards_once_and_uses_trusted_tier(self):
  root,levels=setup();p='nzrv';g=update_player({},root,levels,p,MAN,NOW);d=next(d for d in levels if not d.get(p) and d['difficulty']=='Easy');complete(root,p,d);root['pasados'][d['id']]['tier']=999
  g=update_player(g,root,merged(root['pasados'],CAT),p,MAN,NOW+2000);entry=g['wallet']['ledger']['level_'+d['id']];self.assertEqual(entry['amount'],20+math.floor(next(x for x in CAT if x['id']==d['id'])['tier']*2))
  again=update_player(g,root,merged(root['pasados'],CAT),p,MAN,NOW+3000);self.assertEqual(again['wallet']['balance'],g['wallet']['balance'])
 def test_daily_half_and_weekly_sixty_percent(self):
  root,levels=setup();t=period(NOW)
  for p,c in root['desafios']['diarios'][t['day']].items():self.assertLessEqual(c['tier'],hardest(levels,p)*.6);self.assertAlmostEqual(c['targetTier'],rounded(hardest(levels,p)*.5));self.assertFalse(next(d for d in levels if d['id']==c['id']).get(p))
  weekly=root['desafios']['semanales'][t['week']];mean=sum(hardest(levels,p) for p in PLAYERS)/3;self.assertEqual(weekly['targetTier'],rounded(mean*.6));self.assertLessEqual(weekly['tier'],mean*.6*1.15)
 def test_assignments_remain_frozen(self):
  root,levels=setup();self.assertEqual(assignments(root,[*levels,{'id':'999999999','name':'New','creator':'X','difficulty':'Extreme','tier':99,'nzrv':True}],NOW+1000),{})
 def test_stats_baseline_and_no_post_deadline_credit(self):
  root,levels=setup();q={'id':'q','kind':'stat','stat':'stars','title':'Ganar estrellas','target':20,'baseline':1000,'baselineAt':NOW,'progress':0,'createdAt':NOW,'completed':False,'reward':25};end=NOW+10000
  root['verifiedProfiles']['nzrv']={'at':NOW+5000,'stats':{'stars':1012}}
  a=progress_quest(q,root,levels,'nzrv',NOW,end,NOW+5000);self.assertEqual(a['progress'],12);self.assertFalse(a['completed'])
  root['verifiedProfiles']['nzrv']={'at':end+1,'stats':{'stars':1050}};b=progress_quest(a,root,levels,'nzrv',NOW,end,end+1);self.assertEqual(b['progress'],12);self.assertFalse(b['completed']);self.assertTrue(b['expired'])
 def test_stale_profile_does_not_start_baseline(self):
  root,levels=setup();root['verifiedProfiles']['nzrv']['at']=NOW-3600000;q=make_quest(root,levels,'nzrv','day',2,NOW);self.assertTrue(q['waitingBaseline']);self.assertNotIn('baseline',q)
  root['verifiedProfiles']['nzrv']['at']=NOW+1000;a=progress_quest(q,root,levels,'nzrv',NOW,NOW+5000,NOW+1000);self.assertEqual(a['progress'],0);self.assertFalse(a['waitingBaseline'])
 def test_percentage_separate_from_goal_and_requires_period(self):
  root,levels=setup();d=next(x for x in levels if not x.get('nzrv'));q={'id':'q','kind':'percent','level':d,'target':50,'createdAt':NOW,'progress':0,'completed':False};root['runs']={'nzrv':{d['id']:{'best':70,'updatedAt':NOW-1}}};self.assertFalse(progress_quest(q,root,levels,'nzrv',NOW,NOW+5000,NOW+100)['completed'])
  root['runs']['nzrv'][d['id']]['updatedAt']=NOW+100;self.assertTrue(progress_quest(q,root,levels,'nzrv',NOW,NOW+5000,NOW+100)['completed']);self.assertNotIn('objetivos',root)
 def test_cooperative_requires_all_three_for_bonus(self):
  root,levels=setup();t=period(NOW);c=root['cooperativas'][t['day']];g={p:update_player({},root,levels,p,MAN,NOW) for p in PLAYERS}
  for p in PLAYERS[:2]:complete(root,p,c)
  levels=merged(root['pasados'],CAT)
  for p in PLAYERS:g[p]=update_player(g[p],root,levels,p,MAN,NOW+2000);self.assertNotIn('team_'+t['day'],g[p]['wallet']['ledger'])
  complete(root,PLAYERS[2],c,NOW+2500);levels=merged(root['pasados'],CAT)
  for p in PLAYERS:
   g[p]=update_player(g[p],root,levels,p,MAN,NOW+3000);self.assertIn('team_'+t['day'],g[p]['wallet']['ledger']);balance=g[p]['wallet']['balance'];g[p]=update_player(g[p],root,levels,p,MAN,NOW+4000);self.assertEqual(balance,g[p]['wallet']['balance'])
 def test_buying_same_item_from_two_requests_deducts_once(self):
  root,levels=setup();g=update_player({},root,levels,'nzrv',MAN,NOW);before=g['wallet']['balance'];root['requests']={'nzrv':{'one':{'kind':'purchase','item':'color_gold','at':NOW},'two':{'kind':'purchase','item':'color_gold','at':NOW+1}}};g=update_player(g,root,levels,'nzrv',MAN,NOW+100);self.assertEqual(g['wallet']['balance'],before-350);self.assertEqual(len([k for k in g['wallet']['ledger'] if k=='buy_color_gold']),1)
  g=update_player(g,root,levels,'nzrv',MAN,NOW+200);self.assertEqual(g['wallet']['balance'],before-350)
 def test_insufficient_funds_and_unowned_equip(self):
  root,levels=setup();g=update_player({},root,levels,'michaeelp',MAN,NOW);before=g['wallet']['balance'];root['requests']={'michaeelp':{'one':{'kind':'purchase','item':'title_veterano','at':NOW},'two':{'kind':'equip','item':'title_veterano','at':NOW+1}}};g=update_player(g,root,levels,'michaeelp',MAN,NOW+100);self.assertEqual(g['wallet']['balance'],before);self.assertFalse(g['processed']['one']['ok']);self.assertFalse(g['processed']['two']['ok'])
 def test_bingo_scales_and_remains_possible_for_weakest(self):
  root,levels=setup();late=int(datetime.fromisoformat('2026-10-31T20:00:00+00:00').timestamp()*1000)
  for p in PLAYERS:
   b=make_bingo(root,levels,p,late);self.assertEqual(len(b['cells']),16)
   for q in b['cells']:
    self.assertGreater(q['target'],0)
    if q['kind']=='awards':self.assertLessEqual(q['target'],1)
   if p=='michaeelp':self.assertFalse(any(q.get('awardType')=='weekly' for q in b['cells']))
 def test_bingo_rerolls_preserve_other_cells_and_limit(self):
  root,levels=setup();g=update_player({},root,levels,'nzrv',MAN,NOW);before=deepcopy(g['bingo']['cells']);root['requests']={'nzrv':{str(i):{'kind':'rerollBingo','index':i,'period':'2026-10','at':NOW+i} for i in range(3)}};g=update_player(g,root,levels,'nzrv',MAN,NOW+1000);self.assertEqual(g['bingo']['replacementsUsed'],2);self.assertEqual(g['bingo']['cells'][2],before[2]);self.assertFalse(g['processed']['2']['ok'])
 def test_midnight_monday_and_month_rollover(self):
  self.assertEqual(period(int(datetime.fromisoformat('2026-10-16T02:59:59+00:00').timestamp()*1000))['day'],'2026-10-15')
  self.assertEqual(period(int(datetime.fromisoformat('2026-10-16T03:00:00+00:00').timestamp()*1000))['day'],'2026-10-16')
  self.assertEqual(period(int(datetime.fromisoformat('2026-10-19T03:00:00+00:00').timestamp()*1000))['week'],'2026-10-19')
  self.assertEqual(period(int(datetime.fromisoformat('2026-11-01T02:59:59+00:00').timestamp()*1000))['month'],'2026-10')
 def test_combined_mission_requires_both_parts(self):
  root,levels=setup();q=None
  for seed in range(100):
   candidate=make_quest(root,levels,'nzrv','combo'+str(seed),1,NOW)
   if candidate['kind']=='combo':q=candidate;break
  self.assertIsNotNone(q);a,b=q['parts'];complete(root,'nzrv',a['level']);levels=merged(root['pasados'],CAT)
  partial=progress_quest(q,root,levels,'nzrv',NOW,NOW+10000,NOW+2000);self.assertEqual(partial['progress'],1);self.assertFalse(partial['completed'])
  root['verifiedProfiles']['nzrv']['at']=NOW+3000;root['verifiedProfiles']['nzrv']['stats'][b['stat']]=b['baseline']+b['target']
  done=progress_quest(partial,root,levels,'nzrv',NOW,NOW+10000,NOW+4000);self.assertTrue(done['completed']);self.assertEqual(done['progress'],2)
 def test_source_data_unchanged(self):
  root,levels=setup();before=json.dumps(root,sort_keys=True)
  for p in PLAYERS:update_player({},root,levels,p,MAN,NOW)
  self.assertEqual(json.dumps(root,sort_keys=True),before)
if __name__=='__main__':unittest.main(verbosity=2)
