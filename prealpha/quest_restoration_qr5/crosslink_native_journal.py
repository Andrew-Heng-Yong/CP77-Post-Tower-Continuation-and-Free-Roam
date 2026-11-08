"""Cross-link existing native foreign writer into the affected quest contracts."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
out=O/'adjudications/G03_02_crosswriter.json';assert not out.exists()
ap=O/'groups/G14/corrections/CVI02_NID02_crosswrite_01/addendum.json';a=read(ap);assert a['status']=='CONDITIONAL_NATIVE_FOREIGN_JOURNAL_WRITER_NO_REPAIR'
assert sha(a['extends_contract'])==a['extends_contract_sha256']
q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json');x=next(x for x in q['quests']if x['id']=='sts_pac_cvi_02');updated={}
for stage in ['journal','shared_dependencies']:
 v=x['contracts'][stage];v['proven']+=['Native NID02 OW graphroot/4/138 node72 (player mounted on van_001/#nid_02_com).True→92.Inactive writes CVI02 get_to_the_van, then92.Out→62.In. Exact native embedded donor and current source payload match; the mount predicate itself has no journal-state guard. No assertion is made that every ancestor lacks other conditions.']
 v['remaining']+=['CONDITIONAL_FOREIGN_NATIVE_WRITER: Native JournalManager behavior for terminal CVI02 parent/child states, ordering with the NID02 mount route and actual save context is unresolved. This is unchanged native behavior, not a restoration-only defect; do not insert a speculative guard/reset.']
 v['evidence']+=[{'path':str(ap),'sha256':sha(ap)}];v['central_crosslink']={'path':str(out),'original_addendum_sha256':sha(ap)};updated[stage]=copy.deepcopy(v)
 for row in rows:
  if row['quest_id']==x['id']and row['stage']==stage:row.update(copy.deepcopy(v))
write(out,{'status':'AFFECTED_QUEST_CROSSLINK_OF_EXISTING_NATIVE_EVIDENCE','quest_id':x['id'],'updated_contracts':updated,'source_addendum':str(ap),'source_addendum_sha256':sha(ap),'independent_trigger':str(O/'reviews/worker_a/central_supersession/verification_01/review.json'),'native_or_runtime_changes':0,'status_changes':0,'scope':'NID02 own journal proof was retained globally; now its affected CVI02 journal/shared rows link the exact source and engine limitation too.'})
x.setdefault('central_addenda',[]).append({'path':str(out),'sha256':sha(out)})
write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
print({'affected_contract_crosslinks':2,'status_changes':0,'runtime_changes':0})
