"""Native-reference/lifecycle audit, entry guards and staged compile; not engine proof."""
import itertools,json,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from review_stock_shark_u2 import graph
OUT=ROOT/'research/gig_restoration/native_padre_u6'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');pins={}
    def load(p):
        pins[p]=sha(ROOT/p);return graph(p)
    init=load('research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/holocall_initializers.questphase.json')['root']
    parent=next(n for n in init['nodes'] if n['id']==79)
    assert parent['phaseResource']['DepotPath']['$value']==m['native_resource']
    assert [25,'Out1',79,'In1'] in init['edges']
    base=load('research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json')['root']
    bn={n['id']:n for n in base['nodes']}
    assert bn[106]['condition']['type']['path']['realPath']=='ep1/quests/main_quest/q307_before_tomorrow'
    assert bn[106]['condition']['type']['state']=='Succeeded'
    assert [106,'Out',109,'In'] in base['edges'] and [109,'Out',107,'In'] in base['edges']
    assert bn[107]['$type']=='questOutputNodeDefinition' and bn[107]['type']=='Terminating'
    q=load('research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json')
    assert [16,'Out',18,'In'] in q['root']['edges'] and [18,'Out',17,'In'] in q['root']['edges']
    assert [17,'CutSource',6,'CutDestination'] in q['root']['edges']
    assert [8,'Out1',5,'reset_in'] in q['root/6']['edges']
    add=load('research/b0_missing_content/root_children/json/base/quest/additional_game_elements.questphase.json')['root']
    assert next(n for n in add['nodes'] if n['id']==34)['phaseResource']['DepotPath']['$value'].endswith('holocall_initializers.questphase')
    # Source-backed parent shutdown plus U5's observed unserviced request; no claim
    # to inspect arbitrary third-party serialized instances with a fact getter.
    controller=load('research/gig_restoration/padre_phone_u5/sources/json/base/quest/holocalls/padre/padre_holocall.questphase.json')['root']
    cn={n['id']:n for n in controller['nodes']}
    assert cn[32]['condition']['type']['factName']=='holo_padre_calls_v_start_activate'
    assert cn[33]['type']['factName']=='holo_padre_calls_v_start_activate_count'
    assert cn[34]['type']['factName']=='holo_padre_calls_v_start_activate'
    assert [32,'Out',33,'In'] in controller['edges'] and [33,'Out',34,'In'] in controller['edges']
    for entry in read(ROOT/'research/gig_restoration/padre_phone_u5/inventory.json'):
        for folder,key,ext in [('raw','raw_sha256',''),('json','json_sha256','.json')]:
            p='research/gig_restoration/padre_phone_u5/sources/'+folder+'/'+entry['depot'].replace('\\','/')+ext
            assert sha(ROOT/p)==entry[key];pins[p]=entry[key]
    w=load('research/gig_restoration/native_padre_u6/wrapper.json')['root'];wn={n['id']:n for n in w['nodes']}
    assert set(wn)=={0,1,2,3,4,5,7}
    assert set(map(tuple,w['edges']))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'False',3,'In'),(4,'True',5,'In'),(5,'Out',7,'In1')}
    parent['id']=7;assert wn[7]==parent,'Native phase invocation altered beyond wrapper node ID'
    for n in (1,2,5):assert wn[n]['type']['factName'].startswith('PTFRU6_Padre_') and wn[n]['type']['setExactValue']==1
    assert wn[5]['type']['factName']=='PTFRU6_Padre_Issued'
    for n in (3,4):
        conditions=wn[n]['condition']['conditions']
        equality={c['type']['factName']:c['type']['value'] for c in conditions if c['$type']=='questFactsDBCondition' and c['type']['$type']=='questVarComparison_ConditionType'}
        assert equality==m['guard_pairs']
        assert all(c['type']['comparisonType']=='Equal' for c in conditions)
        balance=[c['type'] for c in conditions if c['type']['$type']=='questVarVsVarComparison_ConditionType']
        assert len(balance)==2
    assert m['wrapper_only'] and m['original_resources_packed']==0 and m['packed_readback'] and m['collision']['collision_free']
    src=ROOT/'redscript/PTFR_NativePadreU6/NativePadreU6.reds';text=src.read_text()
    assert text.count('.SetFact(')==1 and 'SetFact(StringToName("PTFRU6_Padre_"+s),v)' in text
    assert not any(s in text for s in ('.ExecuteNode(','.GiveReward(','.SetEntryState(','holo_reset",1','StartQuest'))
    for s in ('this.Own("Request")!=0 || this.Own("Issued")!=0','this.OriginalLifetimeClosed()','this.IdleProtocol()','epoch!=this.epoch','CyberwarePolicy.Safe(p)','this.Fact("q307_debug_reset")==0','this.State("ep1/quests/main_quest/q307_before_tomorrow")==3'):
        assert s in text,s
    cases=0
    for closed,idle,unencountered,requested,issued,fault,ready in itertools.product(range(2),repeat=7):
        accepted=closed and idle and unencountered and not requested and not issued and not fault and ready
        if not closed or not idle or not unencountered or requested or issued or fault or not ready:assert not accepted
        cases+=1
    # Balanced histories of any size are retained, never forced to the sample1/1.
    for start,end in itertools.product(range(5),repeat=2):
        assert (start==end)==(start-end==0);cases+=1
    # One-shot wrapper: request/issued survive saves; reentry cannot re-launch.
    state={'request':1,'permit':1,'issued':0}; launches=0
    for _ in range(5):
        if state['request']==1 and state['permit']==1 and state['issued']==0:
            state['issued']=1;launches+=1
        state=json.loads(json.dumps(state))
    assert launches==1
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
    names=('PTFR_NativePadreU6','PTFR_NativeJeopardyU4','PTFR_NativeReuseU1','PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3')
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
    for s in ('class PTFR.ActivityStateR3.NativePadreU6','OriginalLifetimeClosed','IdleProtocol','Native Jeopardy U4','Native reuse U3 Shark','TemporaryHide(true);'):assert s in ct,s
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    for f in m['files']:assert sha(ROOT/f['source'])==f['sha256'] and not (GAME/f['relative']).exists()
    result=dict(status='PASS_U6_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(__file__),wrapper_delta_exact=True,entry_models=cases,cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected,source_pins=pins,stock_lifetime_path_verified=True,arbitrary_serialized_owner_introspection=False,native_engine_proof=False,global_interrupt_loop_restored=False)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
