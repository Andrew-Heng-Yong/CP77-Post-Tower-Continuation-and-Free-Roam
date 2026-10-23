"""Exact source slices, interfaces and actual script compilation; not engine tests."""
import copy,itertools,json,re,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha
from review_stock_shark_u2 import graph
OUT=ROOT/'research/gig_restoration/gig_phone_u9'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SRC=OUT/'sources/json'

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');pins=dict(m['source_pins'])
    for p,h in pins.items():assert sha(ROOT/p)==h
    def load(p):
        p=Path(p);p=p if p.is_absolute() else ROOT/p
        pins[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
        return graph(str(p))['root']
    init=load(SRC/'base/quest/holocalls/holocall_initializers.questphase.json')
    orig_cleanup=load(SRC/'base/quest/holocalls/holocall_cleanup.questphase.json')
    source_parent=load('research/b0_missing_content/root_children/json/base/quest/additional_game_elements.questphase.json')
    phone=load(OUT/'fixer_initializer.json');cleanup=load(OUT/'fixer_cleanup.json')
    parent=load(OUT/'fixer_parent.json');wrapper=load(OUT/'support_wrapper.json')
    contacts=['dakota','dino','mr_hands','muamar','padre','reggie','rogue','wakako']
    ids={5,25,50,53,73,75,79,84,86,97,102,107,108,114,115,116,117,118,119,120,124,131,132}
    def exact_nodes(candidate,original,selected,refs={}):
        ns={n['id']:n for n in candidate['nodes']};stock={n['id']:n for n in original['nodes']}
        assert set(ns)==set(selected)
        for i,n in ns.items():
            expected=copy.deepcopy(stock[i])
            if i in refs:expected['phaseResource']['DepotPath']['$value']=refs[i]
            assert n==expected,(i,'stock node payload mismatch')
    def verify_phone(g):
        exact_nodes(g,init,ids,{124:r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'})
        assert sorted(g['edges'])==sorted(e for e in init['edges'] if e[0] in ids and e[2] in ids)
    verify_phone(phone)
    assert next(n for n in phone['nodes'] if n['id']==107)['type']=='Terminating'
    assert len([n for n in phone['nodes'] if n.get('phaseResource',{}).get('DepotPath',{}).get('$value','').endswith('holocall_interrupts.questphase')])==1
    actual_controllers={n['phaseResource']['DepotPath']['$value'] for n in phone['nodes'] if n['id'] in {50,53,73,75,79,84,86,97}}
    assert actual_controllers=={fr'base\quest\holocalls\{c}\{c}_holocall.questphase' for c in contacts}
    exact_nodes(parent,source_parent,{0,34,35},{34:r'towercontinued\gig_phone_u9\fixer_initializer.questphase'})
    parent_edges={(0,'Out',34,'In1'),(34,'reset_out',35,'In1'),(35,'Out1',34,'reset_in')}
    assert set(map(tuple,parent['edges']))==parent_edges and parent_edges.issubset(set(map(tuple,source_parent['edges'])))
    stock={n['id']:n for n in orig_cleanup['nodes']};edges=orig_cleanup['edges']
    contact_nodes={n['id'] for n in stock.values() if n.get('phaseResource',{}).get('DepotPath',{}).get('$value') in {fr'base\quest\holocalls\{c}\{c}_cleanup.questphase' for c in contacts}}
    condition_nodes={e[0] for e in edges if e[1]=='True' and e[2] in contact_nodes}
    assert len(contact_nodes)==len(condition_nodes)==8
    selected={0,1,6,7,423,424,495}|contact_nodes|condition_nodes
    expected_cleanup=[]
    for e in edges:
        if e[0] not in selected:continue
        if e[0]==424:expected_cleanup.append([424,'Out1',6,'In2']);continue
        out=list(e);seen=set()
        while out[2] not in selected:
            assert out[2] not in seen;seen.add(out[2])
            assert stock[out[2]]['$type']=='questConditionNodeDefinition'
            next_edges=[x for x in edges if x[0]==out[2] and x[1]=='False'];assert len(next_edges)==1
            out[2:]=next_edges[0][2:]
        expected_cleanup.append(out)
    def verify_cleanup(g):
        exact_nodes(g,orig_cleanup,selected)
        assert sorted(g['edges'])==sorted(expected_cleanup)
    verify_cleanup(cleanup)
    assert next(n for n in cleanup['nodes'] if n['id']==1)['type']=='Terminating'
    assert stock[7]['condition']['type']['minutes']==1
    assert 504 not in selected and 502 not in selected
    # Project original contact chain against all 256 selected-active patterns.
    # Omitted contacts are inactive because their owners are not restarted.
    def trace(g,active):
        ns={n['id']:n for n in g['nodes']};out=[];current=423;visited=set()
        while current!=424:
            assert current not in visited;visited.add(current)
            n=ns[current]
            if n['$type']=='questConditionNodeDefinition':s='True' if current in active else 'False'
            elif n['$type']=='questPhaseNodeDefinition':
                out.append(current);s=next(e[1] for e in g['edges'] if e[0]==current)
            else:s='Out1'
            follow=[e for e in g['edges'] if e[0]==current and e[1]==s and e[2] not in (7,)]
            assert len(follow)==1,(current,follow);current=follow[0][2]
        return out
    for bits in itertools.product((False,True),repeat=8):
        active={n for n,b in zip(sorted(condition_nodes),bits) if b}
        assert trace(orig_cleanup,active)==trace(cleanup,active)
    # Child interface validation from official definitions, not imagined sockets.
    closure={r'towercontinued\gig_phone_u9\fixer_parent.questphase':parent,r'towercontinued\gig_phone_u9\fixer_initializer.questphase':phone,r'towercontinued\gig_phone_u9\fixer_cleanup.questphase':cleanup}
    for c in contacts:
        for kind in ('holocall','cleanup'):
            depot=fr'base\quest\holocalls\{c}\{c}_{kind}.questphase';closure[depot]=load(SRC/Path(depot+'.json'))
    interrupt=load(SRC/'base/quest/holocalls/holocall_interrupts.questphase.json')
    closure[r'base\quest\holocalls\holocall_interrupts.questphase']=interrupt
    def interfaces(g):
        for n in g['nodes']:
            if n['$type']!='questPhaseNodeDefinition':continue
            child=closure[n['phaseResource']['DepotPath']['$value']]
            ins={x['socketName']['$value'] for x in child['nodes'] if x['$type']=='questInputNodeDefinition'}
            outs={x['socketName']['$value'] for x in child['nodes'] if x['$type']=='questOutputNodeDefinition'}
            for e in g['edges']:
                if e[2]==n['id']:assert e[3] in ins,(n['id'],e,ins)
                if e[0]==n['id']:assert e[1] in outs,(n['id'],e,outs)
    for g in (wrapper,parent,phone,cleanup):interfaces(g)
    wn={n['id']:n for n in wrapper['nodes']};assert set(wn)==set(range(7))
    assert set(map(tuple,wrapper['edges']))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'False',3,'In'),(4,'True',5,'In'),(5,'Out',6,'Input')}
    assert wn[5]['type']['factName']=='PTFRU9_Support_Issued'
    assert wn[3]['condition']==wn[4]['condition']
    def evaluate(c,f):
        if c['$type']=='questLogicalCondition':assert c['operation']=='AND';return all(evaluate(x,f) for x in c['conditions'])
        t=c['type'];assert t['comparisonType']=='Equal'
        return f.get(t['factName'],0)==t['value'] if 'factName' in t else f.get(t['factName1'],0)==f.get(t['factName2'],0)
    conditions=wn[3]['condition']['conditions']
    pairs={c['type']['factName']:c['type']['value'] for c in conditions if 'factName' in c['type']}
    balances={(c['type']['factName1'],c['type']['factName2']) for c in conditions if 'factName1' in c['type']}
    assert pairs==m['guard_pairs'] and balances==set(map(tuple,m['balances']))
    facts=dict(pairs);assert evaluate(wn[3]['condition'],facts);cases=1
    for p in pairs:
        f=dict(facts);f[p]+=1;assert not evaluate(wn[3]['condition'],f);cases+=1
    for a,b in balances:
        for start,end in itertools.product(range(5),repeat=2):
            f=dict(facts);f[a]=start;f[b]=end
            assert evaluate(wn[3]['condition'],f)==(start==end);cases+=1
    # Source lifecycle proof: initializers cease at Tower success, not mere idle.
    base=load('research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json')
    bn={n['id']:n for n in base['nodes']}
    assert bn[107]['type']=='Terminating' and bn[106]['condition']['type']['state']=='Succeeded'
    assert [106,'Out',109,'In'] in base['edges'] and [109,'Out',107,'In'] in base['edges']
    qp='research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json';q=graph(qp)
    assert [17,'CutSource',6,'CutDestination'] in q['root']['edges'] and [18,'Out',17,'In'] in q['root']['edges']
    assert next(n for n in q['root/6']['nodes'] if n['id']==5)['phaseResource']['DepotPath']['$value'].endswith('holocall_initializers.questphase')
    mutants=0
    for original,verify in ((phone,verify_phone),(cleanup,verify_cleanup)):
        for mode in ('delete-edge','wrong-target','payload'):
            bad=copy.deepcopy(original)
            if mode=='delete-edge':bad['edges'].pop()
            elif mode=='wrong-target':bad['edges'][0][2]=65000
            else:bad['nodes'][0]['unsafe']=1
            try:verify(bad)
            except AssertionError:mutants+=1
            else:raise AssertionError('Unsafe graph accepted')
    bad=copy.deepcopy(wrapper);bad['edges'][-1][-1]='In1'
    try:interfaces(bad)
    except AssertionError:mutants+=1
    else:raise AssertionError('Wrong native Input accepted')
    text=(ROOT/'redscript/PTFR_GigPhoneU9/GigPhoneU9.reds').read_text()
    generated=(ROOT/'redscript/PTFR_GigPhoneU9/GigPhoneDataU9.generated.reds').read_text()
    for func,values in [('IdleFacts',m['idle_facts']),('PredecessorFacts',m['predecessor_facts']),('BalanceStarts',[x[0] for x in m['balances']]),('BalanceEnds',[x[1] for x in m['balances']])]:
        body=re.search(r'func '+func+r'\(\).*?return (\[.*?\]);',generated).group(1)
        assert json.loads(body)==values
    assert text.count('.SetFact(')==1 and 'SetFact(StringToName("PTFRU9_Support_"+s),v)' in text
    for bad in ('Set("Issued"','Set("Ready"','.ExecuteNode(','.GiveReward(','.SetEntryState('):assert bad not in text
    for need in ('epoch!=this.epoch','this.LegacyIdle()','this.OriginalLifetimeClosed()','CyberwarePolicy.Safe(p)','this.Own("Request")!=0 || this.Own("Issued")!=0'):assert need in text
    for f in m['files']:assert sha(ROOT/f['source'])==f['sha256'] and not (GAME/f['relative']).exists()
    assert m['packed_readback'] and m['collision']['collision_free'] and len(m['resources'])==4
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()};deps={}
    for n in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/n,cache/n)
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);d=stage/'scripts'/p.relative_to(GAME/'r6/scripts');d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    for f in m['files']:
        if f['relative'].endswith('.reds'):
            d=stage/'scripts'/Path(f['relative']).relative_to('r6/scripts');d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f['source'],d)
    helper=ROOT/'redscript/PTFR_GigBatchU9/EntryInterlocks.reds';deps[str(helper)]=sha(helper)
    d=stage/'scripts/PTFR_GigBatchU9/EntryInterlocks.reds';d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(helper,d)
    assert text.count('GigBatchLockU9.Ready()')==3
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    # Headless compiler first, so an error cannot summon the engine's dialog.
    args=[str(cli),'compile']
    # EquipmentEx uses an engine-supported temporary expression rejected by the
    # separate CLI compiler; full SCC below still checks the actual whole set.
    for p in (stage/'scripts').iterdir():
        if p.is_dir() and p.name.startswith('PTFR_'):args+=['-s',str(p)]
    for p in plugins:args+=['-s',p]
    args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    r=subprocess.run(args,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert r.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n',encoding='utf-8');compiled=cache/'compiled.redscripts'
    r=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=r.stdout+r.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert r.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';r=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90);assert r.returncode==0
    flattext=flat.read_text(encoding='utf-8-sig');assert 'class PTFR.ActivityStateR3.GigPhoneU9' in flattext and 'class PTFR.ActivityStateR3.GigPhoneDataU9' in flattext
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    result=dict(status='PASS_U9_PHONE_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(__file__),source_pins=pins,entry_predicate_cases=cases,cleanup_pattern_models=256,negative_graph_variants=mutants,exact_native_node_payloads=True,scoped_cleanup_edges=True,interfaces=True,cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected,native_engine_proof=False,cleanup_scope='Only selected controllers; unrelated-contact False branches bypassed, terminal dead EP1 reset handshake omitted; original condition predicates, per-contact cleanup, timeout and terminating output preserved.')
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])

if __name__=='__main__':main()
