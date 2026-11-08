"""Independently reconcile every native news phase reference to selected quests."""
from pathlib import Path
import sys,re,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
out=O/'shared/ronald_family_inventory_01.json';assert not out.exists()
pp=O/'groups/G20/ronald_verification_02/source_pins.json';pins=read(pp);p=next(x for x in pins if x['depot'].endswith('q302_ronald_tree.questphase'))
assert sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256']
m=Resource(read(p['json'])).normalize();q=read(O/'queue.json');selected={x['id']:x for x in q['quests']};progress=read(O/'progress.json');investigated=set(progress['completed_quests'])|set(read(W/'prealpha/quest_restoration_qr4/queue.json')['deep_reviewed_ids']);rows=[];numeric=[]
for gp,g in m['graphs'].items():
 if not any(gp==s or gp.startswith(s+'/')for s in ['root/11','root/12']):continue
 for i,n in g['nodes'].items():
  for dep in n['refs']:
   if dep.isdecimal():numeric.append({'graph':gp,'node':i,'reference':dep})
   match=re.search(r'q302_msg_ronald_([^\\/]+)\.questphase$',dep)
   if not match:continue
   ident=match.group(1);rows.append({'native_owner_graph':gp,'native_phase_node':i,'message_resource':dep,'quest_id_from_native_resource':ident,'selected':ident in selected,'batch':selected[ident]['batch']if ident in selected else None,'investigated_in_prior_or_current_scope':ident in investigated,'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i],'source_payload_sha256':n['payload_sha256']})
affected=sorted({r['quest_id_from_native_resource']for r in rows if r['selected']})
write(out,{'status':'SOURCE_PINNED_NATIVE_FAMILY_TO_CURRENT_SELECTION_RECONCILIATION','branches':rows,'affected_selected_quests':affected,'unselected_or_unreconciled_native_branches':[r for r in rows if not r['selected']],'unresolved_numeric_references':numeric,'native_root_prefabs':m['root_prefabs'],'source_pin':p,'source_pins_file_sha256':sha(pp),'selected_queue_sha256_at_inventory':sha(O/'queue.json'),'checker_sha256':sha(__file__),'limits':['This enumerates native explicit message-resource refs in11/12; dynamic/external engine providers remain outside its scope.','Per-branch predicates, native timers/receipts, lifecycle/marker ownership and live delivery require separate source/independent reviews.','An unselected/unreconciled branch is not permission to restore it or count another deeply reviewed quest.']})
print({'native_branches':len(rows),'affected_selected':affected,'unresolved_numeric_refs':len(numeric)})
