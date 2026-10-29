"""Append WA3 identities to the existing admission driver; retain WA2 receipts."""
from pathlib import Path
import json,hashlib,re
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
m=R(H/'manifest_01.json');assert m['status']=='WA3_REVIEWED_NATIVE_SUPPORT_COHORT'
oldpath=W/'prealpha/world_actions_wa2/candidate_01/script_source/PTFR_RestorationBaseline.reds'
old=oldpath.read_text(encoding='utf-8-sig');out=C/'script_source/PTFR_RestorationBaseline.reds';assert not out.exists()
assert old.encode('utf-8')==oldpath.read_bytes(), 'Unexpected source encoding or newline conversion'
assert old.count('ArrayPush(this.groups, g);')==238
rows=[]
for g in m['groups']:
 rows.append(f'    g = new AmbientWorkspotGroupW2(); g.id = {g["id"]}; g.prefix = "{g["prefix"]}";')
 for h,ref in zip(g['spawner_hashes'],g['community_refs']):
  assert h.isdecimal() and '"'not in ref and '\\'not in ref
  rows.append(f'    ArrayPush(g.spawners, EntityID.FromHash({h}ul)); ArrayPush(g.communities, ToNodeRef("{ref}"));')
 rows.append('    ArrayPush(this.groups, g);')
append='\n'.join(rows)+'\n'
needle='  }\n  private func Safe(game: GameInstance, q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Bool {'
assert old.count(needle)==1
new=old.replace(needle,append+needle)
method='  private func NativeAdmissionWA3(q: ref<QuestsSystem>, index: Int32) -> Bool {\n'
for g in m['groups']:
 facts=g['native_admission_facts']
 if not facts:continue
 tests=[]
 for f in facts:
  assert f['comparison'] in ['Equal','Greater']
  tests.append(f'q.GetFact(n"{f["fact"]}") '+('==' if f['comparison']=='Equal' else '>')+f' {f["value"]}')
 method+=f'    if this.groups[index].id == {g["id"]} {{ return '+ ' && '.join(tests)+'; }\n'
method+='    return true;\n  }\n'
open_needle='  private func Open(q: ref<QuestsSystem>, index: Int32) -> Bool {'
assert new.count(open_needle)==1
new=new.replace(open_needle,method+open_needle)
return_old='    return q.GetFact(StringToName(p+"Ready")) == 1 &&'
return_new='    return this.NativeAdmissionWA3(q,index) && q.GetFact(StringToName(p+"Ready")) == 1 &&'
assert new.count(return_old)==1;new=new.replace(return_old,return_new)
# Reject only the exact new community entry lacking authored local support.
entry_code='';exclusions=[]
for g in m['groups']:
 for e in g.get('entry_exclusions',[]):
  ref_index=g['spawner_hashes'].index(e['spawner_hash'])
  assert re.fullmatch(r'[A-Za-z0-9_]+',e['entry'])
  entry_code+=f'    if group.id == {g["id"]} && s.refIndex == {ref_index} && Equals(s.entry,n"{e["entry"]}") {{ return false; }}\n'
  exclusions.append(dict(e,id=g['id'],ref_index=ref_index))
entry_needle='    let group = this.groups[s.groupIndex];\n'
assert new.count(entry_needle)==1;new=new.replace(entry_needle,entry_needle+entry_code)
assert new.replace(append,'',1).replace(method,'',1).replace(return_new,return_old,1).replace(entry_code,'',1)==old
assert new.count('ArrayPush(this.groups, g);')==238+len(m['groups'])
allhash=[h for g in m['groups'] for h in g['spawner_hashes']];assert len(allhash)==len(set(allhash))
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(new,encoding='utf-8',newline='\n')
proof={'status':'PASS_WA3_APPEND_AND_NEW_OWNER_GATES','source':str(oldpath),'source_sha256':sha(oldpath),'candidate':str(out),'candidate_sha256':sha(out),'old_group_count':238,'new_group_count':len(m['groups']),'total_group_count':238+len(m['groups']),'new_spawner_count':len(allhash),'old_runtime_reconstruction_byte_exact':True,'new_native_fact_gates':[{ 'id':g['id'],'facts':g['native_admission_facts']}for g in m['groups']if g['native_admission_facts']],'new_entry_exclusions':exclusions,'new_classes':0,'new_persistent_fields':0,'game_writes':0,'save_writes':0}
(out.parent/'build_01.json').write_text(json.dumps(proof,indent=2)+'\n',newline='\n');print(json.dumps(proof,indent=2))
