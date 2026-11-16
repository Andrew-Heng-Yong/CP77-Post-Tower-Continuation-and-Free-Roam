"""Pin the ordinary Boolean initialization fields eligible for the PE1 policy."""
from pathlib import Path
from collections import defaultdict
import json
import re
from inventory import HERE,WS,BASE,CACHE,read,sha,write,function_bodies,literal,indexed_literals

SIDE_RULES={
 ('SideJobDataS23','mq044_jakes_vehicle'):['mq044_started','mq_044_started_in_main'],
 ('SideJobDataS23','mq030_melisa'):['mq030_active'],
 ('SideJobDataS23','mq011_wilson'):['mq011_active'],
 ('SideJobDataS23','wst_ep1_04'):['wst_ep1_04_active'],
 ('SideJobDataS24','mq010_barry'):['mq010_active'],
 ('SideJobDataS24','mq305_combat_zone_report'):['mq305_active','mq305_01_active','mq305_started'],
 ('SideJobDataS24','sq_q001_wakako'):['sq_q001_active'],
 ('SideJobDataS28','mq022_ezekiel'):['mq022_active'],
 ('SideJobDataS29','mq028_stalker'):['mq028_started'],
 ('SideJobDataS29','sq023_hit_order'):['sq023_active'],
 ('SideJobDataS29','mq060_nitro'):['mq060_active'],
 ('SideJobDataS29','sts_ep1_12_pickup'):['wst_ep1_02_start'],
}
U9_RULES={
 'sts_bls_ina_11':['bls_ina_11_active'],
 'sts_cct_dtn_05':['dtn_05_active'],
 'sts_ep1_03':['sts_ep1_03_start_community'],
 'sts_ep1_13':['sts_ep1_13_active'],
 'sts_ep1_06':['sts_ep1_06_active'],
}


