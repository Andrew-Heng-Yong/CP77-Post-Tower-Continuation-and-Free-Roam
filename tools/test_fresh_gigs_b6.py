"""Native payload/edge comparisons and source-linked models, not engine proof."""
import itertools,json,re,sys
from catalog_gig_rollout_r2 import ROOT,read,sha
from test_gig_pilot_r1 import Resource,reachable
from audit_activity_batches_b1 import flatten
from test_fresh_gigs_b5_1 import body,normalize
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
OUT=ROOT/'research/gig_restoration/fresh_b6'

def graph_checks():
    review=read(OUT/'source_review.json');count=0;graphs=0
    for x in review['resources']:
        name='native' if x['prefabs'] else 'gpl' if '_combat.' in x['depot'] else 'ow'
        o=Resource(read(ROOT/x['json']));p=Resource(read(OUT/f'j2_{name}.questphase.json'))
        og={g['path']:g for g in flatten(o,o.obj['Data']['RootChunk'])};pg={g['path']:g for g in flatten(p,p.obj['Data']['RootChunk'])}
        assert set(og)==set(pg)
        assert o.obj['Data']['RootChunk']['phasePrefabs']==p.obj['Data']['RootChunk']['phasePrefabs']
        for path,g in og.items():
            on={n['id']:n for n in g['nodes']};pn={n['id']:n for n in pg[path]['nodes']};assert set(on)<=set(pn)
            for ident,n in on.items():
                a=dict(n);b=dict(pn[ident])
                if 'phaseResource' in a and a['phaseResource']['DepotPath']['$value'] in [z['depot'] for z in review['resources']]:
                    dep=a.pop('phaseResource');patched=b.pop('phaseResource');assert patched['DepotPath']['$value'].startswith('towercontinued\\fresh_b6\\')
                assert a==b,(name,path,ident,'native payload changed');count+=1
            oe={tuple(e) for e in g['edges']};pe={tuple(e) for e in pg[path]['edges']}
            if name=='ow' and path=='root/3':
                assert pe=={(f,s,112 if t==170 and d=='Start 0' else t,'Active' if t==170 and d=='Start 0' else d) for f,s,t,d in oe}
                assert 170 not in reachable(pe,0),'shared prebrief reachable'
                assert len(pn)==len(on)
            elif name=='ow' and path=='root/6':
                expected={(f,s,59 if t==46 and d=='Start 0' else t,'Active' if t==46 and d=='Start 0' else d) for f,s,t,d in oe}
                for ident in (33,36):
                    base=4000+ident*4 if ident==33 else 6000
                    expected={(f,s,base if t==ident else t,d) for f,s,t,d in expected if f!=ident}
                expected|={(4132,'True',4133,'In'),(4133,'Out',33,'In'),(33,'Out',4134,'In'),(4132,'False',4135,'In'),(4134,'Out',34,'In')}
                expected|={(6000,'Out',6001,'In'),(6001,'Out',6002,'In'),(6002,'True',6003,'In'),(6003,'Out',36,'In'),(36,'Out',6004,'In'),(6002,'False',6005,'In'),(6004,'Out',50,'In')}
                assert pe==expected,('cleanup edges',pe-expected,expected-pe)
                assert 46 not in reachable(pe,0),'shared debrief reachable'
                assert set(pn)-set(on)=={4132,4133,4134,4135,6000,6001,6002,6003,6004,6005}
                assert pn[6002]['condition']['conditions'][-2:]==[{'$type':'questFactsDBCondition','type':{'$type':'questVarVsVarComparison_ConditionType','comparisonType':'Equal','factName1':'PTFRB6_J2_CountBase','factName2':'wbr_sts_counter'}},{'$type':'questFactsDBCondition','type':{'$type':'questVarVsVarComparison_ConditionType','comparisonType':'Equal','factName1':'PTFRB6_J2_AchBase','factName2':'wbr_achievement'}}]
            else:assert oe==pe and set(on)==set(pn),(name,path,'unexpected edges/nodes')
            graphs+=1
    boot=Resource(read(OUT/'j2_boot.questphase.json'));root=boot.obj['Data']['RootChunk'];bn=boot.nodes(root['graph']);be=boot.edges(root['graph'])
    assert not root['phasePrefabs'] and not root['inplacePhases']
    assert be=={(0,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In'),(5,'Out',7,'In1'),(7,'Out1',6,'In'),(6,'Out',1,'In')}
    assert bn[4]['$type']=='questPauseConditionNodeDefinition' and bn[7]['phaseResource']['DepotPath']['$value']=='towercontinued\\fresh_b6\\j2_native.questphase'
    parent=Resource(read(ROOT/review['parent']['binding']['source']));child=parent.nodes(parent.obj['Data']['RootChunk']['graph'])[7]
    a=parent.payload(child);b=boot.payload(bn[7]);a.pop('phaseResource');b.pop('phaseResource');assert a==b,'boot binding changed beyond owned resource'
    xl=(ROOT/'build/FreshGigsB6/TowerContinued_FreshB6.archive.xl').read_text()
    assert xl=='quest:\n  phases:\n    - path: towercontinued\\fresh_b6\\j2_boot.questphase\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out\n'
    assert read(OUT/'manifest.json')['packed_readback']
    return count,graphs

def main():
    assert not (OUT/'install_receipt.json').exists()
    c=read(OUT/'compile_result.json');assert c['equipmentex'] and c['persistence_readback']
    for p,h in c['sources'].items():assert sha(ROOT/p)==h
    for p,h in (c['protected']|c['dependencies']).items():assert sha(p)==h
    old=OUT/'predecessor';b5=(ROOT/'redscript/PTFR_FreshGigsB5/FreshGigsB5.reds').read_text();old5=(old/'FreshGigsB5.reds').read_text()
    assert sha(old/'FreshGigsB5.reds')=='B171430B760F99902A2815139D31BBDA3EF0865F557608B52582AC502ECC7418'
    assert sha(old/'ActivityStateR3.reds')=='6B3D48216763BA4BD2FD61B4A3E1D6948733B606B850A5694F801B30198ECCE9'
    for n in set(re.findall(r'\bfunc (\w+)\(',old5))-{'OtherOwnerIdle'}:assert normalize(body(b5,n))==normalize(body(old5,n)),n
    assert '"japantown/"' not in b5 and 'this.Fact(n"PTFRB6_J2_Request")!=0 && this.Fact(n"PTFRB6_J2_OwnerFinished")!=1' in b5
    state=(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds').read_text();olds=(old/'ActivityStateR3.reds').read_text()
    for n in set(re.findall(r'\bfunc (\w+)\(',olds))-{'Inspect','RestoreGig','RestoreSelected','Override'}:assert normalize(body(state,n))==normalize(body(olds,n)),n
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    b6=(ROOT/'redscript/PTFR_FreshGigsB6/FreshGigsB6.reds').read_text();m6=(ROOT/'redscript/PTFR_GigMarkersM6/GigMarkersM6.reds').read_text()
    assert 'private persistent let slot: FreshSlotB5;' in b6 and 'ArrayPush(this.slots' not in b6
    assert 'this.Fact(n"sts_wbr_jpn_tier_1_2")>0 || (this.Fact(n"sts_wbr_jpn_tier_1")>0 && this.Fact(n"sts_wbr_jpn_tier_1_1")==0)' in b6
    native_count,graphs=graph_checks()
    # Predicate translated from the actual pure source expression.
    rt=LuaRuntime(unpack_returned_tuples=True)
    expr=re.search(r'return (.*?);',body(m6,'Want'))[1].replace('&&',' and ')
    want=rt.execute('return function(tower,request,started,finished,fault,root,poi) return '+expr+' end')
    cases=0
    for args in itertools.product((False,True),(0,1,2),(0,1,2),(0,1,2),(0,1,2),(-1,1,2,3,4),(-1,1,2,3,4)):
        assert want(*args)==(args[0] and args[1:]==(1,1,0,0,1,2));cases+=1
    assert not re.search(r'SetFact|ChangeEntryState|TrackEntry|DebugDiscover|DebugShow',m6)
    assert 'GigMarkerDataM6' in body(m6,'Purge') and 'GigMarkersM6.Index(d.id)>=0' in body(m6,'Purge')
    assert 'GetJournalQuestPathHash()==Cast<Uint32>(jm.GetEntryHash(quest))' in m6 and 'this.Own(i,"Request")' in m6
    assert 'private persistent' not in m6 and 'epoch!=this.epoch' in m6
    assert 'this.Usable(i,p)' in m6 and 'AbsF(p.X-target.X)<100.0 && AbsF(p.Y-target.Y)<100.0' in m6
    # Session handoffs: one fallback, preserve native ownership, no stored IDs.
    transitions=0
    for sequence in itertools.product(('far','native','active','complete','notTower'),repeat=5):
        marker=False;attempt=False;created=removed=0
        for value in sequence:
            desired=value=='far';native=value=='native'
            if not desired or native:
                if marker:removed+=1;marker=False
                if native:attempt=False
            elif not marker and not attempt:marker=True;attempt=True;created+=1
            assert created-removed==int(marker);transitions+=1
    # Accounting from arbitrary current baselines, not sample-specific totals.
    accounts=0
    for base,ach,growth,acked in itertools.product((0,1,4,200), (0,3,500), (0,1,25),(False,True)):
        current=base+int(acked);achievement=ach+1+growth
        writes=0
        if not acked and current==base and achievement>=ach+1:current=base+1;acked=True;writes+=1
        if not acked and current==base:current=base+1;writes+=1
        assert current==base+1 and writes<=1;accounts+=1
    assert 'if this.Own("AccountAck")==1 && !this.slot.counterAck {' in b6
    assert 'this.Fact(n"wbr_sts_counter")!=this.slot.countBase' in b6
    # Validate positions against preserved official streamingsector decoding.
    rows=read(OUT/'world_lookup.json');h7=read(ROOT/'research/gig_restoration/fresh_b5/tyger_world_lookup.json')
    for x,y,z,suffix,source in [(-75.2505112,-324.191193,5.60545921,'hil_07_tr_quest',h7),(-8.7444849,25.3564377,14.8524351,'hil_01_tr_building',rows),(-247.972321,1639.41895,41.1923256,'jpn_02_wp_teleport',rows)]:
        assert any(r.get('reference','').endswith(suffix) and (r['x'],r['y'],r['z'])==(x,y,z) for r in source)
    lua=(ROOT/'diagnostics/PTFR_FreshGigsB6/init.lua').read_text();lua_cases=[]
    def runtime():
        l=LuaRuntime(unpack_returned_tuples=True);l.execute('''calls={};events={};epoch=1;hash="18446744073709550001ULL";IsDefined=function(v) return v~=nil end;registerForEvent=function(n,f) events[n]=f end;Game={};local s={BatchEpoch=function() return epoch end}
        s.Override=function(self,...) table.insert(calls,{...});if bump then epoch=epoch+1 end;if change then hash="2ULL" end;if fail then error("backend") end;return "OK" end
        s.Inspect=function(self,id) return "GETTER" end;Game.GetScriptableSystemsContainer=function() return {Get=function() return s end} end;Game.GetPlayer=function() if missing then return nil end;return {GetEntityID=function() return {hash=hash} end} end;Game.GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end''');return l,l.execute(lua)
    l,m=runtime();assert 'Refused' in m.OverrideAll('bad') and len(l.globals().calls)==0;lua_cases.append('confirmation')
    l,m=runtime();assert 'Cancelled' not in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls)==3;lua_cases.append('stable boxed IDs three once')
    for flag in ('bump','change','fail'):
        l,m=runtime();l.globals()[flag]=True;assert 'Cancelled without retry' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls)==1;lua_cases.append(flag)
    l,m=runtime();l.globals().missing=True;assert 'Cancelled before' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls)==0;lua_cases.append('missing player')
    l,m=runtime();l.globals().hash=None;assert 'entity hash missing' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls)==0;lua_cases.append('missing hash')
    # No mutation bridge disguised as a getter.
    assert not re.search(r'SetFact|ChangeEntryState',lua)
    files=[]
    for source,relative,pred in [
      ('build/FreshGigsB6/TowerContinued_FreshB6.archive','archive/pc/mod/TowerContinued_FreshB6.archive',None),
      ('build/FreshGigsB6/TowerContinued_FreshB6.archive.xl','archive/pc/mod/TowerContinued_FreshB6.archive.xl',None),
      ('redscript/PTFR_FreshGigsB6/FreshGigsB6.reds','r6/scripts/PTFR_FreshGigsB6/FreshGigsB6.reds',None),
      ('redscript/PTFR_GigMarkersM6/GigMarkersM6.reds','r6/scripts/PTFR_GigMarkersM6/GigMarkersM6.reds',None),
      ('diagnostics/PTFR_FreshGigsB6/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB6/init.lua',None),
      ('redscript/PTFR_FreshGigsB5/FreshGigsB5.reds','r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds',sha(old/'FreshGigsB5.reds')),
      ('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds',sha(old/'ActivityStateR3.reds'))]:
        files.append(dict(source=source,relative=relative,sha256=sha(ROOT/source),predecessor=pred))
    result=dict(status='PASS_B6_M6_OFFLINE_LIVE_PENDING',files=files,native_nodes_unchanged=native_count,native_graphs_compared=graphs,exact_edges=True,persistence_verified=True,r3_history_capture_schema_unchanged=True,marker_presentation_only=True,marker_predicate_cases=cases,marker_lifecycle_model_transitions=transitions,accounting_model_cases=accounts,lua_cases=lua_cases,new_gig_adapters=1,total_gig_adapters=6,pending_gig_adapters=66,completed_replay_adapters=0,compile_sha256=sha(OUT/'compile_result.json'),manifest_sha256=sha(OUT/'manifest.json'),tools={'tools/'+n:sha(ROOT/'tools'/n) for n in ('build_fresh_gigs_b6.ps1','compile_fresh_gigs_b6.py','test_fresh_gigs_b6.py')})
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k in ('status','native_nodes_unchanged','native_graphs_compared','marker_predicate_cases','lua_cases')}))
if __name__=='__main__':main()
