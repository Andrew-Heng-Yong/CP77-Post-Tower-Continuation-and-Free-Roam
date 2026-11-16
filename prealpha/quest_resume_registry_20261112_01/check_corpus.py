"""Compare PTFR and selected native quest graphs with the separate audit parser."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from model import load_export
from prepare import HERE,ROOT,sha,write

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--registry',default='registry_02');a=ap.parse_args()
    path=HERE/a.registry;db=sqlite3.connect((path/'registry.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    oracle=ROOT/'tools/parity_audit/model.py';sys.path.insert(0,str(oracle.parent))
    spec=importlib.util.spec_from_file_location('prior_parity_model',oracle);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[];mismatches=[]
    for r in db.execute("""SELECT * FROM resources r WHERE export_path IS NOT NULL AND
      (role='PTFR' OR EXISTS(SELECT 1 FROM quest_resources qr JOIN quests q ON q.id=qr.quest_id
       WHERE qr.rid=r.rid AND q.selection='INCLUDE' AND qr.association='DIRECT_JOURNAL_REFERENCE'))"""):
        assert sha(r['export_path'])==r['export_sha256']
        m=module.Resource(load_export(r['export_path'])).normalize()
        our_graphs={g[0] for g in db.execute('SELECT path FROM graphs WHERE rid=?',(r['rid'],))}
        problems=[]
        if our_graphs!=set(m['graphs']):problems.append({'kind':'GRAPH_SET','ours':sorted(our_graphs),'oracle':sorted(m['graphs'])})
        for gp,g in m['graphs'].items():
            ours={str(n[0]) for n in db.execute('SELECT id FROM nodes WHERE rid=? AND graph=?',(r['rid'],gp))}
            if ours!=set(g['nodes']):problems.append({'kind':'NODE_SET','graph':gp})
            edges=[]
            for e in db.execute('SELECT source,source_socket,destination,destination_socket FROM edges WHERE rid=? AND graph=?',(r['rid'],gp)):
                a,b,c,d=e
                if gp=='scene':
                    bs=json.loads(b);ds=json.loads(d);b=str(bs.get('name',0))+':'+str(bs.get('ordinal',0));d=str(ds.get('name',0))+':'+str(ds.get('ordinal',0))
                edges.append((str(a),b,str(c),d))
            if Counter(edges)!=Counter(map(tuple,g['edges'])):problems.append({'kind':'EDGE_MULTIPLICITY','graph':gp})
        row={'rid':r['rid'],'depot':r['depot'],'sha256':r['sha256'],'graphs':len(m['graphs']),
             'nodes':sum(len(g['nodes']) for g in m['graphs'].values()),'mismatches':problems,'oracle_boundaries':m['errors']}
        rows.append(row)
        if problems:mismatches.append(row)
        if len(rows)%200==0:print('Compared quest providers',len(rows),flush=True)
    write(path/'corpus_verification.json',{'status':'PASS_STRUCTURAL_AGREEMENT' if not mismatches else 'MISMATCH',
      'oracle':str(oracle),'oracle_sha256':sha(oracle),'oracle_common_sha256':sha(oracle.parent/'common.py'),
      'resources':len(rows),'mismatches':mismatches,'rows':rows,
      'limits':'Separate implementation comparison of graph/node/edge structure only. No runtime, condition-satisfiability or safe-resume certification.'})
    print(json.dumps({'resources':len(rows),'mismatches':len(mismatches)}))
    if mismatches:raise SystemExit(1)

if __name__=='__main__':main()
