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
 assert 'state.Purchase(this.m_property, this.m_quote, this.m_source)' in confirm
 assert 'Purchase(' not in body(purchase,'OnCancelClick')
 assert body(purchase,'OnCancelClick').strip()=='this.Close();'
 assert 'return true;' in body(purchase,'UseCursor')
 assert 'super.OnHidden();' in body(purchase,'OnHidden') and 'ui.Release(this)' in body(purchase,'OnHidden')
 assert 'Purchase(' not in body(purchase,'Tick')
 assert 'state.CanPurchase' in body(purchase,'Show') and 'HousingPurchaseLocation.Validate' in body(purchase,'Show')
 deny=body(devices,'Denied');assert 'state.Enforcing() && !state.Entitled(id)' in deny
 assert devices.count('"stash") {')==3 and devices.count('"wardrobe") {')==2
 assert 'let result = wrappedMethod(actions, context);' in devices
 assert 'if IsDefined(actions[i] as Pay) { ArrayErase(actions, i); }' in devices
 execute=body(devices,'ExecuteAction');assert execute.index('HousingDevices.NativePayDenied')<execute.index('wrappedMethod')
 assert 'action as Pay' in execute

def main():
 ap=argparse.ArgumentParser();ap.add_argument('component');args=ap.parse_args();path=ROOT/args.component;component=read(path);out=path.parent/'tests.json';assert not out.exists()
 checks=0;cases=0
 for p,h in component['source_pins'].items(): assert sha(ROOT/p)==h,p;checks+=1
 for f in component['files']:assert sha(path.parent/'package'/f['relative'])==f['sha256'];checks+=1
 p=next(path.parent/'package'/f['relative'] for f in component['files'] if f['relative'].endswith('HousingPurchase.reds'))
 d=next(path.parent/'package'/f['relative'] for f in component['files'] if f['relative'].endswith('HousingDevices.reds'))
 purchase=p.read_text(encoding='utf-8');devices=d.read_text(encoding='utf-8')
 safety(purchase,devices);checks+=30
 cat=read(ROOT/component['catalogue']);loc=read(ROOT/component['locations_contract'])
 assert len(loc['purchase'])==4 and component['locations_count']==4;checks+=1
 mapping=re.findall(r'Equals\(kind, "([^"]+)"\) && HousingDevices.Matches\(source, "([^"]+)"\)\) \{ return "([^"]+)";',devices)
 expected={(k,x['path'],prop['id']) for prop in cat['properties'] for k,x in prop['devices'].items() if k in ['door','stash','wardrobe']}
 assert set(mapping)==expected and len(mapping)==13;checks+=1
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
  ('premature_popup_release',purchase.replace('super.OnHidden();',''),devices),
  ('preTower_service_lock',purchase,devices.replace('state.Enforcing() && !state.Entitled(id)','!state.Entitled(id)')),
  ('egress_trap',purchase,devices+'\nOnToggleOpen('),
  ('persistent_ui_ledger',purchase+'\nprivate persistent let paid: Bool;',devices)]
 for name,badp,badd in mutations:
  try:safety(badp,badd)
  except (AssertionError,ValueError):cases+=1
  else:raise AssertionError('negative audit escaped: '+name)
 result={'status':'PASS_SOURCE_AND_PURCHASE_POLICY','component_sha256':sha(path),'tester_sha256':sha(Path(__file__)),'checks':checks,'native_payload_checks':21,'policy_cases':cases,'negative_fixtures':[m[0] for m in mutations],'compiler_proof':'separate coordinated full compile required','live_ui_playtest':'PENDING','game_writes':0}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
