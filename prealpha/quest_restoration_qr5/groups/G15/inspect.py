"""Coordinator-owned Steven followup source closure; no runtime writes."""
from pathlib import Path
import sys,gzip,collections
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;O=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');E=read(O/'source_epoch_00.json');C=Path(E['candidate']);out=H/'inspection_01';assert not out.exists()
q=next(x for x in read(O/'queue.json')['quests']if x['id']=='sts_ep1_08_steven_meeting_night_city')
selected=set(q['vanilla_candidates']+q['restored_candidates'])
selected|={d for d in I if 'steven' in d and d.endswith(('.questphase','.scene'))}
selected|={d for d,r in I.items()if any(t in r.get('refs',[])for t in list(selected))}
models={};pins=[];missing=[]
for d in sorted(selected):
 if d not in I or d not in MI:missing.append({'depot':d,'reason':'Missing existing decoded input'});continue
 r=I[d];j=Path(r['json']);raw=C/'archive_source'/d if d in E['source_resources']else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 expected=E['source_resources'].get(d,r['sha256']);assert raw.is_file()and sha(raw)==expected,d
 m=Resource(read(j)).normalize();assert not m['errors'],(d,m['errors']);models[d]=m;pins.append({'depot':d,'binary':str(raw),'sha256':expected,'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'provider':r['archive'],'epoch':'QR5:00 frozen QR4 source'})
summary={}
for d,m in models.items():
 hits=[]
 for gp,g in m['graphs'].items():
  for ident,n in g['nodes'].items():
   if d in q['vanilla_candidates']+q['restored_candidates']or any('steven'in str(x).lower()for x in [n['refs'],n['reads'],n['writes'],n['journal_paths'],n['prefabs']]):
    hits.append({'graph':gp,'node':ident,'type':n['type'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'prefabs':n['prefabs'],'journal':n['journal_paths'],'in':[e for e in g['edges']if e[2]==ident],'out':[e for e in g['edges']if e[0]==ident]})
 summary[d]={'root_prefabs':m['root_prefabs'],'hits':hits}
write(out/'models.json',models);write(out/'pins.json',pins);write(out/'summary.json',summary);write(out/'missing.json',missing)
print({'resources':len(pins),'nodes':sum(len(g['nodes'])for m in models.values()for g in m['graphs'].values()),'missing':missing})
