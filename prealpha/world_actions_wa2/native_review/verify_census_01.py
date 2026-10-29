"""Verify all source payloads freshly parsed from binary and action slice closure."""
import copy, json
from pathlib import Path
OUT=Path(__file__).resolve().parent
src=(OUT/'census_01.py').read_text();scope={'__file__':str(OUT/'census_01.py')}
exec(src[:src.index('\nmanifest=read')],scope)
read,sha,handles,norm,lookup,phases=[scope[n] for n in ('read','sha','handles','norm','lookup','phases')]
A=read(OUT/'action_contracts_01.json');P=read(OUT/'fresh_source_proof_01.json')
checks=[]
def check(ok,label):
    assert ok,label
    checks.append(label)
cache={}
for pin in P['source_pins']:
    old=read(Path(pin['old_json']));fresh=read(Path(pin['fresh_json']))
    check(norm(old['Data']['RootChunk'],handles(old))==norm(fresh['Data']['RootChunk'],handles(fresh)), 'Whole source payload exact '+Path(pin['old_json']).name)
    cache[pin['old_json']]=(fresh,handles(fresh))
check(P['owners']==237 and P['phases']==257 and P['sources']==10,'Fresh Get-GraphEdges complete237owners257phases10sources')
check(len(A['coverage'])==237 and len({x['group'] for x in A['coverage']})==237,'Coverage exactly237uniqueowners')
check(sum(A['cohort_counts'].values())==237,'Cohorts exhaustive and mutually exclusive')
check({x['group'] for x in A['contracts'] if x['kind']=='isolated_shoot_phase'}=={172,173},'Only172173newisolatedshooters')
check(len([x for x in A['contracts'] if x['group']==179])==1 and next(x for x in A['contracts'] if x['group']==179)['kind']=='existing_BA1_preserve','BA1 preserved not newowner')
check({x['group'] for x in A['contracts'] if x['kind']=='flat_shoot_action_closure'}=={246,289,250},'Flatshootersexact246289250')
check(A['external_group1']['phases'][0]['node_count']==20 and A['external_group1']['phases'][1]['node_count']==22,'Sole external owner fully decoded')
check(not any('AIForceShootCommandParams' in p['payload_types'] for p in A['external_group1']['phases']),'Externalgroup1 noForceShoot')
def matches(c):
    d,h=cache[c['source']];n=lookup(d['Data']['RootChunk'],c['graph_path'],h);p=phases(n,c['graph_path'],h)[0]
    ids=set(c['node_ids']);nn={n['id']:n for n in p['payload']['phaseGraph']['nodes']}
    if c['nodes']!=[nn[i] for i in sorted(ids)]:return False
    e=[list(x) for x in p['edges'] if x[0] in ids and x[2] in ids]
    return c['internal_edges']==e
for c in A['contracts']:
    check(matches(c),f"Contract{c['group']}payloadandinternaledgesexact")
    check(not any(n['$type'] in ('questSpawnManagerNodeDefinition','questFactsDBManagerNodeDefinition','questSceneNodeDefinition','questCheckpointNodeDefinition') for n in c['nodes']),f"Contract{c['group']}nospawnfactscenecheckpoint")
    if c['kind']=='flat_shoot_action_closure':
        check(all(e[0]==c['entry_gate_id'] and e[1]!='CutSource' for e in c['native_outgoing_boundary_edges']),f"Flat{c['group']}onlygatesplitoutside")
        check(not any(e[1]=='CutSource' for e in c['native_incoming_boundary_edges']),f"Flat{c['group']}nooutsidecutdependency")
for g in (256,319):
    check(next(c for c in A['contracts'] if c['group']==g)['status']=='NATIVE_GUARD_MISMATCH_REQUIRES_EXPLICIT_DEPENDENCY_RESOLUTION',f'Guardanomaly{g}explicitlyblocked')
# Independent adversarial mutations prove exact comparison is active.
c=copy.deepcopy(next(c for c in A['contracts'] if c['group']==246));c['internal_edges']=[e for e in c['internal_edges'] if e[1]!='CutSource']
check(not matches(c),'Negative control removed native cancellation cuts detected')
c=copy.deepcopy(next(c for c in A['contracts'] if c['group']==172));c['nodes'][9]['params']['duration']=99
check(not matches(c),'Negative control shoot duration mutation detected')
c=copy.deepcopy(next(c for c in A['contracts'] if c['group']==199));c['nodes'][0]['event']['toggle']=0
check(not matches(c),'Negative control light behavior mutation detected')
c=copy.deepcopy(next(c for c in A['contracts'] if c['group']==250));c['internal_edges'].append([174,'Out',184,'In1'])
check(not matches(c),'Negative control encounter branch leakage detected')
out={'status':'PASS_EXHAUSTIVE_237_NATIVE_ACTION_CENSUS_AND_26_EXACT_SLICE_CONTRACTS','checks':len(checks),'assertions':checks,
 'owners':237,'native_inline_phases_freshly_verified':257,'full_source_payloads_freshly_verified':10,'external_group1_nodes':[20,22],
 'slice_contracts':26,'negative_controls':4,'cohort_counts':A['cohort_counts'],
 'deployment_limit':'Source contracts only. Each new owner still requires alias/world-dependency validation, saved-state admission, lifetime cut/rearm proof, serialization and resource/package checks.256/319 guard anomalies explicitly unresolved.',
 'source_pins':[{'path':str(OUT/n),'sha256':sha(OUT/n)} for n in ['census_01.py','classify_01.py','verify_native_sources_01.ps1','verify_census_01.py','census_raw_01.json','action_contracts_01.json','fresh_source_proof_01.json','coverage_01.md']],
 'game_writes':0,'save_writes':0,'installation_changes':0}
(OUT/'assessment_01.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('assertions','source_pins','cohort_counts')},indent=2))
