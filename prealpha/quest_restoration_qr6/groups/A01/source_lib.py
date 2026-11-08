"""QR6 worker A pure pinned-resource inspection helpers; no runtime writes."""
from pathlib import Path
import sys,json,gzip,copy,zlib
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,compare_graph
Q5=W/'prealpha/quest_restoration_qr5'
E=read(Q5/'source_epoch_08.json');C=Path(E['candidate'])
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02'
IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
QUEUE={x['id']:x for x in read(Q5/'queue.json')['quests']}
PLANS=[read(p)for i in [29,30]if(p:=W/'research'/f'sidejobs_s{i}'/'plan_01.json').is_file()]
def canon(x,relocations=None):
 x=copy.deepcopy(x)
 def rec(v):
  if isinstance(v,dict):
   v.pop('payload_sha256',None);v.pop('metadata_sha256',None)
   if v.get('$type')=='TweakDBID':
    s=v['$value'];v['$storage']='uint64';v['$value']=str((len(s.encode())<<32)|zlib.crc32(s.encode()))if not str(s).isdigit()else str(s)
   return {k:rec(z)for k,z in v.items()}
  if isinstance(v,list):return[rec(z)for z in v]
  return (relocations or{}).get(v,v)if isinstance(v,str)else v
 return rec(x)
class Store:
 def __init__(self):self.models={};self.pins=[];self.raw={};self.missing=[]
 def load(self,d):
  if d in self.models:return self.models[d]
  if d in IDX:
   r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/d.replace('\\','/')if d in E['source_resources']else j.with_suffix('')
   if not raw.exists():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
   expect=E['source_resources'].get(d,r['sha256']);assert raw.is_file()and sha(raw)==expect,('rawpin',d,raw)
   obj=read(j);m=Resource(obj).normalize()
   if d in MI:
    c=MI[d];assert sha(c['normalized_model'])==c['normalized_sha256'];old=json.loads(gzip.decompress(Path(c['normalized_model']).read_bytes()));old.setdefault('embedded_files',[]);assert canon(old)==canon(m),('jsoncache',d)
   self.pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j),provider=r['archive'],errors=m['errors'],source_epoch='QR5:08'))
  else:
   choices=[]
   for p in PLANS:
    for name,h in p.get('source_pins',{}).items():
     if name.replace('\\','/').endswith('/raw/'+d.replace('\\','/')):choices.append((name,h,p))
   if not choices:self.missing.append(d);raise KeyError(d)
   name,h,p=choices[-1];raw=W/name;j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');assert sha(raw)==h and j.is_file(),d
   jrel=j.relative_to(W).as_posix();jpin={k.replace('\\','/'):v for k,v in p['source_pins'].items()}.get(jrel);assert jpin and sha(j)==jpin,d
   obj=read(j);m=Resource(obj).normalize();self.pins.append(dict(depot=d,binary=str(raw),sha256=h,json=str(j),json_sha256=jpin,provider='Pinned S29/S30 vanilla extraction',errors=m['errors']))
  self.raw[d]=obj;self.models[d]=m;return m
 def n(self,d,i,g='root'):return self.load(d)['graphs'][g]['nodes'][str(i)]
 def g(self,d,g='root'):return self.load(d)['graphs'][g]
 def edge(self,d,a,s,b,t,g='root'):return[str(a),s,str(b),t]in self.g(d,g)['edges']
def rows(m):
 return[dict(graph=gp,node=i,**n,incoming=[e for e in g['edges']if e[2]==i],outgoing=[e for e in g['edges']if e[0]==i])for gp,g in m['graphs'].items()for i,n in g['nodes'].items()]
