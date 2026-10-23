"""Reduce regenerable sector exports to referenced memorial nodes, not full city dumps."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/radio_memorial_validation/world'
MARKER='#loc_q204_columbarium_devices'


def unwrap(value):
    return value.get('$value',value) if isinstance(value,dict) else value


if __name__=='__main__':
    scan=json.loads((BASE/'matches.json').read_text(encoding='utf-8-sig'))
    output=[]
    for row in scan:
        # The typed reader already exported QuestPrefabRefHash and position;
        # avoid parsing the enormous always-loaded city snapshots again.
        selected=[n for n in row['nodes'] if MARKER in n['reference']]
        output.append({k:row[k] for k in ('archive','sector','sha256')}|{'nodes':selected})
    prefixes=sorted({n['reference'].split(MARKER)[0]+MARKER for r in output for n in r['nodes']})
    result={'scope':'bounded base+EP1 nightcity streaming sectors','prefab_prefixes':prefixes,'sectors':output}
    (BASE/'memorial_nodes.json').write_text(json.dumps(result,indent=2)+'\n')
    # Retain only the same exact-reference records in the regenerable scan
    # manifest, too; unrelated always-loaded city node data is not evidence.
    (BASE/'matches.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'prefab_prefixes':prefixes,'matches':len(output),
                      'selected_nodes':sum(len(r['nodes']) for r in output)},indent=2))
    samples=[n for r in output for n in r['nodes'] if 'jackie' in n['reference'].lower()]
    print(json.dumps({'jackie_samples':samples[:6]},indent=2))
