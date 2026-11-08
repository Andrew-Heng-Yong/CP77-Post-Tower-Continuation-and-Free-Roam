"""Fresh read-only QR6 B-group input preparation. No runtime writes."""
from pathlib import Path
import sys,json,hashlib,gzip
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
I=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
MI=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json')
E=read(W/'prealpha/quest_restoration_qr5/source_epoch_08.json');C=Path(E['candidate'])
groups={'B01':['mq050_ken_block_tribute','mq042_nomad','mq059_freedom','mq060_nitro','mq058_semimaru_crystalcoat'],'B02':['mws_wat_08_trauma_drama','mws_se5_07','mq022_ezekiel','mq003_orbitals'],'B03':['sq023_real_passion','sq023_hit_order','sq023_bd_passion','sq025b_delamain_insurgence']}
Q=read(W/'prealpha/quest_restoration_qr5/queue.json')['quests']
if __name__=='__main__':
 for group,ids in groups.items():
  H=W/'prealpha/quest_restoration_qr6/groups'/group;H.mkdir(parents=True,exist_ok=True)
  if (H/'raw_inputs.json').exists():
   print(group,'prepared; preserving evidence');continue
  rows=[q for q in Q if q['id']in ids];assert len(rows)==len(ids)
  save(H/'selected_inputs.json',[{k:q[k]for k in ['id','title','batch','vanilla_candidates','restored_candidates','identity_evidence']}for q in rows])
  roots=set(d for q in rows for d in q['vanilla_candidates']+q['restored_candidates'] if d in I)
  todo=list(roots);allr=set(roots)
  while todo:
   d=todo.pop()
   for ref in I[d]['refs']:
    if ref in I and ref not in allr and ref.endswith(('.questphase','.scene','.workspot')):
     allr.add(ref);todo.append(ref)
  parents={d:[p for p,r in I.items()if d in r['refs']]for d in roots if not d.startswith('towercontinued')and d.endswith('.questphase')}
  # Exact immediate parent graph evidence and known global root retirement chain.
  for ps in parents.values():allr.update(p for p in ps if p.endswith('.questphase'))
  allr.update(d for d in I if d in [r'base\quest\root.quest',r'base\quest\main_quests\quest_secondary.questphase',r'base\quest\main_quests\quest_minor.questphase'])
  inp=[];missing=[]
  for d in sorted(allr):
   r=I[d]
   if 'json'not in r:missing.append({'depot':d,'reason':'inventory has no supported JSON','record':r});continue
   j=Path(r['json']);raw=j.with_suffix('')
   if d.startswith('towercontinued\\'):raw=C/'archive_source'/Path(d.replace('\\','/'));expected=E['source_resources'][d]
   else:expected=r['sha256']
   if not raw.is_file() and 'json'in raw.parts:
    parts=list(raw.parts);parts[parts.index('json')]='raw';raw=Path(*parts)
   if not raw.is_file():missing.append({'depot':d,'reason':'raw absent','expected':str(raw)});continue
   assert sha(raw)==expected,(d,sha(raw),expected)
   inp.append({'depot':d,'raw':str(raw),'hash':expected,'provider':r['archive'],'original_json':str(j),'original_json_sha256':sha(j)})
  save(H/'raw_inputs.json',inp);save(H/'native_parents.json',parents);save(H/'missing_inputs.json',missing)
  print(group,len(rows),'quests',len(inp),'resources',len(missing),'missing')
