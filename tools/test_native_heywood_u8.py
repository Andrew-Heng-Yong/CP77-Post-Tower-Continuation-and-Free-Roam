"""U8 exact stock-node/edge, isolation, packaging and compilation checks.
These checks are not native-engine or save-persistence proof.
"""
import copy,itertools,json,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from review_stock_shark_u2 import graph

OUT=ROOT/'research/gig_restoration/native_heywood_u8'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
PADRE='research/gig_restoration/family_b7/fixers/json/base/open_world/fixers/padre/phases/padre.questphase.json'
COUNT='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json'
IDS={'sts_hey_gle_06','sts_hey_gle_04','sts_hey_spr_01','sts_hey_rey_08','sts_hey_gle_01','sts_hey_spr_03','sts_hey_spr_06'}

def nodes(g):return {n['id']:n for n in g['nodes']}
def edge_set(g):return set(map(tuple,g['edges']))
def pairs(n):return {c['type']['factName']:c['type']['value'] for c in n['condition']['conditions']}
def exact(g,expected):
    assert nodes(g)==nodes(expected),'Node payload delta'
    assert edge_set(g)==edge_set(expected),'Edge delta'

def compile_all(m):
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for n in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/n,cache/n)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);dest=stage/'scripts'/p.relative_to(GAME/'r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for f in m['files']:
        if f['relative'].endswith('.reds'):
            dest=stage/'scripts'/Path(f['relative']).relative_to('r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f['source'],dest)
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe';args=[str(cli),'compile']
    names=('PTFR_NativeHeywoodU8','PTFR_NativeSupportU7','PTFR_NativePadreU6','PTFR_NativeJeopardyU4','PTFR_NativeReuseU1','PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3')
    for name in names:args+=['-s',str(stage/'scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=120);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-5500:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n',encoding='utf-8');compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-5500:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90);assert run.returncode==0
    ct=flat.read_text(encoding='utf-8-sig')
    for s in ('class PTFR.ActivityStateR3.NativeHeywoodU8','Copied Heywood adapter disabled','Native support U7','Native Jeopardy U4','Native reuse U3 Shark','TemporaryHide(true);'):
        assert s in ct,s
    # Preserve tested HP checkpoint repair, all prior installed scripts and caches.
    assert sha(GAME/'r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds')=='BD574FC510FB75969314E64388E0D609DE2B01CDBBD90C2EBF552ACF2C342F12'
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    return dict(cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected)

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');plan=read(ROOT/'research/gig_restoration/family_b7/build_plan.json')
    jobs={j['id']:j for j in plan['jobs'] if j['id'] in IDS};assert set(jobs)==IDS
    pins={**m['source_pins'],**m['native_pins']}
    for p,h in pins.items():assert sha(ROOT/p)==h
    def load(p):pins[p]=sha(ROOT/p);return graph(p)
    padre=load(PADRE);credit=load(COUNT)['root/2/4'];cn=nodes(credit)
    assert cn[3]['type']=={'$type':'questSetVar_NodeType','factName':'hey_sts_counter','setExactValue':0,'value':1}
    assert not any(e[0]==14 for e in credit['edges']),'Hot Merchandise credit topology changed'
    assert cn[14]['condition']['type']['factName']=='sts_hey_spr_06_finished'
    counts={};guard_cases=0;native_nodes=0;negative=0
    for r in m['recipes']:
        counts[r['kind']]=counts.get(r['kind'],0)+1
        p='research/gig_restoration/native_heywood_u8/'+r['depot'].split('\\')[-1].replace('.questphase','.json')
        gs=load(p);g=gs['root'];ns=nodes(g)
        if r['kind']=='gig':
            job=jobs[r['id']];tag='PTFRU8_'+r['id']
            old=load('research/gig_restoration/family_b7/built/towercontinued/family_b7/'+r['id']+'/boot.questphase.json')
            oldroot=read(ROOT/('research/gig_restoration/family_b7/built/towercontinued/family_b7/'+r['id']+'/boot.questphase.json'))['Data']['RootChunk']
            newroot=read(ROOT/p)['Data']['RootChunk']
            assert {k:v for k,v in oldroot.items() if k!='graph'}=={k:v for k,v in newroot.items() if k!='graph'}
            expected=copy.deepcopy(old['root']);en=nodes(expected)
            en[r['child']]['phaseResource']={'DepotPath':{'$type':'ResourcePath','$storage':'string','$value':r['native']},'Flags':'Soft'}
            for i in (65000,65003,65004,65006):en[i]['type']['factName']=en[i]['type']['factName'].replace(job['tag'],tag)
            for i in (65001,65002):
                for c in en[i]['condition']['conditions']:c['type']['factName']=c['type']['factName'].replace(job['tag'],tag)
                extras={job['tag']+'_'+k:0 for k in ('Queued','Request','Started','OwnerFinished','Fault','CounterClaim','CounterAck')};extras['PTFRU7_Support_Issued']=1
                for key,value in extras.items():en[i]['condition']['conditions'].append({'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':key,'value':value}})
            exact(g,expected)
            for path in set(old)-{'root'}:exact(gs[path],old[path])
            # Independently compare every native parent node, nested graph and edge.
            orig=load(job['parent']['binding']['binding']['source'])
            original=orig[job['parent']['binding']['graph']];on=nodes(original)
            for n in job['parent']['ancestors']:assert ns[n['id']]==on[n['id']]
            assert not job['parent']['edits']
            for e in job['parent']['edges']:assert tuple(e) in edge_set(original)
            # Direct original child inputs/outputs and native instance prefabs.
            child=load(job['resources'][0]['binding']['source'])['root']
            ins={n['socketName']['$value'] for n in child['nodes'] if n['$type']=='questInputNodeDefinition'}
            outs={n['socketName']['$value'] for n in child['nodes'] if n['$type']=='questOutputNodeDefinition'}
            for e in g['edges']:
                if e[2]==r['child']:assert e[3] in ins
                if e[0]==r['child']:assert e[1] in outs
            assert ns[r['child']]['phaseInstancePrefabs']==on[r['child']]['phaseInstancePrefabs']
            # Evaluate serialized generated entry guards with each fact corrupted.
            def evaluate(f):return all(f.get(k,0)==v for k,v in pairs(ns[65001]).items())
            base=pairs(ns[65001]);assert evaluate(base);guard_cases+=1
            for key in base:
                altered=dict(base);altered[key]+=1;assert not evaluate(altered);guard_cases+=1
        else:
            source=credit if r['kind']=='credit' else padre['root'] if r['kind']=='tier' else padre['root/'+str(r['phase'])]
            original_nodes=nodes(source);ids=set(r['ids'])
            for i in ids:assert ns[i]==original_nodes[i],(r,i)
            native_nodes+=len(ids)
            edges=[list(e) for e in source['edges'] if e[0] in ids and e[2] in ids]
            if r['kind']=='tier':
                tier=next(t for t in plan['tiers'] if t['region']=='hey' and t['threshold']==r['threshold'])
                assert sorted(edges)==sorted(tier['edges'])
                edges += [[65000,'Out',65001,'In'],[65001,'Out',65002,'In'],[65002,'Out',tier['start'],'In'],[r['last'],'Out',65003,'In']]
                assert set(ns)==ids|{65000,65001,65002,65003}
                assert ns[65000]['socketName']['$value']=='In1'
                assert pairs(ns[65001])=={'PTFRU8_Heywood_TierRequest':1,'PTFRU8_Tier'+str(r['threshold'])+'_Permit':1,'PTFRU8_Tier'+str(r['threshold'])+'_Entered':0,'PTFRU7_Support_Issued':1}
                if r['threshold']==11:assert ns[98]['condition']['type']['factName']=='q103_rogue_done'
            else:
                if r['kind']=='map' and r['activation'] is not None and not any(e[2]==r['activation'] for e in edges):edges.append([0,'Out',r['activation'],'Active'])
                for e in edges:
                    if e[0]==0:e[0]=65001
                edges += [[0,'Out',65000,'In'],[65000,'Out',65001,'In']]
                tag='PTFRU8_'+r['id']
                if r['kind']=='credit':
                    edges.append([3,'Out',65002,'In']);assert set(ns)==ids|{65000,65001,65002}
                    assert pairs(ns[65000])=={tag+'_Started':1,tag+'_CreditEntered':0,tag+'_CreditDone':0}
                    assert ns[65001]['type']['factName']==tag+'_CreditEntered'
                    assert ns[65002]['type']['factName']==tag+'_CreditDone'
                else:
                    assert set(ns)==ids|{65000,65001}
                    assert pairs(ns[65000])=={tag+'_Request':1,tag+'_MapPermit':1,tag+'_MapEntered':0,tag+'_Fault':0,'PTFRU7_Support_Issued':1}
                    for v in walk(g):
                        if str(v.get('realPath','')).startswith('points_of_interest/street_stories/'):assert v['realPath'].endswith('/'+r['id'])
                    # Nested original POI discovery graphs copied without edits.
                    prefix='root/'+str(r['phase'])
                    for path,nested in gs.items():
                        if path!='root':exact(nested,padre[prefix+path[4:]])
            assert edge_set(g)==set(map(tuple,edges)),r
        # Reject an altered node or an added entry/repeat edge.
        for kind in ('node','edge'):
            bad=copy.deepcopy(g)
            if kind=='node':bad['nodes'][0]['id']=65530
            else:bad['edges'].append([0,'Out',0,'In'])
            try:exact(g,bad)
            except AssertionError:negative+=1
            else:raise AssertionError('Graph mutation accepted')
    assert counts=={'gig':7,'credit':6,'tier':4,'map':7},counts
    assert len(m['resources'])==24 and len(m['boots'])==24 and len({c['node_id'] for c in m['collisions']})==24
    assert m['packed_readback'] and m['original_gig_resources_packed']==0
    assert all(p.startswith('towercontinued\\native_heywood_u8\\') for p in m['resources'])
    assert not m['production_auto'] and not m['final_fixer_reward']
    # Models of the original one-shot branch plus serialized program counter.
    models=0
    for armed,completed,baseline in itertools.product((False,True),(False,True),(0,1,4,10,30)):
        s={'pc':0,'counter':baseline}
        for _ in range(4):
            if armed and s['pc']==0:s['pc']=1
            if completed and s['pc']==1:s['counter']+=1;s['pc']=2
            s=json.loads(json.dumps(s))
        assert s['counter']==baseline+int(armed and completed);models+=1
    src=(ROOT/'redscript/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds').read_text()
    assert src.count('.SetFact(')==1 and 'let name="PTFRU8_"+id+"_"+key' in src
    for forbidden in ('.ExecuteNode(','.GiveReward(','.SetEntryState(','StartQuest','Capture','HistoryFresh','this.Set(id,"CreditDone"','this.Set(id,"Started"'):
        assert forbidden not in src
    for required in ('epoch!=this.epoch','this.Own(id,"Request")!=0','this.Terminal(i)','this.EntrySafe(i)','this.OldUnused(i)','this.LegacyIdle()','this.TierUntouched(ns[k])','this.Root(i)==1','PTFRU7_Support_Issued','PTFRU7_Support_Fault'):
        assert required in src
    assert 'this.Fact("sts_hey_rey_tier_1_2")>0 || (this.Fact("sts_hey_rey_tier_1")>0 && this.Fact("sts_hey_rey_tier_1_1")==0)' in src
    b7old=(ROOT/'build/NativeJeopardyU4/GigFamilyB7.reds').read_text();b7=(ROOT/'build/NativeHeywoodU8/GigFamilyB7.reds').read_text()
    insert='\n    // U8: copied Heywood gameplay is superseded for NEW requests only.\n    let u8ids=NativeHeywoodU8.IDs();\n    if ArrayContains(u8ids,id) { return "Copied Heywood adapter disabled; use NativeHeywoodU8 on a disposable save."; }\n'
    assert b7.count(insert)==1 and b7.replace(insert,'')==b7old
    for f in m['files']:
        assert sha(ROOT/f['source'])==f['sha256']
        if f['predecessor']:assert sha(GAME/f['relative'])==f['predecessor']
        else:assert not (GAME/f['relative']).exists()
    result=dict(status='PASS_U8_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(__file__),exact_stock_delta=True,recipes=counts,stock_nodes=native_nodes,entry_guard_cases=guard_cases,negative_graph_mutants=negative,serialization_models=models,source_pins=pins,native_engine_proof=False)
    result.update(compile_all(m))
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
