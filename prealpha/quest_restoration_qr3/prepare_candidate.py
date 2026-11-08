"""Stage an explicitly reviewed, single-resource successor; never install it."""
from pathlib import Path
import sys,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
B=read(W/'prealpha/quest_restoration_qr1/baseline.json');C=O/'candidate_01'
assert not C.exists(),'Fresh successor required'
review=O/'agents/agent_b/reviews/brendan_quarantine.json'
assert review.is_file(),'Independent review required before staging'
R=read(review)
assert str(R.get('status','')).startswith(('PASS','APPROVE_')),R.get('status')
source=Path(B['candidate'])
for sub in ['archive_source','package']:
 for p in (source/sub).rglob('*'):
  assert not (p.stat().st_file_attributes & 0x400),'Refuse reparse input'
 shutil.copytree(source/sub,C/sub)
write(O/'baseline.json',B)
write(C/'repair_plan.json',{'status':'REVIEWED_MINIMAL_PRECLAIM_QUARANTINE','depot':'towercontinued\\sidejobs_s23\\base_b\\mq037.questphase','before':'E42A7DE2591C367ACD1FCFAFD0D9BA728204034D57CEA0577848445C7C8DD94E','remove_edge':['1004','True','1005','In'],'add_edge':['1004','True','1008','In'],'preserve_nodes':['1005','1006','34'],'scope':'Refuse invalid unissued fresh owner that activates excluded Dumpster; retain already-issued descendants and selection catalogue. Valid earned-history sequel adapter remains unsupported.','independent_review':str(review),'review_sha256':sha(review),'source_investigation':str(O/'agents/agent_c/verification_01/defects.json'),'game_writes':0,'save_writes':0})
print('STAGED_REVIEWED_SUCCESSOR_NOT_INSTALLED')
