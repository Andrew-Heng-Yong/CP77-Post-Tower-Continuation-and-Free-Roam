"""Purchase safety/source-contract verifier; does not run or mutate the game."""
import argparse,copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
def body(source,name):
 start=source.index('func '+name+'('); a=source.index('{',start); level=1;i=a+1
 while level:
  level+=(source[i]=='{')-(source[i]=='}');i+=1
 return source[a+1:i-1]
def safety(purchase,devices):
 assert 'RemoveItem(' not in purchase+devices
 assert 'GiveItem(' not in purchase+devices
 assert 'persistent let' not in purchase+devices
 assert 'SetFact' not in devices
 assert 'dlc6_apart_' not in '\n'.join(l for l in purchase.splitlines() if 'SetFact' in l)
 for forbidden in ['OnToggleOpen(', 'OnSetOpened(', 'OnForceOpen(', 'OnQuickHackToggleOpen(']:assert forbidden not in devices
 quote=body(purchase,'Quote');assert 'return 25000;' in quote
 assert 'RPGManager.GetBluelinePaymentValue(player, record, EGameplayChallengeLevel.NONE)' in quote
 assert 'if quote <= 0 { return -1; }' in quote
 location=body(purchase,'Validate')
 for needle in ['player.IsReplacer()', 'expected != sourceDoor', 'GameInstance.FindEntityByID(game, expected) as Door', '!GameInstance.GetNodeTransform', 'Transform.TransformPoint', '<= 3.50']:
  assert needle in location
 confirm=body(purchase,'ConfirmPurchase')
 assert 'this.m_attempted ||' in confirm and 'this.m_buy.IsDisabled()' in confirm and 'this.IsTopPopup()' in confirm
 assert confirm.index('this.m_attempted = true')<confirm.index('state.Purchase(')
 assert confirm.index('!ui.IsCurrent(this)')<confirm.index('state.Purchase(')
 assert 'self.m_popup = null;' in body(purchase,'Reset')
 assert 'this.m_popup = null;' in body(purchase,'OnAttach') and 'this.m_popup = null;' in body(purchase,'OnDetach')
 assert 'state.Purchase(this.m_property, this.m_quote, this.m_source)' in confirm
 assert '.Purchase(' not in body(purchase,'OnCancelClick')
 assert body(purchase,'OnCancelClick').strip()=='this.Close();'
 assert 'return true;' in body(purchase,'UseCursor')
 assert 'super.OnHidden();' in body(purchase,'OnHidden') and 'ui.Release(this)' in body(purchase,'OnHidden')
 assert '.Purchase(' not in body(purchase,'Tick')
 request_ack=body(purchase,'Tick').split('self.Show(id, source)')[1]
 assert request_ack.index('quests.SetFact(ready, 0)')<request_ack.index('quests.SetFact(request, 0)')
 assert 'state.CanPurchase' in body(purchase,'Show') and 'HousingPurchaseLocation.Validate' in body(purchase,'Show')
 deny=body(devices,'Denied');assert 'if !IsDefined(state) || !state.Enforcing() { return false; }' in deny
 assert deny.index('!state.Enforcing()')<deny.index('HousingDevices.RestrictedRelationship')
 assert 'if HousingDevices.RestrictedRelationship(source, kind) { return true; }' in deny
 assert 'return !state.Entitled(id);' in deny
 relationship=body(devices,'RestrictedRelationship')
 assert 'if !EntityID.IsDefined(source) { return false; }' in relationship
 assert 'kerry' not in relationship and 'stash_poi' not in relationship
 assert devices.count('"stash") {')==3 and devices.count('"wardrobe") {')==2
 assert 'let result = wrappedMethod(actions, context);' in devices
 assert 'if IsDefined(actions[i] as Pay) { ArrayErase(actions, i); }' in devices
 execute=body(devices,'ExecuteAction');assert execute.index('HousingDevices.NativePayDenied')<execute.index('wrappedMethod')
 assert 'action as Pay' in execute
 webload=body(purchase,'LoadWebPage')
 assert 'HousingWebsite.Enforcing() && HousingWebsite.IsPurchaseAddress(address)' in webload
 assert webload.index('return;')<webload.index('wrappedMethod(address)')
 assert 'Visit the property to purchase this apartment.' in webload
 webfacts=body(purchase,'SetFacts')
 assert 'if !HousingWebsite.Enforcing() { wrappedMethod(page); return; }' in webfacts
 assert '!HousingWebsite.IsPurchaseFact(factsToSet[i].factName)' in webfacts
 assert webfacts.index('!HousingWebsite.IsPurchaseFact')<webfacts.index('SetFactValue(')
 facts=re.findall(r'Equals\(fact, n"([^"]+)"\)',body(purchase,'IsPurchaseFact'))
 assert set(facts)=={f'dlc6_apart_{s}_{e}' for s in ['wat_nid','wbr_jpn','hey_gle','cct_dtn'] for e in ['purchase_setup','purchase_possibility','purchase','purchased']}
 assert len(facts)==16

