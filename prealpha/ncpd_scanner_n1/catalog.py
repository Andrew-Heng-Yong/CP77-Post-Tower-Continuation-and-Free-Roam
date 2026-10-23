"""Source-backed scanner catalog. Inventory is not runtime restoration proof."""
from collections import Counter
import json
from pathlib import Path
from native_inspect import ROOT, SafeResource, flatten
from catalog_gig_rollout_r2 import read, sha, walk, handles, deref, value

OUT = ROOT / 'research/ncpd_scanner_n1'
JP = ROOT / 'research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json'
VARIANTS = {'GangWatchVariant', 'OutpostVariant', 'HiddenStashVariant'}


def journal():
    obj = read(JP)
    h = handles(obj)
    entries = {}
    def visit(wrapper, path):
        n = deref(wrapper, h)
        path = path + ([n['id']] if n.get('id') else [])
        if n.get('$type') == 'gameJournalPointOfInterestMappin':
            v = deref(n['mappinData']['typedVariant'], h)
            if v.get('variant') in VARIANTS:
                entries['/'.join(path)] = {'id': n['id'], 'variant': v['variant'],
                    'trigger': value(n['notificationTriggerAreaRef']),
                    'static_ref': value(n['staticNodeRef']),
                    'quest': deref(n.get('questPath'), h)}
        for c in n.get('entries', []):
            visit(c, path)
    visit(obj['Data']['RootChunk']['entry'], [])
    return entries


def main():
    pois = journal()
    library = {}
    for group in ('parents_02', 'encounters_02'):
        base = OUT / group / 'json'
        for p in base.rglob('*.json'):
            depot = str(p.relative_to(base))[:-5].replace('/', '\\')
            r = SafeResource(read(p))
            library[depot] = (p, r, r.obj['Data']['RootChunk'])
            for e in r.obj['Data'].get('EmbeddedFiles', []):
                if 'graph' in e['Content']:
                    library[value(e['FileName'])] = (p, r, e['Content'])
    rows = []
    for p in (OUT / 'parents_02/json').rglob('*.json'):
        r = SafeResource(read(p))
        for g in flatten(r, r.obj['Data']['RootChunk']):
            nodes = {n['id']: n for n in g['nodes']}
            for n in g['nodes']:
                if n.get('$type') != 'questJournalNodeDefinition':
                    continue
                poi = n.get('type', {}).get('path', {}).get('realPath')
                if poi not in pois or n.get('$type') != 'questJournalNodeDefinition':
                    continue
                next_edges = [e for e in g['edges'] if e[0] == n['id']]
                owners = [nodes[e[2]] for e in next_edges if nodes[e[2]]['$type'] == 'questPhaseNodeDefinition']
                if len(owners) != 1:
                    rows.append({'id': pois[poi]['id'], 'issue': 'non-direct-owner', 'parent': str(p.relative_to(ROOT)), 'map': n['id'], 'next': next_edges})
                    continue
                owner = owners[0]
                depot = value(owner.get('phaseResource', {}).get('DepotPath'))
                if depot not in library:
                    rows.append({'id': pois[poi]['id'], 'issue': 'unresolved-resource', 'depot': depot})
                    continue
                op, rr, root = library[depot]
                graphs = flatten(rr, root)
                writes = [{'graph': x['path'], 'node': m['id'], **m['type']} for x in graphs for m in x['nodes'] if m['$type'] == 'questFactsDBManagerNodeDefinition']
                scenes = sorted({value(v['sceneFile']['DepotPath']) for v in walk(root) if 'sceneFile' in v})
                facts = sorted({v['factName'] for v in walk(root) if 'factName' in v})
                rows.append({**pois[poi], 'poi': poi, 'parent': str(p.relative_to(ROOT)).replace('\\', '/'),
                    'parent_graph': g['path'], 'map_node': n['id'], 'owner_node': owner['id'],
                    'owner_input': next(e[3] for e in next_edges if e[2] == owner['id']),
                    'depot': depot, 'source': str(op.relative_to(ROOT)).replace('\\', '/'),
                    'finish_facts': [w['factName'] for w in writes if w['factName'].endswith(('_finished', '_done'))],
                    'start_facts': [w['factName'] for w in writes if w['factName'].endswith(('_start', '_started'))],
                    'writes': writes, 'facts': facts, 'scenes': scenes,
                    'phase_refs': sorted({value(v['phaseResource']['DepotPath']) for v in walk(root) if 'phaseResource' in v} - {'0', None}),
                    'prefabs': root.get('phasePrefabs'),
                    'native_nodes': sum(len(x['nodes']) for x in graphs),
                    'owner_outputs': [e for e in g['edges'] if e[0] == owner['id']],
                    'journal_paths': sorted({v['realPath'] for v in walk(root) if 'realPath' in v})})
    report = {'status': 'SOURCE_CATALOG_NOT_IMPLEMENTATION', 'journal_sha256': sha(JP),
        'poi_count': len(pois), 'variants': dict(Counter(p['variant'] for p in pois.values())),
        'rows': rows, 'unbound_pois': [v for k, v in pois.items() if k not in {r.get('poi') for r in rows}],
        'inputs': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in sorted({x[0] for x in library.values()})}}
    dest = OUT / 'catalog_v1.json'
    if dest.exists():
        raise RuntimeError('Preserve evidence; use another revision')
    dest.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pois': report['variants'], 'rows': len(rows), 'unbound': report['unbound_pois'],
        'issues': [r for r in rows if 'issue' in r],
        'completion_exceptions': [{k: r[k] for k in ('id', 'finish_facts', 'start_facts', 'phase_refs')} for r in rows if 'issue' not in r and (len(r['finish_facts']) != 1 or len(r['start_facts']) != 1)],
        'scene_count': len({s for r in rows for s in r.get('scenes', [])})}, indent=2))


if __name__ == '__main__':
    main()
