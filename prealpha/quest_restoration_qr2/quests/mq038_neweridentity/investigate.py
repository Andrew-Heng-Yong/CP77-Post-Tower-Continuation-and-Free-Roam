"""Read-only, pinned-JSON MQ038 lifecycle trace. No runtime/build side effects."""
from pathlib import Path
import sys,json,gzip,hashlib,collections
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
from common import walk,value,sha,write,depots
OUT=Path(__file__).parent
INDEX=json.loads((ROOT/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json').read_text())
MI=json.loads((ROOT/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json').read_text())
def load(d):
 r=INDEX[d]; p=Path(r['json']);m=Resource(json.loads(p.read_text(encoding='utf-8-sig'))).normalize()
 return m
def node_summary(n):
 p=n['payload'];ws=list(walk(p))
 return {'id':n['id'],'type':n['type'],'refs':n['refs'],'sockets':n['sockets'],
 'facts_read':[x for x in ws if x.get('$type') in ['questVarComparison_ConditionType','questVarVsVarComparison_ConditionType']],
 'facts_write':[x for x in ws if x.get('$type')=='questSetVar_NodeType'],
 'journal':[x for x in ws if x.get('$type') in ['questJournalEntryState_ConditionType','questJournalChangeEntryState_NodeType','questJournalEntryState','questTrackQuest_NodeType','questSendMessage_NodeType','questAddRemoveContact_NodeType']],
 'paths':n['journal_paths'],'reward':[x for x in ws if any(s in x.get('$type','') for s in ['Reward','Loot','Inventory','Achievement'])],
 'noderefs':n['node_refs']}
def run():
 ds=[d for d in INDEX if '\\mq038\\' in d or '\\dennis\\' in d or d in ['towercontinued\\sidejobs_s23\\base_b\\mq038.questphase','towercontinued\\judy_dennis_jd1\\dennis_phone.questphase']]
 rows={}
 for d in ds:
  r=INDEX[d];m=load(d)
  rows[d]={'resource_sha256':r['sha256'],'source_json':r['json'],'json_sha256':sha(r['json']),'archive':r['archive'],'type':m['type'],'root_prefabs':m['root_prefabs'],'refs':m['refs'],'errors':m['errors'], 'graphs':{gp:{'entries':g['entries'],'edges':g['edges'],'unreachable':g['unreachable'],'nodes':{i:node_summary(n) for i,n in g['nodes'].items()}} for gp,g in m['graphs'].items()}}
 write(OUT/'trace.json',rows)
 # Search all parent resource roots, not only per-quest name matches.
 parents=[]
 for d,r in INDEX.items():
  if d not in MI:continue
  if not any('mq038\\mq038.questphase' in x or 'dennis_holocall.questphase' in x or 'dennis_cleanup.questphase' in x for x in r.get('refs',[])):continue
  mm=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()))
  for gp,g in mm.get('graphs',{}).items():
   for i,n in g['nodes'].items():
    if any('mq038\\mq038.questphase' in x or 'dennis_holocall.questphase' in x or 'dennis_cleanup.questphase' in x for x in n['refs']):
     parents.append({'resource':d,'sha256':r['sha256'],'graph':gp,'node':i,'payload':n['payload'],'edges':[e for e in g['edges'] if e[0]==i or e[2]==i],'root_prefabs':mm['root_prefabs']})
 write(OUT/'parents.json',parents)
 print(json.dumps({'resources':len(rows),'nodes':sum(len(g['nodes']) for r in rows.values() for g in r['graphs'].values()),'parents':len(parents)}))
if __name__=='__main__':run()
