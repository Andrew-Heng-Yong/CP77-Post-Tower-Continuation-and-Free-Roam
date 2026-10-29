"""Append only verified community250 to the current W3 admission table."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1]
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
proof=read(H/'coverage_review/support_assessment_01.json')
assert proof['status']=='PASS_250_SUPPORT_IDENTITY_ENVIRONMENT__130_WITHHELD_UNRESOLVED_WORLD'
assert proof['checks_passed']==40
rel='r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds'
manifest=read(W/'prealpha/bottle_actions_ba1/candidate_01/install_manifest_01.json')
expected=next(r['after'] for r in manifest['package_files'] if r['path']==rel)
source=GAME/rel;assert sha(source)==expected
old=source.read_bytes();nl=b'\r\n' if b'\r\n' in old else b'\n'
needle=b'  }'+nl+b'  private func Safe(game: GameInstance, q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Bool {'
assert old.count(needle)==1 and b'PTFRWW2_250_' not in old
before=[int(x) for x in re.findall(rb'g\.id = (\d+); g\.prefix = "',old)]
assert len(before)==237 and len(set(before))==237
rows=[
 '    g = new AmbientWorkspotGroupW2(); g.id = 250; g.prefix = "PTFRWW2_250_";',
 '    ArrayPush(g.spawners, EntityID.FromHash(3323904054656225535ul)); ArrayPush(g.communities, ToNodeRef("'+proof['candidate250']['community_ref']+'"));',
 '    ArrayPush(this.groups, g);',
]
insert=nl.join(x.encode() for x in rows)+nl
new=old.replace(needle,insert+needle)
assert new.replace(insert,b'',1)==old
after=[int(x) for x in re.findall(rb'g\.id = (\d+); g\.prefix = "',new)]
assert after==before+[250]
out=H/'candidate_01/script_source';out.mkdir(parents=True,exist_ok=True)
dest=out/'PTFR_RestorationBaseline.reds';assert not dest.exists();dest.write_bytes(new)
result={'status':'PASS_MINIMAL_GROUP250_ADMISSION_APPEND','original_sha256':expected,'candidate_sha256':sha(dest),
 'source':str(source),'candidate':str(dest),'before_groups':237,'after_groups':238,'before_spawners':245,'after_spawners':246,
 'old_group_order_preserved':True,'old_runtime_bytes_unchanged_after_removing_exact_append':True,
 'changed_lines_added':3,'new_persistent_fields':0,'new_classes':0,'admission_algorithm_changed':False,
 'new_group':{'id':250,'prefix':'PTFRWW2_250_','spawner_hash':'3323904054656225535','community_ref':proof['candidate250']['community_ref']},
 'game_writes':0,'save_writes':0}
(out/'support_build_01.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
