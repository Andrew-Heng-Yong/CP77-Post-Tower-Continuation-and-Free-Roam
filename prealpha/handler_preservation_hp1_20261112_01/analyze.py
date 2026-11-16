"""Three-case source and actual saved-registration experiment, without runtime writes."""
from collections import defaultdict
from functools import lru_cache
import json,sqlite3,struct,sys
from pathlib import Path
from prepare import HERE,ROOT,REGISTRY,CASES,read,write,sha

sys.path.insert(0,str(REGISTRY))
from model import normalize,load_export

TARGETS={'mq007_smartgun':6542,'q304_car_retrieval':12821,'mq029_tourist':9197}
ROOTS={9717:0,13718:1}

def phase_hash(path):
    assert path and path[0] in (0,1)
    result=(0x811C9DC5,0x01800013)[path[0]]
    for x in path:
        for b in struct.pack('<H',x):result=((result^b)*0x01000193)&0xFFFFFFFF
    return result

def framed(raw,node,stride):
    if len(raw)<8 or struct.unpack_from('<I',raw)[0]!=node:raise ValueError('Wrong component ID')
    n=struct.unpack_from('<I',raw,4)[0]
    if len(raw)!=8+n*stride:raise ValueError('Wrong component length')
    return raw[8:]

def paths(raw,node):
    b=framed(raw,node,2);words=struct.unpack('<'+'H'*(len(b)//2),b);at=0;out=[]
    while at<len(words):
        n=words[at];at+=1
        if n==0 or at+n>len(words):raise ValueError('Invalid path length')
        out.append(tuple(words[at:at+n]));at+=n
    return out

def freezer(raw,node):
    at=0
    def take(fmt):
        nonlocal at
        s=struct.Struct('<'+fmt)
        if at+s.size>len(raw):raise ValueError('Truncated freezer')
        v=s.unpack_from(raw,at);at+=s.size;return v
    def key(n):
        if n&0xFFFF0000:raise ValueError('Discarded high node bits')
        return n>>32,n&0xFFFF
    ident,size,count=take('III')
    if ident!=node or size!=len(raw)-8 or count>(len(raw)-at)//20:raise ValueError('Invalid freezer header')
    out=[]
    for _ in range(count):
        trigger,owner,n=take('QQI');members=[]
        if n>(len(raw)-at)//12:raise ValueError('Invalid members')
        for _ in range(n):
            member,words=take('QI')
            if words>(len(raw)-at)//8:raise ValueError('Invalid deferred words')
            members.append({'key':key(member),'inputs':take(f'{words}Q')})
        out.append({'trigger':str(trigger),'owner':key(owner),'members':members})
    if at!=len(raw):raise ValueError('Trailing freezer bytes')
    return out

def main():
    out=HERE/'analysis_01';assert not out.exists();out.mkdir()
    plan=read(HERE/'evidence_01/inputs.json');db=sqlite3.connect(Path(plan['registry']).as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    resources={r['rid']:dict(r) for r in db.execute('select * from resources')}
    stock={r['depot']:i for i,r in resources.items() if r['role']=='STOCK'}
    private={r['depot']:i for i,r in resources.items() if r['role']=='PTFR'}
    bydepot={**stock,**private};calls=[dict(r) for r in db.execute('select * from calls')]
    incoming=defaultdict(list);outgoing=defaultdict(list)
    for r in calls:incoming[r['target']].append(r);outgoing[r['rid']].append(r)
    @lru_cache(None)
    def node(rid,graph,num):
        row=db.execute('select type,parameters_json from nodes where rid=? and graph=? and id=?',(rid,graph,num)).fetchone()
        return {'rid':rid,'depot':resources[rid]['depot'],'graph':graph,'node':num,'type':row['type'],'parameters':json.loads(row['parameters_json'])}
    def ancestry(rid,graph='root',seen=()):
        marker=(rid,graph)
        if marker in seen:return []
        if graph!='root':
            if not graph.startswith('root/'):return []
            parent,num=graph.rsplit('/',1);result=[]
            for row in ancestry(rid,parent,seen+(marker,)):
                result.append({'path':row['path']+[int(num)],'steps':row['steps']+[node(rid,parent,int(num))]})
            return result
        if rid in ROOTS:return [{'path':[ROOTS[rid]],'steps':[]}]
        result=[]
        for call in incoming[resources[rid]['depot']]:
            if resources[call['rid']]['role']!='STOCK' or call['field']!='phaseResource':continue
            for row in ancestry(call['rid'],call['graph'],seen+(marker,)):
                result.append({'path':row['path']+[call['node']],'steps':row['steps']+[node(call['rid'],call['graph'],call['node'])]})
        return result
    def closure(seed):
        todo=[seed];result=set()
        while todo:
            rid=todo.pop()
            if rid in result:continue
            result.add(rid)
            for call in outgoing[rid]:
                if call['target'] in bydepot:todo.append(bydepot[call['target']])
        return result
    packets={};needed=set()
    for qid,target in TARGETS.items():
        q=json.loads(db.execute('select record_json from quests where id=?',(qid,)).fetchone()[0])
        routes=ancestry(target);assert len(routes)==1,(qid,routes)
        descendants=closure(target);needed|=descendants|{s['rid'] for s in routes[0]['steps']}
        regs=[dict(db.execute('select * from registrations where ordinal=?',(i,)).fetchone()) for i in q['registered_resource_paths']]
        for r in regs:r['binding']=json.loads(r.pop('binding_json'))
        privates=set(q['private_journal_resources'])
        for r in regs:
            depot=r['binding'].get('path')
            if depot in private:privates|=closure(private[depot])
        needed|=privates
        packets[qid]={'title':q['title'],'case':CASES[qid],'native_root_rid':target,'route':routes[0],'native_body_resources':sorted(descendants),'private_resources':sorted(privates),'registrations':regs}
    # Keep the actual outer cuts and pickup/cleanup graph evidence in the packet.
    for r in resources.values():
        if r['role']=='STOCK' and r['depot'].endswith(('\\q307.quest','\\q307_01_pickup.questphase','\\q307_cleanup.questphase','\\ep1.questphase','\\cyberpunk2077.questphase')):needed.add(r['rid'])
    source_rows=[];source_graphs={}
    for rid in sorted(needed):
        r=resources[rid];assert r['export_path'] and sha(r['export_path'])==r['export_sha256'],r['depot']
        m=normalize(load_export(r['export_path']))
        for g in m['graphs']:
            for n in g['nodes']:
                indexed=node(rid,g['path'],n['id']);assert n['type']==indexed['type'] and n['parameters']==indexed['parameters']
            expected=[tuple(row) for row in db.execute('select source,source_socket,source_type,destination,destination_socket,destination_type from edges where rid=? and graph=?',(rid,g['path']))]
            assert sorted(expected)==sorted(g['edges'])
        source_rows.append({k:r[k] for k in ('rid','depot','key','role','archive','sha256','export_path','export_sha256')})
        source_graphs[str(rid)]=m
    write(out/'sources.json',source_rows);write(out/'graphs.json',source_graphs)
    results={}
    for fixture in plan['saves']:
        folder=HERE/'saves_01'/fixture['slot'];m=read(folder/'manifest.json');assert m['source_sha256']==fixture['source_sha256']
        raw={};ids={}
        for r in m['nodes']:
            assert sha(r['path'])==r['sha256'];raw[r['name']]=Path(r['path']).read_bytes();ids[r['name']]=r['id']
        assert m['save_version']>=139 and m['root_gap_hex']=='026B577A51814903CAE118A84B9942C8C4'
        catalog=paths(raw['customArray'],ids['customArray']);events=list(struct.iter_unpack('<QII',framed(raw['eventManager'],ids['eventManager'],16)))
        frozen=freezer(raw['questPhaseFreezer'],ids['questPhaseFreezer']);hashes=defaultdict(set)
        for p in catalog:hashes[phase_hash(p)].add(p)
        cases={}
        for qid,p in packets.items():
            prefix=tuple(p['route']['path']);subpaths={x for x in catalog if x[:len(prefix)]==prefix};keys={phase_hash(x) for x in subpaths}
            assert all(len(hashes[k])==1 for k in keys)
            rows=[{'slot':i,'type_token':str(t),'phase_hash':h,'node':n,'path':list(next(iter(hashes[h])))} for i,(t,h,n) in enumerate(events) if h in keys and t and n!=0xFFFF]
            ancestors=[]
            for index,n in enumerate(prefix[1:],1):
                parent=prefix[:index];h=phase_hash(parent);assert len(hashes[h])<=1
                members=[{'slot':i,'type_token':str(t),'node':v} for i,(t,k,v) in enumerate(events) if k==h and v==n and t]
                ancestors.append({'parent':parent,'node':n,'rows':members})
            freeze_rows=[g for g in frozen if g['owner'][0] in keys or any(r['key'][0] in keys for r in g['members']) or any(g['owner']==(phase_hash(prefix[:i]),prefix[i]) for i in range(1,len(prefix)))]
            cases[qid]={'root_path':prefix,'catalog_paths':len(subpaths),'handler_count':len(rows),'handlers':rows,'ancestor_handlers':ancestors,'freezer_groups':freeze_rows}
        results[fixture['slot']]={'source_sha256':fixture['source_sha256'],'facts':m['facts'],'journals':m['journals'],'cases':cases,'total_handlers':sum(bool(t and n!=0xFFFF) for t,h,n in events),'total_freezer_groups':len(frozen)}
    write(out/'cases.json',packets);write(out/'save_comparison.json',results)
    for qid,p in packets.items():
        print(json.dumps({'quest':p['title'],'native_path':p['route']['path'],'native_resources':len(p['native_body_resources']),'private_resources':len(p['private_resources']),'saves':{k:{'handlers':s['cases'][qid]['handler_count'],'catalog_paths':s['cases'][qid]['catalog_paths'],'freezer_groups':len(s['cases'][qid]['freezer_groups'])} for k,s in results.items()}}))
    print('Source exports independently parsed and graph-index compared:',len(source_rows))

if __name__=='__main__':main()
