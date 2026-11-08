"""Discover exact Steven writers/listeners beyond the initial catalogue closure."""
from pathlib import Path
import sys,gzip,json
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;O=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');E=read(O/'source_epoch_00.json');C=Path(E['candidate']);out=H/'context_scan_01';assert not out.exists()
tokens=['steven_santos_default_on','steven_default.questphase','sts_ep1_08_steven_meeting_night_city'];models={};pins=[];hits=[]
for d,row in MI.items():
 data=gzip.decompress(Path(row['normalized_model']).read_bytes())
 if not any(t.encode()in data for t in tokens):continue
 r=I[d];j=Path(r['json']);raw=C/'archive_source'/d if d in E['source_resources']else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 expected=E['source_resources'].get(d,r['sha256']);assert raw.is_file()and sha(raw)==expected,d
 m=Resource(read(j)).normalize();assert not m['errors'];models[d]=m;pins.append({'depot':d,'binary':str(raw),'sha256':expected,'json':str(j),'json_sha256':sha(j),'model':row['normalized_model'],'model_sha256':sha(row['normalized_model']),'provider':r['archive']})
 for gp,g in m['graphs'].items():
  for ident,n in g['nodes'].items():
   if any(t in str(n['payload'])for t in tokens):hits.append({'depot':d,'graph':gp,'node':ident,'type':n['type'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'journal':n['journal_paths'],'prefabs':n['prefabs'],'in':[e for e in g['edges']if e[2]==ident],'out':[e for e in g['edges']if e[0]==ident]})
script_hits=[]
for p in (C/'package').rglob('*'):
 if p.is_file()and p.suffix in ['.reds','.lua','.yaml','.xl']:
  text=p.read_text(encoding='utf-8-sig');ls=[{'line':i+1,'text':line}for i,line in enumerate(text.splitlines())if any(t in line for t in tokens)]
  if ls:script_hits.append({'path':str(p),'sha256':sha(p),'lines':ls})
write(out/'models.json',models);write(out/'pins.json',pins);write(out/'hits.json',hits);write(out/'script_hits.json',script_hits)
write(out/'summary.json',{'global_models_scanned':len(MI),'matching_resources':list(models),'matched_nodes':len(hits),'script_files':len(script_hits),'scope':'Frozen QR5epoch00; only later ARR12 entry differs and contains none of these tokens. No live scheduling or external mod execution proved.'})
print({'models_scanned':len(MI),'resources':len(models),'matched_nodes':len(hits),'script_files':len(script_hits)})
