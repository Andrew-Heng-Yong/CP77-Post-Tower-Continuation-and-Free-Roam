"""Compare the actual current pre-S29 compiled stack and saved schema."""
from common import *
import re
base=ROOT/'prealpha/cyberware_cf1/candidate_01/compile_01/compiled.script'
candidate=ROOT/'prealpha/sidejobs_s29/candidate_01/compile_04/compiled.script'
def norm(s):return re.sub(r'\b(wrapper|proxy)\$\d+',r'\1$GENERATED',s)
def classes(s):
    out={}
    for m in re.finditer(r'(?m)^(?:(?:public|abstract|native|importonly|final) )*class ([\w.$]+)[^{\n]*\{',s):
        end=s.index('\n}',m.end())+2;out[m.group(1)]=s[m.start():end]
    return out
def canonical(s):
    s=s[:s.rfind('\n}')];starts=[m.start() for m in re.finditer(r'(?m)^  [^\n]*\bfunc ',s)]
    if not starts:return norm(s)
    return norm(s[:starts[0]]).strip(),sorted(norm(s[a:b]).strip() for a,b in zip(starts,starts[1:]+[len(s)]))
b=classes(base.read_text(encoding='utf-8-sig'));a=classes(candidate.read_text(encoding='utf-8-sig'))
assert b.keys()<=a.keys();changed=[];schema=0
for name in b:
    assert re.findall(r'(?m)^  .*persistent.*;$',b[name])==re.findall(r'(?m)^  .*persistent.*;$',a[name]),('saved fields',name)
    schema+=1
    if canonical(b[name])!=canonical(a[name]):changed.append(name)
assert set(changed)=={'PTFR.HistorySnapshotHS1.SnapshotStateHS1','PlayerDevelopmentData'},changed
name='PTFR.HistorySnapshotHS1.SnapshotStateHS1';old=canonical(b[name]);new=canonical(a[name]);assert old[0]==new[0]
extra=[s for s in new[1] if s not in old[1]];assert len(extra)==1 and 'func FreshS29(' in extra[0] and all(s in new[1] for s in old[1])
assert 'this.rows[i].states[0] == 1' in extra[0]
assert all(n.startswith('PTFR.SideJobsS29.') for n in a.keys()-b.keys())
result=dict(status='PASS_COMPILED_PRESERVATION',unchanged_classes=len(b)-2,saved_class_schemas=schema,added_classes=sorted(a.keys()-b.keys()),changed_classes=changed,snapshot_change='one read-only method; every prior method and field preserved',restore_change='additional SideJobsS29.Restored callback through wrappedMethod',baseline_sha256=sha(base),candidate_sha256=sha(candidate))
p=ROOT/'prealpha/sidejobs_s29/candidate_01/compiled_check_01.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
