"""Independent inventory/readback checks. Does not certify gameplay or stage safety."""
import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from prepare import HERE, read, sha, write

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--registry',default='registry_01');a=ap.parse_args()
    out=HERE/a.registry;db=sqlite3.connect((out/'registry.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;checks=[]
    def check(name,passed,details=None):
        checks.append({'check':name,'passed':bool(passed),'details':details})
        if not passed:raise AssertionError((name,details))
    check('sqlite_integrity',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    prepared=read(HERE/'evidence_01/prepared.json')
    check('installed_files_unchanged',all(sha(r['path'])==r['sha256'] for r in prepared['checks']),len(prepared['checks']))
    source=[json.loads(l) for l in (HERE/'evidence_02/resources.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    actual=list(db.execute('SELECT * FROM resources ORDER BY rid'))
    check('provider_inventory_exact',len(source)==len(actual) and all(
      (s['archive'],s['key'],s['sha256'],s.get('json_sha256'))==(r['archive'],r['key'],r['sha256'],r['export_sha256']) for s,r in zip(source,actual)),len(source))
    check('opaque_sources_retained',all(r['status'] in ('OPAQUE','NORMALIZATION_BLOCKED') for s,r in zip(source,actual) if s['status']=='OPAQUE'))
    bad=list(db.execute('SELECT e.* FROM edges e LEFT JOIN nodes n ON e.rid=n.rid AND e.graph=n.graph AND e.source=n.id WHERE n.id IS NULL'))
    check('all_edge_sources_bound',not bad,len(bad))
    bad=list(db.execute('''SELECT e.* FROM edges e LEFT JOIN nodes n
      ON e.rid=n.rid AND e.graph=n.graph AND e.destination=n.id
      WHERE n.id IS NULL AND NOT EXISTS(SELECT 1 FROM boundaries b
      WHERE b.rid=e.rid AND b.graph=e.graph AND b.node=e.source AND b.kind='SCENE_DESTINATION_UNBOUND')'''))
    check('edge_destinations_bound_or_explicit_boundary',not bad,len(bad))
    selection=read(HERE/'evidence_01/selection.json')
    expected={(r['id'],r['decision'],r['journal_path']) for r in selection['rows']}
    observed={tuple(r) for r in db.execute('SELECT id,selection,journal_root FROM quests')}
    check('all_selection_rows_preserved',observed==expected,len(expected))
    mismatches=[]
    for s in db.execute('SELECT * FROM stages'):
        root=db.execute('SELECT journal_root FROM quests WHERE id=?',(s['quest_id'],)).fetchone()[0]
        if not (s['path']==root or s['path'].startswith(root+'/')):mismatches.append(dict(s))
        for ref in json.loads(s['record_json'])['sites']:
            if not db.execute('SELECT 1 FROM nodes WHERE rid=? AND graph=? AND id=?',(ref['rid'],ref['graph'],ref['node'])).fetchone():mismatches.append(ref)
    check('stages_have_exact_quest_roots_and_node_evidence',not mismatches,len(mismatches))
    direct={r['quest_id'] for r in db.execute('SELECT DISTINCT quest_id FROM stages')}
    check('machine_gun_deliver_stage_indexed',bool(db.execute("SELECT 1 FROM stages WHERE quest_id='mq007_smartgun' AND path LIKE '%/01_deliver_skippy'").fetchone()))
    graph=db.execute("SELECT rid FROM resources WHERE role='STOCK' AND depot=?",('base\\quest\\minor_quests\\mq007\\mq007.questphase',)).fetchone()
    check('machine_gun_native_provider_bound',graph is not None)
    grant=db.execute("SELECT parameters_json FROM nodes WHERE rid=? AND graph='root/5' AND id=30",(graph[0],)).fetchone()
    journal=db.execute("SELECT parameters_json FROM nodes WHERE rid=? AND graph='root/5' AND id=11",(graph[0],)).fetchone()
    check('grant_and_delivery_nodes_remain_distinct','Items.mq007_skippy' in grant[0] and '01_deliver_skippy' in journal[0] and 'Items.mq007_skippy' not in journal[0])
    check('snapshot_denomination_reconciled',set(read(out/'summary.json')['selected_without_snapshot'])=={'mq006_rollercoaster','mws_se5_07','mws_wat_08_trauma_drama'} and read(out/'summary.json')['snapshot_outside_selection']==['mq026_conspiracy'])
    check('registry_read_only_api',not any(token in (HERE/'query.py').read_text() for token in ('SetFact','Game.Get','UPDATE ','DELETE ')))
    write(out/'verification.json',{'status':'PASS_BOUNDED_STRUCTURAL_CHECKS','checks':checks,
       'limitations':'Does not prove full socket reachability, actual native/saved owner retirement, world-support completeness, safe resume seams or runtime behavior.'})
    print(json.dumps({'checks':len(checks),'status':'PASS_BOUNDED_STRUCTURAL_CHECKS'},indent=2))

if __name__=='__main__':main()
