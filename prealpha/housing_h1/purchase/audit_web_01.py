"""Exact native website entry witnesses, including the UI templates and consumers."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()
def val(o):return o.get('$value') if isinstance(o,dict) else o
def walk(o,path=''):
 if isinstance(o,dict):
  yield path,o
  for k,v in o.items():yield from walk(v,path+'/'+k)
 elif isinstance(o,list):
  for i,v in enumerate(o):yield from walk(v,path+'/'+str(i))
def main():
 out=ROOT/'research/housing_h1/purchase/web_audit_01.json';assert not out.exists()
 journal='research/sidejobs_s28/journal_variants_05/ep1_2_gamedata/json/base/journal/cooked_journal.journal.json'
 raw=journal.replace('/json/','/raw/').removesuffix('.json')
 source='research/redscript_2_5/main_probe_01/smoke_readback_03.script'
 wi='research/housing_h1/purchase/web_official_01/inventory.json'
 cat='research/housing_h1/native/catalog_01.json'
 pins={p:sha(p) for p in [journal,raw,source,wi,cat,'prealpha/housing_h1/purchase/audit_web_01.py','prealpha/housing_h1/purchase/extract_web_01.ps1','research/framework_pr63_01/codeware/scripts/UI/Popups/GenericMessageNotification.reds']}
 pages=[];facts=set();checks=0
 for path,o in walk(read(journal)):
  if o.get('$type')=='gameJournalInternetPage' and o.get('address','').startswith('NETdir://ezestates.web/for_rent'):
   fs=[{'name':val(f['factName']),'value':f['factValue']} for f in o['factsToSet']]
   pages.append({'json_path':path,'id':o['id'],'address':o['address'],'activatedAtStart':o['activatedAtStart'],'facts':fs,'widget':val(o['widgetFile']['DepotPath'])})
   facts.update(f['name'] for f in fs)
 for suffix in ['wat_nid','wbr_jpn','hey_gle','cct_dtn']:
  for ending in ['purchase_setup','purchase_possibility']:assert f'dlc6_apart_{suffix}_{ending}' in facts;checks+=1
 assert not any('h10' in f for f in facts);checks+=1
 widgets=[];inventory=read(wi)
 for row in inventory['rows']:
  for p in [row['raw'],row['json']]:pins[p]=sha(p)
  types=sorted({o['$type'] for _,o in walk(read(row['json'])) if o.get('$type')=='WebPage' or 'Controller' in o.get('$type','')})
  assert types==['LinkController','WebPage'];checks+=1
  assert not any('Payment' in o.get('$type','') or 'quest' in o.get('$type','').lower() for _,o in walk(read(row['json'])));checks+=1
  widgets.append({'source':row,'controllers':types,'fact_or_currency_controller':False})
 consumers=[]
 for prop in read(cat)['properties']:
  if prop['id']=='h10':continue
  source_phase=prop['source'];data=read(source_phase['json']);resource=SafeResource(data)
  for p in [source_phase['raw'],source_phase['json']]:pins[p]=sha(p)
  graphs=flatten(resource,resource.obj['Data']['RootChunk'])
  for g in graphs:
   payment=[n for n in g['nodes'] if any(o.get('$type')=='PaymentBalanced_ScriptConditionType' for _,o in walk(n))]
   if not payment:continue
   facts_here=[{'node':n['id'],'type':o.get('$type'),'name':o['factName'],'value':o.get('value')} for n in g['nodes'] for _,o in walk(n) if 'factName' in o]
   assert any(x['name']==prop['native_purchase_fact'] for x in facts_here);checks+=1
   consumers.append({'id':prop['id'],'source':source_phase['json'],'graph':g['path'],'payment_node_ids':[n['id'] for n in payment],'facts':facts_here,'edges':g['edges']})
  assert any(x['id']==prop['id'] for x in consumers);checks+=1
 text=(ROOT/source).read_text();lines=text.splitlines()
 api=[]
 for needle in ['private final func LoadWebPage(const address:', 'protected cb func OnPageSpawned(widget:', 'private final func SetFacts(page:','let factsToSet = page.GetFactsToSet();','this.SetFacts(this.m_currentRequestedPage);']:
  hits=[i+1 for i,l in enumerate(lines) if needle in l];assert hits;checks+=1;api.append({'needle':needle,'lines':hits})
 result={'status':'PASS_EXACT_WEBSITE_ENTRY_AUDIT','checks':checks,'journal_pages':pages,'widget_sources':widgets,'native_charge_consumers':consumers,'api_source':source,'api_witnesses':api,'source_pins':pins,'metadata_only_sources':[journal,raw],'current_official_sources':inventory['rows'],'finding':'BrowserController directly writes the current journal page facts, independently of quest-owner liveness. Original apartment pages can write purchase_setup and purchase_possibility. The exact native site graph consumes purchase and owns the native payment/purchased write. H1 must not feed this old entry even when native owner liveness is unknown.','remediation':'While H1 Enforcing, intercept only four exact apartment purchase URLs before page load with visit-property notice. At render-time filter sixteen exact ordinary-apartment purchase facts. Pre-Tower and unrelated websites/makeovers remain unchanged. H10 has no native website apartment-purchase page.','limits':['No assertion that a killed original DLC6 quest owner has restarted post-Tower.','The full native setup-to-purchase bridge is not required for the fix: the source-proven browser writes are blocked before they can reach any old consumer.','Journal JSON is used as metadata evidence only; its known unrelated map-icon decode omissions are not treated as native payload equivalence.'],'game_writes':0}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':checks,'pages':len(pages),'widgets':len(widgets),'consumers':len(consumers)}))
if __name__=='__main__':main()
