"""Read-only source checks; writes only a regenerable workspace evidence report."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/restoration_checklist_audit.json'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def walk(item):
    if isinstance(item, dict):
        yield item
        for value in item.values():
            yield from walk(value)
    elif isinstance(item, list):
        for value in item:
            yield from walk(value)


def snapshot(path):
    file = ROOT / path
    doc = read(path)
    root = doc['Data']['RootChunk']
    objects = list(walk(root))
    return {
        'path': path, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
        'game_version': doc['Header'].get('GameVersion'),
        'root_type': root['$type'],
        'facts': sorted({o['factName'] for o in objects if 'factName' in o}),
        'writers': [dict(fact=o['factName'], value=o.get('value'), exact=o.get('setExactValue'))
                    for o in objects if o.get('$type') == 'questSetVar_NodeType'],
    }


def main():
    ordinary = read('research/b0_ordinary_vendor_batch/cohort.json')['sites']
    special = read('research/b0_special_services/cohort.json')['sites']
    expanded = read('research/b0_vendor_rollout/expanded_service_inventory.json')
    assert len(ordinary) == 25 and len(special) == 19
    assert len(expanded) == 143
    assert len({r['scene'] for r in expanded}) == 125
    verified = []
    for site in special:
        for field, hash_field in [('owner_json', 'owner_sha256'), ('scene_json', 'scene_sha256')]:
            path = ROOT / site[field]
            actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            assert actual == site[hash_field].upper(), (site['key'], field)
            verified.append({'site': site['key'], 'kind': field, 'path': site[field], 'sha256': actual})
    files = [
        'research/b0_club_dancing/riot_original_owner.json',
        'research/b0_tv_media/original.json',
        'research/b0_story_services/pepe_quest_sources/json/base/quest/minor_quests/mq040/mq040_biosculpt.questphase.json',
        'research/b0_vendor_rollout/special_scene_sources/json/base/open_world/vendors/westbrook/japantown/wbr_jpn_tech_01/wbr_jpn_tech_01.scene.json',
    ]
    sources = [snapshot(p) for p in files]
    assert 'riot_dancefloor_on' in sources[0]['facts']
    assert 'tv_on' in sources[1]['facts']
    pairs = {(w['fact'], w['value']) for w in sources[2]['writers']}
    assert {('elcoyote_barman_default_on', 0), ('elcoyote_barman_default_on', 1),
            ('mq040_active', 0), ('mq040_active', 1)} <= pairs
    assert 'sq012_christine_dd' in sources[3]['facts'] and not sources[3]['writers']
    checklist = ROOT / 'research/restoration_checklist.md'
    targets = re.findall(r'\]\(([^)]+)\)', checklist.read_text(encoding='utf-8'))
    local_links = [p for p in targets if not p.startswith(('https://', 'http://'))]
    missing = [p for p in local_links if (checklist.parent / p).resolve() != OUT.resolve()
               and not (checklist.parent / p).resolve().exists()]
    assert not missing, missing
    report = dict(
        status='STATIC_CHECKLIST_SOURCE_PASS_NOT_RUNTIME_CERTIFICATION',
        date='2026-09-27', ordinary_sites=len(ordinary), special_sites=len(special),
        expanded_occurrences=len(expanded), unique_scene_resources=len({r['scene'] for r in expanded}),
        special_source_hash_checks=verified, selected_vanilla_sources=sources,
        local_links_checked=len(local_links), missing_links=missing,
        no_game_save_or_fact_writes=True,
        limitations=['No all-site runtime pass', 'No current installed-file hash certification',
                     'Fact mentions alone are not reconstructed availability predicates'])
    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in
                      {'special_source_hash_checks', 'selected_vanilla_sources'}}, indent=2))


if __name__ == '__main__':
    main()
