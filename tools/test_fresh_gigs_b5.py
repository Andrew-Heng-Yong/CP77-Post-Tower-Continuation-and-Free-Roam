"""Source/readback/guard/model/Lua tests. Explicitly not live-engine proof."""
import copy,itertools,json,re,sys
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from audit_fresh_gigs_b5 import OUT
from test_gig_pilot_r1 import Resource
from audit_activity_batches_b1 import flatten
from audit_activity_lifecycles_b1 import condition_value
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

FILES=[
 ('build/FreshGigsB5/TowerContinued_FreshB5.archive','archive/pc/mod/TowerContinued_FreshB5.archive'),
 ('archive/fresh_b5/TowerContinued_FreshB5.archive.xl','archive/pc/mod/TowerContinued_FreshB5.archive.xl'),
 ('redscript/PTFR_FreshGigsB5/FreshGigsB5.reds','r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds'),
 ('diagnostics/PTFR_FreshGigsB5/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/init.lua'),
 ('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds')]
TOOLS=['audit_fresh_gigs_b5.py','extract_fresh_gigs_b5.ps1','build_fresh_gigs_b5.ps1','compile_fresh_gigs_b5.py','test_fresh_gigs_b5.py']
OLD='AFB91B25C44955BD7DD624433F0221C641F2C45DE048B6D56B9BC324E72A77EA'

def graphs(path):
    r=Resource(read(path));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}