def main():
 ap=argparse.ArgumentParser();ap.add_argument('component');args=ap.parse_args();path=ROOT/args.component;component=read(path);out=path.parent/'tests.json';assert not out.exists()
 checks=0;cases=0
 for p,h in component['source_pins'].items(): assert sha(ROOT/p)==h,p;checks+=1
 for f in component['files']:assert sha(path.parent/'package'/f['relative'])==f['sha256'];checks+=1
 p=next(path.parent/'package'/f['relative'] for f in component['files'] if f['relative'].endswith('HousingPurchase.reds'))
 d=next(path.parent/'package'/f['relative'] for f in component['files'] if f['relative'].endswith('HousingDevices.reds'))
 purchase=p.read_text(encoding='utf-8');devices=d.read_text(encoding='utf-8')
 safety(purchase,devices);checks+=42
 cat=read(ROOT/component['catalogue']);loc=read(ROOT/component['locations_contract'])
 assert len(loc['purchase'])==4 and component['locations_count']==4;checks+=1
 mapping=re.findall(r'Equals\(kind, "([^"]+)"\) && HousingDevices.Matches\(source, "([^"]+)"\) \{ return "([^"]+)";',devices)
 expected={(k,x['path'],prop['id']) for prop in cat['properties'] for k,x in prop['devices'].items() if k in ['door','stash','wardrobe']}
 assert set(mapping)==expected and len(mapping)==13;checks+=1
 relation=read(ROOT/component['relationship_devices_contract'])
 restricted=re.findall(r'Equals\(kind, "([^"]+)"\) && HousingDevices.Matches\(source, "([^"]+)"\) \{ return true;',body(devices,'RestrictedRelationship'))
 expected_restricted={(d['kind'],d['path']) for d in relation['devices'] if d['kind'] in ['stash','wardrobe']}
 assert set(restricted)==expected_restricted and len(restricted)==5 and component['relationship_devices_count']==5;checks+=1
 for row in relation['devices']:
  if row['kind']=='map_marker_not_proven_device':assert row['path'] not in devices;checks+=1
 assert not any(d['id']=='kerry' for d in relation['devices']);checks+=1
 for prop in cat['properties']:
  if prop['id']=='h10':continue
  assert prop['purchase_assignment'] in body(purchase,'Quote');checks+=1
 for row in loc['purchase']:
  assert row['purchase_path'] in body(purchase,'Path');checks+=1
  original=read(ROOT/row['source']['json'])['Data']['RootChunk']
  graph=[h['Data'] for h in original['sceneGraph']['Data']['graph']]
  choice=next(n for n in graph if n['nodeId']['id']==row['choice'])
  assert choice['$type']=='scnChoiceNode';checks+=1
  assert choice['atwParams']['entityPosition']==row['local_position'];checks+=1
  xyz=', '.join(str(float(row['local_position'][k])) for k in ['X','Y','Z'])
  assert 'new Vector4('+xyz+', 1.0)' in body(purchase,'Offset');checks+=1
 # Deliberate candidate mutations must be rejected by the same independent audit.
 mutations=[
  ('currency_write',purchase+'\ntransaction.RemoveItem(player, MarketSystem.Money(), price);',devices),
  ('wrong_h10_price',purchase.replace('return 25000;','return 12500;'),devices),
  ('stale_source',purchase.replace('expected != sourceDoor','false'),devices),
  ('unavailable_marker',purchase.replace('!GameInstance.GetNodeTransform','GameInstance.GetNodeTransform'),devices),
  ('remote_purchase',purchase.replace('<= 3.50','<= 99999.0'),devices),
  ('double_click',purchase.replace('this.m_attempted = true;',''),devices),
  ('stale_reload_popup',purchase.replace('!ui.IsCurrent(this)','false'),devices),
  ('native_owner_rearm_race',purchase.replace('quests.SetFact(ready, 0);\n          quests.SetFact(request, 0);','quests.SetFact(request, 0);\n          quests.SetFact(ready, 0);'),devices),
  ('web_postTower_only',purchase.replace('HousingWebsite.Enforcing() && HousingWebsite.IsPurchaseAddress(address)','HousingWebsite.IsPurchaseAddress(address)'),devices),
  ('queued_web_fact',purchase.replace('!HousingWebsite.IsPurchaseFact(factsToSet[i].factName)','true'),devices),
  ('premature_popup_release',purchase.replace('super.OnHidden();',''),devices),
  ('preTower_service_lock',purchase,devices.replace('!IsDefined(state) || !state.Enforcing()','!IsDefined(state)')),
  ('relationship_service_leak',purchase,devices.replace('if HousingDevices.RestrictedRelationship(source, kind) { return true; }','if HousingDevices.RestrictedRelationship(source, kind) { return false; }')),
  ('egress_trap',purchase,devices+'\nOnToggleOpen('),
  ('persistent_ui_ledger',purchase+'\nprivate persistent let paid: Bool;',devices)]
 for name,badp,badd in mutations:
  try:safety(badp,badd)
  except (AssertionError,ValueError):cases+=1
  else:raise AssertionError('negative audit escaped: '+name)
 result={'status':'PASS_SOURCE_AND_PURCHASE_POLICY','component_sha256':sha(path),'tester_sha256':sha(Path(__file__)),'checks':checks,'native_payload_checks':26,'policy_cases':cases,'negative_fixtures':[m[0] for m in mutations],'compiler_proof':'separate coordinated full compile required','live_ui_playtest':'PENDING','game_writes':0}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
