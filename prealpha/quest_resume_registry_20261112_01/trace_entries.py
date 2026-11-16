"""Follow caller-selected input sockets; retain unresolved/default-entry boundaries.

All conditions are MAY branches. Source connectivity is not runtime admission,
return-path feasibility, timed concurrency, or saved-owner execution evidence.
"""
import argparse
import json
import sqlite3
from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path
from model import value
from prepare import HERE, read, sha, write

def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))

class Tracer:
    def __init__(self,db):
        self.db=db;self.db.row_factory=sqlite3.Row
        self.resources={r['rid']:dict(r) for r in db.execute('SELECT rid,depot,key,role,sha256,status FROM resources')}
        by_depot=defaultdict(list)
        for r in self.resources.values():by_depot[r['depot']].append(r)
        self.winners={}
        for depot,rs in by_depot.items():
            candidates=[r for r in rs if r['role']!='STOCK'] or rs
            if len({r['sha256'] for r in candidates})==1:
                self.winners[depot]=next((r['rid'] for r in candidates if r['status'] not in ('OPAQUE','NORMALIZATION_BLOCKED')),candidates[0]['rid'])
                keys={r['key'] for r in candidates}
                if len(keys)==1:self.winners[next(iter(keys))]=self.winners[depot]

    @lru_cache(maxsize=128)
    def graph(self,rid,path):
        row=self.db.execute('SELECT * FROM graphs WHERE rid=? AND path=?',(rid,path)).fetchone()
        if row is None:return None
        nodes={n['id']:dict(n) for n in self.db.execute('SELECT * FROM nodes WHERE rid=? AND graph=?',(rid,path))}
        for n in nodes.values():n['parameters']=json.loads(n.pop('parameters_json'));n['sockets']=json.loads(n.pop('sockets_json'))
        edges=[dict(e) for e in self.db.execute('SELECT * FROM edges WHERE rid=? AND graph=?',(rid,path))]
        entries={}
        if row['kind']=='quest':
            for n in nodes.values():
                if n['type'] in ('questInputNodeDefinition','questStartNodeDefinition'):
                    name=str(value(n['parameters'].get('socketName','')))
                    entries.setdefault(name,[]).append(n['id'])
        else:
            support=json.loads(self.db.execute('SELECT support_json FROM resources WHERE rid=?',(rid,)).fetchone()[0])
            for e in support.get('entryPoints',[]):entries.setdefault(str(value(e['name'])),[]).append(value(e['nodeId']))
        return {'kind':row['kind'],'nodes':nodes,'edges':edges,'entries':entries}

    def trace(self,root):
        unresolved=[];reached=set();contexts=set();todo=[];links=[]
        rid=self.winners.get(root.lower().replace('/','\\'))
        if rid is None:return contexts,reached,links,[{'kind':'ROOT_PROVIDER_UNRESOLVED','root':root}]
        g=self.graph(rid,'root')
        if not g:return contexts,reached,links,[{'kind':'ROOT_GRAPH_UNRESOLVED','rid':rid}]
        if len(g['entries'])!=1:unresolved.append({'kind':'DEFAULT_INPUT_AMBIGUOUS','rid':rid,'entries':g['entries']})
        def add(r,p,e):
            context=(r,p,e)
            if context not in contexts:contexts.add(context);todo.append(context)
        for entry in g['entries']:add(rid,'root',entry)
        while todo:
            r,path,entry=todo.pop();g=self.graph(r,path)
            if not g or entry not in g['entries']:
                unresolved.append({'kind':'INPUT_UNRESOLVED','rid':r,'graph':path,'entry':entry});continue
            if len(g['entries'][entry])!=1:
                unresolved.append({'kind':'DUPLICATE_INPUT_NAME','rid':r,'graph':path,'entry':entry})
            adj=defaultdict(list)
            for e in g['edges']:
                if e['source_type']=='Output' and e['destination_type']=='Input':adj[e['source']].append(e)
            local=set(g['entries'][entry]);queue=deque(local);incoming=defaultdict(set)
            while queue:
                n=queue.popleft()
                for e in adj[n]:
                    incoming[e['destination']].add(e['destination_socket'])
                    if e['destination'] not in local:local.add(e['destination']);queue.append(e['destination'])
            for nid in local:
                if nid not in g['nodes']:
                    unresolved.append({'kind':'NODE_UNRESOLVED','rid':r,'graph':path,'node':nid});continue
                reached.add((r,path,nid));n=g['nodes'][nid];p=n['parameters'];inputs=incoming[nid]
                child=path+'/'+str(nid);child_graph=self.graph(r,child)
                callp=p
                if n['type']=='scnQuestNode':
                    callp=p.get('questNode') or {}
                    # Port conversion is required only for dispatch into a quest
                    # subgraph. Ordinary embedded action/condition parameters and
                    # their scene socket stamps remain in the source index.
                    if child_graph or any(field in callp for field in ('phaseResource','sceneFile')):
                        mapped=set()
                        for inp in inputs:
                            stamp=json.loads(inp);ordinal=stamp.get('ordinal',0);names=p.get('isockMappings',[])
                            if stamp.get('name',0)==0 and ordinal<len(names):mapped.add(str(value(names[ordinal])))
                            else:unresolved.append({'kind':'SCENE_INPUT_MAPPING_UNRESOLVED','rid':r,'graph':path,'node':nid,'stamp':stamp})
                        inputs=mapped
                    else:inputs=set()
                if child_graph:
                    for inp in inputs:
                        add(r,child,inp);links.append({'caller':[r,path,nid],'target':[r,child,inp],'kind':'INLINE'})
                for field,graph in [('phaseResource','root'),('sceneFile','scene')]:
                    ref=callp.get(field) or {};target=str(value(ref.get('DepotPath',''))).lower().replace('/','\\')
                    if target in ('','0','none'):continue
                    dest=self.winners.get(target)
                    if dest is None:
                        unresolved.append({'kind':'CALL_PROVIDER_UNRESOLVED','rid':r,'graph':path,'node':nid,'target':target});continue
                    for inp in inputs:
                        add(dest,graph,inp);links.append({'caller':[r,path,nid],'target':[dest,graph,inp],'kind':field})
        return contexts,reached,links,unresolved

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--registry',default='registry_01');ap.add_argument('--output',default='routes_01');a=ap.parse_args()
    source=HERE/a.registry;out=HERE/a.output
    assert out.parent==HERE and not out.exists()
    out.mkdir();db=sqlite3.connect((source/'registry.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);t=Tracer(db)
    result=sqlite3.connect(out/'routes.sqlite3')
    result.executescript('''CREATE TABLE roots(ordinal INT PRIMARY KEY,depot TEXT,binding_json TEXT);
      CREATE TABLE contexts(root INT,rid INT,graph TEXT,entry TEXT);
      CREATE TABLE reached(root INT,rid INT,graph TEXT,node INT);
      CREATE INDEX reached_node ON reached(rid,graph,node);
      CREATE TABLE links(root INT,record_json TEXT);
      CREATE TABLE boundaries(root INT,record_json TEXT);
      CREATE TABLE quest_routes(quest_id TEXT,root INT,source_sites INT,stage_sites INT);''')
    root_counts=[];all_boundaries=[]
    for reg in db.execute('SELECT * FROM registrations'):
        if 'zzzz_PTFR_Combined.archive.xl' not in reg['file']:continue
        binding=json.loads(reg['binding_json']);root=binding['path'];ordinal=reg['ordinal']
        contexts,nodes,links,unknown=t.trace(root)
        result.execute('INSERT INTO roots VALUES(?,?,?)',(ordinal,root,j(binding)))
        result.executemany('INSERT INTO contexts VALUES(?,?,?,?)',[(ordinal,*c) for c in contexts])
        result.executemany('INSERT INTO reached VALUES(?,?,?,?)',[(ordinal,*c) for c in nodes])
        result.executemany('INSERT INTO links VALUES(?,?)',[(ordinal,j(x)) for x in links])
        result.executemany('INSERT INTO boundaries VALUES(?,?)',[(ordinal,j(x)) for x in unknown])
        all_boundaries.extend({'registration_ordinal':ordinal,**u} for u in unknown)
        root_counts.append({'ordinal':ordinal,'depot':root,'contexts':len(contexts),'nodes':len(nodes),'boundaries':len(unknown)})
        if len(root_counts)%100==0:result.commit();print('Traced roots',len(root_counts),flush=True)
    missing=[];quest_summary=[];known_roots=set()
    for q in db.execute('SELECT id,title,selection,journal_root FROM quests'):
        known_roots.add(q['journal_root'])
        jp=q['journal_root'];sites=[dict(r) for r in db.execute('SELECT * FROM journals WHERE path=? OR (path>=? AND path<?)',(jp,jp+'/',jp+'0'))]
        counts=defaultdict(lambda:[0,0])
        for site in sites:
            for row in result.execute('SELECT DISTINCT root FROM reached WHERE rid=? AND graph=? AND node=?',(site['rid'],site['graph'],site['node'])):
                counts[row[0]][0]+=1
                if site['class'] in ('gameJournalQuestPhase','gameJournalQuestObjective'):counts[row[0]][1]+=1
        result.executemany('INSERT INTO quest_routes VALUES(?,?,?,?)',[(q['id'],r,*v) for r,v in counts.items()])
        quest_summary.append({'id':q['id'],'title':q['title'],'selection':q['selection'],'root_ordinals':sorted(counts)})
        if q['selection']=='INCLUDE' and not counts:missing.append(q['id'])
    extra=defaultdict(list)
    for site in db.execute("SELECT * FROM journals WHERE class='gameJournalQuest'"):
        if site['path'] in known_roots:continue
        bound=[r[0] for r in result.execute('SELECT DISTINCT root FROM reached WHERE rid=? AND graph=? AND node=?',(site['rid'],site['graph'],site['node']))]
        if bound:extra[site['path']].append({**dict(site),'root_ordinals':bound})
    unknown_scope=[{'journal_root':path,'classification':'SCOPE_REVIEW_REQUIRED' if any(x['operation']=='WRITE' for x in sites) else 'PREREQUISITE_REFERENCE_ONLY',
                   'sites':sites} for path,sites in sorted(extra.items())]
    result.commit();result.close();db.close()
    write(out/'summary.json',{'status':'CALLER_SOCKET_MAY_CLOSURE','source_registry_sha256':sha(source/'registry.sqlite3'),
       'root_counts':root_counts,'quest_routes':quest_summary,'selected_without_connected_journal_site':missing,
       'uncatalogued_connected_quest_roots':unknown_scope,
       'boundaries':all_boundaries,'limits':['Conditions and caller return feasibility are unsolved.',
       'Ambiguous root default inputs are traced separately and flagged.',
       'Connected source paths do not prove installed admission, saved owners, support liveness or safe resume entry.']})
    print(j({'roots':len(root_counts),'boundaries':len(all_boundaries),'selected_without_connected_journal_site':missing}))

if __name__=='__main__':main()
