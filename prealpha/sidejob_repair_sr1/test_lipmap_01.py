import json
from pathlib import Path

here = Path(__file__).resolve().parent
candidate = here / 'candidate_02'
plan = json.loads((here / 'lipmap_plan_01.json').read_text(encoding='utf-8'))
resource = json.loads((candidate / 'lipmap_readback_01.json').read_text(encoding='utf-8'))['Data']['RootChunk']
assert resource['$type'] == 'animLipsyncMapping'
assert resource['languageCodeName']['$value'] == 'en-us'
assert len(plan['rows']) == len(resource['scenePaths']) == len(resource['sceneEntries']) == 44
assert len({x['private_hash'] for x in plan['rows']}) == 44
for row, scene_hash, entry in zip(plan['rows'], resource['scenePaths'], resource['sceneEntries']):
    assert int(scene_hash) == row['private_hash']
    assert set(row['required_voice_tags']) <= set(entry['actorVoiceTags'])
    assert all(asset['DepotPath']['$value'].startswith('base\\localization\\en-us\\lipsync\\') for asset in entry['animSets'])
config = (candidate / 'package/archive/pc/mod/zzzz_PTFR_SideJobs_SR1_Lipmap.archive.xl').read_text(encoding='utf-8')
assert config == 'localization:\n  lipmaps:\n    en-us: towercontinued\\sidejob_repair_sr1\\en-us.lipmap\n'
result = {'status': 'ENGLISH_44_LIPMAP_REGISTRATIONS_AND_CONFIG_PASS', 'scene_entries': 44, 'scene_paths': 44, 'language': 'en-us', 'game_writes': 0, 'save_writes': 0}
(candidate / 'test_lipmap_01.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
