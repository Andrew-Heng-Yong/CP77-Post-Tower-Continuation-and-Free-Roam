"""Build a queryable provider-pinned structural registry, without runtime writes."""
import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict, deque
from pathlib import Path
from model import effects, journal_refs, load_export, normalize, resource_refs, value, walk
from prepare import HERE, ROOT, read, sha, write

def j(x): return json.dumps(x, ensure_ascii=False, separators=(',',':'))

def depot_key(path):
    h=14695981039346656037
    for b in path.lower().replace('/','\\').encode('utf-8'):h=((h^b)*1099511628211)&0xffffffffffffffff
    return str(h)

def create_db(db):
    db.executescript('''
    CREATE TABLE resources(rid INTEGER PRIMARY KEY,depot TEXT,key TEXT,role TEXT,archive TEXT,sha256 TEXT,
      export_path TEXT,export_sha256 TEXT,status TEXT,error TEXT,root_type TEXT,support_json TEXT);
    CREATE INDEX resource_depot ON resources(depot);
    CREATE TABLE graphs(rid INT,path TEXT,kind TEXT,inputs_json TEXT,PRIMARY KEY(rid,path));
    CREATE TABLE nodes(rid INT,graph TEXT,id INT,type TEXT,from_any_input INT,parameters_json TEXT,sockets_json TEXT,
      PRIMARY KEY(rid,graph,id));
    CREATE TABLE edges(rid INT,graph TEXT,source INT,source_socket TEXT,source_type TEXT,
      destination INT,destination_socket TEXT,destination_type TEXT);
    CREATE INDEX edge_source ON edges(rid,graph,source);
    CREATE TABLE journals(rid INT,graph TEXT,node INT,path TEXT,class TEXT,operation TEXT);
    CREATE INDEX journal_path ON journals(path);
    CREATE TABLE journal_definitions(rid INT,path TEXT,class TEXT,parameters_json TEXT);
    CREATE INDEX journal_definition_path ON journal_definitions(path);
    CREATE TABLE refs(rid INT,graph TEXT,node INT,target TEXT);
    CREATE INDEX ref_target ON refs(target);
    CREATE TABLE calls(rid INT,graph TEXT,node INT,field TEXT,target TEXT);
    CREATE INDEX call_target ON calls(target);
    CREATE TABLE effects(rid INT,graph TEXT,node INT,type TEXT,parameters_json TEXT);
    CREATE TABLE features(rid INT,graph TEXT,node INT,kind TEXT,types_json TEXT);
    CREATE INDEX feature_resource ON features(rid);
    CREATE TABLE boundaries(rid INT,graph TEXT,node INT,kind TEXT,details_json TEXT);
    CREATE TABLE registrations(ordinal INT PRIMARY KEY,file TEXT,source_sha256 TEXT,binding_json TEXT);
    CREATE TABLE quests(id TEXT PRIMARY KEY,title TEXT,selection TEXT,category TEXT,journal_root TEXT,record_json TEXT);
    CREATE TABLE stages(quest_id TEXT,path TEXT,class TEXT,record_json TEXT,PRIMARY KEY(quest_id,path));
    CREATE TABLE quest_resources(quest_id TEXT,rid INT,association TEXT,PRIMARY KEY(quest_id,rid,association));
    CREATE TABLE script_mentions(quest_id TEXT,file TEXT,line INT,sha256 TEXT,role TEXT);
    ''')

