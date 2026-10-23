"""Bounded street-art/NPC inventory. Planning only; never starts the ending."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/misty_viktor_world'
ALLOW = {'worldStaticMeshNode', 'worldStaticDecalNode', 'worldCollisionNode'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def val(x):
    return x.get('$value', x) if isinstance(x, dict) else x

def main():
    groups = read(ROOT / 'research/phase2b_p4/compiled_staging_members.json')
    ranges = []
    cache = {}
    for group in groups:
        if group['variant']['name'] != 'q307_misty_alley':
            continue
        depot = group['sector']
        path = ROOT / 'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json' / (depot + '.json')
        raw = ROOT / 'research/phase2b_p4/variant_sectors/ep1_1_nightcity/raw' / depot
        if depot not in cache:
            cache[depot] = read(path)['Data']['RootChunk']
        sector = cache[depot]
        selected, pending = [], []
        for index in range(group['range_start'], group['range_end_exclusive']):
            instance = sector['nodeData']['Data'][index]
            node = sector['nodes'][instance['NodeIndex']]['Data']
            row = {'data_index': index, 'node_index': instance['NodeIndex'],
                   'type': node['$type'], 'name': val(node.get('debugName')),
                   'position': [instance['Position'][a] for a in ('X', 'Y', 'Z')]}
            for field in ('mesh', 'material', 'entityTemplate'):
                if isinstance(node.get(field), dict):
                    row[field] = val(node[field].get('DepotPath'))
            (selected if row['type'] in ALLOW else pending).append(row)
        ranges.append({'source_sector': depot, 'source_block': group['block'],
                       'descriptor_index': group['descriptor_index'], 'variant': group['variant'],
                       'range': [group['range_start'], group['range_end_exclusive']],
                       'raw_path': str(raw.relative_to(ROOT)),
                       'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
                       'selected': selected, 'pending_payload_audit': pending})
    logo = [dict(source_sector=r['source_sector'], **n) for r in ranges for n in r['selected']
            if n['data_index'] == 386 and r['source_sector'].endswith(r'ep1\exterior_-25_18_0_0.streamingsector')]
    assert len(logo) == 1 and 'zetatech' in str(logo[0]).lower(), logo

    template = read(OUT / 'street_npc_sources/json/ep1/quest/main_quests/q307/communities/q307_com_alley.community.json')
    entries = template['Data']['RootChunk']['communityTemplate']['Data']['entries']
    ambient, excluded = [], []
    for handle in entries:
        entry = handle['Data']
        record = val(entry['characterRecordId'])
        row = {'entry': val(entry['entryName']), 'record': record, 'phases': [], 'unresolved_phase_handles': []}
        for phase in entry['phases']:
            if 'Data' not in phase:
                row['unresolved_phase_handles'].append(phase)
                continue
            data = phase['Data']
            row['phases'].append({'name': val(data['phaseName']),
                                  'appearances': [val(v) for v in data['appearances']],
                                  'spots': [val(v) for t in data['timePeriods'] for v in t['spotNodeRefs']]})
        (excluded if record.startswith('Character.q307_') else ambient).append(row)
    assert len(entries) == 35 and len(ambient) == 31 and len(excluded) == 4
    terry = read(OUT / 'terry_record_audit.json')
    modifiers = [n['fields'] for n in terry['gameplay_dependencies']
                 if n['type'].endswith('StatModifier_Record')]
    assert terry['display_name'] == 'Terry' and terry['record'] == 'Character.q307_thug_01'
    assert terry['tags'] == ['Invulnerable']
    assert all(m.get('statType_resolved') not in ('BaseStats.IsInvulnerable', 'BaseStats.IsImmortal') for m in modifiers)
    result = {'status': 'SOURCE_INVENTORY_ONLY_NOT_BUILT_OR_INSTALLED',
              'requested_scope': 'Tower storefront/local street art, generic ambient replacement, plus Terry only',
              'facade_logo': logo[0], 'source_ranges': ranges,
              'passive_types': dict(Counter(n['type'] for r in ranges for n in r['selected'])),
              'pending_types': dict(Counter(n['type'] for r in ranges for n in r['pending_payload_audit'])),
              'ambient_entries': ambient, 'excluded_staged_entries': excluded,
              'terry': {'source_record': terry['record'], 'appearance': terry['appearance'],
                        'name_key': terry['display_key'], 'original_invulnerable': True,
                        'required_private_record': 'Character.PTFRMV_Terry',
                        'original_record_changes': 0, 'observed_direct_ability_invulnerability_modifiers': 0,
                        'live_damage_or_death_tested': False},
              'forbidden': ['q307 replay', 'original Terry record edits', 'Jim/Misty/Johnny/clerk spawns',
                            'whole ending bundles', 'global crowd disable', 'V restriction changes', 'story fact writes'],
              'remaining': ['audited old/new decoration swap and support/collision footprint',
                            'lights/destructibles/advertisement payload isolation',
                            'ambient workspot residency, local crowd suppression and natural reactions',
                            'private Terry combat lifecycle, damage/death and duplicate prevention',
                            'combined opt-in build/offline verification/closed-game install/live check']}
    (OUT / 'street_selection_plan.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'logo': logo[0]['name'],
                      'passive': result['passive_types'], 'pending': result['pending_types'],
                      'ambient_humans': len(ambient), 'named_exception': terry['display_name']}, indent=2))

if __name__ == '__main__':
    main()
