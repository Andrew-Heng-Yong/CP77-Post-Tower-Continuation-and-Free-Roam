"""Read-only source witnesses for H1 purchase pricing, devices, and UI APIs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()
def walk(o,path=''):
 if isinstance(o,dict):
  yield path,o
  for k,v in o.items():yield from walk(v,path+'/'+k)
 elif isinstance(o,list):
  for i,v in enumerate(o):yield from walk(v,path+'/'+str(i))
def val(o):return o.get('$value') if isinstance(o,dict) else o
def main():
 out=ROOT/'research/housing_h1/purchase/evidence_01.json';assert not out.exists()
 invpath='research/housing_h1/native/official_01/inventory.json';inv=read(invpath)
 catpath='research/housing_h1/native/catalog_01.json';cat=read(catpath)
 pins={p:sha(p) for p in [invpath,catpath,'prealpha/housing_h1/purchase/evidence_01.py']}
 records=[];checks=0
 for p in cat['properties']:
  for kind,d in p['devices'].items():
   source=read(d['source'])['Data']['RootChunk']['nodeRefs'][d['index']]
   assert val(source)==d['path'];checks+=1
  if p['id']=='h10':continue
  phase=p['source'];scene=next(r for r in inv['rows'] if r['depot']==p['service_scene'])
  checks_here=[];money=[]
  for source in [phase,scene]:
   for f in [source['raw'],source['json']]:pins[f]=sha(f)
   assert pins[source['raw']]==source['raw_sha256'];assert pins[source['json']]==source['json_sha256'];checks+=2
   for path,o in walk(read(source['json'])):
    if o.get('$type')=='PaymentBalanced_ScriptConditionType':
     assert val(o['questAssignment'])==p['purchase_assignment'];assert o['difficulty']=='NONE';assert o['inverted']==0;checks+=3
     checks_here.append({'source':source['json'],'path':path,'assignment':val(o['questAssignment']),'difficulty':o['difficulty'],'payWhenSucceded':o['payWhenSucceded']})
    if o.get('nodeType')=='RemoveByItemID' and val(o.get('itemID'))=='Items.money':money.append({'source':source['json'],'path':path,'quantity':o['quantity']})
  assert len(checks_here)==2 and sorted(x['payWhenSucceded'] for x in checks_here)==[0,1];checks+=1
  assert len(money)==1 and money[0]['quantity']>0;checks+=1
  records.append({'id':p['id'],'native_payment_checks':checks_here,'native_door_fixed_payment':money[0]})
 current='research/redscript_2_5/main_probe_01/smoke_readback_03.script'
 text=(ROOT/current).read_text(encoding='utf-8');lines=text.splitlines();pins[current]=sha(current)
 needles=['func GetBluelinePaymentValue(', 'func ExecuteBluelineAction(playerObject: GameObject)', 'func GetNodeTransform(self: GameInstance', 'func TransformPoint(xform: Transform', 'class StashControllerPS ', 'class WardrobeControllerPS ', 'protected const final func ExecuteAction(action: DeviceAction, opt executor: wref<GameObject>) -> Bool']
 api=[]
 for needle in needles:
  found=[i+1 for i,line in enumerate(lines) if needle in line];assert found;checks+=1
  api.append({'needle':needle,'lines':found})
 for relative in ['Popups/InGamePopup.reds','Popups/CustomPopup.reds','Popups/InGamePopupHeader.reds','Popups/Manager/CustomPopupManager.reds','Buttons/CustomButton.reds','Buttons/PopupButton.reds']:
  f='research/framework_pr63_01/codeware/scripts/UI/'+relative;pins[f]=sha(f)
 pins.update(cat['source_pins'])
 result={'status':'PASS_SOURCE_WITNESSES','checks':checks,'ordinary_prices':records,'h10_price':{'value':25000,'authority':'User-approved Phase5 repurchase policy; not a vanilla rental price'},'api_source':current,'api_witnesses':api,'device_scope':{'stash':5,'wardrobe':5,'named_doors':3,'generic_door_egress_preserved':True},'source_pins':pins,'limitations':['Registry references identify authored devices; they do not establish current live entity presence.','Quoted runtime price comes from the native EconomicAssignment at difficulty NONE. Missing record/system/nonpositive quote defers.','Popup visual placement and normal player interaction require live play verification.'],'game_writes':0}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':checks,'pins':len(pins)}))
if __name__=='__main__':main()
