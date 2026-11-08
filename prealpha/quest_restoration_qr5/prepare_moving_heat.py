"""Fresh successor, gated by the independently reviewed exact source proposal."""
from pathlib import Path
import sys,argparse,shutil,json
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--review',required=True);a=ap.parse_args()
rp=Path(a.review).resolve();r=read(rp);assert r['status'].startswith(('APPROVE','PASS')),r['status']
pp=O/'groups/G18/moving_heat_prefab_03/proposal.json';assert sha(pp)=='96611DFB60C246C52DDAFA18144CCE142373EA9403657ABA8A285340C5738036';p=read(pp)
assert sha(pp)in json.dumps(r),'Independent review must pin this exact source proposal'
e=read(O/'source_epoch_05.json');src=Path(e['candidate']);C=O/'candidate_03';assert not C.exists()
assert C.resolve().parent==O.resolve()and O.resolve().is_relative_to(W.resolve())
assert sha(src/'archive_source'/p['resource'])==p['before_sha256']
for dep,h in e['source_resources'].items():assert sha(src/'archive_source'/dep)==h
for row in e['package_files']:assert sha(src/'package'/row['path'])==row['sha256']
pins=read(O/'groups/G18/moving_heat_prefab_03/source_pins.json');native=next(x for x in pins if x['depot']==p['native_donor']);assert sha(native['raw'])==p['native_donor_sha256']
for sub in ['archive_source','package']:
 for f in (src/sub).rglob('*'):assert not f.stat().st_file_attributes&0x400
 shutil.copytree(src/sub,C/sub)
write(C/'moving_heat_plan.json',{'proposal':str(pp),'proposal_sha256':sha(pp),'review':str(rp),'review_sha256':sha(rp),'native':native,'predecessor_epoch':str(O/'source_epoch_05.json'),'predecessor_epoch_sha256':sha(O/'source_epoch_05.json'),'resource':p['resource'],'before':p['before_sha256'],'scope':'Unpackaged future accepted-stage support lease only; all candidate02 bytes copied and verified. No canonical change until serialized validation.'})
print({'fresh_candidate':str(C),'runtime_changes_in_this_step':0})