def main():
    target=HERE/'decisions_01.json';assert not target.exists()
    inventory=read(HERE/'inventory_02.json');scan=read(HERE/'scan_01.json');roots=read(HERE/'roots_03.json')
    native_cache=read(CACHE)
    current={r['depot']:r for r in inventory['resources']}
    tables={t['class']:t for t in inventory['script_tables']}
    rules=[]
    for (cls,identity),flags in SIDE_RULES.items():
        table=tables[cls];row,=[r for r in table['rows'] if r['id']==identity]
        candidates=[t for t in roots['traces'] if set(flags)<=set(t['candidate_setup_flags'])]
        assert len(candidates)==1,(identity,len(candidates))
        trace=candidates[0];assert not trace['unresolved']
        names=row['FactNames'];lo=row['FactMin'];hi=row['FactMax']
        changes=[f for f in flags if hi[names.index(f)]==0]
        assert changes and all(lo[names.index(f)]==0 for f in flags)
        text=Path(table['file']).read_text(encoding='utf-8-sig')
        start=text.index('class '+cls)
        tail=text[start:]
        next_class=re.search(r'\npublic (?:abstract )?class ',tail)
        if next_class:tail=tail[:next_class.start()]
        methods=function_bodies(tail)
        baselines=literal(methods.get('BaselineIDs'+str(row['index'])))
        if baselines is None:baselines=indexed_literals(methods.get('BaselineIDs')).get(row['index'])
        if baselines is None:baselines=[identity]
        snapshot=tables['SnapshotDataHS1']
        snapshot_ids={r['id'] for r in snapshot['rows']}
        assert all(s in snapshot_ids for s in baselines),(identity,baselines)
        rules.append({'family':'SIDE','id':identity,'title':row['title'],'class':cls,'index':row['index'],'script':str(Path(table['file']).relative_to(BASE/'package')).replace('\\','/'),'entry':trace['guard']['depot'],'flags':changes,'already_allowed_flags':[f for f in flags if f not in changes],'baseline_ids':baselines,'trace_entry':trace['guard']['depot'],'source_writes':[w for w in trace['pre_interaction_positive_writes'] if w['write']['factName'] in changes]})
    table=tables['NativeGigDataU9']
    for identity,flags in U9_RULES.items():
        row,=[r for r in table['rows'] if r['id']==identity]
        entry='towercontinued\\native_gigs_u9\\'+identity+'_entry.questphase'
        trace,=[t for t in roots['traces'] if t['guard']['depot']==entry]
        assert not trace['unresolved'] and set(flags)<=set(trace['candidate_setup_flags']),(identity,flags)
        assert set(flags)<=set(row['Facts'])
        rules.append({'family':'U9','id':identity,'title':row['title'],'class':'NativeGigDataU9','index':row['index'],'script':str(Path(table['file']).relative_to(BASE/'package')).replace('\\','/'),'entry':entry,'flags':flags,'baseline_ids':[identity],'source_writes':[w for w in trace['pre_interaction_positive_writes'] if w['write']['factName'] in flags]})
    for rule in rules:
        assert all(w['write']['setExactValue']==1 and w['write']['value']==1 for w in rule['source_writes']),rule['id']
        assert set(rule['flags'])=={w['write']['factName'] for w in rule['source_writes']}
        found=[]
        for g in scan['guards']:
            if g['depot']!=rule['entry']:continue
            fs=sorted(set(g['zero_facts'])&set(rule['flags']))
            owned=any(r['factName'].startswith('PTFR') and r['factName'].endswith(('_Issued','_Started','_ParentEntered','_OwnerActive')) and r['value']==0 for r in g['other_reads'])
            if fs and owned:
                found.append({'graph':g['graph'],'node':g['node'],'flags':fs})
        rule['native_guards']=found
        if rule['family']=='SIDE':assert found,rule['id']
    # Every original zero-gated flag is classified. Unselected guards remain exact.
    allowed={(r['entry'],f) for r in rules for f in r['flags']}
    classifications=[]
    for g in scan['guards']:
        for f in g['zero_facts']:
            status='PRESERVE_EXISTING_PROGRESS_OR_OWNERSHIP_GUARD'
            if (g['depot'],f) in allowed:status='QUALIFIED_BOOLEAN_INITIALIZATION_0_OR_1'
            if f.startswith(('PTFR','q307_','q115_','q305_johnny','holo_','phonecall_')):status='PRESERVE_ENDING_PRIVATE_OWNER_OR_PHONE_CONCURRENCY_GUARD'
            classifications.append({'entry':g['depot'],'graph':g['graph'],'node':g['node'],'fact':f,'decision':status})
    # Current provider checks include every source phase plus the native prefix
    # resources actually used by approved rules and the two retirement roots.
    queries={d:{'depot':d,'expected_sha256':r['sha256'],'selected_archive':'zzzz_PTFR_Combined.archive','scope':'INSTALLED_SOURCE'} for d,r in current.items()}
    for rule in rules:
        trace,=[t for t in roots['traces'] if t['guard']['depot']==rule['entry']]
        depots={a['depot'] for a in trace['prefix_effects']+trace['boundaries']+trace['pre_interaction_positive_writes']}
        for w in rule['source_writes']:
            depots.update(d for d,_,_ in w.get('call_stack',[]))
        for d in depots:
            if d in queries:continue
            r=native_cache[d]
            queries[d]={'depot':d,'expected_sha256':r['resource_sha256'],'scope':'NATIVE_PREFIX_EVIDENCE','source_model':r['normalized_model'],'source_model_sha256':r['normalized_sha256']}
    for d in [r'base\quest\cyberpunk2077.quest',r'base\quest\cyberpunk2077.questphase',r'ep1\quest\ep1.quest',r'ep1\quest\ep1.questphase']:
        if d not in queries:
            if d in native_cache:
                r=native_cache[d];queries[d]={'depot':d,'expected_sha256':r['resource_sha256'],'scope':'NATIVE_RETIREMENT_EVIDENCE','source_model':r['normalized_model'],'source_model_sha256':r['normalized_sha256']}
            else:
                km1=[r for r in read(WS/'prealpha/kold_mirage_km1/source_01/providers.json')['resources'] if r['depot']==d]
                if km1:
                    assert len(km1)==1
                    queries[d]={'depot':d,'expected_sha256':km1[0]['sha256'],'scope':'NATIVE_RETIREMENT_EVIDENCE'}
                    continue
                originals=[r for r in read(WS/'research/q307_extracted/inventory.json') if r['ResourcePath']==d]
                assert originals and len({r['Sha256'].upper() for r in originals})==1,d
                queries[d]={'depot':d,'expected_sha256':originals[0]['Sha256'].upper(),'scope':'NATIVE_RETIREMENT_EVIDENCE'}
    result={'schema':1,'status':'SOURCE_QUALIFIED_GLOBAL_BOOLEAN_INITIALIZATION_POLICY','policy':'For an unclaimed restored owner with an accepted Inactive baseline and the original Inactive current quest/child stages, admit reviewed exact-to-one initialization fields at zero or one. Retain all unrelated facts, counters, completion/failure, choices, items, rewards, shared leases and native prerequisites. Use the original marker/encounter owner; never independently force a pin or restart a progressed encounter.','rules':rules,'already_supported':['KM1 mq016_active 0/1','MQ040 reviewed idle-service handoff','QR19 retained-message MQ018 adapter','N21 four exact initialized scanner adapters'],'unchanged_counter_example':{'id':'q304_car_retrieval','facts':['q304_car_retrieval_started','q304_car_retrieval_active'],'reason':'Native initialization increments these counters. A scalar widening would turn retained one into two; existing earned-stage handling and guards are preserved.'},'all_zero_gate_classifications':classifications,'phase_resources_reviewed':1000,'registered_roots':roots['registered_root_count'],'changed_side_jobs':sum(r['family']=='SIDE' for r in rules),'changed_gigs':sum(r['family']=='U9' for r in rules),'changed_initialization_fields':sum(len(r['flags']) for r in rules),'unchanged_unresolved_native_scopes':[t['guard']['depot'] for t in roots['traces'] if t['unresolved']],'limits':'This audits and changes admission policy, not full quest parity or universal stage support. Counter, combat, phone and later-stage flags are not reclassified as ordinary initialization. Existing already-issued owners are never restarted.','game_writes':0,'save_writes':0}
    write(target,result)
    write(HERE/'provider_queries_01.json',{'queries':list(queries.values()),'current_phase_count':1000})
    print(json.dumps({'side_jobs':result['changed_side_jobs'],'gigs':result['changed_gigs'],'fields':result['changed_initialization_fields'],'native_guard_nodes':sum(len(r['native_guards']) for r in rules),'provider_queries':len(queries)}))
    for r in rules:print(r['id'],r['flags'],r['native_guards'],r['baseline_ids'])


if __name__=='__main__':
    main()
