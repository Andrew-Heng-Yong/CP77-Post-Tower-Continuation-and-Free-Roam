"""Targeted source/snapshot projection checks; no engine simulation or runtime writes."""
from pathlib import Path
import argparse, collections, copy, hashlib, json, re, sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
sys.path.insert(0,str(WORK/'tools/parity_audit'))
from model import Resource

Q='sts_ep1_03'
PREP=Q+'_start_community'
COURIER='sa_ep1_114_toggledoff_force'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def method(source,name):
    m=re.search(r'\bfunc '+re.escape(name)+r'\([^\n]*?\{',source)
    assert m,name
    start=m.end();depth=1
    for end in range(start,len(source)):
        depth+=(source[end]=='{')-(source[end]=='}')
        if depth==0:return source[start:end]
    raise ValueError('Unclosed source method '+name)
def array(body): return json.loads(re.search(r'return\s*(\[.*?\]);',body,re.S)[1])
def case_array(body,index):
    return json.loads(re.search(r'if\s+i\s*==\s*'+str(index)+r'\s*\{\s*return\s*(\[.*?\]);',body,re.S)[1])
def edge(graph,a,s,b,t):return [str(a),s,str(b),t] in graph['edges']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    assert re.fullmatch(r'analysis_[0-9]{2}',args.out)
    out=HERE/args.out;assert not out.exists()
    checks=[]
    def ck(name,ok):
        checks.append({'name':name,'pass':bool(ok)});assert ok,name
    providers=[];models={};manifests=[]
    for dirname in ['providers_01','courier_providers_01']:
        p=HERE/dirname/'manifest.json';d=read(p);manifests.append({'path':str(p),'sha256':sha(p)})
        ck('no_missing_inputs_'+dirname,not d['missing'])
        by=collections.defaultdict(list)
        for r in d['resources']:by[r['depot']].append(r)
        ck('single_provider_per_query_'+dirname,len(by)==len(d['queries']) and all(len(v)==1 for v in by.values()))
        for rows in by.values():
            r=rows[0]
            ck('current_payload_and_export_'+r['depot'],r['decode_error'] is None and sha(r['raw'])==r['sha256'] and sha(r['json'])==r['json_sha256'])
            model=Resource(read(r['json'])).normalize();ck('handle_graph_decode_'+r['depot'],not model['errors'])
            models[r['depot']]=model;providers.append(r)
    def one(suffix):return next((d,m) for d,m in models.items() if d.endswith(suffix))
    sd,street=one('ep1_street_stories.questphase');ed,ep=one('ep1.questphase');wd,world=one('ep1_open_world.questphase')
    epg=ep['graphs']['root/10'];sg=street['graphs']['root/50']
    ck('native_cut_before_receipt',edge(epg,8,'Out',9,'In') and edge(epg,9,'CutSource',5,'CutDestination') and edge(epg,9,'Out',10,'In') and epg['nodes']['10']['writes'][0]['factName']=='q307_ep1_killed')
    ck('exact_original_owner_ancestry',wd in epg['nodes']['5']['refs'] and sd in world['graphs']['root']['nodes']['2']['refs'] and any(r.endswith('sts_ep1_03_phase.questphase') for r in sg['nodes']['19']['refs']))
    pd,phase=one('sts_ep1_03_phase.questphase');gd,gameplay=one('sts_ep1_03_gameplay.questphase');od,openworld=one('sts_ep1_03_openworld.questphase')
    pg=phase['graphs']['root'];gg=gameplay['graphs']['root'];startup=gameplay['graphs']['root/1'];og=openworld['graphs']['root/2']
    ck('native_main_only_one_input',pg['entries']=={'In1':'4'})
    ck('main_fans_both_support_paths',edge(pg,4,'Out',5,'In2') and edge(pg,4,'Out',6,'In1'))
    ck('gameplay_startup_then_ambient',gg['edges']==[['1','Out1','3','In1'],['7','Out','1','In1']])
    actions=[]
    for i,action,ref in [('101','Activate','#sts_ep1_03_gunfight_broken_car'),('142','Activate','#sts_ep1_03_gunfight_crowd_com'),('143','Deactivate','#sts_ep1_03_pre_gunfight_com')]:
        n=startup['nodes'][i];a=n['payload']['actions'][0]['type']
        ck('startup_action_before_approach_'+i,edge(startup,0,'Out',i,'In') and a['action']==action and a['spawnerReference']['$value']==ref)
        actions.append({'depot':gd,'graph':'root/1','node':i,'payload':n['payload']})
    ck('independently_armed_preparation_waits',all(edge(og,13,'Out',i,'In') for i in [3,12,14]))
    ck('courier_nonexact_write',edge(og,14,'Out',15,'In') and og['nodes']['15']['writes'][0]=={'$type':'questSetVar_NodeType','factName':COURIER,'setExactValue':0,'value':1})
    zd,zone=one('sa_ep1_pacifica_zone.questphase');cd,courier=one('sa_ep1_114.questphase')
    zg=zone['graphs']['root'];cg=courier['graphs']['root']
    reads=zg['nodes']['102']['reads']
    ck('shared_courier_eligibility_uses_zero',any(r.get('factName')==COURIER and r['comparisonType']=='Equal' and r['value']==0 for r in reads) and edge(zg,102,'True',32,'In1') and cd in zg['nodes']['32']['refs'])
    ck('shared_courier_cleanup_requests',edge(cg,129,'Out',131,'In') and edge(cg,131,'Out',134,'In') and edge(cg,134,'Out',130,'In') and cg['nodes']['134']['writes'][0]['factName']=='sa_ep1_courier_allow_unrestricted_cleanup' and cg['nodes']['130']['writes'][0]['factName']=='sa_ep1_courier_spot_force_toggled_off')
    ck('courier_cut_scope_not_whole_owner',{e[2] for e in cg['edges'] if e[0]=='131' and e[1]=='CutSource'}=={'116','120','124'})
    source=WORK/'prealpha/quest_restoration_qr13/candidate_01/package/r6/scripts/PTFR_Consolidated'
    activity=source/'PTFR_ActivityStateR3.reds';history=source/'PTFR_HistorySnapshotHS1.reds'
    a=activity.read_text();h=history.read_text();data=a.split('public abstract class NativeGigDataU9 {',1)[1].split('public class NativeGigsU9',1)[0]
    ni=array(method(data,'IDs')).index(Q)
    names=case_array(method(data,'Facts'),ni);paths=case_array(method(data,'Paths'),ni);classes=case_array(method(data,'Classes'),ni)
    snapshot=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_HistorySnapshotHS1\snapshot_hs1_20261104T052650Z_38_1.json')
    doc=read(snapshot);target=[r for r in doc['rows'] if r['definition']['id']==Q];ck('exact_snapshot_identity',len(target)==1)
    row=target[0];definition=row['definition'];values=dict(zip(definition['fact_names'],row['facts']));states=dict(zip(map(tuple,definition['journals']),row['states']))
    ck('snapshot_shapes_match_current_U9_row',names==definition['fact_names'] and list(zip(paths,classes))==list(map(tuple,definition['journals'])))
    ck('stable_postending_projection',doc['origin']=='post_ending_fallback' and row['stable'] and not row['legacy_pre_ending_certificate'] and set(row['states'])=={1} and [(n,v) for n,v in values.items() if v]!=[] and [(n,v) for n,v in values.items() if v]==[(PREP,1)])
    ck('courier_value_absent_from_entire_snapshot',not any(COURIER in r['definition']['fact_names'] for r in doc['rows']))
    si=int(next(n for n,q in re.findall(r'func ID([0-9]+)\(\) -> String \{ return "([^"]+)";',h) if q==Q))
    fact_indices=array(method(h,'U9FactIndices'+str(si)));state_indices=array(method(h,'U9StateIndices'+str(si)))
    ck('source_live_guard_rejects_any_nonzero_fact','if this.Fact(a[k])!=0' in method(a[a.index('public class NativeGigsU9'):],'EntrySafe'))
    ck('source_frozen_guard_rejects_nonzero','if this.rows[i].facts[indices[k]]!=0' in method(h,'FreshU9'))
    live=lambda vv,ss,allow=False:all(ss[(p,c)]==1 for p,c in zip(paths,classes)) and all(vv[n]==0 or (allow and n==PREP and vv[n]==1) for n in names)
    frozen=lambda:all(row['facts'][i]==0 for i in fact_indices) and all(row['states'][i]==1 for i in state_indices)
    ck('observed_state_rejected_independently_by_both_gates',not live(values,states) and not frozen())
    ck('live_only_exemption_does_not_fix_frozen_admission',live(values,states,True) and not frozen())
    fresh=dict.fromkeys(names,0);ck('allzero_projection_positive_control',live(fresh,states))
    bad=copy.deepcopy(states);bad[(paths[0],classes[0])]=4;ck('failed_history_refused',not live(fresh,bad,True))
    bad=copy.deepcopy(values);bad[next(n for n in names if n!=PREP)]=1;ck('other_nondefault_history_still_refused',not live(bad,states,True))
    review=HERE/'review_01/run_01/review.json';extra=HERE/'review_01/courier_addendum_01.json'
    ck('independent_no_repair_disposition',read(review)['status']=='NO_SOURCE_PROVEN_PREPARED_RESUME_REPAIR_APPROVED')
    result={'status':'SOURCE_CONFIRMED_PREPARED_STATE_DEFER_NO_SAFE_REPAIR','quest':Q,'checks':checks,'provider_manifests':manifests,'provider_pins':providers,'source_pins':[{'path':str(p),'sha256':sha(p)} for p in [activity,history,Path(__file__),WORK/'tools/parity_audit/model.py',WORK/'tools/parity_audit/common.py']],
      'snapshot':{'source':str(snapshot),'sha256':sha(snapshot),'copy':str(out/'snapshot.json'),'origin':doc['origin'],'revision':doc['revision'],'definition':definition,'states':row['states'],'facts':row['facts'],'stable':row['stable'],'legacy_certificate':row['legacy_pre_ending_certificate'],'missing_shared_fact':COURIER,'limit':'A naturally exported post-ending sidecar corroborates the same scalar projection; it does not identify an executing save body, pending graph node or owner/lease.'},
      'native_owner_cut':{'depot':ed,'graph':'root/10','nodes':{i:epg['nodes'][i]['payload'] for i in ['5','8','9','10']},'edges':[e for e in epg['edges'] if e[0] in ['8','9']],'ancestry':[ed,wd,sd,pd],'limit':'Intended original subtree cut is established; exact saved/native/third-party owner retirement remains unknown.'},
      'native_startup':{'depot':pd,'only_entry':pg['entries'],'ancestor_prefabs':phase['root_prefabs'],'entry_edges':pg['edges'],'gameplay_edges':gg['edges'],'immediate_world_actions':actions,'limit':'Reapplying native actions is proven; actor duplication or non-idempotence in the actual save is not proven.'},
      'courier_coupling':{'producer_depot':od,'producer_graph':'root/2','edges':og['edges'],'writer':og['nodes']['15']['payload'],'eligibility_depot':zd,'eligibility_graph':'root','eligibility_node':zg['nodes']['102']['payload'],'cleanup_depot':cd,'cleanup_graph':'root','cleanup_nodes':{i:cg['nodes'][i]['payload'] for i in ['129','131','134','130']},'cleanup_edges':[e for e in cg['edges'] if e[0] in ['129','131','134']],'limit':'Actual shared-service dependency, not a claim that this user triggered it, a courier currently failed, or trigger geometry permits every imagined history.'},
      'independent_reviews':[{'path':str(p),'sha256':sha(p)} for p in [review,extra]],'decision':'Do not relax live/snapshot gates or pick a nested/debug input. No source-proven save-compatible repair or runtime successor is selected.','next_requirements':['Exact prepared pending-node, saved community/spawner and ancestor-owner/lease evidence or a demonstrated non-replaying native support transition.','Shared courier branch/state and lifecycle/spatial contract, not a scalar guess or counter reset.','A conservative save-bound adapter preserving old catalogue fingerprint, resources/nodes, progress/outcomes and one-time rewards.'],
      'game_calls':0,'runtime_changes':0,'save_or_fact_writes':0,'new_package':None}
    out.mkdir();(out/'snapshot.json').write_bytes(snapshot.read_bytes());assert sha(out/'snapshot.json')==result['snapshot']['sha256']
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'current_payloads':len(providers),'snapshot_journals':len(paths),'snapshot_facts':len(names),'result':str(out/'result.json')}))

if __name__=='__main__':main()
