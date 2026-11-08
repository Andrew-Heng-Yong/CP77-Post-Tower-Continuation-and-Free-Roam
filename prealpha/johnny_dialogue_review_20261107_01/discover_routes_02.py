"""Read-only graph discovery for the revised five-quest transcript pilot."""
import collections
import json
import sqlite3
from pathlib import Path

TASK = Path(__file__).resolve().parent
WS = TASK.parents[1]
DB = WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
SCENES = ['90c76218185ecad8483a5352', '93e6400371356f3e8610840b',
          '46c42e83bb787eaa82671b92', '8b75d3f39fc0712f252a3483']


def main():
    con = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    out = TASK / 'evidence_03'
    out.mkdir(exist_ok=True)
    captures = []
    for rid in SCENES:
        root = rid + '/root'
        nodes = {r['node_id']: dict(r) for r in con.execute("select * from nodes where root_id=? and graph_path='scene'", (root,))}
        edges = [list(r) for r in con.execute("select source_node,output_stamp,destination_node,input_stamp from edges where root_id=? and graph_path='scene'", (root,))]
        adjacent = collections.defaultdict(list)
        for edge in edges:
            adjacent[edge[0]].append(edge)
        spoken = {r[0] for r in con.execute("select distinct node_id from events where root_id=? and graph_path='scene' and type='scnDialogLineEvent'", (root,))}
        choices = {}
        for r in con.execute("select * from choices where root_id=? and graph_path='scene'", (root,)):
            row = dict(r)
            texts = [x[0] for x in con.execute("select text from localization where loc_id=? and root_id=? and locale='en_us' and text<>''", (row['loc_id'], root))]
            row['english_labels'] = sorted(set(texts))
            choices.setdefault(row['node_id'], []).append(row)

        def next_boundaries(start):
            found = []
            for first in adjacent[start]:
                queue = collections.deque([(first[2], [first])])
                seen = set()
                while queue:
                    node, path = queue.popleft()
                    if node in seen or len(path) > 45:
                        continue
                    seen.add(node)
                    if node in spoken or node in choices:
                        found.append(path)
                        continue
                    for edge in adjacent[node]:
                        queue.append((edge[2], path + [edge]))
            return found

        paths = {n: next_boundaries(n) for n in spoken | set(choices)}
        capture = {'resource_id': rid, 'nodes': nodes, 'edges': edges,
                   'spoken_nodes': sorted(spoken), 'choices': choices, 'possible_boundary_paths': paths}
        captures.append(capture)
        print('\nRESOURCE', rid)
        for n in sorted(spoken | set(choices), key=int):
            if rid == '8b75d3f39fc0712f252a3483' and n not in ('134', '172'):
                continue
            print(n, 'CHOICE' if n in choices else 'SPEECH',
                  [(p[0][1], p[-1][2], len(p)) for p in paths[n]][:18])
            if n in choices:
                print('OPTIONS', [(r['output_stamp'], r['english_labels']) for r in choices[n]])
    target = out / 'route_discovery.json'
    assert not target.exists()
    target.write_text(json.dumps(captures, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