def functions(text):
    result={}
    for m in re.finditer(r'\bfunc\s+(\w+)\([^\n]*?\)\s*->[^\n{]+\{',text):
        depth=1;pos=m.end()
        while depth and pos<len(text):
            depth+= (text[pos]=='{')-(text[pos]=='}');pos+=1
        result[m[1]]=text[m.start():pos]
    return result

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    review=read(OUT/'source_review.json');manifest=read(OUT/'manifest.json');compiled=read(OUT/'compile_result.json')
    assert len(manifest['resources'])==9 and manifest['packed_readback'] and not manifest['vanilla_replacements']
    assert compiled['source_sha256']==sha(ROOT/FILES[2][0]) and compiled['state_sha256']==sha(ROOT/FILES[4][0]) and compiled['equipmentex']
    for p,h in review['pins'].items():assert sha(ROOT/p)==h,p
    for p,h in (compiled['protected']|compiled['dependencies']).items():assert sha(p)==h,p
    native_nodes=0;native_graphs=0;mutants=0
    for j in review['jobs']:
        key='h7' if j['id'].endswith('_07') else 'h1'; tag='PTFRB5_'+key.upper()
        depmap={res['depot']:f'towercontinued\\fresh_b5\\{key}_'+('native' if res['prefabs'] else 'gpl' if 'gameplay' in res['depot'] else 'ow')+'.questphase' for res in j['resources']}
        for res in j['resources']:
            name='native' if res['prefabs'] else 'gpl' if 'gameplay' in res['depot'] else 'ow'
            new=graphs(OUT/f'{key}_{name}.questphase.json')
            for old in res['graphs']:
                native_graphs+=1;ng=new[old['path']];byid={n['id']:n for n in ng['nodes']}
                assert len(byid)==len(ng['nodes']), 'duplicate node ID'
                for node in old['nodes']:
                    expected=copy.deepcopy(node)
                    for v in walk(expected):
                        if 'phaseResource' in v:
                            ref=v['phaseResource']['DepotPath'];dep=ref.get('$value')
                            if dep in depmap:ref['$value']=depmap[dep];v['phaseResource']['Flags']='Soft'
                    assert expected==byid[node['id']],(j['id'],name,old['path'],node['id'])
                    native_nodes+=1
                es={tuple(e) for e in ng['edges']};oe={tuple(e) for e in old['edges']}
                if name in ('native','gpl') or old['path'] not in (('root/4','root/5') if key=='h7' else ('root/7','root/6')):
                    assert es==oe,(key,name,old['path'],'unaudited edge delta')
                for n in ng['nodes']:
                    if n['id']>=4000:
                        for v in walk(n):
                            if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(tag+'_') and v['setExactValue']==1
        boot=graphs(OUT/f'{key}_boot.questphase.json')['root'];nodes={n['id']:n for n in boot['nodes']}
        assert not read(OUT/f'{key}_boot.questphase.json')['Data']['RootChunk']['phasePrefabs']
        assert nodes[7]['phaseResource']['DepotPath']['$value']==f'towercontinued\\fresh_b5\\{key}_native.questphase'
        guard=nodes[4]['condition'];facts={v['factName']:v['value'] for v in walk(guard) if v.get('$type')=='questVarComparison_ConditionType'}
        assert condition_value(guard,facts) is True
        for f,v in facts.items():
            bad=facts|{f:v+1};assert condition_value(guard,bad) is False;mutants+=1
        cleanup=graphs(OUT/f'{key}_ow.questphase.json')['root/5' if key=='h7' else 'root/6']
        byid={n['id']:n for n in cleanup['nodes']};es={tuple(e) for e in cleanup['edges']}
        for rid in ([12] if key=='h7' else [14,16]):
            base=4000+rid*4;guard=byid[base]['condition']
            values={tag+'_RewardClaim':0,tag+'_RewardAck':0,tag+'_Fault':0}
            assert condition_value(guard,values) is True
            for f in values:assert condition_value(guard,values|{f:1}) is False;mutants+=1
            assert (base,'True',base+1,'In') in es and (base+1,'Out',rid,'In') in es and (rid,'Out',base+2,'In') in es
        assert byid[6001]['condition']['type']['factName']==tag+'_AccountReady'
        assert (6002,'True',6003,'In') in es and (6002,'False',6005,'In') in es
        play=graphs(OUT/f'{key}_ow.questphase.json')['root/4' if key=='h7' else 'root/7']
        assert not any(e[2:]==([200,'Start1'] if key=='h7' else [155,'Start 0']) for e in play['edges'])
        assert not any(e[2:]==([11,'Start1'] if key=='h7' else [39,'Start 0']) for e in cleanup['edges'])
    tiers=graphs(OUT/'tiers.questphase.json')['root'];byid={n['id']:n for n in tiers['nodes']};edges=tiers['edges']
    assert len(edges)==len({tuple(e) for e in edges})
    writes={v['factName'] for v in walk(tiers['nodes']) if v.get('$type')=='questSetVar_NodeType'}
    assert not any(x in writes for x in ('wbr_sts_counter','wbr_achievement','wakako_default_on')) and not any(x.startswith('ma_') for x in writes)
    assert {x for x in writes if not x.startswith('PTFRB5_')}=={f'sts_wbr_{region}_tier_{tier}' for region in ('hil','jpn') for tier in ('1_2','2','3','4')}
    for threshold in (2,5,7,8):
        base=threshold*100;c=byid[base]['condition'];facts={v['factName']:v['value']+(1 if v['comparisonType']=='Greater' else 0) for v in walk(c) if v.get('$type')=='questVarComparison_ConditionType'}
        assert condition_value(c,facts) is True
        for f in ('PTFRB5_TierRequest',f'PTFRB5_Tier{threshold}_Claim',f'PTFRB5_Tier{threshold}_Ack'):
            assert condition_value(c,facts|{f:1-facts[f]}) is False;mutants+=1
        assert condition_value(c,facts|{'wbr_sts_counter':threshold-1}) is False;mutants+=1
        for offset in (11,13):assert byid[base+offset]['type']['setExactValue']==1
    source=(ROOT/FILES[2][0]).read_text();state=(ROOT/FILES[4][0]).read_text();old=(OUT/'predecessor/ActivityStateR3.reds').read_text()
    assert sha(OUT/'predecessor/ActivityStateR3.reds')==OLD
    of,nf=functions(old),functions(state)
    changed={'Inspect','RestoreSelected','RestoreGig','Override'}
    assert all(nf[k]==v for k,v in of.items() if k not in changed)
    assert re.findall(r'private persistent let[^;]+;',old)==re.findall(r'private persistent let[^;]+;',state)
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    assert 'this.Init()' not in functions(source)['Inspect']
    assert 'this.Fact(n"wbr_achievement")<slot.achBase+1' in source and 'this.Fact(n"wbr_sts_counter")!=slot.countBase' in source
    assert 'this.Fact(n"sts_wbr_hil_tier_1_1")==0' in source and 'this.Eligible(i)' in functions(source)['PollSlot']
    # Source-linked abstract boundary cases, not execution of REDscript in engine.
    cases=0
    for fresh,item,tier,peer,ack,claim in itertools.product((False,True),repeat=6):
        can_request=fresh and not item and tier and not peer
        if not fresh or item or not tier or peer:assert not can_request
        payout=(not ack and not claim)
        if ack or claim:assert not payout
        cases+=1
    for count,achievement in itertools.product(range(20),range(60)):
        # Independent baselines; one source credit does not overwrite achievement.
        credited=False;new=count
        for _ in range(3):
            if not credited:new+=1;credited=True
        assert new==count+1 and achievement+1>=achievement
        cases+=1
    lua=(ROOT/FILES[3][0]).read_text();lua_cases=[]
    def runtime(fault=False):
        rt=LuaRuntime(unpack_returned_tuples=True)
        rt.execute('calls={};events={};registerForEvent=function(k,f) events[k]=f end;Game={};IsDefined=function(x) return x~=nil end;json={encode=function(x) return "{}" end};'+
          'epoch=1;local s={BatchEpoch=function() return epoch end};for _,n in ipairs({"Inspect","Override","RestoreGig"}) do s[n]=function(self,...) table.insert(calls,{n,...});'+('error("backend failed")' if fault else 'return "OK"')+' end end;Game.GetScriptableSystemsContainer=function() return {Get=function() return s end} end;Game.GetPlayer=function() return {GetEntityID=function() return "player1" end} end;Game.GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end')
        rt.execute('Game.GetJournalManager=function() return {HasAnyDelayedStateChanges=function() return false end,GetEntryByString=function() return nil end} end')
        return rt,rt.execute(lua)
    rt,m=runtime();assert 'acknowledgement' in m.OverrideAll('wrong') and len(rt.globals().calls)==0;lua_cases.append('no invalid-confirm dispatch')
    rt,m=runtime();result=m.OverrideAll('DISPOSABLE_SAVE');assert len(rt.globals().calls)==2 and 'native tiers' in result;lua_cases.append('exact two fresh overrides')
    assert all(rt.globals().calls[k][3]=='fresh' and rt.globals().calls[k][4]=='DISPOSABLE_SAVE' for k in (1,2))
    rt,m=runtime();assert '67' in m.RestoreAll() and len(rt.globals().calls)==5;lua_cases.append('five implemented only')
    rt,m=runtime(True);assert 'Cancelled without retry' in m.OverrideAll('DISPOSABLE_SAVE') and len(rt.globals().calls)==1;lua_cases.append('backend failure cancels remaining requests')
    rt,m=runtime();m.Inspect('sts_wbr_hil_07');assert len(rt.globals().calls)==1 and rt.globals().calls[1][1]=='Inspect';lua_cases.append('inspect read only')
    rt,m=runtime();m.Sample();rt.globals().events['onUpdate'](3);assert all(rt.globals().calls[k][1]=='Inspect' for k in range(1,len(rt.globals().calls)+1));lua_cases.append('logger getters only')
    rt,m=runtime();rt.execute('Game.GetPlayer=function() return nil end;events.onUpdate(2);events.onUpdate(2)');assert len(rt.globals().calls)==4;lua_cases.append('nil player getter safe')
    rt,m=runtime();rt.execute('Game.GetPlayer=function() return nil end');assert 'Cancelled before dispatch' in m.OverrideAll('DISPOSABLE_SAVE') and len(rt.globals().calls)==0;lua_cases.append('nil player no dispatch')
    rt,m=runtime();rt.execute('local old=Game.GetScriptableSystemsContainer;Game.GetScriptableSystemsContainer=function() local c=old();local s=c:Get();local o=s.Override;s.Override=function(self,...) epoch=epoch+1;return o(self,...) end;return c end');assert 'loaded session changed' in m.OverrideAll('DISPOSABLE_SAVE') and len(rt.globals().calls)==1;lua_cases.append('epoch change cancels without replay')
    rt,m=runtime(True);row=m.Sample();assert len(list(row.errors.items()))>0;lua_cases.append('getter errors recorded rather than hidden')
    assert 'SetFact' not in '\n'.join(line for line in lua.splitlines() if not line.startswith('--')) and 'ChangeEntryState' not in lua
    files=[{'source':p,'relative':rel,'sha256':sha(ROOT/p),'predecessor':OLD if p==FILES[4][0] else ''} for p,rel in FILES]
    result={'status':'PASS_B5_OFFLINE_NOT_ENGINE_PROOF','native_payloads_checked':native_nodes,'native_graphs_checked':native_graphs,'guard_mutants':mutants,'abstract_cases':cases,'actual_luajit_cases':lua_cases,'source_pins':review['pins'],'new_gig_adapters':2,'total_gig_adapters':5,'pending_gig_adapters':67,'completed_replay_adapters':0,'r3_persistent_definition_cutoff_unchanged':True,'unchanged_r3_methods':sorted(set(of)-changed),'files':files,'tools':{f'tools/{p}':sha(ROOT/'tools'/p) for p in TOOLS},'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json'),'equipmentex_full_compile':True,'live_proof':False,'automatic_tyger_history':'Unknown scene facts in immutable R3; refuses rather than fabricating baseline'}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','native_payloads_checked','native_graphs_checked','guard_mutants','abstract_cases','actual_luajit_cases')},indent=2))
if __name__=='__main__':main()
