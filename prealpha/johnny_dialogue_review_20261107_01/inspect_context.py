"""Read-only, bounded source qualification for the Step 3 review pilot."""
import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource


def main():
    evidence = Path(__file__).parent / 'evidence_01'
    out = Path(__file__).parent / 'evidence_02'
    out.mkdir(exist_ok=True)
    sources = json.loads((evidence / 'sources.json').read_text(encoding='utf-8-sig'))
    captured = []
    for source in sources['resources']:
        model = Resource(json.loads(Path(source['json']).read_text(encoding='utf-8-sig'))).normalize()
        captured.append({'source': source, 'normalized': model})
        print('\nSOURCE', source['depot'], 'ERRORS', model['errors'])
        for gp, graph in model['graphs'].items():
            print('GRAPH', gp, 'ENTRIES', graph['entries'], 'NODES', len(graph['nodes']))
            for node_id, node in graph['nodes'].items():
                if 'sq023_restaurant.questphase' in source['depot']:
                    print('NODE', node_id, node['type'], json.dumps(node['payload'], ensure_ascii=False)[:800])
                    print('EDGES', [e for e in graph['edges'] if node_id in (e[0], e[2])])
    target = out / 'context_source_graphs.json'
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(captured, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
