"""Pure G19 exact epoch05/native source loader; no builders or peer verifiers imported."""
from pathlib import Path
import sys,json,gzip,copy,zlib
H=Path(__file__).resolve().parent;W=H.parents[3];F=H.parents[1]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource
SEL=read(H/'selection.json');Q=SEL['ids'];ROWS=SEL['quests'];E=read(F/'source_epoch_05.json');C=Path(E['candidate']);A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
def canon(x):
 x=json.loads(json.dumps(x))
 for q in walk(x):
  q.pop('payload_sha256',None);q.pop('metadata_sha256',None)
  if q.get('$type')=='TweakDBID':
   s=q['$value'];v=(len(s.encode())<<32)|zlib.crc32(s.encode())if q['$storage']=='string'else int(s);q['$storage']='uint64';q['$value']=str(v)
 return x
def load(d):
 if d.startswith('recipe:'):
  u=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');raw=W/d[7:];j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');jp=j.relative_to(W).as_posix();expected={k.replace('\\','/'):v for k,v in u['source_pins'].items()}.get(jp);assert expected and sha(j)==expected,jp;m=Resource(read(j)).normalize();return m,dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j),historical_raw_sha256=None,provenance='Pinned U9 original JSON; raw hash measured where no original raw pin',errors=m['errors'])
 if d==r'towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase':
  raw=C/'archive_source'/d.replace('\\','/');man=read(F/'reviews/worker_a/STEVEN_serialized/readback_01/manifest.json');p=next(x for x in man if x['name']=='after');assert sha(raw)==p['sha256']==E['source_resources'][d] and sha(p['json'])==p['json_sha256'];m=Resource(read(p['json'])).normalize();return m,dict(depot=d,binary=str(raw),sha256=sha(raw),json=p['json'],json_sha256=p['json_sha256'],provenance='Actual changed candidate02 serialized after, exact epoch05 resource, approved_changes03 plus Aindependent140/5. NOT old cached wholebody equality.',errors=m['errors'])
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/d.replace('\\','/')if d in E['source_resources']else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==E['source_resources'].get(d,r['sha256']),d
 m=Resource(read(j)).normalize();p={'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'provider':r['archive'],'errors':m['errors'],'source_epoch':'CanonicalQR5epoch05 candidate02; exact resourcehash'}
 if d in MI:
  c=MI[d];assert sha(c['normalized_model'])==c['normalized_sha256'];cache=json.loads(gzip.decompress(Path(c['normalized_model']).read_bytes()));cache.setdefault('embedded_files',[]);assert canon(m)==canon(cache),d;p.update(model=c['normalized_model'],model_sha256=sha(c['normalized_model']))
 return m,p
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);o=Path(ap.parse_args().output).resolve();assert not o.exists();M={};pins=[];missing=[]
 for d in SEL['depots']:
  if not d.startswith('recipe:')and d not in MI:missing.append({'depot':d,'status':'NOT_IN_DECODED_GRAPH_INVENTORY','inventory':IDX.get(d)});continue
  M[d],p=load(d);pins.append(p)
 write(o/'models.json',M);write(o/'source_pins.json',pins);write(o/'missing.json',missing);print({'resources':len(M),'missing':len(missing),'nodes':sum(len(g['nodes'])for m in M.values()for g in m['graphs'].values())})
