"""Check the final generated admission driver against manifest and WA2 byte history."""
from pathlib import Path
from hashlib import sha256
import json,re
H=Path(__file__).resolve().parent;C=H/'candidate_01';W=H.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
mp=H/'manifest_01.json';m=read(mp)
oldpath=W/'prealpha/world_actions_wa2/candidate_01/script_source/PTFR_RestorationBaseline.reds'
newpath=C/'script_source/PTFR_RestorationBaseline.reds'
old=oldpath.read_bytes().decode('utf-8');new=newpath.read_bytes().decode('utf-8')
assert '\r' not in old and '\r' not in new
safe='  }\n  private func Safe(game: GameInstance, q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Bool {'
assert old.count(safe)==new.count(safe)==1
before=old[:old.index(safe)];assert new.startswith(before)
append=new[len(before):new.index(safe)]
group_pattern=re.compile(r'    g = new AmbientWorkspotGroupW2\(\); g.id = (\d+); g.prefix = "([A-Za-z0-9_]+)";\n((?:    ArrayPush\(g.spawners, EntityID.FromHash\(\d+ul\)\); ArrayPush\(g.communities, ToNodeRef\("[^"\n]+"\)\)\;\n)+)    ArrayPush\(this.groups, g\);\n')
groups=list(group_pattern.finditer(append));assert ''.join(x.group() for x in groups)==append
assert len(groups)==len(m['groups'])
manifest={g['id']:g for g in m['groups']};assert len(manifest)==len(groups)
seen=[];new_hashes=[]
for match in groups:
    gid=int(match[1]);g=manifest[gid];seen.append(gid);assert match[2]==g['prefix']==f'PTFRWA3_{gid}_'
    identities=re.findall(r'EntityID.FromHash\((\d+)ul\)\); ArrayPush\(g.communities, ToNodeRef\("([^"\n]+)"\)',match[3])
    assert identities==list(zip(g['spawner_hashes'],g['community_refs']))
    new_hashes.extend(x[0] for x in identities)
assert len(seen)==len(set(seen)) and len(new_hashes)==len(set(new_hashes))
old_ids=set(map(int,re.findall(r'g.id = (\d+); g.prefix = ',old)))
old_hashes=set(re.findall(r'ArrayPush\(g.spawners, EntityID.FromHash\((\d+)ul\)',old))
assert not old_ids.intersection(seen),'New owner reuses existing group ID'
assert not old_hashes.intersection(new_hashes),'New owner duplicates existing community identity'
helper_start='  private func NativeAdmissionWA3(q: ref<QuestsSystem>, index: Int32) -> Bool {\n'
helper_end='    return true;\n  }\n'
start=new.index(helper_start);end=new.index(helper_end,start)+len(helper_end);helper=new[start:end]
clauses={}
for line in helper[len(helper_start):-len(helper_end)].splitlines():
    match=re.fullmatch(r'    if this.groups\[index\].id == (\d+) \{ return (.+); \}',line);assert match,line
    gid=int(match[1]);assert gid not in clauses
    tests=[]
    for test in match[2].split(' && '):
        term=re.fullmatch(r'q.GetFact\(n"([A-Za-z0-9_]+)"\) (==|>) (\d+)',test);assert term,test
        tests.append({'fact':term[1],'comparison':'Equal' if term[2]=='==' else 'Greater','value':int(term[3])})
    clauses[gid]=tests
assert clauses=={g['id']:g['native_admission_facts'] for g in m['groups'] if g['native_admission_facts']}
entry_pattern=re.compile(r'    if group.id == (\d+) && s.refIndex == (\d+) && Equals\(s.entry,n"([A-Za-z0-9_]+)"\) \{ return false; \}\n')
entries=list(entry_pattern.finditer(new));actual={(int(x[1]),int(x[2]),x[3]) for x in entries}
expected={(g['id'],g['spawner_hashes'].index(e['spawner_hash']),e['entry']) for g in m['groups'] for e in g.get('entry_exclusions',[])}
assert len(entries)==len(actual) and actual==expected
changed_return='    return this.NativeAdmissionWA3(q,index) && q.GetFact(StringToName(p+"Ready")) == 1 &&'
original_return='    return q.GetFact(StringToName(p+"Ready")) == 1 &&'
assert new.count(changed_return)==1
rebuilt=new.replace(append,'',1).replace(helper,'',1).replace(changed_return,original_return,1)
for entry in entries:rebuilt=rebuilt.replace(entry.group(),'',1)
assert rebuilt.encode('utf-8')==oldpath.read_bytes(),'Unapproved old runtime change'
out=C/'independent_driver_01.json';assert not out.exists()
result={'status':'PASS_INDEPENDENT_DRIVER_APPEND_AND_GATES','new_groups':len(groups),'new_spawners':len(new_hashes),'old_runtime_bytes_exact':True,'native_gate_groups':len(clauses),'entry_exclusions':sorted(actual),'new_persistent_fields':0,'pins':[{'path':str(p.resolve()),'sha256':digest(p)} for p in [mp,oldpath,newpath,Path(__file__)]],'game_writes':0,'save_writes':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='pins'}))
