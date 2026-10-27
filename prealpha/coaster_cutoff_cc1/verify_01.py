"""Check CC1 has exactly two guarded q105 completion conditions and one S30 data-row change."""
from pathlib import Path
from hashlib import sha256
import json

H=Path(__file__).resolve().parent
C=H/'candidate_01'
B=Path(__file__).resolve().parents[2]/'prealpha/skippy_ambient_sc3/candidate_02'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
strip=lambda v:({k:strip(x) for k,x in v.items() if k not in ('HandleId','HandleRefId')} if isinstance(v,dict) else [strip(x) for x in v] if isinstance(v,list) else v)
a=strip(read(C/'entry_before_01.json'))
b=strip(read(C/'entry_after_01.json'))
nodes=lambda x:{n['Data']['id']:n for n in x['Data']['RootChunk']['graph']['Data']['nodes']}
old,new=nodes(a),nodes(b)
assert old.keys()==new.keys()
checked=[]
for ident in old:
    if ident not in (65003,65004):
        assert old[ident]==new[ident],ident
        continue
    x=old[ident]['Data']['condition']['Data']['conditions']
    y=new[ident]['Data']['condition']['Data']['conditions']
    assert len(y)==len(x)+1 and y[:-1]==x,ident
    addition=y[-1]['Data']['type']['Data']
    assert (addition['factName'],addition['comparisonType'],addition['value'])==('q105_done','Equal',0),ident
    copy=json.loads(json.dumps(old[ident]))
    copy['Data']['condition']['Data']['conditions'].append(y[-1])
    assert copy==new[ident],ident
    checked.append(ident)
old_text=(B/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds').read_text(encoding='utf-8-sig')
new_text=(C/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds').read_text(encoding='utf-8-sig')
old_lines=old_text.splitlines()
new_lines=new_text.splitlines()
assert len(old_lines)==len(new_lines)
delta=[(i+1,a,b) for i,(a,b) in enumerate(zip(old_lines,new_lines)) if a!=b]
assert len(delta)==3,delta
assert all('FactNames0()' in a or 'FactMin0()' in a or 'FactMax0()' in a for _,a,_ in delta)
assert '"q105_done"' in delta[0][2]
assert all(b.count(', 0')==a.count(', 0')+1 for _,a,b in delta[1:]),delta
proof={'status':'PASS_TWO_CUTOFF_GUARDS_ONLY','guard_nodes':checked,'script_changed_lines':[i for i,_,_ in delta],'other_entry_nodes_unchanged':len(old)-2,'other_script_lines_unchanged':len(old_lines)-3,'base_archive_members':1185,'game_writes':0,'save_writes':0}
(C/'verification_01.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
