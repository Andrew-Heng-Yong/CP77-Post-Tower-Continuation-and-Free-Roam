"""Generate the source-validated face catalogue; no game or original-asset writes."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
AUDIT = BASE / 'faces_r5'
SOURCE = BASE / 'appearance_rules'
DEST = ROOT / 'redscript/PTFR_Afterlife_Faces_R5'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def value(obj): return obj.get('$value') if isinstance(obj, dict) else obj
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def face(definition):
    rows = []
    for c in definition.get('components', []):
        mesh = value(c.get('mesh', {}).get('DepotPath', {}))
        if not mesh or not c.get('isEnabled', 1): continue
        if '\\characters\\head\\' not in mesh or not mesh.split('\\')[-1].lower().startswith('h0_'): continue
        if 'cyberware' in str(value(c.get('name'))).lower(): continue
        rows.append((mesh, value(c.get('meshAppearance')), c.get('chunkMask')))
    return sorted(set(rows))

def main():
    AUDIT.mkdir(parents=True, exist_ok=True); DEST.mkdir(parents=True, exist_ok=True)
    pools = read(SOURCE / 'audit.json')['pools']
    registry = next(c for c in read(BASE / 'patron_vanilla_registry.json') if c['community_index'] == 1070)
    entries = {e['name']: e['data'] for e in registry['entries']}
    templates, by_resource, hashes = [], defaultdict(list), {}
    ownership = {e['entry']:e['ready_fact'] for e in read(BASE/'population_r2/manifest.json')['entries']}
    for role, pool in enumerate(pools):
        path = next((SOURCE / 'sources/json').rglob(pool['record'].split('.')[-1] + '.ent.json'))
        template = read(path)['Data']['RootChunk']; hashes[str(path.relative_to(ROOT))] = sha(path)
        phase = next(p['Data'] for p in entries[pool['entry']]['phases'] if value(p['Data']['phaseName']) == 'q005')
        phase_names = [value(a) for a in phase['appearances']]
        mapping = template['appearances']
        # Both lists are authored for this exact ordinary role/phase. Final
        # selection uses explicit leaf aliases, eliminating unresolved native
        # precedence and a second parent-based randomization stage.
        allowed_names = set(pool['record_pool']) | (set(phase_names) - {'default','None','random'})
        roots = {(value(m['appearanceResource']['DepotPath']), value(m['appearanceName'])) for m in mapping if value(m['name']) in allowed_names}
        templates.append({'role': role, 'entry': pool['entry'], 'record': pool['record'],
                          'quantity': pool['configured_allocations_not_census'], 'source': str(path.relative_to(ROOT)),
                          'pool': pool['record_pool'], 'phase_names': phase_names,
                          'known_names':[value(m['name']) for m in mapping], 'owned_fact':ownership[pool['entry']]})
        for m in mapping:
            resource = value(m['appearanceResource']['DepotPath'])
            if not any(r == resource for r, n in roots): continue
            by_resource[resource].append({'role': role, 'name': value(m['name']),
                'definition': value(m['appearanceName']), 'allowed_definitions': {n for r,n in roots if r == resource}})
    candidates, rejected = [], []
    for resource, mappings in sorted(by_resource.items()):
        rel = Path(*resource.split('\\'))
        path = next(r/'json'/(str(rel)+'.json') for r in (SOURCE/'sources',SOURCE/'other_sources',AUDIT/'phase_sources') if (r/'json'/(str(rel)+'.json')).exists())
        definitions = {value(d['Data']['name']): d['Data'] for d in read(path)['Data']['RootChunk']['appearances']}
        hashes[str(path.relative_to(ROOT))] = sha(path)
        parents = defaultdict(list)
        for name, d in definitions.items(): parents[value(d.get('parentAppearance'))].append(name)
        for m in mappings:
            d = definitions[m['definition']]; ancestor = m['definition']; seen = set(); allowed = False
            while ancestor in definitions and ancestor not in seen:
                seen.add(ancestor)
                if ancestor in m['allowed_definitions']: allowed = True
                ancestor = value(definitions[ancestor].get('parentAppearance'))
            if not allowed: continue
            signature = face(d)
            if parents[m['definition']] or not signature:
                rejected.append({'role':m['role'], 'name':m['name'], 'reason':'parent_has_children' if parents[m['definition']] else 'head_unknown'})
                continue
            key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
            candidates.append({'role':m['role'], 'name':m['name'], 'resource':resource, 'definition':m['definition'],
                               'face_key':key, 'head_skin_components':signature})
        del definitions
    role_keys = [sorted({c['face_key'] for c in candidates if c['role'] == r}) for r in range(4)]
    # Allocate disjoint role pools, preserving each native quota. This prevents
    # arrival order from exhausting another role's only compatible faces.
    slots = [r for r in sorted(range(4), key=lambda r:len(role_keys[r])) for _ in range(templates[r]['quantity'])]
    owner = {}
    def augment(slot, seen):
        for key in role_keys[slots[slot]]:
            if key in seen: continue
            seen.add(key)
            if key not in owner or augment(owner[key], seen): owner[key] = slot; return True
        return False
    matched = sum(augment(i,set()) for i in range(len(slots)))
    assert matched == len(slots), f'Not enough verified leaf faces: {[len(k) for k in role_keys]}, matched {matched}/{len(slots)}; do not build'
    partition = {key:slots[slot] for key,slot in owner.items()}
    for key in sorted(set().union(*map(set,role_keys)) - set(partition)):
        roles = [r for r in range(4) if key in role_keys[r]]
        partition[key] = min(roles, key=lambda r:(sum(v==r for v in partition.values())/templates[r]['quantity'],r))
    # Prefer the dedicated cyberpunk role for its original record-pool faces
    # where the broader generic phase has enough alternatives. Do not needlessly
    # remove two of six cyberpunk-female faces merely to fill a matching minimum.
    for role in (2,3):
        for key in role_keys[role]:
            old = partition[key]
            if old != role and sum(v==old for v in partition.values()) > templates[old]['quantity']:
                partition[key] = role
    selected = [c for c in candidates if partition[c['face_key']] == c['role']]
    # Alias variants sharing a face stay together; the runtime draws a face
    # once, then chooses among that face's compatible alias variants.
    face_numbers = {key:i+1 for i,key in enumerate(sorted(partition))}
    for c in selected: c['face'] = face_numbers[c['face_key']]
    for r in range(4):
        templates[r]['eligible_faces'] = sorted({c['face'] for c in selected if c['role']==r})
        assert len(templates[r]['eligible_faces']) >= templates[r]['quantity']
    lines=['module PTFR.AfterlifeFacesR5','', '// GENERATED by tools/build_afterlife_faces_r5.py; existing vanilla leaf aliases only.',
           'public class FaceOptionR5 extends IScriptable {', '  public let role: Int32;', '  public let face: Int32;', '  public let appearance: CName;',
           '  public static func Make(role: Int32, face: Int32, appearance: CName) -> ref<FaceOptionR5> {',
           '    let row = new FaceOptionR5(); row.role = role; row.face = face; row.appearance = appearance; return row;', '  }','}',
           'public class FaceCatalogR5 extends IScriptable {', '  public static func Create() -> array<ref<FaceOptionR5>> {', '    let rows: array<ref<FaceOptionR5>>;']
    for c in sorted(selected,key=lambda c:(c['role'],c['face'],c['name'])):
        lines.append(f'    ArrayPush(rows, FaceOptionR5.Make({c["role"]}, {c["face"]}, n"{c["name"]}"));')
    lines += ['    return rows;', '  }', '  public static func Role(record: TweakDBID) -> Int32 {']
    for r in templates: lines.append(f'    if record == t"{r["record"]}" {{ return {r["role"]}; }}')
    lines += ['    return -1;','  }','  public static func Entry(role: Int32) -> CName {']
    for r in templates: lines.append(f'    if role == {r["role"]} {{ return n"{r["entry"]}"; }}')
    lines += ['    return n"None";','  }','  public static func Quota(role: Int32) -> Int32 {']
    for r in templates: lines.append(f'    if role == {r["role"]} {{ return {r["quantity"]}; }}')
    lines += ['    return 0;','  }','  public static func Owned(role: Int32) -> CName {']
    for r in templates: lines.append(f'    if role == {r["role"]} {{ return n"{r["owned_fact"]}"; }}')
    lines += ['    return n"None";','  }','  public static func Known(role: Int32, appearance: CName) -> Bool {']
    for r in templates:
        lines.append(f'    if role == {r["role"]} {{')
        for name in r['known_names']: lines.append(f'      if Equals(appearance, n"{name}") {{ return true; }}')
        lines.append('    }')
    lines += ['    return false;','  }','}']
    generated = DEST/'FaceCatalogR5.reds'; generated.write_text('\n'.join(lines)+'\n')
    manifest={'status':'CATALOG_BUILT_NOT_INSTALLED','roles':templates,'options':selected,'rejected':rejected,
              'source_hashes':hashes,'catalog_sha256':sha(generated),'native_community_id':'16642022925330812742',
              'scope':'four exact original q005 ordinary community entries; no named/scene cast',
              'selection':'uniform available face, then uniform valid alias; disjoint role pools; no new faces/assets/records/actors',
              'game_writes':0}
    (AUDIT/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'roles':[{k:r[k] for k in ('entry','quantity','eligible_faces')} for r in templates], 'aliases':len(selected)}))

if __name__ == '__main__': main()
