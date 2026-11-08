"""Pure local inspection helpers for G09; no build or game writes."""
from pathlib import Path
import json,gzip,hashlib,sys
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
class Store:
 def __init__(self):
  self.A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';self.I=read(self.A/'resource_inventory.json');self.MI=read(self.A/'model_inventory.json');self.models={};self.pins=[]
 def load(self,d):
  if d in self.models:return self.models[d]
  r=self.I[d];j=Path(r['json']);raw=j.with_suffix('')
  if d.startswith('towercontinued\\'):raw=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'/Path(d.replace('\\','/'))
  if not raw.is_file() and 'json' in j.parts:
   parts=list(j.parts);parts[parts.index('json')]='raw';raw=Path(*parts).with_suffix('')
  assert raw.is_file(),str(raw)
  assert sha(raw)==r['sha256'],('Changed source requires newer JSON, not old model',d)
  m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(self.MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
  assert m==cached,('SourceJSON/model disagreement',d)
  self.models[d]=m;self.pins.append({'depot':d,'binary':str(raw),'resource_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':self.MI[d]['normalized_model'],'model_sha256':sha(self.MI[d]['normalized_model']),'provider':r['archive'],'errors':m['errors'],'epoch':'QR3 successor v1; these resources unchanged from pinned PH3'})
  return m
 def g(self,d,gp='root'):return self.load(d)['graphs'][gp]
 def n(self,d,i,gp='root'):return self.g(d,gp)['nodes'][str(i)]
 def edge(self,d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in self.g(d,gp)['edges']
 def extra(self,raw_name,manifest):
  key='vanilla_recipe:'+raw_name
  if key in self.models:return key
  raw=W/raw_name;jname=raw_name.replace('/raw/','/json/')+'.json';j=W/jname
  assert raw.is_file() and j.is_file(),(raw,j)
  mp={k.replace('\\','/'):v for k,v in manifest['source_pins'].items()}
  assert jname in mp and sha(j)==mp[jname]
  raw_pin=mp.get(raw_name)
  if raw_pin:assert sha(raw)==raw_pin
  m=Resource(read(j)).normalize();assert not m['errors'],m['errors'];self.models[key]=m
  self.pins.append({'depot':key,'binary':str(raw),'resource_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'provider':'Pinned U9 original vanilla extraction; source JSON exact manifest hash','raw_pin_in_original_manifest':bool(raw_pin),'binary_JSON_correspondence':'Existing extraction evidence; no new export performed','errors':m['errors']})
  return key
def evaluate(x,f,j):
 t=x['$type']
 if t=='questLogicalCondition':
  z=[evaluate(v,f,j) for v in x['conditions']]
  if any(v is None for v in z):return None
  return all(z) if x['operation']=='AND' else any(z) if x['operation']=='OR' else not any(z) if x['operation']=='NOR' else None
 if t in ['questFactsDBCondition','questJournalCondition']:return evaluate(x['type'],f,j)
 if t=='questObjectCondition':return evaluate(x['type'],f,j)
 if t=='questInventory_ConditionType':
  key='fixture_inventory:'+str(val(x['itemID']))
  if key not in f:return None
  a=f[key];b=x['quantity'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in f:return None
  a=f[x['factName']];b=x['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  p=x['path']['realPath'];return None if p not in j else (j[p]==x['state']) != bool(x.get('inverted',0))
 return None
