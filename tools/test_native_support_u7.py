"""Exact stock-slice/entry/package/compile checks. Not native-engine proof."""
import copy,itertools,json,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from review_stock_shark_u2 import graph
OUT=ROOT/'research/gig_restoration/native_support_u7'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
INIT='research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/holocall_initializers.questphase.json'
PARENT='research/b0_missing_content/root_children/json/base/quest/additional_game_elements.questphase.json'
COUNT='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json'

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');pins=dict(m['source_pins'])
    for p,h in pins.items():assert sha(ROOT/p)==h
    def load(p):pins[p]=sha(ROOT/p);return graph(p)
    init=load(INIT)['root'];ins={n['id']:n for n in init['nodes']}
    phone=load('research/gig_restoration/native_support_u7/padre_initializer.json')['root']
    parent=load('research/gig_restoration/native_support_u7/padre_parent.json')['root']
    credit=load('research/gig_restoration/native_support_u7/jeopardy_credit.json')['root']
    wrapper=load('research/gig_restoration/native_support_u7/support_wrapper.json')['root']
    ids={5,25,79,102,107,108,114,115,116,117,118,119,120,124,131,132}
    def verify_phone(candidate):
        ns={n['id']:n for n in candidate['nodes']};assert set(ns)==ids
        for i,n in ns.items():
            original=copy.deepcopy(ins[i])
            if i==124:original['phaseResource']['DepotPath']['$value']=r'base\quest\holocalls\padre\padre_cleanup.questphase'
            assert original==n,(i,'stock node payload changed')
        edges=[list(e) for e in init['edges'] if e[0] in ids and e[2] in ids]
        for e in edges:
            if e[2]==124:e[3]='In42'
            if e[0]==124:e[1]='Out42'
        assert sorted(edges)==sorted(candidate['edges'])
    verify_phone(phone)
    assert ins[107]['type']=='Terminating'
    assert ins[79]['phaseResource']['DepotPath']['$value']==r'base\quest\holocalls\padre\padre_holocall.questphase'
    assert ins[102]['phaseResource']['DepotPath']['$value']==r'base\quest\holocalls\holocall_interrupts.questphase'
    add=load(PARENT)['root'];an={n['id']:n for n in add['nodes']}
    for n in parent['nodes']:
        original=copy.deepcopy(an[n['id']])
        if n['id']==34:original['phaseResource']['DepotPath']['$value']=r'towercontinued\native_support_u7\padre_initializer.questphase'
        assert original==n
    assert {n['id'] for n in parent['nodes']}=={0,34,35}
    expected={(0,'Out',34,'In1'),(34,'reset_out',35,'In1'),(35,'Out1',34,'reset_in')}
    assert set(map(tuple,parent['edges']))==expected
    assert expected.issubset(set(map(tuple,add['edges'])))
    cleanup=load('research/gig_restoration/padre_phone_u5/sources/json/base/quest/holocalls/padre/padre_cleanup.questphase.json')['root']
    assert next(n for n in cleanup['nodes'] if n['id']==1)['socketName']['$value']=='In42'
    assert next(n for n in cleanup['nodes'] if n['id']==3)['socketName']['$value']=='Out42'
    interrupt=load('research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/holocall_interrupts.questphase.json')['root']
    inn={n['id']:n for n in interrupt['nodes']}
    assert inn[31]['type']=='Terminating' and inn[31]['socketName']['$value']=='holocall_reset_out'
    assert [124,'Out',129,'In'] in interrupt['edges'] and [125,'Out1',31,'In'] in interrupt['edges']
    assert any(v.get('statusEffectID')=='GameplayRestriction.PhoneNoCalling' for v in walk(inn[184]))
    # Original lifetime: both possible base initializers are stopped by Tower.
    base=load('research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json')['root']
    bn={n['id']:n for n in base['nodes']}
    assert bn[107]['type']=='Terminating'
    assert bn[106]['condition']['type']['path']['realPath']=='ep1/quests/main_quest/q307_before_tomorrow'
    assert bn[106]['condition']['type']['state']=='Succeeded'
    assert [106,'Out',109,'In'] in base['edges'] and [109,'Out',107,'In'] in base['edges']
    q=load('research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json')
    assert [16,'Out',18,'In'] in q['root']['edges'] and [18,'Out',17,'In'] in q['root']['edges'] and [17,'CutSource',6,'CutDestination'] in q['root']['edges']
    assert next(n for n in q['root/6']['nodes'] if n['id']==5)['phaseResource']['DepotPath']['$value'].endswith('holocall_initializers.questphase')
    native_credit=load(COUNT)['root/2/4'];cn={n['id']:n for n in native_credit['nodes']}
    assert {n['id'] for n in credit['nodes']}=={0,3,8,65000}
    for n in credit['nodes']:
        if n['id']!=65000:assert n==cn[n['id']]
    assert cn[8]['condition']['type']['factName']=='rey_06_finished'
    assert cn[3]['type']=={'$type':'questSetVar_NodeType','factName':'hey_sts_counter','setExactValue':0,'value':1}
    assert set(map(tuple,credit['edges']))=={(0,'Out',8,'In'),(8,'Out',3,'In'),(3,'Out',65000,'In')}
    assert next(n for n in credit['nodes'] if n['id']==65000)['type']['factName']=='PTFRU7_Support_CreditDone'
    wn={n['id']:n for n in wrapper['nodes']}
    assert set(wn)==set(range(9))
    assert set(map(tuple,wrapper['edges']))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'False',3,'In'),(4,'True',5,'In'),(5,'Out',6,'Input'),(5,'Out',8,'In'),(8,'Out',7,'In1')}
    # Cross-resource socket contracts, not merely internal edge consistency.
    controller=load('research/gig_restoration/padre_phone_u5/sources/json/base/quest/holocalls/padre/padre_holocall.questphase.json')['root']
    closure={
        r'towercontinued\native_support_u7\padre_parent.questphase':parent,
        r'towercontinued\native_support_u7\padre_initializer.questphase':phone,
        r'towercontinued\native_support_u7\jeopardy_credit.questphase':credit,
        r'base\quest\holocalls\padre\padre_holocall.questphase':controller,
        r'base\quest\holocalls\padre\padre_cleanup.questphase':cleanup,
        r'base\quest\holocalls\holocall_interrupts.questphase':interrupt,
    }
    def check_interfaces(g):
        for n in g['nodes']:
            if n['$type']!='questPhaseNodeDefinition':continue
            child=closure[n['phaseResource']['DepotPath']['$value']]
            inputs={v['socketName']['$value'] for v in child['nodes'] if v['$type']=='questInputNodeDefinition'}
            outputs={v['socketName']['$value'] for v in child['nodes'] if v['$type']=='questOutputNodeDefinition'}
            for e in g['edges']:
                if e[2]==n['id']:assert e[3] in inputs,(n['id'],e,inputs)
                if e[0]==n['id']:assert e[1] in outputs,(n['id'],e,outputs)
    for g in (wrapper,parent,phone):check_interfaces(g)
    bad=copy.deepcopy(wrapper)
    next(e for e in bad['edges'] if e[2]==6)[3]='In1'
    try:check_interfaces(bad)
    except AssertionError:pass
    else:raise AssertionError('Incorrect parent Input socket accepted')
    assert wn[5]['type']['factName']=='PTFRU7_Support_Issued'
    for i in (3,4):
        conds=wn[i]['condition']['conditions']
        pairs={c['type']['factName']:c['type']['value'] for c in conds if c['type']['$type']=='questVarComparison_ConditionType'}
        assert pairs==m['guard_pairs']
        assert all(c['type']['comparisonType']=='Equal' for c in conds)
        assert {(c['type']['factName1'],c['type']['factName2']) for c in conds if c['type']['$type']=='questVarVsVarComparison_ConditionType'}=={('holo_padre_calls_v_start_count','holo_padre_calls_v_end_count'),('holo_v_calls_padre_start_count','holo_v_calls_padre_end_count')}
    # Evaluate the actual generated native entry predicates, including mutations.
    def evaluate(condition,facts):
        if condition['$type']=='questLogicalCondition':return all(evaluate(c,facts) for c in condition['conditions'])
        t=condition['type'];assert t['comparisonType']=='Equal'
        if 'factName' in t:return facts.get(t['factName'],0)==t['value']
        return facts.get(t['factName1'],0)==facts.get(t['factName2'],0)
    facts=dict(m['guard_pairs']);assert evaluate(wn[3]['condition'],facts)
    cases=1
    for fact in m['guard_pairs']:
        altered=dict(facts);altered[fact]+=1
        assert not evaluate(wn[3]['condition'],altered);cases+=1
    for start,end in itertools.product(range(5),repeat=2):
        f=dict(facts,holo_padre_calls_v_start_count=start,holo_padre_calls_v_end_count=end)
        assert evaluate(wn[3]['condition'],f)==(start==end);cases+=1
    # Negative graph variants must fail exact-source comparison.
    mutants=[]
    for node,key,value in [(79,'saveLock',1),(107,'type','NonTerminating')]:
        bad=copy.deepcopy(phone);next(n for n in bad['nodes'] if n['id']==node)[key]=value;mutants.append(bad)
    bad=copy.deepcopy(phone);bad['edges'].append([25,'Out1',79,'In1']);mutants.append(bad)
    for bad in mutants:
        try:verify_phone(bad)
        except AssertionError:pass
        else:raise AssertionError('Unsafe graph mutant accepted')
    # Model serialized graph progress, not native save-engine proof.
    for baseline in (0,3,4,10,100):
        state={'issued':0,'pc':0,'counter':baseline}
        for done in (False,False,True,True,True):
            if not state['issued']:state['issued']=1;state['pc']=8
            if state['pc']==8 and done:state['pc']=3
            if state['pc']==3:state['counter']+=cn[3]['type']['value'];state['pc']=65000
            state=json.loads(json.dumps(state))
        assert state['counter']==baseline+1
    src=ROOT/'redscript/PTFR_NativeSupportU7/NativeSupportU7.reds';text=src.read_text()
    assert text.count('.SetFact(')==1 and 'SetFact(StringToName("PTFRU7_Support_"+s),v)' in text
    for forbidden in ('.ExecuteNode(','.GiveReward(','.SetEntryState(','StartQuest','this.Set("CreditDone"'):
        assert forbidden not in text
    for required in ('GigDataB7.Index("sts_hey_rey_06")>=0','epoch!=this.epoch','CyberwarePolicy.Safe(p)','this.Own("Request")!=0 || this.Own("Issued")!=0','this.UnusedPilot()','this.IdleProtocol()'):
        assert required in text
    old=(ROOT/'redscript/PTFR_NativePadreU6/NativePadreU6.reds').read_text()
    new=(ROOT/'build/NativeSupportU7/NativePadreU6.reds').read_text()
    insert='\n    return "U6 standalone entry superseded while U7 is installed. Use NativeSupportU7 on the original pre-U6/U4 snapshot; existing owners are not migrated.";\n  }\n  private func LegacyStartUnused(confirmation: String) -> String {'
    assert new.replace(insert,'')==old and new.count(insert)==1
    assert m['packed_readback'] and m['collision']['collision_free'] and len(m['resources'])==4
    # Compile against full installed environment in workspace cache, not game cache.
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
    names=('PTFR_NativeSupportU7','PTFR_NativePadreU6','PTFR_NativeJeopardyU4','PTFR_NativeReuseU1','PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3')
    for name in names:args+=['-s',str(stage/'scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=120);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-4500:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-4500:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90);assert run.returncode==0
    ct=flat.read_text(encoding='utf-8-sig')
    for s in ('class PTFR.ActivityStateR3.NativeSupportU7','OriginalLifetimeClosed','IdleProtocol','U6 standalone entry superseded','Native Jeopardy U4','Native reuse U3 Shark','TemporaryHide(true);'):assert s in ct,s
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    for f in m['files']:
        assert sha(ROOT/f['source'])==f['sha256']
        if f['predecessor']:assert sha(GAME/f['relative'])==f['predecessor']
        else:assert not (GAME/f['relative']).exists()
    result=dict(status='PASS_U7_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(__file__),wrapper_delta_exact=True,entry_predicate_cases=cases,negative_graph_variants=len(mutants),cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected,source_pins=pins,native_engine_proof=False,scope='Native Padre-only reset parent/initializer slice plus isolated original Jeopardy completion credit; no other contacts, custom reward or historical credit replay.')
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
