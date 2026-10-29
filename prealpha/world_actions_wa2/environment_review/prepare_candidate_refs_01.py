from pathlib import Path
from hashlib import sha256
import json
H=Path(__file__).resolve().parent; C=H.parent/'candidate_01'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
cohort=read(C/'cohort_proof_01.json'); groups=cohort['shooting_groups']+cohort['vehicle_groups']
refs=set();files=[]
def visit(x):
    if isinstance(x,dict):
        if x.get('$type')=='NodeRef':refs.add(x['$value'])
        for v in x.values():visit(v)
    elif isinstance(x,list):
        for v in x:visit(v)
for gid in groups:
    suffix='02' if gid in cohort['vehicle_groups'] else '01'
    p=C/f'owner_{gid}_readback_{suffix}.json';visit(read(p));files.append({'group':gid,'path':str(p),'sha256':digest(p)})
p=H/'candidate_refs_input_01.json';assert not p.exists()
p.write_text(json.dumps({'groups':files,'refs':sorted(refs),'cohort_sha256':digest(C/'cohort_proof_01.json')},indent=2)+'\n')
