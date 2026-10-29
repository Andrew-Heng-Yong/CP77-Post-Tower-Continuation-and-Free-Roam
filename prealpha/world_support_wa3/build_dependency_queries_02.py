"""Exact native winners used by every support owner and reviewed dialogue payload."""
from pathlib import Path
import json,re,hashlib
H=Path(__file__).resolve().parent;W=H.parents[1]
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
groups=R(H/'manifest_02.json')['groups'];queries={};paths={}
def archive_name(path):
 return next(p for p in Path(path).parts if p.endswith('.archive'))
def add(depot,digest,kind,archive=None):
 q={'depot':depot,'sha256':digest,'kind':kind}
 if archive:q['expected_archive']=archive
 if depot in queries:assert queries[depot]['sha256']==digest;return
 queries[depot]=q
for p in (W/'diagnostics/world_npc_idle_20261026_01/combat_owners').glob('*.questphase.json'):
 for raw in re.findall(r'"\$value":\s*"([^"\r\n]+\.questphase)"',p.read_text(encoding='utf-8-sig')):
  dep=json.loads('"'+raw+'"');paths[dep.replace('\\','_')]=dep
for r in R(H/'native_review/outside_phases_native_01/report_01.json')['hits']:
 paths[Path(r['copy']).name]=r['depot']
for g in groups:
 add(g['support_sector_resource'],g['support_sector_sha256'],'native_support_sector',archive_name(g['support_sector_raw']))
 p=Path(g['native_binary']);dep=g.get('native_resource') or paths.get(p.name)
 if not dep:
  parts=p.parts;idx=next(i for i,v in enumerate(parts)if v.endswith('.archive'))
  if len(parts)-idx>2:dep='\\'.join(parts[idx+1:])
 assert dep,f'Unmapped parent depot {p}'
 add(dep,g['native_binary_sha256'],'native_support_parent_phase')
for report in ['native_review/conversation_native_01/report_01.json','native_review/conversation_scenes_native_01/report_01.json','native_review/outside_conversation_native_01/report_01.json','native_review/outside_conversation_scenes_native_01/report_01.json','native_review/combat_conversations_native_01/report_01.json']:
 for r in R(H/report)['hits']:add(r['depot'],r['sha256'],'native_ambient_dialogue')
for report in ['native_review/ep1_ambient_scenes_native_01/report_01.json','native_review/corpse_native_01/report_01.json','native_review/corpse_appearances_native_01/report_01.json']:
 for r in R(H/report)['hits']:add(r['depot'],r['sha256'],'native_reviewed_payload_dependency',archive_name(r['archive']))
# Optional player dance, selected corpse templates/appearances, exact current registry and world descriptors.
p=R(H/'native_review/party_assessment_01.json')['scene'];add('base\\open_world\\scenes\\dancefloors\\dancefloor_cs_goons_rave_party.scene',p['binary_sha256'],'native_optional_player_dance')
add('base\\worlds\\03_night_city\\_compiled\\default\\always_loaded_1.streamingsector',sha(H/'additional_extracted_04/ep1_1_nightcity.archive/always_loaded_1.streamingsector'),'native_community_registry','ep1_1_nightcity.archive')
add('base\\worlds\\03_night_city\\_compiled\\default\\blocks\\all.streamingblock',sha(H/'environment_variants/extract_02/ep1_1_nightcity_539214763179621144.streamingblock'),'native_world_descriptor','ep1_1_nightcity.archive')
ep1block=H/'native_review/ep1_block_native_01/ep1_1_nightcity.archive/base/worlds/03_night_city/_compiled/default/ep1/blocks/all.streamingblock'
add('base\\worlds\\03_night_city\\_compiled\\default\\ep1\\blocks\\all.streamingblock',sha(ep1block),'native_ep1_world_descriptor','ep1_1_nightcity.archive')
out=H/'dependencyqueries_02.json';out.write_text(json.dumps(list(queries.values()),indent=2)+'\n',newline='\n')
print(json.dumps({'queries':len(queries),'support_payloads':sum(q['kind']=='native_support_sector'for q in queries.values()),'parents':sum(q['kind']=='native_support_parent_phase'for q in queries.values())}))
