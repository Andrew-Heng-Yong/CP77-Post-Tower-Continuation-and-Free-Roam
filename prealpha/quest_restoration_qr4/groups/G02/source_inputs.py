from pathlib import Path
import sys,json,gzip,hashlib
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
C=W/'prealpha/quest_restoration_qr3/candidate_01'
P='towercontinued\\sidejobs_s25\\families\\sq025_fresh.questphase';N='base\\quest\\side_quests\\sq025\\sq025.questphase'
def selected():
 out=[]
 for d,r in IDX.items():
  if not r.get('graphs'):continue
  if ('\\sq025\\' in d and '\\versions\\' not in d) or d in [P] or d.startswith('towercontinued\\sidejobs_s22\\delamain\\') or 'sq025b_delamain_insurgence' in d or '\\holocalls\\delamain\\' in d or d in ['towercontinued\\gig_phone_u9\\fixer_cleanup.questphase','towercontinued\\phone_studios_ph3\\studio_support.questphase']:
   out.append(d)
 return sorted(out)
def load(d):
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/')) if d.startswith('towercontinued\\') else j.with_suffix('')
 if not raw.is_file() and not d.startswith('towercontinued\\'):
  raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file(),str(raw)
 assert sha(raw)==r['sha256'],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 assert m==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'source_json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']}
if __name__=='__main__':
 O=Path(__file__).resolve().parent/'inspection_01';assert not O.exists()
 ms={};pins=[]
 for d in selected():
  m,r=load(d);ms[d]=m;pins.append(r)
 write(O/'models.json',ms);write(O/'pins.json',pins)
 print(json.dumps({'models':len(ms),'graphs':sum(len(m['graphs']) for m in ms.values()),'nodes':sum(len(g['nodes']) for m in ms.values() for g in m['graphs'].values())}))
