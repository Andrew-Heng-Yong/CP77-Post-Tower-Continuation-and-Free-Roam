"""Independent bounded source review. Writes only a fresh review evidence folder."""
from pathlib import Path
import argparse, collections, copy, hashlib, json, sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sys.path.insert(0,str(WORK/'tools/parity_audit'))
from model import Resource

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    out=HERE/args.out
    assert out.parent==HERE and not out.exists()
    manifest=WORK/'prealpha/quest_restoration_qr15/providers_01/manifest.json'
    inp=read(manifest);assert not inp['missing']
    by=collections.defaultdict(list)
    for r in inp['resources']:by[r['depot']].append(r)
    assert len(by)==10 and all(len(rows)==1 for rows in by.values())
    models={};pins=[]
    for depot,rows in by.items():
        r=rows[0];assert r['decode_error'] is None
        assert sha(r['raw'])==r['sha256'] and sha(r['json'])==r['json_sha256']
        m=Resource(read(r['json'])).normalize();assert not m['errors']
        models[depot]=m;pins.append(r)
    def one(suffix):return next((d,m) for d,m in models.items() if d.endswith(suffix))
    pd,p=one('sts_ep1_03_phase.questphase');od,o=one('sts_ep1_03_openworld.questphase');gd,g=one('sts_ep1_03_gameplay.questphase')
    pg=p['graphs']['root'];og=o['graphs']['root/2'];gg=g['graphs']['root'];setup=g['graphs']['root/1']
    checks=[]
    def ck(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    def edge(gr,a,s,b,t):return [str(a),s,str(b),t] in gr['edges']
    ck('main_has_only_native_In1',pg['entries']=={'In1':'4'})
    ck('main_concurrently_enters_gameplay_and_openworld',edge(pg,4,'Out',5,'In2') and edge(pg,4,'Out',6,'In1'))
    ck('three_native_ancestor_prefabs',set(p['root_prefabs'])=={'#sts_ep1_03_streetstory','#sts_ep1_03_gunfight_streetstory','#loc_sts_ep1_03_combat'})
    ck('gameplay_entry_enters_startup_only',gg['entries']=={'In2':'7'} and gg['edges']==[['1','Out1','3','In1'],['7','Out','1','In1']])
    ck('startup_terminating_output_precedes_ambient_child',setup['nodes']['1']['payload']['type']=='Terminating' and edge(setup,158,'Out',1,'In'))
    actions=[]
    for i,action,ref in [('101','Activate','#sts_ep1_03_gunfight_broken_car'),('142','Activate','#sts_ep1_03_gunfight_crowd_com'),('143','Deactivate','#sts_ep1_03_pre_gunfight_com')]:
        n=setup['nodes'][i];a=n['payload']['actions'][0]['type']
        ck('unconditional_native_startup_'+i,edge(setup,0,'Out',i,'In') and a['action']==action and a['spawnerReference']['$value']==ref)
        actions.append({'depot':gd,'graph':'root/1','node':i,'edge':['0','Out',i,'In'],'payload':n['payload']})
    writer=og['nodes']['13']['writes'][0]
    ck('community_receipt_is_exact_one',writer=={'$type':'questSetVar_NodeType','factName':'sts_ep1_03_start_community','setExactValue':1,'value':1})
    ck('receipt_fans_independent_waits',all(edge(og,13,'Out',i,'In') for i in [3,12,14]))
    courier=og['nodes']['15']['writes'][0]
    ck('courier_wait_to_nonexact_writer',edge(og,14,'Out',15,'In') and courier['factName']=='sa_ep1_114_toggledoff_force' and courier['setExactValue']==0 and courier['value']==1)
    ck('courier_branch_has_no_selected_receipt',not og['nodes']['15']['journal_paths'] and len(og['nodes']['15']['writes'])==1)
    snapshot=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_HistorySnapshotHS1\snapshot_hs1_20261104T052650Z_38_1.json')
    sd=read(snapshot);row=next(r for r in sd['rows'] if r['definition']['id']=='sts_ep1_03');names=row['definition']['fact_names']
    ck('exact_target_snapshot_not_foreign_ref',row['definition']['id']=='sts_ep1_03')
    ck('snapshot_matches_observed_prepared_state',sd['origin']=='post_ending_fallback' and row['stable'] and set(row['states'])=={1} and [(k,v)for k,v in zip(names,row['facts'])if v]!=[ ] and [(k,v)for k,v in zip(names,row['facts'])if v]==[('sts_ep1_03_start_community',1)])
    ck('courier_absent_from_target_projection',courier['factName'] not in names)
    ck('no_legacy_preending_certificate',not row['legacy_pre_ending_certificate'])
    # These mutants exercise the independent reviewer checks, not engine execution.
    mutant=copy.deepcopy(pg);mutant['edges'].remove(['4','Out','5','In2'])
    ck('drop_parallel_gameplay_mutant_detected',not edge(mutant,4,'Out',5,'In2'))
    mutant=copy.deepcopy(og);mutant['edges'].remove(['14','Out','15','In'])
    ck('drop_courier_link_mutant_detected',not edge(mutant,14,'Out',15,'In'))
    report={'status':'NO_SOURCE_PROVEN_PREPARED_RESUME_REPAIR_APPROVED','recommendation':'Keep current prepared fixture deferred. A widened zero-fact gate is insufficient. An adapter needs a precise saved/native stage and support-owner transition; do not reset facts, skip arbitrary native prefixes or use debug entry.',
      'provider_manifest':{'path':str(manifest),'sha256':sha(manifest)},'source_pins':pins,'checks':checks,
      'corrected_ordering':{'depot':gd,'graph':'root','edges':gg['edges'],'meaning':'In2 enters startup child1; child3 follows only child1.Out1. It is not a direct two-child fanout.'},
      'startup_world_actions':actions,'preparation_branch':{'depot':od,'graph':'root/2','edges':og['edges'],'receipt_node13':writer,'courier_wait14':og['nodes']['14']['payload'],'courier_writer15':courier},
      'snapshot':{'path':str(snapshot),'sha256':sha(snapshot),'origin':sd['origin'],'revision':sd['revision'],'stable':row['stable'],'journal_count':len(row['states']),'fact_count':len(row['facts']),'nondefault_facts':[(k,v)for k,v in zip(names,row['facts'])if v],'courier_absent':True,'legacy_certificate':row['legacy_pre_ending_certificate']},
      'limits':['World actions may be idempotent in some saved states; no duplicate actor/spawner bug is claimed from source dispatch alone.','Courier trigger geometry has not been compared to approach trigger geometry. Do not claim a specific courier-before-main history is physically reachable merely because graph branches are independent.','Native cut ancestry identifies intended retirement. A killed fact alone does not prove exact saved original/third-party owner or lease retirement.','All29inactive journals and55fact values do not decode native pending node positions, world communities, actor persistent states or shared courier state.','No authored prepared-resume socket was found in the exact native main phase; choosing a nested main input would bypass support/approach paths and needs a separate contract.'],
      'evidence_that_would_enable_progress':['An exact saved prepared-stage/pending-node and ancestor-retirement observation for a genuine supported history.','Native community/spawner/prefab persistence and re-acquisition behavior for the existing prepared instance, or an independently source-reviewed non-replaying lease adapter.','Shared courier controller fact ownership/lifecycle and its actual saved state, including trigger spatial relationship; a scalar alone is not branch ownership.','A versioned, save-bound adapter admission derived from existing snapshot plus new actual evidence, without changing old catalogue identity or inventing pre-Tower history.'],
      'runtime_changes':0,'game_calls':0,'save_or_fact_writes':0}
    out.mkdir();(out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':len(checks),'result':str(out/'review.json')}))

if __name__=='__main__':main()