def ingest(db, rows, start=0):
    for rid,r in enumerate(rows):
        if rid<start:continue
        status=r['status'];err=r.get('error');m=None
        if r.get('json'):
            assert sha(r['json'])==r['json_sha256'], r['json']
            try: m=normalize(load_export(r['json']))
            except (KeyError,ValueError,TypeError,RecursionError) as exc:
                status='NORMALIZATION_BLOCKED';err=repr(exc)
        db.execute('INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
          (rid,r['depot'],r['key'],r['role'],r['archive'],r['sha256'],r.get('json'),r.get('json_sha256'),status,err,r.get('root_type'),j(m['support']) if m else None))
        if not m:
            db.execute('INSERT INTO boundaries VALUES(?,?,?,?,?)',(rid,None,None,status,j(err)))
            continue
        for ref in resource_refs(m['support']): db.execute('INSERT INTO refs VALUES(?,?,?,?)',(rid,'support',None,ref))
        if m['root_type']=='gameJournalResource':
            def entry(x,parent):
                if not isinstance(x,dict):return
                path='/'.join(p for p in (parent,str(x.get('id',''))) if p)
                db.execute('INSERT INTO journal_definitions VALUES(?,?,?,?)',(rid,path,x.get('$type',''),j({k:v for k,v in x.items() if k!='entries'})))
                for child in x.get('entries',[]):entry(child,path)
            entry(m['support'].get('entry'), '')
        for embedded in m['support'].get('embedded_resources',[]):
            if embedded['scene_graph_unindexed']:
                db.execute('INSERT INTO boundaries VALUES(?,?,?,?,?)',(rid,None,None,'EMBEDDED_SCENE_UNINDEXED',j(embedded['depot'])))
        for g in m['graphs']:
            path=g['path']
            db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(rid,path,g['kind'],j(g['inputs'])))
            for n in g['nodes']:
                p=n['parameters'];nid=n['id'];typ=n['type']
                db.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?)',(rid,path,nid,typ,int(n['from_any_input']),j(p),j(n['sockets'])))
                op='WRITE' if any(x.get('$type')=='questJournalNodeDefinition' for x in walk(p)) else 'READ'
                for jp,cl in journal_refs(p):db.execute('INSERT INTO journals VALUES(?,?,?,?,?,?)',(rid,path,nid,jp,cl,op))
                for ref in resource_refs(p):db.execute('INSERT INTO refs VALUES(?,?,?,?)',(rid,path,nid,ref))
                for x in walk(p):
                    for field in ('phaseResource','sceneFile'):
                        if field in x:
                            for ref in resource_refs(x[field]):db.execute('INSERT INTO calls VALUES(?,?,?,?,?)',(rid,path,nid,field,ref))
                for e in effects(p):db.execute('INSERT INTO effects VALUES(?,?,?,?,?)',(rid,path,nid,e['$type'],j(e)))
                types=sorted({x.get('$type','') for x in walk(p)})
                groups={
                  'PREDICATE':('Condition','Comparison'), 'LOGICAL_JOIN':('Logical','Xor','XOR'),
                  'CHOICE':('ChoiceNode','ChoiceHub'), 'WAIT':('TimeCondition','PauseCondition','Delay','Timer'),
                  'CLEANUP_CONTROL':('CutControl','Deletion','Despawn','Disableable','Termination'),
                  'WORLD_SUPPORT':('Spawn','Community','Prefab','Workspot','Camera','EntityReference','NodeRef'),
                  'REWARD_OR_INVENTORY':('Reward','ItemManager','Inventory','Achievement')}
                for kind,tokens in groups.items():
                    found=[t for t in types if any(token in t for token in tokens)]
                    if found:db.execute('INSERT INTO features VALUES(?,?,?,?,?)',(rid,path,nid,kind,j(found)))
            for e in g['edges']:db.execute('INSERT INTO edges VALUES(?,?,?,?,?,?,?,?)',(rid,path,*e))
            fans=Counter((e[0],e[1],e[2]) for e in g['edges'] if e[2]=='Output' and e[5]=='Input')
            for (nid,sock,typ),number in fans.items():
                if number>1:db.execute('INSERT INTO features VALUES(?,?,?,?,?)',(rid,path,nid,'FANOUT',j({'socket':sock,'destinations':number})))
            for e in g.get('unresolved_scene_destinations',[]):
                db.execute('INSERT INTO boundaries VALUES(?,?,?,?,?)',(rid,path,e[0],'SCENE_DESTINATION_UNBOUND',j(e)))
            for e in g.get('unresolved_connections',[]):
                db.execute('INSERT INTO boundaries VALUES(?,?,?,?,?)',(rid,path,None,'NULL_CONNECTION_ENDPOINT',j(e)))
        if rid%200==0:
            db.commit();print('Indexed providers',rid,flush=True)
    db.commit()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='registry_01');ap.add_argument('--resume-index');args=ap.parse_args()
    out=HERE/args.output
    assert out.parent==HERE and not out.exists(), 'Fresh contained output required'
    capture=read(HERE/'evidence_02/capture.json');assert not capture['changed']
    prepared=read(HERE/'evidence_01/prepared.json')
    # Recheck exact Core/dependencies at analysis time. The source capture is pinned independently.
    for x in prepared['checks']:assert sha(x['path'])==x['sha256'],x['path']
    rows=[json.loads(l) for l in (HERE/'evidence_02/resources.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    assert len(rows)==capture['providers']
    registrations=read(HERE/'evidence_01/registrations.json');assert not registrations['errors']
    aliases=defaultdict(set)
    for r in rows:
        for name in [r['depot'],*r['imports']]:
            if '\\' in name:aliases[depot_key(name)].add(name.lower().replace('/','\\'))
    for r in registrations['phase_bindings']:
        for name in (r['binding']['path'],r['binding']['parent']):aliases[depot_key(name)].add(name.lower().replace('/','\\'))
    resolutions=[]
    for r in rows:
        names=aliases[r['key']]
        if len(names)==1:
            canonical=next(iter(names))
            if r['depot']!=canonical:resolutions.append({'key':r['key'],'original':r['depot'],'canonical':canonical})
            r['depot']=canonical
    out.mkdir();db=sqlite3.connect(out/'registry.sqlite3');db.row_factory=sqlite3.Row
    start=0
    if args.resume_index:
        previous=HERE/args.resume_index
        assert previous.parent==HERE and not (previous/'summary.json').exists()
        prev=sqlite3.connect((previous/'registry.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)
        assert prev.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert prev.execute('SELECT COUNT(*) FROM registrations').fetchone()[0]==0
        existing=prev.execute('SELECT rid,archive,key,sha256,export_sha256 FROM resources ORDER BY rid').fetchall()
        for rid,archive,key,h,export_h in existing:
            r=rows[rid];assert (archive,key,h,export_h)==(r['archive'],r['key'],r['sha256'],r.get('json_sha256'))
            if r.get('json'):assert sha(r['json'])==export_h
        start=len(existing);assert [r[0] for r in existing]==list(range(start))
        # The successor only handles null endpoints, which caused the predecessor to
        # abort before committing that provider. All successfully indexed rows took
        # the unchanged normal path. Preserve the failed index and validate its prefix.
        prev.backup(db);prev.close()
        write(out/'prefix_reuse.json',{'source':str(previous),'source_sha256':sha(previous/'registry.sqlite3'),
          'verified_prefix_providers':start,'normalizer_delta':'Retain literal null connection endpoints as boundaries; non-null normalization unchanged.'})
    else:create_db(db)
    ingest(db,rows,start)
    for i,r in enumerate(registrations['phase_bindings']):
        db.execute('INSERT INTO registrations VALUES(?,?,?,?)',(i,r['file'],r['sha256'],j(r['binding'])))
    providers=defaultdict(list)
    for rid,r in enumerate(rows):providers[r['depot']].append(rid)
    # Every provider remains visible. A different third-party override is never silently selected.
    winners={};collisions=[]
    for depot,ids in providers.items():
        mod=[i for i in ids if rows[i]['role']!='STOCK']
        cand=mod or ids
        hashes={rows[i]['sha256'] for i in cand}
        if len(hashes)==1:winners[depot]=cand[0]
        else:collisions.append({'depot':depot,'provider_ids':ids,'status':'PROVIDER_ORDER_REVIEW_REQUIRED'})
    calls=defaultdict(set)
    parents=defaultdict(list)
    for x in db.execute('SELECT * FROM calls'):
        parents[x['target']].append(dict(x))
        if x['target'] in winners:calls[x['rid']].add(winners[x['target']])
    root_closure={}
    for i,r in enumerate(registrations['phase_bindings']):
        if 'zzzz_PTFR_Combined.archive.xl' not in r['file']:continue
        target=r['binding']['path']
        if target not in winners:continue
        seen={winners[target]};todo=deque(seen)
        while todo:
            for child in calls[todo.popleft()]-seen:seen.add(child);todo.append(child)
        root_closure[i]=seen
    selection=read(HERE/'evidence_01/selection.json')
    snap={x['id']:x['index'] for x in prepared['snapshot']}
    scripts=[]
    game=Path(prepared['game_root'])
    for x in prepared['checks']:
        p=Path(x['path'])
        if p.suffix=='.reds':scripts.append((p,x['sha256'],p.read_text(encoding='utf-8-sig').splitlines()))
    records=[];by_id={}
    for q in selection['rows']:
        qid=q['id'];jp=q['journal_path']
        assert qid not in by_id,'Selection ID duplicated'
        related=[dict(x) for x in db.execute('SELECT * FROM journals WHERE path=? OR (path>=? AND path<?)',(jp,jp+'/',jp+'0'))]
        direct={x['rid'] for x in related}
        native={i for i in direct if rows[i]['role']=='STOCK'}
        private={i for i in direct if rows[i]['role']=='PTFR'}
        roots=[i for i,closure in root_closure.items() if closure&direct]
        installed=set().union(*(root_closure[i] for i in roots)) if roots else set()
        # Full graph context stays queryable, including unreachable inputs and sibling branches.
        # The registry intentionally does not equate resource closure with socket reachability.
        owner_calls=[]
        for i in sorted(native|private):
            for call in parents[rows[i]['depot']]:owner_calls.append(call)
        stages=defaultdict(list)
        for x in related:
            if x['class'] in ('gameJournalQuestPhase','gameJournalQuestObjective'):stages[x['path']].append(x)
        definitions=defaultdict(list)
        for x in db.execute('SELECT * FROM journal_definitions WHERE path=? OR (path>=? AND path<?)',(jp,jp+'/',jp+'0')):
            if x['class'] in ('gameJournalQuestPhase','gameJournalQuestObjective'):
                definitions[x['path']].append(dict(x));stages[x['path']]
        stage_rows=[]
        for path,sites in sorted(stages.items()):
            writes=[x for x in sites if x['operation']=='WRITE']
            for site in writes:
                node=db.execute('SELECT parameters_json FROM nodes WHERE rid=? AND graph=? AND id=?',(site['rid'],site['graph'],site['node'])).fetchone()
                params=json.loads(node[0])
                site['optional_flags']=[x['optional'] for x in walk(params) if x.get('$type')=='questJournalQuestEntry_NodeType']
                site['incoming_sockets']=[x[0] for x in db.execute('SELECT DISTINCT destination_socket FROM edges WHERE rid=? AND graph=? AND destination=?',(site['rid'],site['graph'],site['node']))]
            row={'path':path,'class':sites[0]['class'] if sites else definitions[path][0]['class'],'sites':sites,
              'journal_definitions':definitions[path],
              'journal_writers':writes,'resume_status':'REQUIRES_STAGE_OWNER_AND_EFFECT_REVIEW',
              'ordering':'Use source edges and predicates; journal path order is not execution order.'}
            db.execute('INSERT INTO stages VALUES(?,?,?,?)',(qid,path,row['class'],j(row)))
            stage_rows.append({'path':path,'class':row['class'],'sites':len(sites),'writers':len(writes)})
        mentions=[]
        for p,h,lines in scripts:
            for no,line in enumerate(lines,1):
                if '"'+qid+'"' in line or '"'+jp+'"' in line:
                    role='SNAPSHOT' if p.name=='PTFR_HistorySnapshotHS1.reds' else 'SCRIPT_REFERENCE'
                    db.execute('INSERT INTO script_mentions VALUES(?,?,?,?,?)',(qid,str(p),no,h,role))
                    mentions.append({'file':p.name,'line':no,'role':role})
        issues=[]
        if q['decision']=='INCLUDE' and not roots:issues.append('NO_REGISTERED_PHASE_RESOURCE_PATH_BOUND')
        if q['decision']=='INCLUDE' and not native:issues.append('NATIVE_JOURNAL_OWNER_NOT_BOUND')
        if q['decision']=='INCLUDE' and not stages:issues.append('NO_STAGE_JOURNAL_REFERENCE_BOUND')
        if q['decision']=='INCLUDE' and qid not in snap:issues.append('NOT_IN_SNAPSHOT_CATALOGUE')
        if q['decision']!='INCLUDE' and qid in snap:issues.append('SNAPSHOT_ROW_OUTSIDE_CURRENT_SELECTION')
        feature_counts=Counter();feature_sites=defaultdict(list)
        for rid in sorted(direct|installed):
            for feature in db.execute('SELECT graph,node,kind FROM features WHERE rid=?',(rid,)):
                feature_counts[feature['kind']]+=1
                feature_sites[feature['kind']].append({'rid':rid,'graph':feature['graph'],'node':feature['node']})
        record={'id':qid,'title':q['title'],'category':q['category'],'selection':q['decision'],
          'journal_root':jp,'selection_requirements':q.get('requirements'),'selection_reason':q.get('reason'),
          'snapshot_index':snap.get(qid),'stages':stage_rows,'native_journal_resources':sorted(native),
          'private_journal_resources':sorted(private),'registered_resource_paths':roots,
          'parent_call_sites':owner_calls,'script_mentions':mentions,'findings':issues,
          'feature_counts':dict(feature_counts),'feature_sites':dict(feature_sites),
          'ownership_status':'STATIC_CALLERS_ONLY; saved/native liveness and released support remain unqualified',
          'stage_coverage_status':'SOURCE_CENSUS; exact entry sockets, stage combinations and safe seams require review',
          'reward_status':'Effect nodes indexed by exact provider/graph/node; one-time receipt review required',
          'installed_path_status':'Registration plus syntactic phase/scene references; not an executing-owner proof'}
        for i in direct:db.execute('INSERT INTO quest_resources VALUES(?,?,?)',(qid,i,'DIRECT_JOURNAL_REFERENCE'))
        for i in installed:db.execute('INSERT INTO quest_resources VALUES(?,?,?)',(qid,i,'REGISTERED_RESOURCE_CLOSURE'))
        db.execute('INSERT INTO quests VALUES(?,?,?,?,?,?)',(qid,q['title'],q['decision'],q['category'],jp,j(record)))
        by_id[qid]=record;records.append(record)
    snapshot_unmapped=sorted(set(snap)-set(by_id))
    db.commit()
    counts={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in
      ['resources','graphs','nodes','edges','journals','journal_definitions','calls','effects','features','registrations','quests','stages','boundaries']}
    selected=[r for r in records if r['selection']=='INCLUDE']
    summary={'schema':1,'status':'STRUCTURAL_REGISTRY_BUILT_SEMANTIC_STAGE_REVIEW_PENDING',
      'core_epoch':prepared['core_epoch'],'counts':counts,
      'selected_counts':dict(Counter(r['category'] for r in selected)),
      'selection_counts':selection['counts'],'snapshot_rows':len(snap),'snapshot_unmapped':snapshot_unmapped,
      'selected_without_snapshot':[r['id'] for r in selected if r['snapshot_index'] is None],
      'snapshot_outside_selection':[r['id'] for r in records if r['snapshot_index'] is not None and r['selection']!='INCLUDE'],
      'selected_without_registered_path':[r['id'] for r in selected if not r['registered_resource_paths']],
      'selected_without_native_binding':[r['id'] for r in selected if not r['native_journal_resources']],
      'selected_without_stage_refs':[r['id'] for r in selected if not r['stages']],
      'provider_collisions':collisions,'source_capture_sha256':sha(HERE/'evidence_02/resources.jsonl'),
      'resource_name_resolutions':resolutions,
      'selection_sha256':prepared['selection_sha256'],'game_writes':0,'save_writes':0,
      'remaining_work':['Resolve actual entry sockets across registered roots, nested phases and scene calls.',
        'Classify optional routes, parallel stage combinations and reward receipts in their path context.',
        'Review source boundaries and native/saved owner and support contracts per quest.',
        'Reconcile separate-scope restored activities without expanding excluded quest selection.']}
    write(out/'registry.json',{'schema':1,'records':records})
    write(out/'summary.json',summary)
    db.close()
    write(out/'manifest.json',{'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()},
      'tools':{p.name:sha(p) for p in HERE.glob('*.py')}})
    print(json.dumps({k:summary[k] for k in ('status','counts','selected_counts','selected_without_snapshot',
      'snapshot_outside_selection','selected_without_registered_path','selected_without_native_binding','selected_without_stage_refs')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
