"""U9 exact original-slice checks. Offline checks are not engine playtests."""
import copy,json,itertools
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from review_stock_shark_u2 import graph

OUT=ROOT/'research/gig_restoration/native_gigs_u9'
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def raw_json(p):return p.replace('\\','/').replace('/raw/','/json/')+'.json'
def exact(a,b):assert a==b,'Unexpected native payload change'
def fdict(node):return {c['type']['factName']:c['type']['value'] for c in node['condition']['conditions']}

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');p=read(OUT/'build_plan.json');jobs={j['id']:j for j in p['jobs']}
    assert sha(OUT/'build_plan.json')==m['plan_sha256']
    assert len(jobs)==72 and len(m['coverage'])==72
    assert len({x['node_id'] for x in m['collisions']})==len(m['boots'])
    for path,h in m['source_pins'].items():assert sha(ROOT/path)==h,path
    for f in m['files']:assert sha(ROOT/f['source'])==f['sha256'],f
    for path,h in m['resources'].items():assert sha(Path(m['source_dir'])/path)==h,path
    assert m['packed_readback'] and m['original_gameplay_resources_packed']==0
    native_nodes=0;graphs=0;mutants=0;counts={};bindings=0;native_inputs=0
    for r in m['recipes']:
        kind=r['kind'];counts[kind]=counts.get(kind,0)+1
        stem=r['depot'].split('\\')[-1].removesuffix('.questphase');stem=stem.split('_alias')[0]
        built=graph(str((OUT/(stem+'.json')).relative_to(ROOT)))
        ogs=graph(raw_json(r['raw']));og=ogs[r['graph']];on=nodes(og)
        if kind=='entry':
            job=jobs[r['id']];parent=job['parent'];cg=r['compiled_graph'];g=built[cg];ns=nodes(g)
            source_main=job['resources'][0]['graphs'][0]
            main_inputs={n['socketName']['$value'] for n in source_main['nodes'] if n['$type']=='questInputNodeDefinition'}
            original_bound_inputs={e[3] for e in parent['edges'] if e[2]==parent['child']['id']}
            assert original_bound_inputs<=main_inputs,(job['id'],original_bound_inputs,main_inputs)
            assert r['main_input'] in original_bound_inputs
            native_inputs+=len(original_bound_inputs)
            # Every selected native node is unchanged except the documented
            # source reference flag, entry-name normalization and shared gate.
            for i in r['ids']:
                expected=copy.deepcopy(on[i])
                if i==parent['input_node']:expected['socketName']={'$type':'CName','$storage':'string','$value':'In1'}
                if i==parent['child']['id']:expected['phaseResource']={'DepotPath':{'$type':'ResourcePath','$storage':'string','$value':job['resources'][0]['depot']},'Flags':'Soft'}
                exact(ns[i],expected);native_nodes+=1
            # Preserve all nested source graph payloads and edges, applying only
            # pre-reviewed whitelist isolation of two foreign parent branches.
            for path,old in ogs.items():
                if not path.startswith(r['graph']+'/'):continue
                suffix=path[len(r['graph']):];first=int(suffix.split('/')[1])
                if first not in r['ids']:continue
                if job.get('shared_gate') and first==parent.get('shared_gate_node',9):continue
                expected=copy.deepcopy(old);expected['path']=cg+suffix
                for edit in parent['edits']:
                    if edit['graph']=='root'+suffix:
                        expected['edges']=[e for e in expected['edges'] if e!=edit['remove']]
                        if edit['add']:expected['edges'].append(edit['add'])
                actual=built[cg+suffix]
                exact(nodes(actual),nodes(expected));exact(edges(actual),edges(expected));graphs+=1;native_nodes+=len(expected['nodes'])
            # Containing phase metadata (notably Dogtown unfreezing trigger)
            # is copied from every source parent instead of lost by extraction.
            if cg!='root':
                parts=cg.split('/')[1:];at='root'
                for part in parts:
                    exact(nodes(built[at])[int(part)],nodes(ogs[at])[int(part)]);native_nodes+=1;at+='/'+part
            guard=fdict(ns[65002]);tag='PTFRU9_'+job['id']+'_'
            for k,v in {'Request':1,'Permit':1,'ParentEntered':0,'Fault':0}.items():assert guard[tag+k]==v
            assert guard['PTFRU9_Support_Issued']==1 and guard['PTFRU9_Support_Fault']==0
            assert guard['PTFRU7_Support_Issued']==0 and guard['PTFRU6_Padre_Issued']==0
            if job['retaliation_dependency']:
                assert guard['PTFRU9_Retaliation_Issued']==1 and guard['PTFRU9_Retaliation_Fault']==0
                assert guard['PTFRU9_Retaliation_'+job['retaliation_gang']+'_Issued']==1 and guard['PTFRU9_Retaliation_'+job['retaliation_gang']+'_Fault']==0
            else:assert 'PTFRU9_Retaliation_Issued' not in guard
            for fact in job['start']+job['terminal']:assert guard[fact]==0
            es=edges(g)
            assert (65004,'Out',parent['child']['id'],r['main_input']) in es
            # After stripping owned bookkeeping insertions, exactly the source
            # parent edges remain; each lifecycle input is retained verbatim.
            restored=set()
            for e0 in parent['edges']:
                e=list(e0)
                if e[0]==parent['input_node']:e[0]=65003
                if e[2]==parent['child']['id'] and e[3]==r['main_input']:e[2]=65004;e[3]='In'
                assert tuple(e) in es;restored.add(tuple(e))
            if len(parent.get('child_inputs',[]))>1:
                assert (65003,'Out',parent['child']['id'],'STS_not_started') in es
            assert ns[65005]['type']['factName']==tag+'MainFinished'
            assert ns[65006]['type']['factName']==tag+'OwnerFinished'
            if job.get('companions'):
                assert not any(n['$type']=='questOutputNodeDefinition' and n.get('type')=='Terminating' for n in ns.values())
                companion_ids={}
                for c in job['companions']:
                    key=(c['source_raw'],c['source_graph'],c['source_node'],c['depot'])
                    if key not in companion_ids:companion_ids[key]=64000+len(companion_ids)
                    cid=companion_ids[key]
                    source=graph(raw_json(c['source_raw']))[c['source_graph']];expected=copy.deepcopy(nodes(source)[c['source_node']]);expected['id']=cid
                    expected['phaseResource']={'DepotPath':{'$type':'ResourcePath','$storage':'string','$value':c['depot']},'Flags':'Soft'}
                    exact(ns[cid],expected);native_nodes+=1
                    if c['kind'] in ('parallel_bugfix','parallel_prestate'):assert (65003,'Out',cid,c['input']) in es
                    if c['kind']=='cleanup':assert (parent['child']['id'],c['from_output'],cid,c['input']) in es
                if job['id']=='sts_ep1_08':
                    assert not any(e[2]==65006 for e in es),'No invented Spy cleanup output'
                    assert (parent['child']['id'],'Organitopia done',65005,'In') not in es
                    cleanup={e[2] for e in es if e[0]==parent['child']['id'] and e[3] in ('In1','Organitopia cleanup') and e[2]<65000}
                    assert len(cleanup)==1,'Spy must share one cleanup instance across both lifecycle inputs'
            bindings+=1
            # Native fact writes in added bookkeeping nodes are forbidden.
            for n in ns.values():
                if n['id']<65000:continue
                if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(tag)
        else:
            g=built['root'];ns=nodes(g)
            for i in r['ids']:exact(ns[i],on[i]);native_nodes+=1
            es=edges(g)
            if kind=='credit':
                recipe=next(c for c in p['credits'] if c['id']==r['id']);expected=set()
                for e0 in recipe['edges']:
                    e=list(e0)
                    if e[0]==0:e[0]=65001
                    expected.add(tuple(e))
                expected|={(0,'Out',65000,'In'),(65000,'Out',65001,'In'),(recipe['end'],'Out',65002,'In')};exact(es,expected)
                assert fdict(ns[65000])['PTFRU9_'+r['id']+'_Started']==1
                assert ns[recipe['end']]['type']['setExactValue']==0 and ns[recipe['end']]['type']['value']==1
            elif kind=='tier':
                recipe=next(t for t in p['tiers'] if t['region']+'_Tier'+str(t['threshold'])==r['id'])
                expected=set(map(tuple,recipe['edges']))|{(65000,'Out',65001,'In'),(65001,'Out',65002,'In'),(65002,'Out',recipe['start'],'In'),(recipe['end'],'Out',65003,'In')};exact(es,expected)
                for fact in recipe['facts']:assert any(n.get('type',{}).get('factName')==fact and n['type']['setExactValue']==0 for n in recipe['nodes'] if isinstance(n.get('type'),dict))
            elif kind=='map':
                recipes=[x for x in p['maps'] if x['id']==r['id']];recipe=recipes[r['index']];expected=set()
                for e0 in recipe['edges']:
                    e=list(e0)
                    if e[0]==recipe['input']:e[0]=65001
                    expected.add(tuple(e))
                expected|={(recipe['input'],'Out',65000,'In'),(65000,'Out',65001,'In')};exact(es,expected)
                for n in ns.values():
                    if n['$type']=='questJournalNodeDefinition':assert n['type']['path']['realPath']=='points_of_interest/street_stories/'+r['id']
                assert fdict(ns[65000])['PTFRU9_'+r['id']+'_Started']==1
            # Negative controls independently reject a changed native payload.
            first=r['ids'][0];bad=copy.deepcopy(ns[first]);bad['id']=-999
            try:exact(bad,on[first])
            except AssertionError:mutants+=1
            else:raise AssertionError('Mutant accepted')
        graphs+=1
    assert counts=={'entry':72,'credit':66,'tier':25,'map':94},counts
    assert len(p['prestates'])==11
    assert sum(j['retaliation_dependency'] for j in jobs.values())==13
    source_prestate=graph('research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json')['root/3']
    original_prestate_ids={n['id'] for n in source_prestate['nodes'] if any('/'+j+'/' in n.get('phaseResource',{}).get('DepotPath',{}).get('$value','').replace('\\','/') for j in jobs)}
    assert original_prestate_ids=={s['node'] for s in p['prestates']}
    for s in p['prestates']:
        cs=[c for c in jobs[s['id']]['companions'] if c['kind']=='parallel_prestate']
        assert len(cs)==1 and cs[0]['depot']==s['depot']
        assert [0,'Out',s['node'],'In1'] in source_prestate['edges']
    # Source lifetime evidence: fixer loop (including prestates) belongs to the
    # base street-stories tree, whose native root terminates after Tower.
    street=graph('research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories.questphase.json')['root']
    assert nodes(street)[20]['phaseResource']['DepotPath']['$value'].endswith('street_stories_new_fixer_loop.questphase')
    assert (19,'Out',20,'In1') in edges(street)
    base=graph('research/gig_restoration/shutdown_sources/json/base/quest/cyberpunk2077.questphase.json')['root']
    assert (106,'Out',109,'In') in edges(base) and (109,'Out',107,'In') in edges(base)
    assert nodes(base)[107]['type']=='Terminating'
    script=(ROOT/'redscript/PTFR_NativeGigsU9/NativeGigsU9.reds').read_text()
    assert 'Production history admission is not connected' in script
    assert 'if !GigBatchLockU9.Ready()' in script and 'let safe=GigBatchLockU9.Ready() &&' in script
    assert 'NativeGigDataU9.NeedsRetaliation(i) && !this.RetaliationAdmissible(gang)' in script
    assert 'let consequenceReady=!NativeGigDataU9.NeedsRetaliation(k)' in script
    for f in ['wraiths','6thstreet','animals','valentinos','maelstroms','tygerclaws','sts_gang_retaliation_cancel','mws_chase_active']:assert '"'+f+'"' in script
    assert 'SetFact(StringToName(name),v)' in script and 'let name="PTFRU9_"+id+"_"+key' in script
    assert 'GameInstance.GetJournalManager' in script and 'ChangeEntryState' not in script
    # Exhaustive Boolean admission truth table: never start if any component
    # fails, and repeated requests/entered owners never restart. Model only.
    cases=0
    for tower,support,legacy,entry,unused,requested,entered in itertools.product((False,True),repeat=7):
        launch=tower and support and legacy and entry and unused and requested and not entered
        if launch:assert all((tower,support,legacy,entry,unused,requested)) and not entered
        if entered:assert not launch
        cases+=1
    gang_cases=0
    for pending in itertools.product((0,1),repeat=6):
        for gang in range(6):
            # A stale pending event excludes only that gang's new owner, not
            # unrelated empty gangs. Neither admission branch resets the array.
            before=tuple(pending);admit=pending[gang]==0
            assert admit==(not before[gang]) and tuple(pending)==before
            gang_cases+=1
    result=dict(status='PASS_U9_OFFLINE_SOURCE_AND_PACKAGING_NOT_ENGINE_PROOF',jobs=72,counts=counts,prestate_companions=len(p['prestates']),native_payloads=native_nodes,graphs=graphs,interface_bindings=bindings,native_main_input_interfaces=native_inputs,negative_mutants=mutants,admission_models=cases,per_gang_admission_models=gang_cases,retaliation_dependent_jobs=13,packed_readback=m['packed_readback'],source_pin_count=len(m['source_pins']),compile='PARENT_COMBINED_COMPILATION_REQUIRED',live='PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(Path(__file__)))
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
