"""Read-only registry lookup. Native game and save APIs are never used."""
import argparse
import json
import sqlite3
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('quest',help='Native ID or part of the title')
    ap.add_argument('--registry',default='registry_01')
    ap.add_argument('--stage',help='Substring of a stage path')
    ap.add_argument('--full',action='store_true',help='Include every source site in the quest record')
    ap.add_argument('--node',nargs=3,metavar=('PROVIDER_ID','GRAPH','NODE_ID'))
    a=ap.parse_args()
    path=Path(__file__).resolve().parent/a.registry/'registry.sqlite3'
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    if a.node:
        r=db.execute('SELECT * FROM nodes WHERE rid=? AND graph=? AND id=?',a.node).fetchone()
        if not r:raise SystemExit('Node not found')
        r=dict(r);r['parameters']=json.loads(r.pop('parameters_json'));r['sockets']=json.loads(r.pop('sockets_json'))
        r['provider']=dict(db.execute('SELECT * FROM resources WHERE rid=?',(r['rid'],)).fetchone())
        r['provider'].pop('support_json')
        r['edges']=[dict(x) for x in db.execute('SELECT * FROM edges WHERE rid=? AND graph=? AND (source=? OR destination=?)',(r['rid'],r['graph'],r['id'],r['id']))]
        print(json.dumps(r,ensure_ascii=False,indent=2));return
    matches=[json.loads(r[0]) for r in db.execute('SELECT record_json FROM quests WHERE id=? OR instr(lower(title),lower(?))>0',(a.quest,a.quest))]
    if not matches:raise SystemExit('Quest not found')
    if a.stage:
        for q in matches:
            for r in db.execute('SELECT record_json FROM stages WHERE quest_id=? AND instr(path,?)>0',(q['id'],a.stage)):
                print(json.dumps(json.loads(r[0]),ensure_ascii=False,indent=2))
    else:
        if not a.full:
            for q in matches:
                q.pop('feature_sites',None);q.pop('parent_call_sites',None);q.pop('script_mentions',None)
        print(json.dumps(matches,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
