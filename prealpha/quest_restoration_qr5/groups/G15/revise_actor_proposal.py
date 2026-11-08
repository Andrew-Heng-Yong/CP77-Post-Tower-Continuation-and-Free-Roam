"""Order fresh enrollment before native children; never block original gig flow."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
old=H/'actor_proposal_01/proposal.json';p=read(old);out=H/'actor_proposal_02';assert not out.exists()
p['supersedes']={'path':str(old),'sha256':sha(old),'reason':'Add-only sibling guard did not prove Started0 sampled before native prestate progression; use ordered fork with original main flow on both outcomes.'}
p['parent_removed_edges']=[[65003,'Out',10,'In1'],[65003,'Out',64001,'In1']]
p['parent_added_edges']=[[65003,'Out',1300,'In'],[1300,'True',1301,'In'],[1301,'Out',1302,'In1'],[1301,'Out',10,'In1'],[1301,'Out',64001,'In1'],[1300,'False',10,'In1'],[1300,'False',64001,'In1']]
p['ordering']='Every new65003 pulse evaluates immediate1300 before either original child10 or64001 starts. Both True and False deliver exactly one original pulse to each native child; only True claims/enrolls helper. No AddedFailed/Fault/unknown-journal condition can block or duplicate the original gig. No Started0 race, no relaxed old-save adoption.'
p['required_tests'] += ['Both guard outputs preserve exactly one pulse to old10 and64001; no old65003 direct edge remains, so native Started65004 cannot precede the initial fresh-state check through this route.','Raw removal of either refusal path or reintroduction of direct65003→10 must be detected; private helper refusal leaves native main/bugfix behavior intact.']
write(out/'proposal.json',p);print({'proposal':str(out/'proposal.json'),'sha256':sha(out/'proposal.json'),'parent_removed':len(p['parent_removed_edges']),'parent_added':len(p['parent_added_edges'])})
