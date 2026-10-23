"""Bounded Watson candidate inventory from local native exports; research only."""
import hashlib
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/gig_restoration'
OUT = BASE / 'fresh_candidates'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--extended', action='store_true')
    args = parser.parse_args()
    analysis_path = BASE / 'watson_analysis/analysis.json'
    titles_path = BASE / 'journal_titles.json'
    analysis = json.loads(analysis_path.read_text())
    titles = {q['id']: q for q in json.loads(titles_path.read_text())['quests']}
    groups, sources = {}, {str(p.relative_to(ROOT)): sha(p) for p in (analysis_path, titles_path)}
    roots = [BASE / 'watson_sources/json']
    raw_facts = set()
    if args.extended:
        extra = OUT / 'local_analysis/analysis.json'
        analysis['nodes'].extend(json.loads(extra.read_text())['nodes'])
        sources[str(extra.relative_to(ROOT))] = sha(extra)
        roots.append(OUT / 'local_sources/json')
    for path in (p for root in roots for p in root.rglob('*.json')):
        sources[str(path.relative_to(ROOT))] = sha(path)
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        raw_facts.update(v['factName'] for v in walk(data) if isinstance(v.get('factName'), str))
        source_root = next(root for root in roots if path.is_relative_to(root))
        resource = str(path.relative_to(source_root))[:-5].replace('/', '\\')
        for i, embedded in enumerate(data['Data'].get('EmbeddedFiles', [])):
            name = embedded['FileName']['$value']
            match = re.search(r'(sts_[a-z]{3}_[a-z]{3}_\d+)\\', name)
            if not match:
                continue
            gid = match[1]
            row = groups.setdefault(gid, {'id': gid, 'title': titles[gid]['title'],
                                         'journal_path': titles[gid]['journal_path'], 'phases': [], 'nodes': []})
            prefix = resource + '::Data.EmbeddedFiles.' + str(i) + '.'
            row['phases'].append({'resource': name, 'container': resource, 'embedded_index': i})
            row['nodes'].extend(n for n in analysis['nodes'] if n['graph'].startswith(prefix))
    fact_names = {'PostTowerFreeRoamActive', 'q307_done', 'q307_finished', 'q307_2079',
                  'q307_main_game_killed', 'q307_point_of_no_return', 'q115_point_of_no_return',
                  'wat_sts_counter', 'wat_achievement'}
    fact_names.update(raw_facts)
    fact_names.update(('bls_sts_counter', 'cct_sts_counter'))
    # Include authored district admission facts outside individual gig phases.
    for node in analysis['nodes']:
        for key, value in node['details'].items():
            if 'factName' in key and isinstance(value, str):
                fact_names.add(value)
    candidates = []
    for gid, row in sorted(groups.items()):
        nodes = row.pop('nodes')
        facts = sorted({v for n in nodes for k, v in n['details'].items() if 'factName' in k})
        scenes = sorted({v for n in nodes for k, v in n['details'].items() if k == 'sceneFile.DepotPath' and v != '0'})
        row.update(node_count=len(nodes), fact_names=facts, scenes=scenes,
                   external_story_facts=[f for f in facts if f.startswith(('q', 'sq', 'mq'))],
                   start_finish_failure_names=[f for f in facts if any(s in f for s in ('start', 'finish', 'fail'))],
                   status='SOURCE_CANDIDATE_NOT_FRESHNESS_OR_RUNTIME_ADMISSION')
        candidates.append(row)
    OUT.mkdir(exist_ok=True)
    products = {
        'watson_inventory.json': {'status': 'RESEARCH_ONLY', 'scope': 'Embedded gig lifecycles in inspected districts; not all-game census',
                                  'sources': sources, 'candidates': candidates, 'game_writes': 0, 'save_writes': 0},
        'fact_catalogue.json': {'status': 'READ_ONLY_FACT_SELECTION_NOT_ADMISSION',
                                'fact_names': sorted(f for f in fact_names if re.fullmatch(r'[A-Za-z0-9_]+', f)),
                                'excluded_from_fact_probe': sorted(f for f in fact_names if not re.fullmatch(r'[A-Za-z0-9_]+', f)),
                                'sources': sources, 'scope': 'Actual recursive fact names in inspected raw district graphs plus explicit Tower/counter context'},
    }
    for name, data in products.items():
        target = OUT / (('extended_' if args.extended else '') + name)
        assert not target.exists(), f'Refusing to replace evidence: {target}'
        target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidates': len(candidates), 'fact_names': len(fact_names), 'output': str(OUT)}))


if __name__ == '__main__':
    main()
