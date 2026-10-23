"""Bounded native MQ025 audit. Read-only unless an explicit output is given."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten

def graphs(path):
    r=SafeResource(json.loads(path.read_text(encoding='utf-8-sig')))
    return flatten(r,r.obj['Data']['RootChunk'])

def main():
    for p in sorted((ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq025').rglob('*.json')):
        if sys.argv[1:] and sys.argv[1] not in p.name:continue
        gs=graphs(p);print('FILE',p.relative_to(ROOT))
        for g in gs:
            if len(sys.argv)>2 and sys.argv[2]=='root' and g['path']!='root':continue
            print('GRAPH',g['path'])
            for n in g['nodes']:
                t=n.get('type',{})
                detail={k:n[k] for k in ['condition','socketName','phaseResource'] if k in n}
                if isinstance(t,dict) and t.get('$type') in ['questSetVar_NodeType','questJournalQuestEntry_NodeType']:detail['type']=t
                print(n['id'],n['$type'],json.dumps(detail,separators=(',',':')))
            print('EDGES',g['edges'])
if __name__=='__main__':main()
