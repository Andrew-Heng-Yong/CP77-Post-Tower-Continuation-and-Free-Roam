"""Qualify isolated native community aliases and apply reviewed field corrections."""
from pathlib import Path
import json, hashlib
HERE=Path(__file__).resolve().parent
C=HERE/'candidate_01'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
contracts=read(HERE/'native_review/action_contracts_02.json')['contracts']
environment=read(HERE/'environment_review/assessment_01.json')
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
for contract in contracts:
    group=contract['group']
    if group in (172,173,179): continue # Separate independently checked owner builders.
    revision='02' if 'vehicle' in contract['kind'] else '01'
    src=C/f'owner_{group}_unqualified_{revision}.json'
    dst=C/f'owner_{group}_qualified_{revision}.json'
    if dst.exists(): continue
    data=read(src)
    community=(read(HERE/'coverage_review/support_assessment_01.json')['candidate250']['community_ref']
               if group==250 else contract['community_refs'][0])
    assert community.startswith('$/'), (group,community)
    changes=[]
    for node in walk(data):
        if node.get('$type')=='NodeRef':
            old=node['$value']
            if old.startswith('#') and old!='#player':
                assert 'com' in old, (group,old)
                node['$value']=community
                changes.append({'old':old,'new':community,'reason':'qualify native owner-local community alias'})
    if group==246:
        corrections=environment['required_candidate_corrections']
        controller=next(n for n in walk(data) if n.get('$type')=='questPhaseNodeDefinition' and n.get('id')==60000)
        for correction in corrections:
            node=next(n for n in controller['phaseGraph']['Data']['nodes'] if n['Data']['id']==correction['node'])['Data']
            field=node['condition']['Data']['type']['Data']['objectRef']
            assert field['$type']=='NodeRef' and field['$value']==correction['old']
            field['$value']=correction['new']
            changes.append(correction)
    if group in (256,319):
        reviewed=read(HERE/'environment_review/community_rebinds_01.json')
        assert reviewed['status']=='PASS_EXACT_256_319_COMMUNITY_REBINDS'
        controller=next(n for n in walk(data) if n.get('$type')=='questPhaseNodeDefinition' and n.get('id')==60000)
        nodes={n['Data']['id']:n['Data'] for n in controller['phaseGraph']['Data']['nodes']}
        corrections=[r for r in reviewed['required_candidate_corrections'] if r['group']==group and r['node'] in contract['node_ids'] and r['graph']==contract['graph_path']]
        assert len(corrections)==(2 if group==256 else 1)
        for correction in corrections:
            fields=[n for n in walk(nodes[correction['node']]) if n.get('$type')=='NodeRef' and n.get('$value')==correction['old']]
            assert len(fields)==1
            fields[0]['$value']=correction['new']
            changes.append(correction)
    dst.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    proof={'status':'WA2_EXPLICIT_REFERENCE_PATCHES','group':group,'changes':changes,
           'input_sha256':digest(src),'output_sha256':digest(dst),
           'contract_sha256':digest(HERE/'native_review/action_contracts_02.json')}
    (C/f'owner_{group}_qualification_{revision}.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(f'Qualified {group}: {len(changes)} fields')
